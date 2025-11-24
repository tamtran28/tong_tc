import streamlit as st
from streamlit_extras.colored_header import colored_header
from streamlit_extras.switch_page_button import switch_page

# Import các phân hệ
from module.phoi_the import run_phoi_the
from module.chuyen_tien import run_chuyen_tien
from module.to_khai_hq import run_to_khai_hq
from module.tindung import run_tin_dung
from module.hdv import run_hdv
from module.ngoai_te_vang import run_ngoai_te_vang
from module.DVKH import run_dvkh_5_tieuchi
from module.tieuchithe import run_module_the

# ==================================
# CẤU HÌNH GIAO DIỆN
# ==================================

st.set_page_config(
    page_title="Hệ thống Kiểm toán tổng hợp",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS LÀM ĐẸP
st.markdown("""
<style>
    .main {
        background-color: #f4f6f9;
    }
    .block-container {
        padding-top: 1rem;
    }
    .header-title {
        font-size: 30px !important;
        font-weight: 900 !important;
        color: #1b4f72;
        text-align: center;
        padding: 10px;
    }
    .module-box {
        background: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
        margin-top: 10px;
    }
    .stTabs [role="tab"] {
        font-size: 18px;
        font-weight: 600;
        padding: 12px 20px;
    }
    .stTabs [role="tab"][aria-selected="true"] {
        background: #1b4f7222;
        border-bottom: 4px solid #1b4f72 !important;
        color: #1b4f72 !important;
    }
</style>
""", unsafe_allow_html=True)


# ==================================
# HEADER
# ==================================

st.markdown("<div class='header-title'>📊 HỆ THỐNG KIỂM TOÁN TỔNG HỢP NGÂN HÀNG</div>", unsafe_allow_html=True)
st.markdown("##### Hỗ trợ toàn bộ các phân hệ kiểm toán nội bộ – phiên bản Streamlit Dashboard.")


# ==================================
# MENU TABS
# ==================================

tabs = st.tabs([
    "📘 Phôi Thẻ – GTCG",
    "💸 Mục 09 – Chuyển tiền",
    "📑 Tờ khai Hải quan",
    "🏦 Tín dụng CRM4–32",
    "💼 HDV (TC1 – TC3)",
    "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
    "👥 DVKH",
    "📇 Tiêu chí thẻ"
])

with tabs[0]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_phoi_the()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[1]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_chuyen_tien()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[2]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_to_khai_hq()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[3]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_tin_dung()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[4]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_hdv()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[5]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_ngoai_te_vang()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[6]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_dvkh_5_tieuchi()
    st.markdown("</div>", unsafe_allow_html=True)

with tabs[7]:
    st.markdown("<div class='module-box'>", unsafe_allow_html=True)
    run_module_the()
    st.markdown("</div>", unsafe_allow_html=True)
