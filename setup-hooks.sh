#!/bin/bash

# Configuration
# In production, this would be your actual deployed URL
API_URL="${GUARDRAILS_API_URL:-http://127.0.0.1:8000/api/v1/scan}" 

# Define paths
HOOK_DIR=".git/hooks"
PRE_COMMIT_HOOK="$HOOK_DIR/pre-commit"

echo "🛡️  AI Guardrails: Installing Local Hook..."

# Ensure .git/hooks exists
if [ ! -d "$HOOK_DIR" ]; then
    echo "❌ Error: .git directory not found. Please run this from the root of your repository."
    exit 1
fi

# Check if pre-commit already exists
if [ -f "$PRE_COMMIT_HOOK" ]; then
    if ! grep -q "AI Guardrails" "$PRE_COMMIT_HOOK"; then
        echo "⚠️  A pre-commit hook already exists. Backing it up to pre-commit.bak"
        mv "$PRE_COMMIT_HOOK" "$PRE_COMMIT_HOOK.bak"
    else
        echo "ℹ️  AI Guardrails hook already installed. Updating..."
    fi
fi

# Write the Python Hook Script directly
cat <<EOF > "$PRE_COMMIT_HOOK"
#!/usr/bin/env python3
import sys
import os
import subprocess
import json
import urllib.request
import urllib.error

# Configured Endpoint
API_URL = "$API_URL"

def get_staged_files():
    try:
        result = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], encoding='utf-8')
        return [f for f in result.splitlines() if f]
    except subprocess.CalledProcessError:
        return []

def read_file_content(filepath):
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

    files_payload = []
    for f in files:
        if os.path.exists(f) and not f.endswith(('.png', '.jpg', '.lock', '.zip')):
            files_payload.append({
                "filename": f,
                "content": read_file_content(f),
                "patch": ""
            })
            
    if not files_payload:
        sys.exit(0)

    payload = {
        "repo_full_name": "local/repo",
        "pr_number": None,
        "commit_sha": "local-staged",
        "files": files_payload,
        "is_copilot_generated": False
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
            print("\n❌ BLOCKING ISSUES FOUND (AI Guardrails):")
            for v in data.get("violations", []):
                if v["severity"] == "BLOCKING":
                    print(f"  - [{v['rule_id']}] {v['file_path']}: {v['message']}")
            
            print("\n🚫 Commit rejected. Please fix blocking issues.")
            sys.exit(1)
            
        print("✅ Guardrails passed.")
        sys.exit(0)

    except urllib.error.URLError as e:
        print(f"⚠️  Could not connect to Guardrails API at {API_URL}")
        print(f"   (Proceeding commit in fail-open mode)")
        sys.exit(0)
    except Exception as e:
        print(f"Error checking guardrails: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
EOF

# Make executable
chmod +x "$PRE_COMMIT_HOOK"

echo "✅ Installed successfully!"
echo "   Configured API: $API_URL"
