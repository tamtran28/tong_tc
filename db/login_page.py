# db/login_page.py
import streamlit as st

from db.auth_db import init_db, authenticate_user
from db.auth_jwt import create_access_token, verify_access_token


# Khởi tạo DB ngay khi import module
init_db()


SESSION_TOKEN_KEY = "auth_token"
SESSION_USER_KEY = "auth_user"


def is_authenticated() -> bool:
    """
    Kiểm tra trong session có token hợp lệ hay không.
    """
    token = st.session_state.get(SESSION_TOKEN_KEY)
    if not token:
        return False

    payload = verify_access_token(token)
    if payload is None:
        # token hết hạn hoặc lỗi -> xoá khỏi session
        st.session_state.pop(SESSION_TOKEN_KEY, None)
        st.session_state.pop(SESSION_USER_KEY, None)
        return False

    # cập nhật lại user (phòng trường hợp sửa role sau này)
    st.session_state[SESSION_USER_KEY] = payload
    return True


def get_current_user():
    return st.session_state.get(SESSION_USER_KEY)


def logout_button():
    """
    Hiển thị nút logout ở sidebar / đầu trang
    """
    if st.button("🚪 Đăng xuất"):
        st.session_state.pop(SESSION_TOKEN_KEY, None)
        st.session_state.pop(SESSION_USER_KEY, None)
        st.experimental_rerun()


def show_login_page():
    """
    Vẽ màn hình đăng nhập.
    Gọi hàm này trong app.py nếu chưa đăng nhập.
    """
    st.markdown("## 🔐 Đăng nhập hệ thống KTNB")

    col1, col2 = st.columns([2, 1])
    with col1:
        username = st.text_input("👤 Tên đăng nhập", key="login_username")
        password = st.text_input("🔑 Mật khẩu", type="password", key="login_password")
        login_btn = st.button("Đăng nhập", type="primary")

        if login_btn:
            if not username or not password:
                st.error("Vui lòng nhập đủ username và password.")
                return

            user = authenticate_user(username.strip(), password)
            if user is None:
                st.error("Sai tên đăng nhập hoặc mật khẩu.")
                return

            # Tạo JWT token
            token = create_access_token(
                {
                    "sub": user["username"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                }
            )

            st.session_state[SESSION_TOKEN_KEY] = token
            st.session_state[SESSION_USER_KEY] = {
                "username": user["username"],
                "full_name": user["full_name"],
                "role": user["role"],
            }

            st.success("Đăng nhập thành công! Đang chuyển vào hệ thống...")
            st.experimental_rerun()

    with col2:
        st.info(
            """
**Tài khoản mặc định**  
- User: `admin`  
- Pass: `admin123`  

Hãy đổi mật khẩu / tạo user mới trong DB nếu cần.
"""
        )
