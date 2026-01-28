#!/usr/bin/env python3
import sys
import os
import re
import subprocess
import yaml

# Path to rules - Assume we are running from repo root or .git/hooks which is usually .git/hooks/pre-commit
# But the script is located in backend/hooks/pre_commit.py and symlinked or called.
# Let's assume this script is CALLED by the bash pre-commit hook or IS the hook.
# To be safe, we'll assume this script is copied or symlinked to .git/hooks/pre-commit

def get_staged_files():
    """Get list of staged files"""
    try:
        # git diff --cached --name-only
        result = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], encoding='utf-8')
        return [f for f in result.splitlines() if f]
    except subprocess.CalledProcessError:
        return []

def load_rules():
    """Load matching rules from backend/rules/default_rules.yaml"""
    # Try to locate the rules file relative to the git root
    repo_root = os.getcwd() # Hook runs in repo root
    rules_path = os.path.join(repo_root, 'backend', 'rules', 'default_rules.yaml')
    
    if not os.path.exists(rules_path):
        print(f"⚠️  Configuration not found at {rules_path}. Skipping guardrails.")
        return []
        
    try:
        with open(rules_path, 'r') as f:
            data = yaml.safe_load(f)
            return data.get('rules', [])
    except Exception as e:
        print(f"⚠️  Failed to load rules: {e}")
        return []

def scan_file(filepath, rules):
    """Scan a single file for violations"""
    if not os.path.exists(filepath):
        return []
        
    violations = []
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for rule in rules:
            # Skip non-blocking for pre-commit (keep it fast and annoying only for critical stuff)
            # Actually, let's enforce BLOCKING ones only
            if rule.get('severity') != 'BLOCKING':
                continue
                
            pattern = rule.get('pattern')
            if re.search(pattern, content):
                violations.append(rule)
    except Exception:
        pass # Ignore binary files etc
        
    return violations

def main():
    print("🛡️  AI Guardrails: Pre-commit Scan...")
    files = get_staged_files()
    if not files:
        sys.exit(0)
        
    all_rules = load_rules()
    if not all_rules:
        sys.exit(0)
        
    has_error = False
    
    for filename in files:
        # Ignore deleted files
        if not os.path.exists(filename):
            continue
            
        # Ignore likely non-source files
        if filename.endswith(('.png', '.jpg', '.lock', '.zip')):
            continue

        violations = scan_file(filename, all_rules)
        if violations:
            for v in violations:
                print(f"❌ [BLOCKING] {v['id']} in {filename}: {v['message']}")
            has_error = True

    if has_error:
        print("\n🚫 Commit rejected by Guardrails. Please fix blocking issues above.")
        sys.exit(1)
        
    print("✅ Guardrails passed.")
    sys.exit(0)

if __name__ == "__main__":
    main()
