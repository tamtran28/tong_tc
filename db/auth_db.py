# db/auth_db.py
import os
import sqlite3
from typing import Optional, Dict

from db.security import hash_password, verify_password

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


# ==========================
# KẾT NỐI DB
# ==========================
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ==========================
# KHỞI TẠO DB + USER MẶC ĐỊNH
# ==========================
def init_db():
    """
    Tạo bảng users nếu chưa có.
    Đồng thời tạo user mặc định:
        username: admin
        password: 123456
        role    : admin
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
            is_active INTEGER NOT NULL DEFAULT 1
        )
        """
    )

    # Nếu chưa có user nào -> tạo admin mặc định
    cur.execute("SELECT COUNT(*) FROM users")
    count = cur.fetchone()[0]
    if count == 0:
        cur.execute(
            """
            INSERT INTO users (username, full_name, role, password_hash, is_active)
            VALUES (?, ?, ?, ?, 1)
            """,
            ("admin", "Quản trị hệ thống", "admin", hash_password("123456")),
        )
        conn.commit()

    conn.close()


# ==========================
# HÀM LẤY / TẠO USER
# ==========================
def get_user_by_username(username: str) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, full_name, role, password_hash, is_active FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "id": row["id"],
        "username": row["username"],
        "full_name": row["full_name"],
        "role": row["role"],
        "password_hash": row["password_hash"],
        "is_active": bool(row["is_active"]),
    }


def create_user(username: str, password: str, full_name: str, role: str = "user"):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users(username, full_name, role, password_hash, is_active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (username, full_name, role, hash_password(password)),
    )
    conn.commit()
    conn.close()


# ==========================
# HÀM AUTH CHO LOGIN
# ==========================
def authenticate_user(username: str, password: str) -> Optional[Dict]:
    user = get_user_by_username(username)
    if not user:
        return None
    if not user["is_active"]:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    # Không trả password_hash ra ngoài
    user = user.copy()
    user.pop("password_hash", None)
    return user
