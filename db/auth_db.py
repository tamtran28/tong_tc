# db/auth_db.py
import sqlite3
from pathlib import Path
from datetime import datetime

from db.security import hash_password, verify_password  # dùng lại hàm hash

DB_PATH = Path(__file__).with_name("users.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Tạo bảng users nếu chưa có.
    Đồng thời tạo user admin mặc định nếu chưa tồn tại.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()

    # tạo admin mặc định: admin / admin123 nếu chưa có
    cur.execute("SELECT * FROM users WHERE username = ?", ("admin",))
    row = cur.fetchone()
    if row is None:
        password_hash = hash_password("admin123")
        cur.execute(
            """
            INSERT INTO users(username, full_name, role, password_hash, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "admin",
                "Quản trị hệ thống",
                "admin",
                password_hash,
                1,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()

    conn.close()


def create_user(username: str, password: str, full_name: str = "", role: str = "user"):
    conn = get_connection()
    cur = conn.cursor()
    password_hash = hash_password(password)
    cur.execute(
        """
        INSERT INTO users(username, full_name, role, password_hash, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            username,
            full_name,
            role,
            password_hash,
            1,
            datetime.utcnow().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()
    conn.close()


def get_user_by_username(username: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def authenticate_user(username: str, password: str):
    """
    Trả về dict user nếu đăng nhập đúng, ngược lại trả về None
    """
    row = get_user_by_username(username)
    if row is None:
        return None
    if not row["is_active"]:
        return None
    if not verify_password(password, row["password_hash"]):
        return None

    # chuyển về dict
    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
    }
