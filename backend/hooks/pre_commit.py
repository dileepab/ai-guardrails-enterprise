#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import urllib.request
import urllib.error

# DEFAULT CONFIG
API_URL = os.environ.get("GUARDRAILS_API_URL", "http://127.0.0.1:8000/api/v1/scan")
# In production, users should set this env var or update the script

def get_staged_files():
    """Get list of staged files"""
    try:
        result = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], encoding='utf-8')
        return [f for f in result.splitlines() if f]
    except subprocess.CalledProcessError:
        return []

def read_file_content(filepath):
    """Read content of a file"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return ""

def main():
    print("🛡️  AI Guardrails: Local Scan...")
    
    files = get_staged_files()
    if not files:
        sys.exit(0)

    # Prepare payload
    files_payload = []
    for f in files:
        if os.path.exists(f) and not f.endswith(('.png', '.jpg', '.lock', '.zip')):
            files_payload.append({
                "filename": f,
                "content": read_file_content(f),
                "patch": "" # Optional for local scan
            })
            
    if not files_payload:
        sys.exit(0)

    payload = {
        "repo_full_name": "local/repo",
        "pr_number": None,
        "commit_sha": "local-staged",
        "files": files_payload,
        "is_copilot_generated": False # We could detect this via git config user.name potentially
    }

    try:
        req = urllib.request.Request(API_URL)
        req.add_header('Content-Type', 'application/json')
        jsondata = json.dumps(payload).encode('utf-8')
        req.add_header('Content-Length', len(jsondata))
        
        response = urllib.request.urlopen(req, jsondata)
        res_body = response.read()
        data = json.loads(res_body)
        
        if not data.get("succeeded", True):
            print("\n❌ Blocking Issues Found:")
            for v in data.get("violations", []):
                if v["severity"] == "BLOCKING":
                    print(f"  - [{v['rule_id']}] {v['file_path']}: {v['message']}")
            
            print("\n🚫 Commit rejected. Please fix the above issues.")
            sys.exit(1)
            
        print("✅ Guardrails passed.")
        sys.exit(0)

    except urllib.error.URLError as e:
        print(f"⚠️  Could not connect to Guardrails API at {API_URL}")
        print(f"   Error: {e}")
        print("   Proceeding with commit (fail-open strategy for local dev).")
        sys.exit(0) # Fail open if server down
    except Exception as e:
        print(f"Error validating commit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
