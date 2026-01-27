import logging
import json
import datetime
import os
from app.models.scan import ScanRequest, ScanResponse

# Setup Structured Logger
log_dir = os.path.join(os.getcwd(), "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "audit.log")

logger = logging.getLogger("audit_logger")
logger.setLevel(logging.INFO)
handler = logging.FileHandler(log_file)
formatter = logging.Formatter('%(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class AuditLogger:
    def log_scan(self, request: ScanRequest, response: ScanResponse):
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "event": "SCAN_COMPLETED",
            "repo": request.repo_full_name,
            "pr_number": request.pr_number,
            "commit_sha": request.commit_sha,
            "status": response.status,
            "violations_count": len(response.violations),
            "succeeded": response.succeeded,
            "violations": [v.dict() for v in response.violations]
        }
        logger.info(json.dumps(entry))

audit_logger = AuditLogger()
