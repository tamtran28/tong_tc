import hashlib
import os

def hash_password(password: str) -> str:
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password: str, hashed_value: str) -> bool:
    try:
        salt, hashed = hashed_value.split("$")
        return hashlib.sha256((password + salt).encode()).hexdigest() == hashed
    except:
        return False

def require_role(user, allowed_roles):
    """
    Check user role. allowed_roles: ['admin', 'pos']
    """
    if not user:
        return False

    return user.get("role") in allowed_roles

# # db/security.py
# import hashlib
# import hmac
# import os
# import streamlit as st

# # Dùng làm “muối” để hash password
# SECRET_KEY = os.getenv("APP_SECRET_KEY", "change_me_please")


# # ==========================
# # HASH & VERIFY PASSWORD
# # ==========================
# def hash_password(password: str) -> str:
#     """
#     Hash mật khẩu bằng HMAC-SHA256.
#     """
#     if password is None:
#         return ""
#     pwd_bytes = password.encode("utf-8")
#     salt = SECRET_KEY.encode("utf-8")
#     return hmac.new(salt, pwd_bytes, hashlib.sha256).hexdigest()


# def verify_password(password: str, password_hash: str) -> bool:
#     """
#     So sánh mật khẩu người dùng nhập với hash trong DB.
#     """
#     if not password_hash:
#         return False
#     return hmac.compare_digest(hash_password(password), str(password_hash))


# # ==========================
# # PHÂN QUYỀN
# # ==========================
# def require_role(allowed_roles):
#     """
#     Gọi trong module:
#         from db.security import require_role
#         require_role(["admin", "ktnb"])

#     Nếu user không có role phù hợp -> dừng luôn module.
#     """
#     role = st.session_state.get("role")

#     if role not in allowed_roles:
#         st.error("⛔ Bạn không có quyền truy cập chức năng này!")
#         st.stop()
