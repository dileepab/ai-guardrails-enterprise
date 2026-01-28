from fastapi import APIRouter
import json
import os
from datetime import datetime, timedelta
from app.core.database import get_db

router = APIRouter()

# Assuming a default SQLite DB path
DATABASE_URL = "sqlite:///./audit.db" 

def get_db():
    conn = sqlite3.connect("audit.db") # Connect to the SQLite database
    conn.row_factory = sqlite3.Row # Optional: to access columns by name
    return conn

from datetime import datetime, timedelta

@router.get("/stats")
async def get_audit_stats(days: int = 30):
    """
    Returns statistics from the audit log for the dashboard.
    Args:
        days: Number of days to filter by (default 30). Use -1 for all time.
    """
    stats = {
        "categories": {"SECURITY": 0, "STYLE": 0, "COMPLIANCE": 0},
        "severities": {"BLOCKING": 0, "WARNING": 0, "INFO": 0},
        "scans": 0,
        "violations": 0,
        "recent": [],
        "riskyFiles": {}
    }

    conn = get_db()
    cursor = conn.cursor()

    # Time Filter
    date_filter = ""
    params = []
    if days > 0:
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        date_filter = "WHERE timestamp >= ?"
        params.append(cutoff_date)

    # 1. Count Scans
    cursor.execute(f"SELECT COUNT(*) FROM audit_logs {date_filter}", params)
    stats["scans"] = cursor.fetchone()[0]

    # 2. Fetch Violations Data
    # We fetch all matching rows and parse JSON in Python. 
    # (SQLite JSON1 extension exists but this is safer for pure python env compatibility)
    cursor.execute(f"SELECT timestamp, violations_json, repo, commit_sha FROM audit_logs {date_filter} ORDER BY timestamp DESC LIMIT 200", params)
    rows = cursor.fetchall()
    
    for row in rows:
        ts = row[0]
        repo_val = row[2]
        commit_val = row[3]
        try:
            violations = json.loads(row[1])
            if not violations:
                continue

            for v in violations:
                stats["violations"] += 1
                
                # Category Stats
                cat = v.get("category", "UNKNOWN")
                stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
                
                # Severity Stats
                sev = v.get("severity", "INFO")
                stats["severities"][sev] = stats["severities"].get(sev, 0) + 1

                # Risky Files
                fpath = v.get("file_path", "unknown")
                stats["riskyFiles"][fpath] = stats["riskyFiles"].get(fpath, 0) + 1

                # Recent Table Entry (Only add if we have space in the "recent" list limit)
                # We flattened the list, so we might have duplicate timestamps for same scan.
                stats["recent"].append({
                    "time": ts.split("T")[0] + " " + ts.split("T")[1][:5],
                    "file": fpath,
                    "id": v.get("rule_id", "?"),
                    "cat": cat,
                    "sev": sev,
                    "repo": repo_val,
                    "commit_sha": commit_val
                })

        except json.JSONDecodeError:
            pass

    conn.close()

    # Post-processing
    stats["riskyFiles"] = dict(sorted(stats["riskyFiles"].items(), key=lambda x: x[1], reverse=True)[:5])
    stats["recent"] = stats["recent"][:10] # Top 10 flattened violations

    return stats
