import streamlit as st
from db.auth_db import authenticate_user
from db.auth_jwt import login_user, is_authenticated

def show_login_page():
    st.title("🔐 ĐĂNG NHẬP HỆ THỐNG KTNB")

    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")

    if st.button("Đăng nhập"):
        user = authenticate_user(username, password)

        if user:
            st.success("Đăng nhập thành công!")
            login_user(user)
            st.experimental_rerun()
        else:
            st.error("Sai tên đăng nhập hoặc mật khẩu!")

def logout_button():
    if st.button("Đăng xuất"):
        from db.auth_jwt import logout
        logout()
        st.experimental_rerun()
