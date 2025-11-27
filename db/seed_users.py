# db/seed_users.py
from db.auth_db import create_user, init_db

if __name__ == "__main__":
    init_db()
    # Ví dụ tạo thêm 1 user
    create_user(
        username="ktnb01",
        password="password123",
        full_name="Kiểm toán viên 01",
        role="auditor",
    )
    print("Đã tạo user ktnb01 / password123")
