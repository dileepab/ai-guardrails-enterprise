import yaml
import os
from typing import List, Dict, Any

class RuleEngine:
    def __init__(self, rules_path: str = None):
        self.rules = []
        if rules_path is None:
             # Resolve relative to this file: backend/app/core/rule_engine.py -> backend/rules/default_rules.yaml
             base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
             rules_path = os.path.join(base_dir, "rules", "default_rules.yaml")
        
        self._load_rules(rules_path)

    def _load_rules(self, path: str):
        if not os.path.exists(path):
             print(f"Warning: Rules file not found at {path}")
             return

        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            self.rules = data.get("rules", [])

    def get_rules(self, override_config: str = None) -> List[Dict[str, Any]]:
        if override_config:
            try:
                data = yaml.safe_load(override_config)
                return data.get("rules", [])
            except Exception as e:
                print(f"Error parsing override config: {e}")
                # Fallback to default
                return self.rules
        return self.rules

rule_engine = RuleEngine()
