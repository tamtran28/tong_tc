import sqlite3
from passlib.context import CryptContext
from pathlib import Path

DB_PATH = Path("users.db")  # file SQLite sẽ nằm cùng thư mục

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Tạo bảng users nếu chưa có."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_user(username: str, password: str, full_name: str, role: str):
    """Tạo user mới (dùng trong script seed)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO users (username, password_hash, full_name, role)
        VALUES (?, ?, ?, ?)
        """,
        (username, hash_password(password), full_name, role),
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
