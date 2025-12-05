from db.auth_db import init_db
from db.security import hash_password
import sqlite3
from db.auth_db import DB_PATH, init_db, insert_user
DB_PATH = "db/users.db"

def seed_users():
    # Nếu DB có rồi thì không tạo lại
    if os.path.exists(DB_PATH):
        return

    print("🔧 First run: creating user database...")
    
    init_db()

    users = [
        ("admin", "Quản trị hệ thống", "admin", hash_password("123")),
        ("pos01", "Nhân viên POS", "pos", hash_password("123")),
        ("td01", "Nhân viên tín dụng", "credit", hash_password("123")),
        ("tamtnt", "User01", "user", hash_password("123")),
        ("viewer", "Khách xem", "view", hash_password("123")),
    ]

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    for u in users:
        try:
            c.execute("INSERT INTO users VALUES (?,?,?,?)", u)
        except:
            pass

    conn.commit()
    conn.close()

if __name__ == "__main__":
    seed_users()
