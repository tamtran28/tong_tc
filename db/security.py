# db/security.py
import os
import hmac
import base64
import hashlib
from datetime import timedelta

# Khóa bí mật dùng cho JWT
# Có thể đọc từ st.secrets nếu muốn bảo mật hơn
SECRET_KEY = os.environ.get("APP_SECRET_KEY", "change-this-secret-key-123")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token sống 60 phút


def hash_password(password: str) -> str:
    """
    Hash mật khẩu bằng PBKDF2-HMAC (SHA256)
    Trả về chuỗi base64(salt+hash)
    """
    if isinstance(password, str):
        password = password.encode("utf-8")

    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password, salt, 100_000)
    return base64.b64encode(salt + dk).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """
    So sánh mật khẩu người dùng nhập với hash lưu trong DB
    """
    try:
        if isinstance(password, str):
            password = password.encode("utf-8")
        data = base64.b64decode(hashed.encode("utf-8"))
        salt, stored_hash = data[:16], data[16:]
        new_hash = hashlib.pbkdf2_hmac("sha256", password, salt, 100_000)
        return hmac.compare_digest(stored_hash, new_hash)
    except Exception:
        return False
        
def require_role(roles: list):
    """Chặn truy cập nếu user không có role hợp lệ"""
    user_role = st.session_state.get("role")

    if user_role not in roles:
        st.error("⛔ Bạn không có quyền truy cập chức năng này!")
        st.stop()

def get_token_expire_delta() -> timedelta:
    return timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
