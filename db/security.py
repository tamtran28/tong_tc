# ======================================
# security.py — Hash + Verify + Role
# ======================================
import bcrypt


# ===========================
# HASH PASSWORD (bcrypt)
# ===========================
def hash_password(password: str) -> str:
    """
    Tạo mật khẩu hash dùng bcrypt.
    """
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    return hashed.decode()   # lưu dạng string trong DB


# ===========================
# VERIFY PASSWORD (bcrypt)
# ===========================
def verify_password(password: str, hashed_value: str) -> bool:
    """
    Kiểm tra password nhập vào có trùng hash lưu trong DB không.
    """
    try:
        return bcrypt.checkpw(password.encode(), hashed_value.encode())
    except:
        return False


# ===========================
# CHECK ROLE
# ===========================
def require_role(user, allowed_roles):
    """
    Kiểm tra user có quyền hợp lệ không.
    allowed_roles = ['admin', 'pos', 'viewer']
    """
    if not user:
        return False
    return user.get("role") in allowed_roles
# import hashlib
# import os

# def hash_password(password: str) -> str:
#     salt = os.urandom(16).hex()
#     hashed = hashlib.sha256((password + salt).encode()).hexdigest()
#     return f"{salt}${hashed}"

# def verify_password(password: str, hashed_value: str) -> bool:
#     try:
#         salt, hashed = hashed_value.split("$")
#         return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
#     except:
#         return False

# def require_role(user, allowed_roles):
#     """
#     Check user role. allowed_roles: ['admin', 'pos']
#     """
#     if not user:
#         return False

#     return user.get("role") in allowed_roles


