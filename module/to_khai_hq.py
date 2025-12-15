import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime




# ============================================================
# 🔹 HÀM TỰ NHẬN DIỆN & CHUYỂN ĐỊNH DẠNG NGÀY
# ============================================================

REQUIRED_COLUMNS = ["DECLARATION_DUE_DATE", "DECLARATION_RECEIVED_DATE"]


def smart_date_parse(series):

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

    try:
        return pd.to_datetime(
            series,
            errors='coerce',
            dayfirst=dayfirst_detected,
            infer_datetime_format=True,
        )
    except Exception as exc:
        raise UserFacingError(
            "Không thể nhận diện định dạng ngày. Hãy kiểm tra lại dữ liệu ngày trong file TKHQ."
        ) from exc


# ============================================================
# 🔹 XỬ LÝ LOGIC TKHQ
# ============================================================

def process_tkhq_data(df, ngay_kiem_toan):
    """Xử lý logic TKHQ: chuyển ngày, tính quá hạn, xác định gia hạn"""

    normalize_columns(df)

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

    with st.sidebar:
        st.header("Cài đặt và Tải file")
        file = st.file_uploader("📁 Chọn file Excel TKHQ", type=["xlsx"])
        audit_date = st.date_input("📅 Chọn ngày kiểm toán", value=datetime(2025, 5, 31))

    if file is None:
        st.info("⬆️ Vui lòng tải lên file Excel để bắt đầu")
        return

    st.success(f"Đã tải file **{file.name}**")

    def _process():
        with st.spinner("Đang xử lý dữ liệu..."):
