import io
import numpy as np
import pandas as pd
import streamlit as st

# ======================================================
#   MODULE: NGOẠI TỆ & VÀNG (FULL TIÊU CHÍ 1 → 6)
# ======================================================

def run_ngoai_te_vang():

    st.header("💱 NGHIỆP VỤ MUA BÁN NGOẠI TỆ / VÀNG – FULL 6 TIÊU CHÍ")

    st.set_page_config(page_title="Xử lý giao dịch Ngoại tệ", layout="wide")
    
    st.title("📊 HỆ THỐNG XỬ LÝ GIAO DỊCH NGOẠI TỆ – STREAMLIT")
    
    # ======================================================
    # UPLOAD FILES
    # ======================================================
    st.header("📂 Tải lên dữ liệu nguồn")
    
    file_fx = st.file_uploader("Upload file MUC49_1002 (FX)", type=["xlsx"])
    file_a = st.file_uploader("Upload file MUC20_1002", type=["xlsx"])
    file_b = st.file_uploader("Upload file MUC21_1002", type=["xlsx"])
    file_muc19 = st.file_uploader("Upload file MUC19_1002", type=["xlsx"])
    
    if st.button("⚡ Chạy xử lý dữ liệu"):
        if not all([file_fx, file_a, file_b, file_muc19]):
            st.error("⚠ Vui lòng upload đầy đủ 4 file!")
            st.stop()
    
        # Đọc file
        df_fx = pd.read_excel(file_fx)
        df_a = pd.read_excel(file_a)
        df_b = pd.read_excel(file_b)
        df_muc19 = pd.read_excel(file_muc19)
    
        # ======================================================
        # BẮT ĐẦU QUY TRÌNH XỬ LÝ df_filtered (FX)
        # ======================================================
        df_filtered = df_fx[(df_fx['CRNCY_PURCHSD'] != 'GD1') &
                            (df_fx['CRNCY_SOLD'] != 'GD1')].copy()
    
        # Bước lọc dealer
        filter_dot = df_filtered['DEALER'].astype(str).str.contains('.', regex=False, na=False)
        filter_not_robot = ~df_filtered['DEALER'].astype(str).str.contains('ROBOT', case=False, regex=False, na=False)
        df_filtered = df_filtered[filter_dot & filter_not_robot]
    
        # P/S
        df_filtered['P/S'] = np.where(df_filtered['PURCHASED_AMOUNT'].fillna(0) != 0, 'P',
                                      np.where(df_filtered['SOLD_AMOUNT'].fillna(0) != 0, 'S', ''))
    
        # Các cột cơ bản
        df_filtered['AMOUNT'] = np.where(df_filtered['P/S'] == 'P',
                                         df_filtered['PURCHASED_AMOUNT'],
                                         df_filtered['SOLD_AMOUNT'])
    
        df_filtered['Rate'] = np.where(df_filtered['P/S'] == 'P',
                                       df_filtered['PURCHASED_RATE'],
                                       df_filtered['SOLD_RATE'])
    
        df_filtered['Treasury Rate'] = np.where(df_filtered['P/S'] == 'P',
                                                df_filtered['TREASURY_BUY_RATE'],
                                                df_filtered['TREASURY_SELL_RATE'])
    
        df_filtered['Loại Ngoại tệ'] = np.where(df_filtered['P/S'] == 'P',
                                                df_filtered['CRNCY_PURCHSD'],
                                                df_filtered['CRNCY_SOLD'])
    
        df_filtered['SOL'] = df_filtered['SOL_ID']
        df_filtered['Đơn vị'] = df_filtered['SOL_DESC']
        df_filtered['CIF'] = df_filtered['CIF_ID']
        df_filtered['Tên KH'] = df_filtered['CUST_NAME']
    
        df_filtered['DEAL_DATE'] = pd.to_datetime(df_filtered['DEAL_DATE'], errors='coerce')
        df_filtered['DUE_DATE'] = pd.to_datetime(df_filtered['DUE_DATE'], errors='coerce')
    
        df_filtered['TRANSACTION_NO'] = df_filtered['TRANSACTION_NO'].astype(str).strip()
        df_filtered['Quy đổi VND'] = df_filtered['VALUE_VND']
        df_filtered['Quy đổi USD'] = df_filtered['VALUE_USD']
        df_filtered['Mục đích'] = df_filtered['PURPOSE_OF_TRANSACTION']
        df_filtered['Kết quả Lãi/lỗ'] = df_filtered['KETQUA']
        df_filtered['Số tiền Lãi lỗ'] = df_filtered['SOTIEN_LAI_LO']
    
        df_filtered['Maker'] = df_filtered['DEALER']
        df_filtered['Maker Date'] = pd.to_datetime(df_filtered['MAKER_DATE'], errors='coerce')
        df_filtered['Checker'] = df_filtered['VERIFY_ID']
        df_filtered['Verify Date'] = pd.to_datetime(df_filtered['VERIFY_DATE'], errors='coerce')
    
        # Hàm check từ khóa
        def contains_any(text, keywords):
            if pd.isna(text):
                return False
            text = str(text).upper()
            return any(k in text for k in keywords)
    
        # ==== 9 cột đặc biệt ====
        df_filtered['GD bán ngoại tệ CK'] = df_filtered.apply(
            lambda x: 'X' if x['P/S'] == 'S' and contains_any(x['Mục đích'], ['BAN NTE CK', 'CK']) else '', axis=1)
    
        df_filtered['GD bán ngoại tệ mặt'] = df_filtered.apply(
            lambda x: 'X' if x['P/S'] == 'S' and contains_any(x['Mục đích'], ['BAN NTE MAT', 'MAT']) else '', axis=1)
    
        df_filtered['Bán NT - Trợ cấp'] = df_filtered.apply(
            lambda x: 'X' if x['P/S'] == 'S' and contains_any(x['Mục đích'], ['TRO CAP', 'TROCAP']) else '', axis=1)
    
        # ==== 5 nhóm còn lại ====
        special_cols = [
            'Bán NT - Trợ cấp', 'Bán NT - Du học', 'Bán NT - Du lịch',
            'Bán NT - Công tác', 'Bán NT - Chữa bệnh'
        ]
    
        df_filtered['Bán NT - Khác'] = df_filtered.apply(
            lambda x: 'X' if (x['P/S'] == 'S' and all(x[col] == '' for col in special_cols)) else '',
            axis=1
        )
    
        # Giao dịch lỗ > 100k
        df_filtered['GD lỗ >100.000đ'] = df_filtered.apply(
            lambda x: 'X' if x['Kết quả Lãi/lỗ'] == 'LO' and abs(x['Số tiền Lãi lỗ']) >= 100_000 else '',
            axis=1
        )
    
        # GD duyệt trễ > 30 phút
        df_filtered['Trễ'] = df_filtered['Verify Date'] - df_filtered['Maker Date']
        df_filtered['GD duyệt trễ >30p'] = df_filtered['Trễ'].apply(
            lambda x: 'X' if pd.notnull(x) and x.total_seconds() > 1800 else '')
    
        df_filtered.drop(columns=['Trễ'], inplace=True)
    
        # ======================================================
        # KIỂM TRA RATE REQUEST (df_a + df_b)
        # ======================================================
        df_a["FRWRD_CNTRCT_NUM"] = df_a["FRWRD_CNTRCT_NUM"].astype(str).str.strip()
        df_a["TREA_REF_NUM"] = pd.to_numeric(df_a["TREA_REF_NUM"], errors="coerce")
        set_a = set(df_a[df_a["TREA_REF_NUM"].notna()]["FRWRD_CNTRCT_NUM"])
    
        df_filtered['GD Rate Request'] = df_filtered['TRANSACTION_NO'].isin(set_a).map({True: 'X', False: ''})
    
        # ======================================================
        # XỬ LÝ MỤC 19
        # ======================================================
        df = df_muc19.copy()
    
        df['P/S'] = np.where(df['PURCHASED_AMOUNT'].fillna(0) != 0, 'P',
                             np.where(df['SOLD_AMOUNT'].fillna(0) != 0, 'S', ''))
    
        df['AMOUNT'] = np.where(df['P/S'] == 'P', df['PURCHASED_AMOUNT'], df['SOLD_AMOUNT'])
        df['RATE'] = np.where(df['P/S'] == 'P', df['PURCHASED_RATE'], df['SOLD_RATE'])
    
        df['MAKER_DATE'] = pd.to_datetime(df['MAKER_DATE'], errors='coerce')
        df['VERIFY_DATE'] = pd.to_datetime(df['VERIFY_DATE'], errors='coerce')
    
        df['TIME_DELAY'] = df['VERIFY_DATE'] - df['MAKER_DATE']
        df['GD duyệt trễ > 20p'] = df['TIME_DELAY'].apply(
            lambda x: 'X' if (pd.notnull(x) and x.total_seconds() > 1200) else '')
    
        df_baocao = df.copy()
    
        # ======================================================
        # XUẤT KẾT QUẢ
        # ======================================================
    
        buffer = BytesIO()
    
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, sheet_name='Tieu chi 1,2,3,4', index=False)
            df_baocao.to_excel(writer, sheet_name='Tieu chi 5,6', index=False)
    
        st.success("🎉 Xử lý hoàn tất!")
    
        st.download_button(
            label="⬇ Tải file kết quả",
            data=buffer.getvalue(),
            file_name="KQ_xuly_NT.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
        st.write("### 📌 Preview dữ liệu")
        st.dataframe(df_filtered.head(20))
    
