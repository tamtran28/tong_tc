import streamlit as st
from auth_db import get_user_by_username, verify_password, init_db
from auth_jwt import create_access_token
from datetime import timedelta

# đảm bảo có bảng users
init_db()


def login_page():
    st.title("🔐 Đăng nhập hệ thống KTNB")

    with st.form("login_form"):
        username = st.text_input("Tên đăng nhập")
        password = st.text_input("Mật khẩu", type="password")
        submit = st.form_submit_button("Đăng nhập")

    if submit:
        if not username or not password:
            st.error("Vui lòng nhập đủ tên đăng nhập và mật khẩu.")
            return

        user = get_user_by_username(username)
        if not user:
            st.error("❌ Không tồn tại user này.")
            return

        if not verify_password(password, user["password_hash"]):
            st.error("❌ Sai mật khẩu.")
            return

        token = create_access_token(
            {
                "sub": user["username"],
                "role": user["role"],
                "full_name": user["full_name"] or user["username"],
            },
            expires_delta=timedelta(minutes=120),
        )

        st.session_state["access_token"] = token
        st.session_state["username"] = user["username"]
        st.session_state["role"] = user["role"]
        st.session_state["full_name"] = user["full_name"] or user["username"]
        st.session_state["logged_in"] = True

        st.success("✅ Đăng nhập thành công!")
        st.experimental_rerun()
