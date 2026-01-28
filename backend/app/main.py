from fastapi import FastAPI
from fastapi.responses import FileResponse
from pathlib import Path
from app.api.routes import router as api_router
from app.core.config import settings
from app.api import audit # Added for audit router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"]) # Added audit router

@app.get("/dashboard", response_class=FileResponse) # Added dashboard route
async def get_dashboard():
    return FileResponse("dashboard.html")

@app.get("/setup-hooks.sh", response_class=FileResponse)
async def get_hooks_script():
    # Robustly find script relative to this file (backend/app/main.py -> backend/setup-hooks.sh)
    file_path = Path(__file__).parent.parent / "setup-hooks.sh"
    if not file_path.exists():
        return {"error": f"Script not found at {file_path}"}, 404
    return FileResponse(file_path, filename="setup-hooks.sh")

@app.get("/health")
def health_check():
    return {"status": "ok"}
