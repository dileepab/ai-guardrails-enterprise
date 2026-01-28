from app.core.database import log_audit_event

class AuditLogger:
    def log_scan(self, request: ScanRequest, response: ScanResponse):
        # Prepare details
        details = {
            "succeeded": response.succeeded,
            "violations": [v.dict() for v in response.violations]
        }
        
        log_audit_event(
            event_type="SCAN_COMPLETED",
            repo=request.repo_full_name,
            pr_number=request.pr_number,
            commit_sha=request.commit_sha,
            status=response.status,
            details=details
        )

audit_logger = AuditLogger()
