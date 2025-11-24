import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ============================================
#   MODULE TỜ KHAI HẢI QUAN – STREAMLIT
# ============================================

def run_to_khai_hq():

    st.header("📄 TỜ KHAI HẢI QUAN – Mục 09 / Mục 19 / Mục 20 / Mục 21")

    st.write("""
    Đây là module xử lý **Tờ khai hải quan** phục vụ kiểm toán.  
    Vui lòng upload đúng các file Excel theo hướng dẫn.
    """)

    # --- Upload các file ---
    muc09_file = st.file_uploader("📁 Upload file *Mục 09 – Chuyển tiền*", type=["xls", "xlsx"])
    muc19_file = st.file_uploader("📁 Upload file *Mục 19 – Mua/Bán ngoại tệ*", type=["xls", "xlsx"])
    muc20_file = st.file_uploader("📁 Upload file *Mục 20 – Rate Request*", type=["xls", "xlsx"])
    muc21_file = st.file_uploader("📁 Upload file *Mục 21 – Forward Contract*", type=["xls", "xlsx"])

    if st.button("▶️ Chạy xử lý Tờ khai Hải quan"):
        missing = []
        if muc09_file is None: missing.append("Mục 09")
        if muc19_file is None: missing.append("Mục 19")
        if muc20_file is None: missing.append("Mục 20")
        if muc21_file is None: missing.append("Mục 21")

        if missing:
            st.error("❌ Thiếu file: " + ", ".join(missing))
            return

        # ====================
        # ĐỌC FILE
        # ====================
        df_m09 = pd.read_excel(muc09_file, dtype=str)
        df_m19 = pd.read_excel(muc19_file, dtype=str)
        df_m20 = pd.read_excel(muc20_file, dtype=str)
        df_m21 = pd.read_excel(muc21_file, dtype=str)

        st.success("✔ Đọc file thành công, bắt đầu xử lý dữ liệu...")

        # ============================
        # 1. XỬ LÝ MỤC 09 – CHUYỂN TIỀN
        # ============================
        df_m09_processed = df_m09.copy()

        # Ví dụ: chuẩn hóa số tiền
        if "AMOUNT" in df_m09_processed.columns:
            df_m09_processed["AMOUNT"] = pd.to_numeric(df_m09_processed["AMOUNT"], errors="coerce")

        # ============================
        # 2. XỬ LÝ MỤC 19 – MUA BÁN NT
        # ============================
        df_m19_processed = df_m19.copy()

        if "SOTIEN_LAI_LO" in df_m19_processed.columns:
            df_m19_processed["SOTIEN_LAI_LO"] = pd.to_numeric(df_m19_processed["SOTIEN_LAI_LO"], errors="coerce")

        df_m19_processed["LỖ > 100K"] = df_m19_processed["SOTIEN_LAI_LO"].apply(
            lambda x: "X" if x < -100000 else ""
        ) if "SOTIEN_LAI_LO" in df_m19_processed.columns else ""

        # ============================
        # 3. GHÉP RATE REQUEST (M20 & M21)
        # ============================
        df_merge_rate = pd.merge(
            df_m20, df_m21,
            left_on="TRAN_ID", right_on="FRWRD_CNTRCT_NUM",
            how="left"
        )

        # ============================
        # 4. HIỂN THỊ KẾT QUẢ
        # ============================
        st.subheader("📌 KẾT QUẢ XỬ LÝ")

        tab1, tab2, tab3, tab4 = st.tabs([
            "Mục 09 – Chuyển tiền",
            "Mục 19 – Mua bán NT",
            "Mục 20 – Rate Request",
            "Ghép Mục 20 + 21"
        ])

        with tab1:
            st.dataframe(df_m09_processed)

        with tab2:
            st.dataframe(df_m19_processed)

        with tab3:
            st.dataframe(df_m20)

        with tab4:
            st.dataframe(df_merge_rate)

        # ============================
        # XUẤT FILE EXCEL
        # ============================
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_m09_processed.to_excel(writer, sheet_name="Muc09", index=False)
            df_m19_processed.to_excel(writer, sheet_name="Muc19", index=False)
            df_m20.to_excel(writer, sheet_name="Muc20", index=False)
            df_merge_rate.to_excel(writer, sheet_name="Muc20_21_Merge", index=False)

        buffer.seek(0)

        st.download_button(
            "⬇️ Tải file Tổng hợp Tờ khai HQ",
            data=buffer,
            file_name="To_khai_hai_quan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.success("🎉 Hoàn tất module Tờ khai Hải quan!")


# END MODULE

