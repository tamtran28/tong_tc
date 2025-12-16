import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ======================================================
#   MODULE: CHUYỂN TIỀN (Mục 09)
# ======================================================

def run_chuyen_tien():

    st.header("🏦 MỤC 09 – CHUYỂN TIỀN RA NƯỚC NGOÀI")

    uploaded = st.file_uploader("📁 Upload file Mục 09 (Chuyển tiền)", type=["xls", "xlsx"])

    if uploaded is None:
        st.info("Vui lòng upload file Mục 09 để xử lý.")
        return

    if st.button("▶️ Chạy Mục 09"):
        df = pd.read_excel(uploaded, dtype=str)

        # ================================
        # XỬ LÝ CÁC CỘT PHỔ BIẾN
        # ================================
        df["AMOUNT"] = pd.to_numeric(df.get("AMOUNT", 0), errors="coerce")
        df["FX_RATE"] = pd.to_numeric(df.get("FX_RATE", 0), errors="coerce")

        # Flag cảnh báo nếu số tiền lớn
        df["GD > 500TR"] = df["AMOUNT"].apply(lambda x: "X" if x >= 500_000_000 else "")

        # Chuyển tiền bất thường (ví dụ: không có invoice)
        df["THIẾU CHỨNG TỪ"] = df.get("INVOICE_NO", "").apply(
            lambda x: "X" if (pd.isna(x) or x == "") else ""
        )

        st.success("✔ Đã xử lý Mục 09")

        st.dataframe(df)

        # ================================
        # XUẤT FILE
        # ================================
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Muc09", index=False)

        st.download_button(
            "⬇️ Tải file Muc09_processed.xlsx",
            data=buffer.getvalue(),
            file_name="Muc09_processed.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


# import streamlit as st
# import pandas as pd
# import numpy as np
# from io import BytesIO

# from module.error_utils import render_error

# # ======================================================
# #   MODULE: CHUYỂN TIỀN (Mục 09)
# # ======================================================

# def run_chuyen_tien():

#     st.header("🏦 MỤC 09 – CHUYỂN TIỀN RA NƯỚC NGOÀI")

#     uploaded = st.file_uploader("📁 Upload file Mục 09 (Chuyển tiền)", type=["xls", "xlsx"])

#     if uploaded is None:
#         st.info("Vui lòng upload file Mục 09 để xử lý.")
#         return

#     if st.button("▶️ Chạy Mục 09"):
#         try:
#             df = pd.read_excel(uploaded, dtype=str)
#         except Exception as exc:  # đọc file lỗi
#             render_error(
#                 "Không thể đọc file Excel. Vui lòng kiểm tra định dạng (.xls, .xlsx) hoặc thử tải lại file.",
#                 exc,
#             )
#             return

#         try:
#             # ================================
#             # XỬ LÝ CÁC CỘT PHỔ BIẾN
#             # ================================
#             df["AMOUNT"] = pd.to_numeric(df.get("AMOUNT", 0), errors="coerce")
#             df["FX_RATE"] = pd.to_numeric(df.get("FX_RATE", 0), errors="coerce")

#             missing_columns = [col for col in ["AMOUNT", "FX_RATE", "INVOICE_NO"] if col not in df.columns]
#             if missing_columns:
#                 st.warning(
#                     "⚠️ File đang thiếu cột: "
#                     + ", ".join(missing_columns)
#                     + ". Một số tiêu chí có thể không được đánh dấu đầy đủ."
#                 )

#             # Flag cảnh báo nếu số tiền lớn
#             df["GD > 500TR"] = df["AMOUNT"].apply(lambda x: "X" if x >= 500_000_000 else "")

#             # Chuyển tiền bất thường (ví dụ: không có invoice)
#             df["THIẾU CHỨNG TỪ"] = df.get("INVOICE_NO", "").apply(
#                 lambda x: "X" if (pd.isna(x) or x == "") else ""
#             )

#             st.success("✔ Đã xử lý Mục 09")

#             st.dataframe(df)

#             # ================================
#             # XUẤT FILE
#             # ================================
#             buffer = BytesIO()
#             with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
#                 df.to_excel(writer, sheet_name="Muc09", index=False)

#             st.download_button(
#                 "⬇️ Tải file Muc09_processed.xlsx",
#                 data=buffer.getvalue(),
#                 file_name="Muc09_processed.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#             )
#         except Exception as exc:  # xử lý lỗi runtime
#             render_error(
#                 "Đã xảy ra lỗi khi xử lý dữ liệu Mục 09. Vui lòng kiểm tra lại định dạng cột và giá trị trong file.",
#                 exc,
#             )
