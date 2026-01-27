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
        response = await analyzer.analyze(request)
        audit_logger.log_scan(request, response)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
