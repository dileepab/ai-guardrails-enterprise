from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Violation(BaseModel):
    rule_id: str
    message: str
    severity: str  # "INFO", "WARNING", "BLOCKING"
    file_path: str
    line_number: int
    suggestion: Optional[str] = None
    category: str # "SECURITY", "STYLE", "COMPLIANCE"

class ScanRequest(BaseModel):
    repo_full_name: str
    pr_number: int
    commit_sha: str
    files: List[Dict[str, str]]
    # Req #2: Repository-level config override (YAML string)
    config_override: Optional[str] = None 
    # Req #1: Flag for Copilot-generated code (mapped from Commit/PR context)
    is_copilot_generated: bool = False
    
class ScanResponse(BaseModel):
    status: str # "success", "failed"
    violations: List[Violation]
    succeeded: bool # True if no blocking violations (or if advisory)
    summary: str
    enforcement_mode: str = "blocking" # "blocking" or "advisory"
