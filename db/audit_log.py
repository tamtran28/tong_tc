import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")

def log_action(action: str, username="admin"):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            action TEXT
        )
    """)
    c.execute(
        "INSERT INTO audit_log (timestamp, username, action) VALUES (?, ?, ?)",
        (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), username, action)
    )
    conn.commit()
    conn.close()


def get_logs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT timestamp, username, action FROM audit_log ORDER BY id DESC")
    logs = c.fetchall()
    conn.close()
    return logs
