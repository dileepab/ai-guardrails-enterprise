from fastapi import APIRouter
import json
import os

router = APIRouter()

AUDIT_LOG_FILE = "audit.log"

@router.get("/stats")
async def get_audit_stats():
    """
    Returns statistics from the audit log for the dashboard.
    """
    stats = {
        "categories": {"SECURITY": 0, "STYLE": 0, "COMPLIANCE": 0},
        "scans": 0,
        "violations": 0,
        "recent": [],
        "riskyFiles": {}
    }

    if not os.path.exists(AUDIT_LOG_FILE):
        return stats

    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    stats["scans"] += 1
                    
                    # This depends on your audit log structure. 
                    # Assuming basic structure for now to prevent crashes.
                    if "violations" in entry:
                        for v in entry["violations"]:
                            stats["violations"] += 1
                            cat = v.get("category", "UNKNOWN")
                            if cat in stats["categories"]:
                                stats["categories"][cat] += 1
                            else:
                                stats["categories"][cat] = 1
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error reading audit log: {e}")

    return stats
