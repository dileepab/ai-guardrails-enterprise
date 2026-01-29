import re

import tempfile
import os
import json
from typing import List
from app.models.scan import Violation
from app.core.rule_engine import rule_engine

class StaticAnalysisService:
    def __init__(self):
        # Load rules from engine
        self.regex_rules = rule_engine.get_rules()

    async def scan_content(self, filename: str, content: str, config_override: str = None) -> List[Violation]:
        violations = []
        
        # 1. Run Regex Checks (with potential override)
        current_rules = rule_engine.get_rules(config_override)
        
        lines = content.split('\n')
        for i, line in enumerate(lines):
            for rule in current_rules:
                if re.search(rule["pattern"], line):
                    violations.append(Violation(
                        rule_id=rule["id"],
                        message=rule["message"],
                        severity=rule["severity"],
                        file_path=filename,
                        line_number=i + 1,
                        category=rule["category"]
                    ))
        
        # 2. Run Bandit (if python)
        if filename.endswith(".py"):
             pass

        return violations

static_analyzer = StaticAnalysisService()
