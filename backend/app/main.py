from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse
from pathlib import Path
from app.api.routes import router as api_router
from app.core.config import settings
from app.api import audit

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])

@app.get("/dashboard", response_class=FileResponse)
async def get_dashboard():
    return FileResponse("dashboard.html")

# Embed the script structure directly to avoid filesystem issues in Docker
SETUP_SCRIPT_TEMPLATE = r"""#!/bin/bash

# Configuration
# Dynamic API URL injected by server
API_URL="{api_url}"

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
"""

@app.get("/setup-hooks.sh", response_class=Response)
async def get_hooks_script(request: Request):
    # Dynamically inject the correct API URL based on where the request came from
    # e.g. https://my-app.railway.app -> https://my-app.railway.app/api/v1/scan
    base_url = str(request.base_url).rstrip("/")
    api_url = f"{base_url}/api/v1/scan"
    
    script_content = SETUP_SCRIPT_TEMPLATE.format(api_url=api_url)
    return Response(content=script_content, media_type="text/x-shellscript")

@app.get("/health")
def health_check():
    return {"status": "ok"}
