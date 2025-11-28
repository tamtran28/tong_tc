import streamlit as st

# ==== LOGIN SYSTEM ====
from db.login_page import show_login_page, logout_button
from db.auth_jwt import is_authenticated, get_current_user
from db.security import require_role

from db.seed_users import seed_users
from db.change_pw import change_password_popup

seed_users()

# log
from log.user_activity_view import view_my_activity

# ==== MODULE NGHIỆP VỤ ====
from module.phoi_the import run_phoi_the
from module.chuyen_tien import run_chuyen_tien
from module.to_khai_hq import run_to_khai_hq
from module.tindung import run_tin_dung
from module.hdv import run_hdv
from module.ngoai_te_vang import run_ngoai_te_vang
from module.DVKH import run_dvkh_5_tieuchi
from module.tieuchithe import run_module_the
from module.module_pos import run_module_pos


# ==== HEADER UI ====
def colored_header(title, subtitle="", color="#4A90E2"):
    st.markdown(
        f"""
        <div style="border-left: 8px solid {color};
                    padding: 8px 12px;
                    margin-top: 10px;
                    margin-bottom: 12px;
                    background-color: #F5F9FF;">
            <h2>{title}</h2>
            <p style="opacity:0.7;">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 🔐 KIỂM TRA LOGIN
# ============================================================
if not is_authenticated():
    show_login_page()
    st.stop()

user = get_current_user()


# ============================================================
# SIDEBAR — LUÔN ĐƯỢC TẠO (KHÔNG BỊ LỖI menu not defined)
# ============================================================
with st.sidebar:
    st.markdown(f"👤 **{user['full_name']}**  \n🔑 Quyền: **{user['role']}**")

    # nút đổi mật khẩu
    if st.button("🔐 Đổi mật khẩu"):
        st.session_state["change_pw"] = True

    logout_button()

    # ===== ADMIN TOOLS =====
    if user["role"] == "admin":
        st.markdown("### 🔧 Admin Tools")

        admin_menu = st.selectbox(
            "Chọn chức năng quản trị",
            [
                "— Chọn chức năng —",
                "👤 Thêm user mới",
                "🔄 Reset mật khẩu user",
                "📜 Xem Audit Trail",
                "📜 Xem hoạt động user"
            ]
        )

        if admin_menu == "👤 Thêm user mới":
            from db.admin_user_manage import create_user_form
            create_user_form()
            st.stop()

        elif admin_menu == "🔄 Reset mật khẩu user":
            from db.admin_reset_pw import admin_reset_password
            admin_reset_password()
            st.stop()

        elif admin_menu == "📜 Xem Audit Trail":
            from db.admin_view_audit import view_audit_logs
            view_audit_logs()
            st.stop()

        elif admin_menu == "📜 Xem hoạt động user":
            from log.user_activity_view import view_my_activity
            if st.session_state.get("view_my_log"):
                view_my_activity(user["username"])
                st.stop()
            
    # ===== MENU NGHIỆP VỤ (luôn có cho mọi user) =====
    menu = st.selectbox(
        "Chọn phân hệ",
        [
            "📘 Phôi Thẻ – GTCG",
            "💸 Mục 09 – Chuyển tiền",
            "📑 Tờ khai Hải quan",
            "🏦 Tiêu chí tín dụng CRM4–32",
            "💼 HDV (TC1 – TC3)",
            "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
            "👥 DVKH (5 tiêu chí)",
            "💳 Tiêu chí thẻ",
            "💳 Tiêu chí máy pos",
        ]
    )


# ============================================================
# POPUP ĐỔI MẬT KHẨU (NẾU USER BẤM)
# ============================================================
if st.session_state.get("change_pw"):
    change_password_popup()
    st.stop()


# ============================================================
# MAIN CONTENT
# ============================================================
st.title("📊 CHƯƠNG TRÌNH CHẠY TIÊU CHÍ CHỌN MẪU – KTNB")

if menu == "📘 Phôi Thẻ – GTCG":
    colored_header("📘 PHÔI THẺ – GTCG")
    run_phoi_the()

elif menu == "💸 Mục 09 – Chuyển tiền":
    colored_header("💸 CHUYỂN TIỀN")
    log_user_action(user["username"], "CHUYỂN TIỀN")
    run_chuyen_tien()

elif menu == "📑 Tờ khai Hải quan":
    colored_header("📑 TỜ KHAI HẢI QUAN")
    run_to_khai_hq()

elif menu == "🏦 Tiêu chí tín dụng CRM4–32":
    colored_header("🏦 TÍN DỤNG CRM4 – CRM32")
    run_tin_dung()

elif menu == "💼 HDV (TC1 – TC3)":
    colored_header("💼 HDV – TC1 đến TC3")
    run_hdv()

elif menu == "🌏 Ngoại tệ & Vàng (TC5 – TC6)":
    colored_header("🌏 NGOẠI TỆ & VÀNG")
    run_ngoai_te_vang()

elif menu == "👥 DVKH (5 tiêu chí)":
    colored_header("👥 DVKH – 5 TIÊU CHÍ")
    run_dvkh_5_tieuchi()

elif menu == "💳 Tiêu chí thẻ":
    colored_header("💳 TIÊU CHÍ THẺ")
    run_module_the()

elif menu == "💳 Tiêu chí máy pos":
    if not require_role(user, ["admin", "pos"]):
        st.error("🚫 Bạn không có quyền truy cập mục POS")
        st.stop()
    colored_header("💳 TIÊU CHÍ MÁY POS")
    run_module_pos()
