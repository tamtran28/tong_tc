import streamlit as st
from db.auth_db import verify_password, update_password
from db.auth_jwt import get_current_user
from db.security import hash_password


def show_change_password_page():
    st.title("🔑 ĐỔI MẬT KHẨU")

    user = get_current_user()
    username = user["username"]

    old_pw = st.text_input("Mật khẩu cũ", type="password")
    new_pw = st.text_input("Mật khẩu mới", type="password")
    confirm_pw = st.text_input("Nhập lại mật khẩu mới", type="password")

    if st.button("Cập nhật mật khẩu"):
        if not old_pw or not new_pw:
            st.error("Vui lòng nhập đầy đủ thông tin!")
            return

        if new_pw != confirm_pw:
            st.error("Mật khẩu xác nhận không khớp!")
            return

        # Kiểm tra mật khẩu cũ
        if not verify_password(username, old_pw):
            st.error("❌ Mật khẩu cũ không đúng!")
            return

        # Cập nhật mật khẩu mới
        hashed = hash_password(new_pw)
        update_password(username, hashed)

        st.success("✔ Đổi mật khẩu thành công! Vui lòng đăng nhập lại.")
        st.session_state.clear()
        st.rerun()
