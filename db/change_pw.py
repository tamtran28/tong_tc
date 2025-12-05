import streamlit as st
from db.auth_jwt import get_current_user
from db.security import verify_password
from db.auth_db import update_password
from db.user_logs import log_password_change, get_latest_password_change


def change_password_popup():
    user = get_current_user()
    if not user:
        st.error("Bạn chưa đăng nhập!")
        return

    st.subheader("🔐 Đổi mật khẩu")

    last_change = get_latest_password_change(user["username"])
    if last_change:
        st.info(f"Lần đổi mật khẩu gần nhất: {last_change}")

    old_pw = st.text_input("Mật khẩu cũ", type="password")
    new_pw = st.text_input("Mật khẩu mới", type="password")
    new_pw2 = st.text_input("Nhập lại mật khẩu mới", type="password")

    if st.button("Cập nhật mật khẩu"):
        if not verify_password(old_pw, user["password_hash"]):
            st.error("❌ Mật khẩu cũ không đúng!")
            return

        if new_pw != new_pw2:
            st.error("❌ Mật khẩu mới không khớp!")
            return

        if not update_password(user["username"], new_pw):
            st.error("⚠️ Không tìm thấy tài khoản để cập nhật mật khẩu.")
            return

        log_password_change(user["username"])
        st.success("✅ Đổi mật khẩu thành công! Hãy đăng nhập lại.")
        st.session_state.clear()
        st.rerun()
