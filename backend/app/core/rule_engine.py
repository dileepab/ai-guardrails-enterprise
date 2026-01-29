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
             import logging
             logging.getLogger(__name__).warning(f"Warning: Rules file not found at {path}")
             return

        with open(path, 'r') as f:
            data = yaml.safe_load(f)
            self.rules = data.get("rules", [])

    def get_rules(self, override_config: str = None) -> List[Dict[str, Any]]:
        current_rules = self.rules
        
        if override_config:
            try:
                data = yaml.safe_load(override_config)
                
                # 1. Check for Rule Pack Selection
                rule_pack = data.get("rule_pack", "default")
                if rule_pack != "default":
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    pack_path = os.path.join(base_dir, "rules", f"{rule_pack}_rules.yaml")
                    
                    if os.path.exists(pack_path):
                        with open(pack_path, 'r') as f:
                            pack_data = yaml.safe_load(f)
                            # Append pack rules to default rules
                            current_rules = self.rules + pack_data.get("rules", [])
                
                # 2. Check for Custom Rules Override
                if "rules" in data:
                    return data["rules"] # If specific rules provided, use ONLY those (or should we merge? Design choice: Override)
                
                return current_rules

            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error parsing override config: {e}")
                return self.rules
                
        return current_rules
        return self.rules

rule_engine = RuleEngine()
