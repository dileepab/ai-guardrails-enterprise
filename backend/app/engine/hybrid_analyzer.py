from typing import List
from app.models.scan import ScanRequest, ScanResponse, Violation
from app.services.static_analysis import static_analyzer
from app.services.llm_service import llm_service

class HybridAnalyzer:
    async def analyze(self, request: ScanRequest) -> ScanResponse:
        violations: List[Violation] = []
        
        # Define helper for single file processing
        async def _analyze_file(file):
            file_violations = []
            content = file.get("content", "")
            filename = file.get("filename", "")
            
            # 1. Static Analysis
            static_violations = await static_analyzer.scan_content(filename, content, request.config_override)
            file_violations.extend(static_violations)

            # 1.5 License Scanning
            from app.services.license_scanner import LicenseScanner
            if filename.endswith(("package.json", "requirements.txt", "pom.xml")):
                lic_violations = LicenseScanner.scan_content(filename, content)
                # Convert dicts to Violation objects
                for v in lic_violations:
                    file_violations.append(Violation(**v))
            
            # 2. AI Analysis (Needs static context, so must run after static)
            # Only run AI analysis on code files, skip dependency configs to save tokens/time
            if not filename.endswith(("package.json", "requirements.txt", "pom.xml")):
                ai_violations = await llm_service.analyze_diff(filename, content, static_violations)
                file_violations.extend(ai_violations)
            
            return file_violations

        # Run all files in parallel
        import asyncio
        results = await asyncio.gather(*[_analyze_file(f) for f in request.files])
        
        # Flatten results
        for res in results:
            violations.extend(res)

        # Determine Enforcement Mode
        enforcement_mode = "blocking"
        if request.config_override:
            try:
                import yaml
                data = yaml.safe_load(request.config_override)
                enforcement_mode = data.get("enforcement_mode", "blocking").lower()
            except:
                pass

        # Calculate Success
        has_blocking_violations = any(v.severity == "BLOCKING" for v in violations)
        
        if enforcement_mode == "advisory":
            succeeded = True
            summary = f"[ADVISORY] Found {len(violations)} violations."
        else:
            succeeded = not has_blocking_violations
            summary = f"Found {len(violations)} violations."
        
        return ScanResponse(
            status="success",
            violations=violations,
            succeeded=succeeded,
            summary=summary,
            enforcement_mode=enforcement_mode
        )

# Global instance (can be dependency injected)
analyzer = HybridAnalyzer()
