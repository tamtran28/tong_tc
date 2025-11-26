import streamlit as st

# ======================
# Hàm header có màu (tự tạo)
# ======================
def colored_header(title, subtitle="", color="#4A90E2"):
    st.markdown(f"""
        <div style="border-left: 8px solid {color};
                    padding: 8px 12px;
                    margin-top: 15px;
                    margin-bottom: 12px;
                    background-color: #F5F9FF;">
            <h2 style="margin-bottom:0;">{title}</h2>
            <p style="margin-top:2px; opacity:0.8;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)


# ======================
# IMPORT MODULE
# ======================
from module.phoi_the import run_phoi_the
from module.chuyen_tien import run_chuyen_tien
from module.to_khai_hq import run_to_khai_hq
from module.tindung import run_tin_dung
from module.hdv import run_hdv
from module.ngoai_te_vang import run_ngoai_te_vang
from module.DVKH import run_dvkh_5_tieuchi
from module.tieuchithe import run_module_the
from module.module_pos import run_module_pos


# ======================
# SETUP APP
# ======================
st.set_page_config(
    page_title="Chương trình chạy tiêu chí chọn mẫu",
    layout="wide",
    page_icon="📊"
)

st.markdown("""
<style>
div[data-testid="stSidebar"] {
    background-color: #EEF3FF;
}
</style>
""", unsafe_allow_html=True)

st.title("📊 CHƯƠNG TRÌNH CHẠY TIÊU CHÍ CHỌN MẪU – KTNB")


# ======================
# SIDEBAR MENU
# ======================
st.sidebar.title("📘 MENU PHÂN HỆ")

menu = st.sidebar.selectbox(
    "Chọn phân hệ:",
    [
        "📘 Phôi Thẻ – GTCG",
        "💸 Mục 09 – Chuyển tiền",
        "📑 Tờ khai Hải quan",
        "🏦 Tiêu chí tín dụng CRM4–32",
        "💼 HDV (TC1 – TC3)",
        "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
        "👥 DVKH (5 tiêu chí)",
        "💳 Tiêu chí thẻ",
        "💳 Tiêu chí máy pos"
    ]
)


# ======================
# RENDER TỪNG MODULE
# ======================
if menu == "📘 Phôi Thẻ – GTCG":
    colored_header("📘 PHÔI THẺ – GTCG", "Module kiểm tra phôi thẻ", "#2C8DFF")
    run_phoi_the()

elif menu == "💸 Mục 09 – Chuyển tiền":
    colored_header("💸 CHUYỂN TIỀN", "Kiểm tra giao dịch chuyển tiền", "#00BFA5")
    run_chuyen_tien()

elif menu == "📑 Tờ khai Hải quan":
    colored_header("📑 TỜ KHAI HẢI QUAN", "Đối chiếu tờ khai HQ", "#9C27B0")
    run_to_khai_hq()

elif menu == "🏦 Tiêu chí tín dụng CRM4–32":
    colored_header("🏦 TÍN DỤNG CRM4 – CRM32", "Các tiêu chí KTNB", "#FF6F00")
    run_tin_dung()
    
elif menu == "💼 HDV (TC1 – TC3)":
    colored_header("💼 HDV – TC1 đến TC3", "Kiểm tra hoạt động vay", "#795548")
    run_hdv()

elif menu == "🌏 Ngoại tệ & Vàng (TC5 – TC6)":
    colored_header("🌏 NGOẠI TỆ & VÀNG", "Kiểm tra giao dịch", "#D81B60")
    run_ngoai_te_vang()

elif menu == "👥 DVKH (5 tiêu chí)":
    colored_header("👥 DVKH – 5 TIÊU CHÍ", "Đánh giá khách hàng", "#3F51B5")
    run_dvkh_5_tieuchi()

elif menu == "💳 Tiêu chí thẻ":
    colored_header("💳 TIÊU CHÍ THẺ", "Các tiêu chí kiểm toán thẻ", "#009688")
    run_module_the()

elif menu == "💳 Tiêu chí thẻ":
    colored_header("💳 TIÊU CHÍ THẺ", "Các tiêu chí kiểm toán thẻ", "#009688")
     run_module_pos()
    
elif menu == "💳 Tiêu chí máy pos":
    colored_header("💳 TIÊU CHÍ MÁY POS", "Các tiêu chí kiểm toán máy pos", "#009688")
    run_module_pos()



