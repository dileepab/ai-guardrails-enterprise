import json
import csv
import argparse
import sys
import os

def export_audit(log_file, output_file):
    if not os.path.exists(log_file):
        print(f"Error: Log file {log_file} not found.")
        return

    print(f"Reading from {log_file}...")
    
    records = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                if line.strip():
                    records.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"Skipping invalid json line")

    if not records:
        print("No records found.")
        return

    print(f"Found {len(records)} records. Writing to {output_file}...")
    
    # Flatten fields for CSV
    flat_records = []
    for r in records:
        flat = {
            "timestamp": r.get("timestamp"),
            "repo": r.get("repo"),
            "pr_number": r.get("pr_number"),
            "commit_sha": r.get("commit_sha"),
            "status": r.get("status"),
            "violations_count": r.get("violations_count"),
            "succeeded": r.get("succeeded"),
        }
        flat_records.append(flat)

    fieldnames = ["timestamp", "repo", "pr_number", "commit_sha", "status", "violations_count", "succeeded"]
    
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for r in flat_records:
            writer.writerow(r)
            
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Audit Log to CSV")
    parser.add_argument("--log", default="audit.log", help="Path to audit.log")
    parser.add_argument("--out", default="audit_report.csv", help="Output CSV path")
    args = parser.parse_args()
    
    export_audit(args.log, args.out)
