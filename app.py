import streamlit as st

# ==== LOGIN SYSTEM ====
from db.login_page import show_login_page, logout_button
from db.auth_jwt import is_authenticated, get_current_user
from db.security import require_role

from db.seed_users import seed_users
from db.change_pw import change_password_popup

# ==== LOGGING SYSTEM ====
from db.user_logs import init_user_logs_table, log_user_action


# ==== KHỞI TẠO DB ====
seed_users()
init_user_logs_table()

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
# SIDEBAR — LUÔN CÓ
# ============================================================
with st.sidebar:
    st.markdown(f"👤 **{user['full_name']}**  \n🔑 Quyền: **{user['role']}**")

    # Xem lịch sử hoạt động của chính mình
    if st.button("📜 Nhật ký hoạt động của tôi"):
        st.session_state["view_user_log"] = True

    # Đổi mật khẩu
    if st.button("🔐 Đổi mật khẩu"):
        st.session_state["change_pw"] = True

    logout_button()

    # --------------------------------------------------------
    # ADMIN TOOLS
    # --------------------------------------------------------
    if user["role"] == "admin":
        st.markdown("### 🔧 Admin Tools")

        admin_menu = st.selectbox(
            "Chọn chức năng quản trị",
            [
                "— Chọn chức năng —",
                "👤 Thêm user mới",
                "🔄 Reset mật khẩu user",
                "📜 Xem toàn bộ Audit Trail"
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

        elif admin_menu == "📜 Xem toàn bộ Audit Trail":
            logs = get_all_logs()
            st.subheader("📜 Audit Trail – Nhật ký hoạt động toàn hệ thống")
            st.dataframe(
                [{"User": u, "Action": a, "Detail": d, "Time": t} for u, a, d, t in logs],
                use_container_width=True
            )
            st.stop()

    # --------------------------------------------------------
    # MENU NGHIỆP VỤ
    # --------------------------------------------------------
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

# GHI LOG MENU
log_user_action(user["username"], "CHỌN MENU", menu)


# ============================================================
# POPUP ĐỔI MẬT KHẨU
# ============================================================
if st.session_state.get("change_pw"):
    change_password_popup()
    st.stop()


# ============================================================
# USER XEM LOG CỦA MÌNH
# ============================================================
if st.session_state.get("view_user_log"):
    st.subheader("📜 Lịch sử hoạt động của bạn")

    logs = get_user_logs(user["username"])
    if logs:
        st.table([
            {"Hành động": a, "Chi tiết": d, "Thời gian": t}
            for a, d, t in logs
        ])
    else:
        st.info("Chưa có dữ liệu log.")

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


# import streamlit as st

# # ==== LOGIN SYSTEM ====
# from db.login_page import show_login_page, logout_button
# from db.auth_jwt import is_authenticated, get_current_user
# from db.security import require_role

# from db.seed_users import seed_users
# from db.change_pw import change_password_popup

# seed_users()

# # ==== MODULE NGHIỆP VỤ ====
# from module.phoi_the import run_phoi_the
# from module.chuyen_tien import run_chuyen_tien
# from module.to_khai_hq import run_to_khai_hq
# from module.tindung import run_tin_dung
# from module.hdv import run_hdv
# from module.ngoai_te_vang import run_ngoai_te_vang
# from module.DVKH import run_dvkh_5_tieuchi
# from module.tieuchithe import run_module_the
# from module.module_pos import run_module_pos


# # ==== HEADER UI ====
# def colored_header(title, subtitle="", color="#4A90E2"):
#     st.markdown(
#         f"""
#         <div style="border-left: 8px solid {color};
#                     padding: 8px 12px;
#                     margin-top: 10px;
#                     margin-bottom: 12px;
#                     background-color: #F5F9FF;">
#             <h2>{title}</h2>
#             <p style="opacity:0.7;">{subtitle}</p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# # ============================================================
# # 🔐 KIỂM TRA LOGIN
# # ============================================================
# if not is_authenticated():
#     show_login_page()
#     st.stop()

# user = get_current_user()


# # ============================================================
# # SIDEBAR — LUÔN ĐƯỢC TẠO (KHÔNG BỊ LỖI menu not defined)
# # ============================================================
# with st.sidebar:
#     st.markdown(f"👤 **{user['full_name']}**  \n🔑 Quyền: **{user['role']}**")

#     # nút đổi mật khẩu
#     if st.button("🔐 Đổi mật khẩu"):
#         st.session_state["change_pw"] = True

#     logout_button()

#     # ===== ADMIN TOOLS =====
#     if user["role"] == "admin":
#         st.markdown("### 🔧 Admin Tools")

#         admin_menu = st.selectbox(
#             "Chọn chức năng quản trị",
#             [
#                 "— Chọn chức năng —",
#                 "👤 Thêm user mới",
#                 "🔄 Reset mật khẩu user",
#                 "📜 Xem Audit Trail"
#             ]
#         )

#         if admin_menu == "👤 Thêm user mới":
#             from db.admin_user_manage import create_user_form
#             create_user_form()
#             st.stop()

#         elif admin_menu == "🔄 Reset mật khẩu user":
#             from db.admin_reset_pw import admin_reset_password
#             admin_reset_password()
#             st.stop()

#         elif admin_menu == "📜 Xem Audit Trail":
#             from db.admin_view_audit import view_audit_logs
#             view_audit_logs()
#             st.stop()

#     # ===== MENU NGHIỆP VỤ (luôn có cho mọi user) =====
#     menu = st.selectbox(
#         "Chọn phân hệ",
#         [
#             "📘 Phôi Thẻ – GTCG",
#             "💸 Mục 09 – Chuyển tiền",
#             "📑 Tờ khai Hải quan",
#             "🏦 Tiêu chí tín dụng CRM4–32",
#             "💼 HDV (TC1 – TC3)",
#             "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
#             "👥 DVKH (5 tiêu chí)",
#             "💳 Tiêu chí thẻ",
#             "💳 Tiêu chí máy pos",
#         ]
#     )


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


# import streamlit as st

# # ==== IMPORT LOGIN SYSTEM (JWT + DB) ====
# from db.login_page import show_login_page, logout_button
# from db.auth_jwt import is_authenticated, get_current_user
# from db.security import require_role

# from db.seed_users import seed_users
# from db.change_pw import change_password_popup

# # from db.admin_user_manage import create_user_form
# # from db.admin_view_audit import view_audit_logs

# seed_users()  # tạo user mặc định nếu chưa có


# # ==== IMPORT MODULE NGHIỆP VỤ ====
# from module.phoi_the import run_phoi_the
# from module.chuyen_tien import run_chuyen_tien
# from module.to_khai_hq import run_to_khai_hq
# from module.tindung import run_tin_dung
# from module.hdv import run_hdv
# from module.ngoai_te_vang import run_ngoai_te_vang
# from module.DVKH import run_dvkh_5_tieuchi
# from module.tieuchithe import run_module_the
# from module.module_pos import run_module_pos


# # ==== HEADER UI ====
# def colored_header(title, subtitle="", color="#4A90E2"):
#     st.markdown(
#         f"""
#         <div style="border-left: 8px solid {color};
#                     padding: 8px 12px;
#                     margin-top: 15px;
#                     margin-bottom: 12px;
#                     background-color: #F5F9FF;">
#             <h2 style="margin-bottom:0;">{title}</h2>
#             <p style="margin-top:2px; opacity:0.8;">{subtitle}</p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# # =====================
# # 🔐 KIỂM TRA ĐĂNG NHẬP
# # =====================
# if not is_authenticated():
#     show_login_page()
#     st.stop()

# user = get_current_user()


# # ===== SIDEBAR =====
# with st.sidebar:
#     st.markdown(f"👤 **{user['full_name']}**  \n🔑 Quyền: **{user['role']}**")

#     # nút đổi mật khẩu
#     if st.button("🔐 Đổi mật khẩu"):
#         st.session_state["change_pw"] = True

#     # nút đăng xuất
#     logout_button()

#    # ========== ADMIN MENU ==========
# if user["role"] == "admin":

#     st.markdown("### 🔧 Admin Tools")

#     admin_menu = st.selectbox(
#         "Chọn chức năng quản trị:",
#         [
#             "— Chọn chức năng —",
#             "👤 Thêm user mới",
#             "🔄 Reset mật khẩu user",
#             "📜 Xem Audit Trail (nhật ký hoạt động)"
#         ]
#     )

#     # 1) Thêm user mới
#     if admin_menu == "👤 Thêm user mới":
#         from db.admin_user_manage import create_user_form
#         create_user_form()
#         st.stop()

#     # 3) Xem nhật ký hoạt động
#     elif admin_menu == "📜 Xem Audit Trail (nhật ký hoạt động)":
#         from db.admin_view_audit import view_audit_logs
#         view_audit_logs()
#         st.stop()


#     # menu phân hệ
#     menu = st.selectbox(
#         "Chọn phân hệ",
#         [
#             "📘 Phôi Thẻ – GTCG",
#             "💸 Mục 09 – Chuyển tiền",
#             "📑 Tờ khai Hải quan",
#             "🏦 Tiêu chí tín dụng CRM4–32",
#             "💼 HDV (TC1 – TC3)",
#             "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
#             "👥 DVKH (5 tiêu chí)",
#             "💳 Tiêu chí thẻ",
#             "💳 Tiêu chí máy pos",
#         ]
#     )


# # ========== SHOW POPUP ĐỔI MẬT KHẨU ==========
# if st.session_state.get("change_pw"):
#     change_password_popup()
#     st.stop()


# # ========== MAIN CONTENT ==========
# st.title("📊 CHƯƠNG TRÌNH CHẠY TIÊU CHÍ CHỌN MẪU – KTNB")


# if menu == "📘 Phôi Thẻ – GTCG":
#     colored_header("📘 PHÔI THẺ – GTCG", "Module kiểm tra phôi thẻ", "#2C8DFF")
#     run_phoi_the()

# elif menu == "💸 Mục 09 – Chuyển tiền":
#     colored_header("💸 CHUYỂN TIỀN", "Kiểm tra giao dịch chuyển tiền", "#00BFA5")
#     run_chuyen_tien()

# elif menu == "📑 Tờ khai Hải quan":
#     colored_header("📑 TỜ KHAI HẢI QUAN", "Đối chiếu tờ khai HQ", "#9C27B0")
#     run_to_khai_hq()

# elif menu == "🏦 Tiêu chí tín dụng CRM4–32":
#     colored_header("🏦 TÍN DỤNG CRM4 – CRM32", "Các tiêu chí KTNB", "#FF6F00")
#     run_tin_dung()

# elif menu == "💼 HDV (TC1 – TC3)":
#     colored_header("💼 HDV – TC1 đến TC3", "Kiểm tra hoạt động vay", "#795548")
#     run_hdv()

# elif menu == "🌏 Ngoại tệ & Vàng (TC5 – TC6)":
#     colored_header("🌏 NGOẠI TỆ & VÀNG", "Kiểm tra giao dịch", "#D81B60")
#     run_ngoai_te_vang()

# elif menu == "👥 DVKH (5 tiêu chí)":
#     colored_header("👥 DVKH – 5 TIÊU CHÍ", "Đánh giá khách hàng", "#3F51B5")
#     run_dvkh_5_tieuchi()

# elif menu == "💳 Tiêu chí thẻ":
#     colored_header("💳 TIÊU CHÍ THẺ", "Các tiêu chí kiểm toán thẻ", "#009688")
#     run_module_the()

# elif menu == "💳 Tiêu chí máy pos":
#     # Bảo vệ phân quyền POS
#     if not require_role(user, ["pos", "admin"]):
#         st.error("🚫 Bạn không có quyền truy cập mục này.")
#         st.stop()

#     colored_header("💳 TIÊU CHÍ MÁY POS", "Các tiêu chí kiểm toán máy pos", "#009688")
#     run_module_pos()


# import streamlit as st
# from db.login_page import show_login_page, logout_button
# from db.auth_jwt import is_authenticated, get_current_user
# from db.security import require_role

# #capnhatmk
# from db.change_pw import change_password_popup
# # IMPORT MODULE NGHIỆP VỤ
# # from module.module_pos import run_module_pos
# ...
# from db.seed_users import seed_users
# seed_users()
# # ===== IMPORT MODULE NGHIỆP VỤ =====
# from module.phoi_the import run_phoi_the
# from module.chuyen_tien import run_chuyen_tien
# from module.to_khai_hq import run_to_khai_hq
# from module.tindung import run_tin_dung
# from module.hdv import run_hdv
# from module.ngoai_te_vang import run_ngoai_te_vang
# from module.DVKH import run_dvkh_5_tieuchi
# from module.tieuchithe import run_module_the
# from module.module_pos import run_module_pos


# # ===== HEADER UI =====
# def colored_header(title, subtitle="", color="#4A90E2"):
#     st.markdown(
#         f"""
#         <div style="border-left: 8px solid {color};
#                     padding: 8px 12px;
#                     margin-top: 15px;
#                     margin-bottom: 12px;
#                     background-color: #F5F9FF;">
#             <h2 style="margin-bottom:0;">{title}</h2>
#             <p style="margin-top:2px; opacity:0.8;">{subtitle}</p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )
# # ========== LOGIN ==========
# if not is_authenticated():
#     show_login_page()
#     st.stop()

# user = get_current_user()

# # ========== SIDEBAR ==========
# with st.sidebar:
#     st.markdown(f"👤 {user['full_name']} ({user['role']})")
#     logout_button()
   

# # ========= MENU ==========
# menu = st.sidebar.selectbox("Chọn phân hệ", [
#             "📘 Phôi Thẻ – GTCG",
#             "💸 Mục 09 – Chuyển tiền",
#             "📑 Tờ khai Hải quan",
#             "🏦 Tiêu chí tín dụng CRM4–32",
#             "💼 HDV (TC1 – TC3)",
#             "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
#             "👥 DVKH (5 tiêu chí)",
#             "💳 Tiêu chí thẻ",
#             "💳 Tiêu chí máy pos",])

# st.title("📊 CHƯƠNG TRÌNH CHẠY TIÊU CHÍ CHỌN MẪU – KTNB")

# if menu == "📘 Phôi Thẻ – GTCG":
#     colored_header("📘 PHÔI THẺ – GTCG", "Module kiểm tra phôi thẻ", "#2C8DFF")
#     run_phoi_the()

# elif menu == "💸 Mục 09 – Chuyển tiền":
#     colored_header("💸 CHUYỂN TIỀN", "Kiểm tra giao dịch chuyển tiền", "#00BFA5")
#     run_chuyen_tien()

# elif menu == "📑 Tờ khai Hải quan":
#     colored_header("📑 TỜ KHAI HẢI QUAN", "Đối chiếu tờ khai HQ", "#9C27B0")
#     run_to_khai_hq()

# elif menu == "🏦 Tiêu chí tín dụng CRM4–32":
#     colored_header("🏦 TÍN DỤNG CRM4 – CRM32", "Các tiêu chí KTNB", "#FF6F00")
#     run_tin_dung()

# elif menu == "💼 HDV (TC1 – TC3)":
#     colored_header("💼 HDV – TC1 đến TC3", "Kiểm tra hoạt động vay", "#795548")
#     run_hdv()

# elif menu == "🌏 Ngoại tệ & Vàng (TC5 – TC6)":
#     colored_header("🌏 NGOẠI TỆ & VÀNG", "Kiểm tra giao dịch", "#D81B60")
#     run_ngoai_te_vang()

# elif menu == "👥 DVKH (5 tiêu chí)":
#     colored_header("👥 DVKH – 5 TIÊU CHÍ", "Đánh giá khách hàng", "#3F51B5")
#     run_dvkh_5_tieuchi()

# elif menu == "💳 Tiêu chí thẻ":
#     colored_header("💳 TIÊU CHÍ THẺ", "Các tiêu chí kiểm toán thẻ", "#009688")
#     run_module_the()

# # elif menu == "💳 Tiêu chí máy pos":
# #     require_role("pos")   # kiểm tra quyền POS
# #     colored_header("💳 TIÊU CHÍ MÁY POS", "Các tiêu chí kiểm toán máy pos", "#009688")
# #     run_module_pos()

# if menu == "💳 Tiêu chí máy pos":
#     if not require_role(user, ["pos", "admin"]):
#         st.error("🚫 Bạn không có quyền truy cập mục này.")
#         st.stop()
#     run_module_pos()


# import sys, os
# sys.path.append(os.path.dirname(__file__))
# sys.path.append(os.path.join(os.path.dirname(__file__), "db"))
# sys.path.append(os.path.join(os.path.dirname(__file__), "module"))

# import streamlit as st

# # ===== IMPORT LOGIN / AUTH =====
# from db.login_page import show_login_page, is_authenticated
# from db.auth_jwt import get_current_user, logout
# from db.security import require_role   # <--- IMPORT CHUẨN

# # ===== IMPORT MODULE NGHIỆP VỤ =====
# from module.phoi_the import run_phoi_the
# from module.chuyen_tien import run_chuyen_tien
# from module.to_khai_hq import run_to_khai_hq
# from module.tindung import run_tin_dung
# from module.hdv import run_hdv
# from module.ngoai_te_vang import run_ngoai_te_vang
# from module.DVKH import run_dvkh_5_tieuchi
# from module.tieuchithe import run_module_the
# from module.module_pos import run_module_pos


# # ===== HEADER UI =====
# def colored_header(title, subtitle="", color="#4A90E2"):
#     st.markdown(
#         f"""
#         <div style="border-left: 8px solid {color};
#                     padding: 8px 12px;
#                     margin-top: 15px;
#                     margin-bottom: 12px;
#                     background-color: #F5F9FF;">
#             <h2 style="margin-bottom:0;">{title}</h2>
#             <p style="margin-top:2px; opacity:0.8;">{subtitle}</p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# # ======================
# # SETUP PAGE
# # ======================
# st.set_page_config(
#     page_title="Chương trình chạy tiêu chí chọn mẫu",
#     layout="wide",
#     page_icon="📊",
# )

# st.markdown(
#     """
# <style>
# div[data-testid="stSidebar"] {
#     background-color: #EEF3FF;
# }
# </style>
# """,
#     unsafe_allow_html=True,
# )

# # ======================
# # KIỂM TRA ĐĂNG NHẬP — PHẢI ĐẶT TRÊN CÙNG
# # ======================
# if not is_authenticated():
#     show_login_page()
#     st.stop()

# # Đã đăng nhập → lấy thông tin user
# user = get_current_user()


# # ======================
# # SIDEBAR
# # ======================
# with st.sidebar:
#     st.title("📘 MENU PHÂN HỆ")

#     # Info user
#     st.markdown(
#         f"👤 **{user.get('full_name', user['username'])}**  \n"
#         f"🔑 Quyền: **{user.get('role','user')}**"
#     )

#     # Nút logout
#     if st.button("🚪 Đăng xuất"):
#         logout()
#         st.experimental_rerun()

#     # MENU
#     menu = st.selectbox(
#         "Chọn phân hệ:",
#         [
#             "📘 Phôi Thẻ – GTCG",
#             "💸 Mục 09 – Chuyển tiền",
#             "📑 Tờ khai Hải quan",
#             "🏦 Tiêu chí tín dụng CRM4–32",
#             "💼 HDV (TC1 – TC3)",
#             "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
#             "👥 DVKH (5 tiêu chí)",
#             "💳 Tiêu chí thẻ",
#             "💳 Tiêu chí máy pos",
#         ],
#     )


# # ======================
# # HIỂN THỊ MODULE
# # ======================

# st.title("📊 CHƯƠNG TRÌNH CHẠY TIÊU CHÍ CHỌN MẪU – KTNB")

# if menu == "📘 Phôi Thẻ – GTCG":
#     colored_header("📘 PHÔI THẺ – GTCG", "Module kiểm tra phôi thẻ", "#2C8DFF")
#     run_phoi_the()

# elif menu == "💸 Mục 09 – Chuyển tiền":
#     colored_header("💸 CHUYỂN TIỀN", "Kiểm tra giao dịch chuyển tiền", "#00BFA5")
#     run_chuyen_tien()

# elif menu == "📑 Tờ khai Hải quan":
#     colored_header("📑 TỜ KHAI HẢI QUAN", "Đối chiếu tờ khai HQ", "#9C27B0")
#     run_to_khai_hq()

# elif menu == "🏦 Tiêu chí tín dụng CRM4–32":
#     colored_header("🏦 TÍN DỤNG CRM4 – CRM32", "Các tiêu chí KTNB", "#FF6F00")
#     run_tin_dung()

# elif menu == "💼 HDV (TC1 – TC3)":
#     colored_header("💼 HDV – TC1 đến TC3", "Kiểm tra hoạt động vay", "#795548")
#     run_hdv()

# elif menu == "🌏 Ngoại tệ & Vàng (TC5 – TC6)":
#     colored_header("🌏 NGOẠI TỆ & VÀNG", "Kiểm tra giao dịch", "#D81B60")
#     run_ngoai_te_vang()

# elif menu == "👥 DVKH (5 tiêu chí)":
#     colored_header("👥 DVKH – 5 TIÊU CHÍ", "Đánh giá khách hàng", "#3F51B5")
#     run_dvkh_5_tieuchi()

# elif menu == "💳 Tiêu chí thẻ":
#     colored_header("💳 TIÊU CHÍ THẺ", "Các tiêu chí kiểm toán thẻ", "#009688")
#     run_module_the()

# elif menu == "💳 Tiêu chí máy pos":
#     require_role("pos")   # kiểm tra quyền POS
#     colored_header("💳 TIÊU CHÍ MÁY POS", "Các tiêu chí kiểm toán máy pos", "#009688")
#     run_module_pos()




# import streamlit as st

# # ======================
# # Hàm header có màu (tự tạo)
# # ======================
# def colored_header(title, subtitle="", color="#4A90E2"):
#     st.markdown(f"""
#         <div style="border-left: 8px solid {color};
#                     padding: 8px 12px;
#                     margin-top: 15px;
#                     margin-bottom: 12px;
#                     background-color: #F5F9FF;">
#             <h2 style="margin-bottom:0;">{title}</h2>
#             <p style="margin-top:2px; opacity:0.8;">{subtitle}</p>
#         </div>
#     """, unsafe_allow_html=True)


# # ======================
# # IMPORT MODULE
# # ======================
# from module.phoi_the import run_phoi_the
# from module.chuyen_tien import run_chuyen_tien
# from module.to_khai_hq import run_to_khai_hq
# from module.tindung import run_tin_dung
# from module.hdv import run_hdv
# from module.ngoai_te_vang import run_ngoai_te_vang
# from module.DVKH import run_dvkh_5_tieuchi
# from module.tieuchithe import run_module_the
# from module.module_pos import run_module_pos


# # ======================
# # SETUP APP
# # ======================
# st.set_page_config(
#     page_title="Chương trình chạy tiêu chí chọn mẫu",
#     layout="wide",
#     page_icon="📊"
# )

# st.markdown("""
# <style>
# div[data-testid="stSidebar"] {
#     background-color: #EEF3FF;
# }
# </style>
# """, unsafe_allow_html=True)

# st.title("📊 CHƯƠNG TRÌNH CHẠY TIÊU CHÍ CHỌN MẪU – KTNB")


# # ======================
# # SIDEBAR MENU
# # ======================
# st.sidebar.title("📘 MENU PHÂN HỆ")

# menu = st.sidebar.selectbox(
#     "Chọn phân hệ:",
#     [
#         "📘 Phôi Thẻ – GTCG",
#         "💸 Mục 09 – Chuyển tiền",
#         "📑 Tờ khai Hải quan",
#         "🏦 Tiêu chí tín dụng CRM4–32",
#         "💼 HDV (TC1 – TC3)",
#         "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
#         "👥 DVKH (5 tiêu chí)",
#         "💳 Tiêu chí thẻ",
#         "💳 Tiêu chí máy pos"
#     ]
# )


# # ======================
# # RENDER TỪNG MODULE
# # ======================
# if menu == "📘 Phôi Thẻ – GTCG":
#     colored_header("📘 PHÔI THẺ – GTCG", "Module kiểm tra phôi thẻ", "#2C8DFF")
#     run_phoi_the()

# elif menu == "💸 Mục 09 – Chuyển tiền":
#     colored_header("💸 CHUYỂN TIỀN", "Kiểm tra giao dịch chuyển tiền", "#00BFA5")
#     run_chuyen_tien()

# elif menu == "📑 Tờ khai Hải quan":
#     colored_header("📑 TỜ KHAI HẢI QUAN", "Đối chiếu tờ khai HQ", "#9C27B0")
#     run_to_khai_hq()

# elif menu == "🏦 Tiêu chí tín dụng CRM4–32":
#     colored_header("🏦 TÍN DỤNG CRM4 – CRM32", "Các tiêu chí KTNB", "#FF6F00")
#     run_tin_dung()
    
# elif menu == "💼 HDV (TC1 – TC3)":
#     colored_header("💼 HDV – TC1 đến TC3", "Kiểm tra hoạt động vay", "#795548")
#     run_hdv()

# elif menu == "🌏 Ngoại tệ & Vàng (TC5 – TC6)":
#     colored_header("🌏 NGOẠI TỆ & VÀNG", "Kiểm tra giao dịch", "#D81B60")
#     run_ngoai_te_vang()

# elif menu == "👥 DVKH (5 tiêu chí)":
#     colored_header("👥 DVKH – 5 TIÊU CHÍ", "Đánh giá khách hàng", "#3F51B5")
#     run_dvkh_5_tieuchi()

# elif menu == "💳 Tiêu chí thẻ":
#     colored_header("💳 TIÊU CHÍ THẺ", "Các tiêu chí kiểm toán thẻ", "#009688")
#     run_module_the()
 
# elif menu == "💳 Tiêu chí máy pos":
#     colored_header("💳 TIÊU CHÍ MÁY POS", "Các tiêu chí kiểm toán máy pos", "#009688")
#     run_module_pos()



