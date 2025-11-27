# db/login_page.py
import streamlit as st

from db.auth_db import init_db, authenticate_user
from db.auth_jwt import create_access_token, decode_access_token

SESSION_TOKEN_KEY = "access_token"
SESSION_USER_KEY = "current_user"


# ==========================
# TRẠNG THÁI LOGIN
# ==========================
def is_authenticated() -> bool:
    """
    Trả về True nếu trong session có token hợp lệ.
    """
    token = st.session_state.get(SESSION_TOKEN_KEY)
    if not token:
        return False

    payload = decode_access_token(token)
    if not payload:
        # token hết hạn / sai -> xóa
        st.session_state.pop(SESSION_TOKEN_KEY, None)
        st.session_state.pop(SESSION_USER_KEY, None)
        return False

    if SESSION_USER_KEY not in st.session_state:
        st.session_state[SESSION_USER_KEY] = {
            "username": payload.get("sub"),
            "role": payload.get("role"),
        }
    return True


def get_current_user():
    return st.session_state.get(SESSION_USER_KEY)


def logout():
    for key in [SESSION_TOKEN_KEY, SESSION_USER_KEY, "role"]:
        st.session_state.pop(key, None)


# ==========================
# UI ĐĂNG NHẬP
# ==========================
def show_login_page():
    """
    Hiển thị form đăng nhập.
    """
    init_db()  # đảm bảo bảng + user mặc định tồn tại

    st.title("🔐 ĐĂNG NHẬP HỆ THỐNG KTNB")

    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")

    col1, col2 = st.columns([1, 3])
    with col1:
        login_btn = st.button("Đăng nhập")

    if login_btn:
        user = authenticate_user(username, password)
        if not user:
            st.error("❌ Sai tên đăng nhập hoặc mật khẩu.")
            return

        token = create_access_token({"sub": user["username"], "role": user["role"]})
        st.session_state[SESSION_TOKEN_KEY] = token
        st.session_state[SESSION_USER_KEY] = {
            "username": user["username"],
            "role": user["role"],
        }
        st.session_state["role"] = user["role"]  # cho require_role dùng

        st.success("✅ Đăng nhập thành công!")
        st.experimental_rerun()
