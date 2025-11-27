import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


# =========================
# TẠO TABLE LƯU LOG (NẾU CHƯA CÓ)
# =========================
def init_user_logs_table():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()


# =========================
# GHI LOG NGƯỜI DÙNG
# =========================
def log_user_action(username, action):
    init_user_logs_table()  # đảm bảo table tồn tại

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO user_logs (username, action, timestamp) VALUES (?,?,?)",
        (username, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    )

    conn.commit()
    conn.close()


# =========================
# LẤY LOG ĐỂ ADMIN XEM
# =========================
def get_all_logs():
    init_user_logs_table()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT username, action, timestamp FROM user_logs ORDER BY id DESC")
    rows = c.fetchall()

    conn.close()
    return rows
