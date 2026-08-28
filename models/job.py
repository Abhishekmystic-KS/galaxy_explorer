import os
import sqlite3
import uuid
import json
from datetime import datetime, timedelta

DB_PATH = "output/jobs.db"

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_job_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Create jobs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            step_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            result_json TEXT,
            error_message TEXT,
            ip_address TEXT
        )
    """)
    conn.commit()
    conn.close()

def create_job(query: str, ip_address: str) -> dict:
    job_id = str(uuid.uuid4())
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO jobs (job_id, query, status, progress, step_message, ip_address)
        VALUES (?, ?, 'pending', 0, 'Job queued', ?)
        """,
        (job_id, query.strip(), ip_address)
    )
    conn.commit()
    conn.close()
    return get_job(job_id)

def get_job(job_id: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        d = dict(row)
        if d["result_json"]:
            d["result"] = json.loads(d["result_json"])
        else:
            d["result"] = None
        return d
    return None

def update_job(job_id: str, status: str, progress: int, step_message: str, result_data: dict = None, error_message: str = None) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    completed_at = datetime.utcnow().isoformat() if status in ("completed", "failed") else None
    result_json = json.dumps(result_data) if result_data else None
    
    cursor.execute(
        """
        UPDATE jobs
        SET status = ?, progress = ?, step_message = ?, result_json = COALESCE(?, result_json), error_message = ?, completed_at = COALESCE(?, completed_at)
        WHERE job_id = ?
        """,
        (status, progress, step_message, result_json, error_message, completed_at, job_id)
    )
    conn.commit()
    conn.close()
    return get_job(job_id)

def get_recent_jobs(limit: int = 10) -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    jobs = []
    for r in rows:
        d = dict(r)
        if d["result_json"]:
            d["result"] = json.loads(d["result_json"])
        else:
            d["result"] = None
        jobs.append(d)
    return jobs

def check_rate_limit(ip_address: str, limit: int = 5, window_seconds: int = 60) -> bool:
    """
    Checks if the IP address has created more than 'limit' jobs in the last 'window_seconds'.
    Returns True if allowed, False if rate-limited.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate time threshold in UTC (SQLite DEFAULT CURRENT_TIMESTAMP is UTC)
    # Note: SQLite's datetime('now') is UTC.
    threshold = (datetime.utcnow() - timedelta(seconds=window_seconds)).strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        """
        SELECT COUNT(*) as count FROM jobs
        WHERE ip_address = ? AND created_at >= ?
        """,
        (ip_address, threshold)
    )
    row = cursor.fetchone()
    conn.close()
    
    count = row["count"] if row else 0
    return count < limit
