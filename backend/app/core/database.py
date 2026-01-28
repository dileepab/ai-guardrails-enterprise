import sqlite3
import json
import os
from datetime import datetime

DB_FILE = os.path.join(os.getcwd(), "audit.db")

def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    # Enable Write-Ahead Logging (WAL) for better concurrency with multiple workers/processes
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    
    # Audit Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            event_type TEXT,
            repo TEXT,
            pr_number INTEGER,
            commit_sha TEXT,
            status TEXT,
            violations_count INTEGER,
            violations_json TEXT,  -- Storing structured data as JSON for flexibility
            metadata_json TEXT
        )
    ''')

    # Admin Overrides Table (Q6 Requirement)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_overrides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            repo TEXT,
            commit_sha TEXT,
            admin_user TEXT,
            reason TEXT
        )
    ''')

    conn.commit()
    conn.close()

# Initialize on import (safe for this scale)
init_db()

def log_audit_event(event_type: str, repo: str, commit_sha: str, pr_number: int = None, status: str = "INFO", details: dict = None):
    """
    Helper to log any event to the DB.
    """
    conn = get_db()
    cursor = conn.cursor()
    
    violations_json = "[]"
    metadata_json = "{}"
    
    if details:
        if "violations" in details:
            violations_json = json.dumps(details.pop("violations"))
        metadata_json = json.dumps(details)

    cursor.execute('''
        INSERT INTO audit_logs (timestamp, event_type, repo, pr_number, commit_sha, status, violations_count, violations_json, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.utcnow().isoformat(),
        event_type,
        repo,
        pr_number,
        commit_sha,
        status,
        len(json.loads(violations_json)),
        violations_json,
        metadata_json
    ))
    
    conn.commit()
    conn.close()
