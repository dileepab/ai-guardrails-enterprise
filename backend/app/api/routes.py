from fastapi import APIRouter, HTTPException
from app.models.scan import ScanRequest, ScanResponse
from app.engine.hybrid_analyzer import analyzer
from app.core.audit import audit_logger

router = APIRouter()

@router.get("/")
def read_root():
    return {"message": "Welcome to AI Guardrails API"}

@router.post("/scan", response_model=ScanResponse)
async def scan_code(request: ScanRequest):
    try:
        from app.core.database import is_commit_overridden
        
        response = await analyzer.analyze(request)
        
        # Check for Admin Override (Persistence)
        # Extract repo/sha from metadata if available (assuming client sends them)
        repo = request.metadata.get("repo_full_name")
        sha = request.metadata.get("commit_sha")
        
        if is_commit_overridden(repo, sha):
            print(f"🔒 Override detected for {repo}@{sha}. Forcing Success.")
            response.succeeded = True
            response.violations = [] # Clear violations so it doesn't block
            
        audit_logger.log_scan(request, response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
