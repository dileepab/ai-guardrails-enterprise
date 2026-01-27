from fastapi import APIRouter
import json
import os

router = APIRouter()

AUDIT_LOG_FILE = "logs/audit.log"

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

    if not os.path.exists(AUDIT_LOG_FILE):
        return stats

    # Calculate cutoff time
    cutoff_date = None
    if days > 0:
        cutoff_date = datetime.utcnow() - timedelta(days=days)

    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    
                    # Time Filter
                    timestamp_str = entry.get("timestamp")
                    if timestamp_str and cutoff_date:
                        try:
                            # Handle ISO format variations if needed, assume standard ISO
                            entry_time = datetime.fromisoformat(timestamp_str)
                            if entry_time < cutoff_date:
                                continue # Skip old entries
                        except ValueError:
                            pass # If bad time format, include it safely or skip? Let's include safe.

                    stats["scans"] += 1
                    
                    if "violations" in entry and entry["violations"]:
                        # Add to recent scans (track the whole entry, but we only need flattened violations for the table)
                        # Let's flatten violations for the "Recent Violations" table
                        timestamp = entry.get("timestamp", "N/A")
                        
                        for v in entry["violations"]:
                            stats["violations"] += 1
                            cat = v.get("category", "UNKNOWN")
                            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
                            
                            sev = v.get("severity", "INFO")
                            stats["severities"][sev] = stats["severities"].get(sev, 0) + 1

                            # Risky Files Logic
                            fpath = v.get("file_path", "unknown")
                            if fpath:
                                stats["riskyFiles"][fpath] = stats["riskyFiles"].get(fpath, 0) + 1
                            
                            # Recent Violations Logic (Store flattened view for table)
                            # We keep simple dicts: {time, file, id, cat, sev}
                            stats["recent"].append({
                                "time": timestamp.split("T")[0] + " " + timestamp.split("T")[1][:5], # Simple fmt
                                "file": fpath,
                                "id": v.get("rule_id", "?"),
                                "cat": cat,
                                "sev": sev
                            })
                            
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        print(f"Error reading audit log: {e}")

    # Post-processing:
    # 1. Sort risky files by count (desc) and take top 5
    sorted_risky = sorted(stats["riskyFiles"].items(), key=lambda x: x[1], reverse=True)[:5]
    stats["riskyFiles"] = dict(sorted_risky)

    # 2. Sort recent by time (desc, assuming log is append-only, reverse list is enough) and take top 10
    stats["recent"] = sorted(stats["recent"], key=lambda x: x["time"], reverse=True)[:10]

    return stats
