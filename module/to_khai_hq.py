import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime

# ===============================
# 🔹 HÀM TỰ NHẬN DIỆN & CHUYỂN ĐỊNH DẠNG NGÀY
# ===============================
def smart_date_parse(series):
    """Tự động nhận diện định dạng dd-mm-yyyy hoặc mm-dd-yyyy"""
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

    # Parse theo kết quả phát hiện
    return pd.to_datetime(series, errors='coerce', dayfirst=dayfirst_detected, infer_datetime_format=True)


# ===============================
# 🔹 HÀM XỬ LÝ NGHIỆP VỤ TKHQ
# ===============================
def process_tkhq_data(df, ngay_kiem_toan):
    """
    Hàm xử lý logic TKHQ: chuyển ngày, tính quá hạn, xác định gia hạn.
    """
    # --- 1. Chuẩn hóa tên cột ---
    df.columns = df.columns.str.strip().str.upper()

    # --- 2. Chuyển định dạng ngày (tự nhận diện) ---
    df['DECLARATION_DUE_DATE'] = smart_date_parse(df.get('DECLARATION_DUE_DATE'))
    df['DECLARATION_RECEIVED_DATE'] = smart_date_parse(df.get('DECLARATION_RECEIVED_DATE'))

    # --- 3. (1) Không nhập ngày đến hạn TKHQ ---
    df['KHÔNG NHẬP NGÀY ĐẾN HẠN TKHQ'] = df['DECLARATION_DUE_DATE'].isna().map(lambda x: 'X' if x else '')

    # --- 4. (2) Số ngày quá hạn TKHQ ---
    df['SỐ NGÀY QUÁ HẠN TKHQ'] = df.apply(
        lambda row: (ngay_kiem_toan - row['DECLARATION_DUE_DATE']).days
        if pd.notnull(row['DECLARATION_DUE_DATE'])
        and pd.isnull(row['DECLARATION_RECEIVED_DATE'])
        and (ngay_kiem_toan - row['DECLARATION_DUE_DATE']).days > 0
        else '',
        axis=1
    )

    # --- 5. (3) Quá hạn nhưng chưa nhập TKHQ ---
    so_ngay_qua_han_numeric = pd.to_numeric(df['SỐ NGÀY QUÁ HẠN TKHQ'], errors='coerce')
    df['QUÁ HẠN CHƯA NHẬP TKHQ'] = so_ngay_qua_han_numeric.apply(lambda x: 'X' if pd.notnull(x) and x > 0 else '')

    # --- 6. (4) Quá hạn >90 ngày nhưng chưa nhập TKHQ ---
    df['QUÁ HẠN > 90 NGÀY CHƯA NHẬP TKHQ'] = so_ngay_qua_han_numeric.apply(lambda x: 'X' if pd.notnull(x) and x > 90 else '')

    # --- 7. (5) Có phát sinh gia hạn TKHQ ---
    def check_gia_han(row):
        if 'AUDIT_DATE2' in row and pd.notnull(row['AUDIT_DATE2']):
            return 'X'
        if 'DECLARATION_REF_NO' in row and isinstance(row['DECLARATION_REF_NO'], str):
            text = row['DECLARATION_REF_NO'].lower().replace(" ", "")
            if 'giahan' in text:
                return 'X'
        return ''

    df['CÓ PHÁT SINH GIA HẠN TKHQ'] = df.apply(check_gia_han, axis=1)

    return df


# ===============================
# 🔹 GIAO DIỆN STREAMLIT
# ===============================
def run to_khai_hq()
    st.set_page_config(layout="wide")
    st.title("📊 Ứng dụng Phân tích Tờ khai Hải quan (TKHQ)")
    
    with st.sidebar:
        st.header("Cài đặt và Tải file")
        uploaded_file = st.file_uploader("📁 Chọn file Excel cần phân tích", type=['xlsx'])
        audit_date = st.date_input("📅 Chọn ngày kiểm toán", value=datetime(2025, 5, 31))
    
    # ===============================
    # 🔹 PHẦN XỬ LÝ CHÍNH
    # ===============================
    if uploaded_file is not None:
        st.info(f"Đã tải lên file: **{uploaded_file.name}**")
    
        if st.button("🚀 Bắt đầu xử lý", type="primary"):
            with st.spinner("Đang đọc và xử lý dữ liệu... Vui lòng chờ."):
                try:
                    df_raw = pd.read_excel(uploaded_file)
                    ngay_kiem_toan_pd = pd.to_datetime(audit_date)
    
                    # --- Gọi hàm xử lý ---
                    df_processed = process_tkhq_data(df_raw, ngay_kiem_toan_pd)
    
                    st.success("✅ Xử lý hoàn tất!")
                    st.subheader("📋 Kết quả phân tích")
                    st.dataframe(df_processed)
    
                    # --- Xuất Excel với format ngày chuẩn ---
                    output_buffer = io.BytesIO()
                    with pd.ExcelWriter(output_buffer, engine='openpyxl', date_format='DD-MM-YYYY') as writer:
                        df_processed.to_excel(writer, index=False, sheet_name='ket_qua_TKHQ')
    
                    st.download_button(
                        label="📥 Tải xuống kết quả Excel",
                        data=output_buffer.getvalue(),
                        file_name=f"ket_qua_TKHQ_{audit_date.strftime('%d%m%Y')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
    
                except Exception as e:
                    st.error(f"❌ Đã có lỗi xảy ra: {e}")
    else:
        st.info("⬆️ Vui lòng tải lên một file Excel để bắt đầu.")
