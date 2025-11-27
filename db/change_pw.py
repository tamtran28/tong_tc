import streamlit as st
from db.auth_db import change_password
from db.login_page import get_current_user

def change_password_popup():
    """Form đổi mật khẩu riêng, độc lập — không ảnh hưởng app chính."""

    with st.form("change_password_form"):
        st.subheader("🔐 Đổi mật khẩu")

        old_pwd = st.text_input("Mật khẩu cũ", type="password")
        new_pwd = st.text_input("Mật khẩu mới", type="password")
        new_pwd2 = st.text_input("Nhập lại mật khẩu mới", type="password")

        submit = st.form_submit_button("Lưu mật khẩu")

        if submit:
            user = get_current_user()
            if not user:
                st.error("Bạn chưa đăng nhập!")
                return

            if new_pwd != new_pwd2:
                st.error("❌ Mật khẩu mới không khớp!")
                return

            if len(new_pwd) < 6:
                st.warning("⚠ Mật khẩu phải >= 6 ký tự!")
                return

            ok = change_password(user["username"], old_pwd, new_pwd)

            if ok:
                st.success("✅ Đổi mật khẩu thành công!")
                st.info("Vui lòng đăng nhập lại.")
                st.session_state.clear()
                st.rerun()
            else:
                st.error("❌ Mật khẩu cũ không đúng!")
