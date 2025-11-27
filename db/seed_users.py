from auth_db import init_db, create_user
from db.auth_db import init_db, add_user

init_db()

# Tạo 1 số user mẫu
create_user("admin", "123456", "Quản trị hệ thống", "admin")
create_user("kt_hn", "hn2025", "Kiểm toán Hà Nội", "audit")
create_user("pos01", "pos2025", "User POS", "pos")
create_user("the01", "the2025", "User Thẻ", "the")

print("Đã tạo xong users.")
