import sqlite3
from db.security import hash_password, verify_password

DB_PATH = "db/users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            full_name TEXT,
            role TEXT,
            password_hash TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT username, full_name, role, password_hash FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()

    if row:
        return {
            "username": row[0],
            "full_name": row[1],
            "role": row[2],
            "password_hash": row[3],
        }
    return None

def authenticate_user(username, password):
    user = get_user_by_username(username)
    if not user:
        return None

    if verify_password(password, user["password_hash"]):
        return user
    return None
