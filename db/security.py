import streamlit as st
import json
import os
import hashlib

USERS_FILE = os.path.join("db", "users.json")

# ======================
# HÀM HASH PASSWORD
# ======================
def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


# ======================
# LOAD USERS DATABASE
# ======================
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)


# ======================
# KIỂM TRA ĐĂNG NHẬP
# ======================
def is_authenticated():
    return st.session_state.get("auth", False)


def login(username, password):
    users = load_users()
    if username not in users:
        return False, "❌ Sai username"

    hashed = hash_password(password)
    if hashed != users[username]["password"]:
        return False, "❌ Sai password"

    st.session_state["auth"] = True
    st.session_state["username"] = username
    st.session_state["role"] = users[username]["role"]
    return True, "✔ Đăng nhập thành công"


def logout():
    for key in ["auth", "username", "role"]:
        if key in st.session_state:
            del st.session_state[key]


# ======================
# UI ĐĂNG NHẬP
# ======================
def login_screen():
    st.title("🔐 ĐĂNG NHẬP HỆ THỐNG")

    username = st.text_input("Tên đăng nhập")
    password = st.text_input("Mật khẩu", type="password")

    if st.button("🚀 Đăng nhập"):
        ok, msg = login(username, password)
        st.info(msg)
        if ok:
            st.rerun()


# ======================
# HÀM PHÂN QUYỀN MODULE
# ======================
def require_role(allowed_roles: list):
    """
    Gọi trong module:
        require_role(["admin", "ktnb"])

    Nếu user không thuộc role → chặn lại
    """
    role = st.session_state.get("role", None)
    if role not in allowed_roles:
        st.error("⛔ Bạn không có quyền truy cập module này!")
        st.stop()
