from fastapi import APIRouter
import json
import os

router = APIRouter()

AUDIT_LOG_FILE = "logs/audit.log"

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
                    
                    if "violations" in entry and entry["violations"]:
                        # Add to recent scans (track the whole entry, but we only need flattened violations for the table)
                        # Let's flatten violations for the "Recent Violations" table
                        timestamp = entry.get("timestamp", "N/A")
                        
                        for v in entry["violations"]:
                            stats["violations"] += 1
                            cat = v.get("category", "UNKNOWN")
                            stats["categories"][cat] = stats["categories"].get(cat, 0) + 1
                            
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
                                "sev": v.get("severity", "INFO")
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
