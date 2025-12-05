import os
from datetime import datetime

from db.sqlite_adapter import sqlite3

from db.auth_db import DB_PATH


# =========================
# TẠO TABLE LƯU LOG (NẾU CHƯA CÓ)
# =========================
def init_user_logs_table():
    # Đảm bảo thư mục lưu DB tồn tại để Streamlit Cloud không mất dữ liệu
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

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


def log_password_change(username):
    """Ghi nhận sự kiện đổi mật khẩu của người dùng."""
    log_user_action(username, "Đổi mật khẩu thành công")


def get_latest_password_change(username):
    """Trả về lần đổi mật khẩu gần nhất của user (nếu có)."""
    init_user_logs_table()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
            SELECT timestamp
            FROM user_logs
            WHERE username = ? AND action = 'Đổi mật khẩu thành công'
            ORDER BY id DESC
            LIMIT 1
        """,
        (username,),
    )
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


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


def get_user_logs(username):
    """Lấy lịch sử hoạt động của một người dùng cụ thể."""
    init_user_logs_table()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT username, action, timestamp FROM user_logs WHERE username = ? ORDER BY id DESC",
        (username,),
    )
    rows = c.fetchall()

    conn.close()
    return rows
