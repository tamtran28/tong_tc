import streamlit as st

# Import các phân hệ
from module.phoi_the import run_phoi_the
from module.chuyen_tien import run_chuyen_tien
from module.to_khai_hq import run_to_khai_hq
from module.tindung import run_tin_dung
from module.hdv import run_hdv
from module.ngoai_te_vang import run_ngoai_te_vang
from module.DVKH import run_dvkh_5_tieuchi
from module.tieuchithe import run_the_module

st.set_page_config(page_title="Hệ thống Kiểm toán tổng hợp", layout="wide")

st.title("📊 HỆ THỐNG KIỂM TOÁN TỔNG HỢP – TẤT CẢ PHÂN HỆ")

# ============================
#  MENU TABS CHÍNH
# ============================

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📘 Phôi Thẻ – GTCG",
    "💸 Mục 09 – Chuyển tiền",
    "📑 Tờ khai Hải quan",
    "🏦 Tiêu chí tín dụng CRM4–32",
    "💼 HDV (TC1 – TC3)",
    "🌏 Ngoại tệ & Vàng (TC5 – TC6)",
    "🌏 DVKH",
    "📑 Tiêu chí thẻ"
])

with tab1:
    run_phoi_the()

with tab2:
    run_chuyen_tien()

with tab3:
    run_to_khai_hq()

with tab4:
    run_tin_dung()

with tab5:
    run_hdv()

with tab6:
    run_ngoai_te_vang()
