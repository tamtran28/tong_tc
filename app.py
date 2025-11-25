# ================================
# 📌 APP.PY – HỆ THỐNG KIỂM TOÁN TỔNG HỢP
# ================================

import streamlit as st

# ======================
# Hàm header có màu (tự tạo)
# ======================
def colored_header(title, subtitle="", color="#4A90E2"):
    st.markdown(f"""
        <div style="border-left: 8px solid {color};
                    padding: 8px 12px;
                    margin-top: 15px;
                    margin-bottom: 10px;
                    background-color: #F5F9FF;">
            <h2 style="margin-bottom:0;">{title}</h2>
            <p style="margin-top:2px; opacity:0.8;">{subtitle}</p>
        </div>
    """, unsafe_allow_html=True)


# ======================
# Import các module
# ======================
from module.phoi_the import run_phoi_the
from module.chuyen_tien import run_chuyen_tien
from module.to_khai_hq import run_to_khai_hq
from module.tindung import run_tin_dung
from module.hdv import run_hdv
from module.ngoai_te_vang import run_ngoai_te_vang
from module.DVKH import run_dvkh_5_tieuchi
from module.tieuchithe import run_module_the


# ======================
# SETUP APP
# ======================
st.set_page_config(
    page_title="Hệ thống Kiểm toán tổng hợp",
    layout="wide",
    page_icon="📊"
)

st.title("📊 HỆ THỐNG KIỂM TOÁN TỔNG HỢP – KTNB")


st.markdown("""
<style>
div[data-testid="stSidebar"] {
    background-color: #EEF3FF;
}
</style>
""", unsafe_allow_html=True)


# ======================
# GIAO DIỆN TABS
# ======================

tabs = st.tabs([
    "📘 Phôi Thẻ – GTCG",
    "💸 Mục 09 – Chuyển tiền",
    "📑 Tờ khai Hải quan",
    "🏦 Tiêu chí tín dụng CRM4–32",
    "💼 HDV (TC1 – TC3)",
    "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
    "👥 DVKH (5 tiêu chí)",
    "💳 Tiêu chí thẻ"
])


# ========== TAB 1 ==========
with tabs[0]:
    colored_header("📘 PHÔI THẺ – GTCG", "Module kiểm tra phôi thẻ", "#2C8DFF")
    run_phoi_the()

# ========== TAB 2 ==========
with tabs[1]:
    colored_header("💸 MỤC 09 – CHUYỂN TIỀN", "Kiểm tra giao dịch chuyển tiền", "#00BFA5")
    run_chuyen_tien()

# ========== TAB 3 ==========
with tabs[2]:
    colored_header("📑 TỜ KHAI HẢI QUAN", "Đối chiếu tờ khai HQ", "#9C27B0")
    run_to_khai_hq()

# ========== TAB 4 ==========
with tabs[3]:
    colored_header("🏦 TÍN DỤNG CRM4–CRM32", "Các tiêu chí KTNB full script", "#FF6F00")
    run_tin_dung()

# ========== TAB 5 ==========
with tabs[4]:
    colored_header("💼 HDV – TC1 đến TC3", "Kiểm tra HOẠT ĐỘNG VAY", "#795548")
    run_hdv()

# ========== TAB 6 ==========
with tabs[5]:
    colored_header("🌏 NGOẠI TỆ & VÀNG – TC5 & TC6", "Giao dịch ngoại tệ – vàng", "#D81B60")
    run_ngoai_te_vang()

# ========== TAB 7 ==========
with tabs[6]:
    colored_header("👥 KHÁCH HÀNG – 5 TIÊU CHÍ", "Đánh giá 5 tiêu chí DVKH", "#3F51B5")
    run_dvkh_5_tieuchi()

# ========== TAB 8 ==========
with tabs[7]:
    colored_header("💳 TIÊU CHÍ THẺ – ĐẦY ĐỦ", "Các tiêu chí thẻ 1.3.2", "#009688")
    run_module_the()

