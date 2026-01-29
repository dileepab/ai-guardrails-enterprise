from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask
from pathlib import Path
from app.api.routes import router as api_router
from app.core.config import settings
from app.api import audit
import logging

logger = logging.getLogger(__name__)

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
API_URL="${api_url}"

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
    print("🛡️  AI Guardrails: Local Scan (v2.1 - Enhanced Output)...")
    
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
            # ANSI Colors
            RED = "\033[91m"
            GREEN = "\033[92m"
            YELLOW = "\033[93m"
            BLUE = "\033[94m"
            BOLD = "\033[1m"
            RESET = "\033[0m"

            print(f"\n{RED}{BOLD}🛡️  AI GUARDRAILS POLICY CHECK FAILED{RESET}")
            print(f"{RED}========================================{RESET}\n")
            
            violations = data.get("violations", [])
            blocking_count = sum(1 for v in violations if v["severity"] == "BLOCKING")
            
            print(f"{BOLD}Found {len(violations)} violations ({blocking_count} BLOCKING){RESET}\n")

            current_file = ""
            for v in violations:
                severity = v["severity"]
                color = RED if severity == "BLOCKING" else YELLOW
                icon = "❌" if severity == "BLOCKING" else "⚠️ "
                
                # Group visual separation by file if needed, but simple list is robust
                print(f"{color}{icon} [{v['rule_id']}] {severity}{RESET}")
                
                line_str = f":{v.get('line_number', '?')}" if v.get('line_number') else ""
                print(f"   📂 File: {BOLD}{v['file_path']}{line_str}{RESET}")
                print(f"   📝 Msg:  {v['message']}")
                
                if v.get("suggestion"):
                    print(f"   💡 Fix:  {BLUE}{v['suggestion']}{RESET}")
                print("") # Spacer

            if blocking_count > 0:
                print(f"{RED}{BOLD}🚫 COMMIT REJECTED{RESET}")
                print("   Blocking violations must be resolved before committing.")
                print("   (Use --no-verify to bypass if absolutely necessary, but this is logged.)")
                sys.exit(1)
            else:
                 print(f"{YELLOW}⚠️  Warnings found, but commit proceeds.{RESET}")
                 sys.exit(0)
            
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

from string import Template

try:
    import httpx
    import traceback
    # Create a robust HTTP client for proxying with extended timeout (60s) for slow scans
    client = httpx.AsyncClient(base_url="http://127.0.0.1:3000", timeout=60.0)
    HTTPX_AVAILABLE = True
except ImportError:
    logger.warning("⚠️  HTTPX not found. Webhook proxy disabled.")
    client = None
    HTTPX_AVAILABLE = False

@app.on_event("shutdown")
async def shutdown_event():
    if client:
        await client.aclose()

@app.get("/")
def root():
    return {"status": "AI Guardrails Active", "docs": "/docs"}

# Proxy GitHub Webhooks to the Node.js App (running on port 3000 internally)
@app.post("/api/github/webhooks", include_in_schema=False)
async def proxy_webhooks(request: Request):
    if not HTTPX_AVAILABLE or not client:
        return Response(content="Webhook Proxy Unavailable (Missing Dependency)", status_code=503)

    try:
        url = httpx.URL(path=request.url.path, query=request.url.query.encode("utf-8"))
        rp_req = client.build_request(
            request.method,
            url,
            headers=request.headers.raw,
            content=await request.body(),
        )
        rp_resp = await client.send(rp_req, stream=True)
        return StreamingResponse(
            rp_resp.aiter_raw(),
            status_code=rp_resp.status_code,
            headers=rp_resp.headers,
            background=BackgroundTask(rp_resp.aclose),
        )
    except Exception as e:
        logger.error(f"Error proxying webhook: {e}")
        traceback.print_exc()
        return Response(content=f"Internal Proxy Error: {str(e)}", status_code=500)

@app.get("/setup-hooks.sh", response_class=Response)
async def get_hooks_script(request: Request):
    # Dynamically inject the correct API URL based on where the request came from
    # e.g. https://my-app.railway.app -> https://my-app.railway.app/api/v1/scan
    base_url = str(request.base_url).rstrip("/")
    api_url = f"{base_url}/api/v1/scan"
    
    # Use string.Template to avoid conflicts with {} in the script
    # Use safe_substitute to ignore bash variables like $HOOK_DIR that are NOT in the dict
    script_content = Template(SETUP_SCRIPT_TEMPLATE).safe_substitute(api_url=api_url)
    return Response(content=script_content, media_type="text/x-shellscript")

@app.get("/health")
def health_check():
    return {"status": "ok"}

# Q6: Admin Override Endpoint
@app.post("/api/v1/override")
async def admin_override(request: Request):
    """
    Allows Admin to override a blocking status.
    1. Log to DB.
    2. Call Node App to update GitHub status.
    """
    try:
        body = await request.json()
        repo = body.get("repo")
        commit_sha = body.get("commit_sha")
        reason = body.get("reason", "Manual Admin Override")
        
        if not repo or not commit_sha:
             return Response(content="Missing repo or commit_sha", status_code=400)

        # 1. Log to SQLite
        from app.core.database import get_db, log_audit_event
        from datetime import datetime
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO audit_overrides (timestamp, repo, commit_sha, admin_user, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (datetime.utcnow().isoformat(), repo, commit_sha, "admin", reason))
        conn.commit()
        conn.close()

        # Log as main audit event too
        log_audit_event(
            event_type="ADMIN_OVERRIDE",
            repo=repo,
            commit_sha=commit_sha,
            status="SUCCESS",
            details={"reason": reason, "action": "BLOCKING_OVERRIDDEN"}
        )

        # 2. Call Node App (Internal)
        if HTTPX_AVAILABLE and client:
            # We use the same 'client' but target port 3000 explicitly
            # client base_url is "http://127.0.0.1:3000"
            res = await client.post("/api/override", json={
                "repo_full_name": repo,
                "commit_sha": commit_sha,
                "reason": reason
            })
            if res.status_code != 200:
                logger.error(f"Node App Override failed: {res.text}")
                return Response(content=f"Upstream Error: {res.text}", status_code=500)
        else:
            return Response(content="Internal Communication Error (HTTPX missing)", status_code=500)

        return {"status": "overridden"}

    except Exception as e:
        logger.error(f"Override Error: {e}")
        return Response(content=str(e), status_code=500)
