import google.genai as genai
from google.genai import types
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings
from typing import List, Dict, Any, Optional
from app.models.scan import Violation
import json
import os
import asyncio

# --- Abstract Base Class ---
class BaseLLMClient:
    async def analyze_diff(self, filename: str, content: str, static_violations: List[Violation]) -> List[Violation]:
        raise NotImplementedError

    def _prepare_prompt(self, filename: str, content: str, static_violations: List[Violation]) -> str:
        static_context = "\n".join([f"- Line {v.line_number}: {v.message}" for v in static_violations])
        return f"""
You are an expert Secure Code Reviewer.
Analyze the following code for:
1. Logic Bugs
2. Security Vulnerabilities (STATIC ANALYSIS MISSED THESE)
3. Performance Issues
4. Best Practices

Static Analysis Context:
{static_context}

File: {filename}
Code Content:
```
{content}
```

REQUIREMENT:
- Map every security vulnerability to an **OWASP Top 10** category (e.g., "A03: Injection") and **CWE ID** (e.g., "CWE-89") if applicable.
- **Check for IP/Copyright Risks**: Flag any code that looks like it was copied from well-known open source projects (GPL/AGPL) or contains copyright headers not matching the project.
- If the code seems AI-generated, be extra strict on logic/security.

Return your findings in valid JSON format ONLY (under "findings" key):
{{
  "findings": [
      {{
        "rule_id": "AI-SEC-...",
        "message": "Description...",
        "severity": "WARNING",
        "line_number": 10,
        "suggestion": "Better code...",
        "owasp_category": "A03:2021-Injection",
        "cwe_id": "CWE-89"
      }}
  ]
}}
"""

    def _parse_response(self, text_response: str, filename: str) -> List[Violation]:
        try:
            # Clean up potential markdown formatting
            if text_response.startswith("```json"):
                text_response = text_response.replace("```json", "").replace("```", "")
            
            data = json.loads(text_response)
            findings = data.get("findings", [])
            
            violations = []
            for f in findings:
                violations.append(Violation(
                    rule_id=f.get("rule_id", "AI-GEN"),
                    message=f.get("message"),
                    severity=f.get("severity", "INFO"),
                    file_path=filename,
                    line_number=f.get("line_number", 1),
                    suggestion=f.get("suggestion"),
                    category="AI_REVIEW"
                ))
            return violations
        except Exception as e:
            print(f"LLM Parse Error: {e}")
            return []

    def _mock_analysis(self, filename: str, content: str) -> List[Violation]:
        # Mock findings if no key provided
        violations = []
        if "sleep" in content:
            violations.append(Violation(
                rule_id="AI-PERF-01",
                message="Avoid using sleep() in production code, consider async or event-driven approaches.",
                severity="WARNING",
                file_path=filename,
                line_number=content.find("sleep") + 1,
                suggestion="await asyncio.sleep(1)",
                category="AI_REVIEW"
            ))
        return violations

# --- Gemini Implementation ---
class GeminiClient(BaseLLMClient):
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
             self.client = genai.Client(api_key=self.api_key)

    @retry(
        retry=retry_if_exception_type(Exception), 
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=1, min=2, max=60)
    )
    async def _call_gemini(self, prompt: str):
        # Configure Safety Settings to ALLOW dangerous content analysis
        # (This is a security tool, so we EXPECT to see dangerous code)
        safety_config = [
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE
            ),
        ]

        return await self.client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=safety_config
            )
        )

    async def analyze_diff(self, filename: str, content: str, static_violations: List[Violation]) -> List[Violation]:
        if not self.client:
            return self._mock_analysis(filename, content)
        
        prompt = self._prepare_prompt(filename, content, static_violations)
        try:
            response = await self._call_gemini(prompt)
            return self._parse_response(response.text, filename)
        except Exception as e:
            # Check for RetryError structure from google.api_core
            if "RetryError" in str(type(e)):
                 print(f"Gemini Retry failed. Underlying cause: {getattr(e, 'cause', e)}")
            else:
                 print(f"Gemini Error: {e}")
            return []

# --- OpenAI Implementation ---
class OpenAIClient(BaseLLMClient):
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.client = None
        if self.api_key:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)

    @retry(
        retry=retry_if_exception_type(Exception), 
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60)
    )
    async def _call_openai(self, prompt: str):
        return await self.client.chat.completions.create(
            model="gpt-3.5-turbo", # Or gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

    async def analyze_diff(self, filename: str, content: str, static_violations: List[Violation]) -> List[Violation]:
        if not self.client:
            return self._mock_analysis(filename, content)
        
        prompt = self._prepare_prompt(filename, content, static_violations)
        try:
            response = await self._call_openai(prompt)
            content = response.choices[0].message.content
            return self._parse_response(content, filename)
        except Exception as e:
            print(f"OpenAI Error: {e}")
            return []

# --- Factory / Singleton Wrapper ---
class LLMServiceWrapper:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        print(f"Initializing LLM Service with provider: {self.provider}")
        
        if self.provider == "openai":
            self.client = OpenAIClient()
        else:
            self.client = GeminiClient()

    async def analyze_diff(self, filename: str, content: str, static_violations: List[Violation]) -> List[Violation]:
        return await self.client.analyze_diff(filename, content, static_violations)

# Export the singleton
llm_service = LLMServiceWrapper()
