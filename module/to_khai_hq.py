import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

from module.error_utils import ensure_required_columns, render_error, UserFacingError


# ============================================================
# 🔹 HÀM TỰ NHẬN DIỆN & CHUYỂN ĐỊNH DẠNG NGÀY
# ============================================================

def smart_date_parse(series):
    """Tự động nhận diện định dạng dd-mm-yyyy hoặc mm-dd-yyyy"""
    if series is None:
        raise UserFacingError("Thiếu cột ngày bắt buộc trong file TKHQ.")
    series = series.astype(str).str.strip()

    # Heuristic: nếu xuất hiện ngày >12 => dd-mm-yyyy
    pattern = re.compile(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})")
    sample = series.dropna().head(20)
    dayfirst_detected = False
    for val in sample:
        m = pattern.match(val)
        if m:
            day, month = int(m.group(1)), int(m.group(2))
            if day > 12:
                dayfirst_detected = True
                break

    return pd.to_datetime(series, errors='coerce', dayfirst=dayfirst_detected, infer_datetime_format=True)


# ============================================================
# 🔹 XỬ LÝ LOGIC TKHQ
# ============================================================

def process_tkhq_data(df, ngay_kiem_toan):
    """Xử lý logic TKHQ: chuyển ngày, tính quá hạn, xác định gia hạn"""

    df.columns = df.columns.str.strip().str.upper()

    # Chuyển ngày
    df["DECLARATION_DUE_DATE"] = smart_date_parse(df.get("DECLARATION_DUE_DATE"))
    df["DECLARATION_RECEIVED_DATE"] = smart_date_parse(df.get("DECLARATION_RECEIVED_DATE"))

    # (1) Không nhập ngày đến hạn
    df["KHÔNG NHẬP NGÀY ĐẾN HẠN TKHQ"] = df["DECLARATION_DUE_DATE"].isna().map(lambda x: "X" if x else "")

    # (2) Số ngày quá hạn
    df["SỐ NGÀY QUÁ HẠN TKHQ"] = df.apply(
        lambda row: (ngay_kiem_toan - row["DECLARATION_DUE_DATE"]).days
        if pd.notnull(row["DECLARATION_DUE_DATE"])
        and pd.isnull(row["DECLARATION_RECEIVED_DATE"])
        and (ngay_kiem_toan - row["DECLARATION_DUE_DATE"]).days > 0
        else "",
        axis=1
    )

    # numeric
    so_ngay_qua_han_numeric = pd.to_numeric(df["SỐ NGÀY QUÁ HẠN TKHQ"], errors="coerce")

    # (3) Quá hạn chưa nhập TKHQ
    df["QUÁ HẠN CHƯA NHẬP TKHQ"] = so_ngay_qua_han_numeric.apply(lambda x: "X" if pd.notnull(x) and x > 0 else "")

    # (4) Quá hạn >90 ngày
    df["QUÁ HẠN > 90 NGÀY CHƯA NHẬP TKHQ"] = so_ngay_qua_han_numeric.apply(lambda x: "X" if pd.notnull(x) and x > 90 else "")

    # (5) Phát sinh gia hạn
    def check_gia_han(row):
        if "AUDIT_DATE2" in row and pd.notnull(row["AUDIT_DATE2"]):
            return "X"
        if "DECLARATION_REF_NO" in row and isinstance(row["DECLARATION_REF_NO"], str):
            if "giahan" in row["DECLARATION_REF_NO"].lower().replace(" ", ""):
                return "X"
        return ""

    df["CÓ PHÁT SINH GIA HẠN TKHQ"] = df.apply(check_gia_han, axis=1)

    return df


# ============================================================
# 🔹 GIAO DIỆN STREAMLIT
# ============================================================

def run_to_khai_hq():

    st.title("📊 Ứng dụng Phân tích Tờ khai Hải quan (TKHQ)")

    # Sidebar
    with st.sidebar:
        st.header("Cài đặt và Tải file")
        file = st.file_uploader("📁 Chọn file Excel TKHQ", type=["xlsx"])
        audit_date = st.date_input("📅 Chọn ngày kiểm toán", value=datetime(2025, 5, 31))

    # Nếu chưa upload file
    if file is None:
        st.info("⬆️ Vui lòng tải lên file Excel để bắt đầu")
        return

    st.success(f"Đã tải file **{file.name}**")

    if st.button("🚀 Bắt đầu xử lý", type="primary"):
        with st.spinner("Đang xử lý dữ liệu..."):

            try:
                df_raw = pd.read_excel(file)
                ensure_required_columns(
                    df_raw,
                    [
                        "DECLARATION_DUE_DATE",
                        "DECLARATION_RECEIVED_DATE",
                    ],
                )

                ngay_kiem_toan_pd = pd.to_datetime(audit_date)
                df_processed = process_tkhq_data(df_raw, ngay_kiem_toan_pd)

                st.success("✅ Xử lý hoàn tất!")

                st.subheader("📋 Kết quả phân tích")
                st.dataframe(df_processed)

                # Xuất Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl", date_format="DD-MM-YYYY") as writer:
                    df_processed.to_excel(writer, index=False, sheet_name="ket_qua_TKHQ")

                st.download_button(
                    "📥 Tải xuống kết quả Excel",
                    output.getvalue(),
                    file_name=f"ket_qua_TKHQ_{audit_date.strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except UserFacingError as exc:
                render_error(str(exc))
            except Exception as exc:
                render_error(
                    "Không thể xử lý file TKHQ. Vui lòng kiểm tra định dạng ngày, tên cột và thử lại.",
                    exc,
                )
