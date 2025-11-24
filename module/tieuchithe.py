import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta


# =====================================================
# HÀM XỬ LÝ THẺ (GIỮ NGUYÊN LOGIC CỦA BẠN)
# =====================================================
def process_the(
    df_muc26,
    df_code_tinh_trang_the,
    df_code_policy,
    df_du_no_m,
    df_du_no_m1,
    df_du_no_m2,
    df_crm4,
    df_crm32,
    df_hdv_ckh,
    df_muc17,
    chi_nhanh
):
    df_muc26 = df_muc26.copy()

    # ◼ Chuẩn hóa cột ngày
    for c in ['NGAY_MO','NGAY_KICH_HOAT','EXPDT']:
        if c in df_muc26.columns:
            df_muc26[c] = pd.to_datetime(df_muc26[c], errors='coerce')

    df_processed = df_muc26.copy()

    # ==========================
    # 1) TÌNH TRẠNG THẺ
    # ==========================
    df_code_tinh_trang_the['Code_policy'] = df_code_tinh_trang_the['Code'].astype(str)
    df_processed['TRANGTHAITHE_is_blank_orig'] = (
        df_processed['TRANGTHAITHE'].isna() |
        df_processed['TRANGTHAITHE'].astype(str).str.strip().eq('')
    )
    df_processed['TRANGTHAITHE_for_merge'] = df_processed['TRANGTHAITHE'].astype(str)

    df_processed = df_processed.merge(
        df_code_tinh_trang_the[['Code_policy', 'Tình trạng thẻ']].rename(
            columns={'Tình trạng thẻ':'POLICY_TinhTrang'}
        ),
        left_on='TRANGTHAITHE_for_merge',
        right_on='Code_policy',
        how='left'
    )
    cond_a_blank = df_processed['TRANGTHAITHE_is_blank_orig']
    cond_c_no_match = (~df_processed['TRANGTHAITHE_is_blank_orig']) & (df_processed['Code_policy'].isna())

    df_processed['TÌNH TRẠNG THẺ'] = np.select(
        [cond_a_blank, cond_c_no_match],
        ["Hoạt động bình thường", "Khác"],
        default=df_processed['POLICY_TinhTrang']
    )

    df_processed.drop(columns=['Code_policy','POLICY_TinhTrang',
                               'TRANGTHAITHE_is_blank_orig','TRANGTHAITHE_for_merge'],
                      errors='ignore', inplace=True)

    # ==========================
    # 2) PHÂN LOẠI POLICY
    # ==========================
    df_code_policy['CODE'] = df_code_policy['CODE'].astype(str)
    df_processed['POLICY_CODE'] = df_processed['POLICY_CODE'].astype(str)

    df_processed = df_processed.merge(
        df_code_policy[['CODE','PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']],
        left_on='POLICY_CODE', right_on='CODE', how='left'
    )

    df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'] = \
        df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].fillna('Khác')

    # ==========================
    # 3 – 5) DƯ NỢ (m-2, m-1, m)
    # ==========================
    for (df_src, colname) in [
        (df_du_no_m2, "DƯ NỢ THẺ 02 THÁNG TRƯỚC"),
        (df_du_no_m1, "DƯ NỢ THẺ 01 THÁNG TRƯỚC"),
        (df_du_no_m,  "DƯ NỢ THẺ HIỆN TẠI")
    ]:
        df_src['OD_ACCOUNT'] = df_src['OD_ACCOUNT'].astype(str)
        df_processed = df_processed.merge(
            df_src[['OD_ACCOUNT','DU_NO_QUY_DOI']],
            left_on='ODACCOUNT', right_on='OD_ACCOUNT', how='left'
        )
        df_processed[colname] = df_processed['DU_NO_QUY_DOI'].fillna("KPS")
        df_processed.drop(columns=['DU_NO_QUY_DOI','OD_ACCOUNT'], inplace=True, errors='ignore')

    # ==========================
    # 6 – 7) NHÓM NỢ
    # ==========================
    df_du_no_m['OD_ACCOUNT'] = df_du_no_m['OD_ACCOUNT'].astype(str)
    df_processed = df_processed.merge(
        df_du_no_m[['OD_ACCOUNT','NHOM_NO_OD_ACCOUNT','NHOM_NO']],
        left_on='ODACCOUNT', right_on='OD_ACCOUNT', how='left'
    )

    df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'] = df_processed['NHOM_NO_OD_ACCOUNT'].fillna("KPS")
    df_processed['NHÓM NỢ HIỆN TẠI CỦA KH']  = df_processed['NHOM_NO'].fillna("KPS")
    df_processed.drop(columns=['NHOM_NO_OD_ACCOUNT','NHOM_NO','OD_ACCOUNT'], inplace=True, errors='ignore')

    # ==========================
    # 8) DƯ NỢ VAY KH (CRM4)
    # ==========================
    df_crm4 = df_crm4.copy()
    df_crm4['CIF_KH_VAY'] = df_crm4['CIF_KH_VAY'].astype(str)
    df_processed['CUSTSEQ'] = df_processed['CUSTSEQ'].astype(str)

    df_crm4['DU_NO_PHAN_BO_QUY_DOI'] = pd.to_numeric(df_crm4['DU_NO_PHAN_BO_QUY_DOI'], errors='coerce').fillna(0)
    df_tong_du_no = df_crm4.groupby('CIF_KH_VAY')['DU_NO_PHAN_BO_QUY_DOI'].sum().reset_index()
    df_tong_du_no.columns = ['CIF_KH_VAY','DƯ NỢ VAY CỦA KH']

    df_processed = df_processed.merge(df_tong_du_no, left_on='CUSTSEQ', right_on='CIF_KH_VAY', how='left')
    df_processed['DƯ NỢ VAY CỦA KH'] = df_processed['DƯ NỢ VAY CỦA KH'].fillna("KPS")
    df_processed.drop(columns=['CIF_KH_VAY'], inplace=True, errors='ignore')

    # ==========================
    # 9) SỐ LƯỢNG TSBĐ – Mục 17
    # ==========================
    df_muc17['C04'] = df_muc17['C04'].astype(str)
    df_muc17['C01'] = df_muc17['C01'].astype(str)

    tsbd_count = df_muc17.groupby('C04')['C01'].nunique().reset_index()
    tsbd_count.columns = ['C04','SL_tam']

    df_processed = df_processed.merge(tsbd_count, left_on='CUSTSEQ', right_on='C04', how='left')
    df_processed['SỐ LƯỢNG TSBĐ'] = df_processed['SL_tam'].fillna("KPS")
    df_processed.drop(columns=['SL_tam','C04'], inplace=True, errors='ignore')

    # ==========================
    # 10) TRỊ GIÁ TSBĐ – CRM4
    # ==========================
    df_crm4['SECU_VALUE'] = pd.to_numeric(df_crm4['SECU_VALUE'], errors='coerce').fillna(0)
    df_val = df_crm4.groupby('CIF_KH_VAY')['SECU_VALUE'].sum().reset_index()
    df_val.columns = ['CIF_KH_VAY','TRỊ GIÁ TSBĐ']

    df_processed = df_processed.merge(df_val, left_on='CUSTSEQ', right_on='CIF_KH_VAY', how='left')
    df_processed['TRỊ GIÁ TSBĐ'] = df_processed['TRỊ GIÁ TSBĐ'].fillna("KPS")
    df_processed.drop(columns=['CIF_KH_VAY'], inplace=True, errors='ignore')

    # ==========================
    # 11 – 12) SỐ LƯỢNG TKTG CKH – SỐ DƯ
    # ==========================
    df_hdv_ckh['CUSTSEQ'] = df_hdv_ckh['CUSTSEQ'].astype(str)

    g1 = df_hdv_ckh.groupby('CUSTSEQ')['IDXACNO'].count().reset_index()
    g1.columns = ['CUSTSEQ','SỐ LƯỢNG TKTG CKH']
    df_processed = df_processed.merge(g1, on='CUSTSEQ', how='left')
    df_processed['SỐ LƯỢNG TKTG CKH'] = df_processed['SỐ LƯỢNG TKTG CKH'].fillna('KPS')

    g2 = df_hdv_ckh.groupby('CUSTSEQ')['CURBAL_VN'].sum().reset_index()
    g2.columns = ['CUSTSEQ','SỐ DƯ TÀI KHOẢN']
    df_processed = df_processed.merge(g2, on='CUSTSEQ', how='left')
    df_processed['SỐ DƯ TÀI KHOẢN'] = df_processed['SỐ DƯ TÀI KHOẢN'].fillna('KPS')

    # ==========================
    # 13) THẺ HM CAO
    # ==========================
    df_processed['PPSCRLMT_numeric'] = pd.to_numeric(df_processed['PPSCRLMT'], errors='coerce')
    df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] = np.where(
        df_processed['PPSCRLMT_numeric'] > 30000000, 'X',''
    )

    # ==========================
    # 16) THẺ CHƯA ĐÓNG
    # ==========================
    df_processed['THẺ CHƯA ĐÓNG'] = np.where(
        ~df_processed['TÌNH TRẠNG THẺ'].isin(['Chấm dứt sử dụng','Yêu cầu đóng thẻ']),
        'X',''
    )

    # ==========================
    # 17) THẺ TÍN CHẤP HM CAO
    # ==========================
    df_processed['THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO'] = ''
    dk17 = (
        df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].isin(
            ['Theo thu nhập/tín chấp','Theo điều kiện về TKTG CKH']
        )
        & (df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)']=='X')
    )
    df_processed.loc[dk17, 'THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO'] = 'X'

    # ==========================
    # 18 – 20) GIẢI CHẤP – QUÁ HẠN
    # ==========================
    df_processed['KH KHÔNG CÓ/KHÔNG CÒN TSBĐ'] = \
        df_processed['SỐ LƯỢNG TSBĐ'].apply(lambda x: 'X' if str(x) in ['0','KPS'] else '')

    df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG'] = \
        df_processed.apply(lambda r:
            'X' if (
                r['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']=='Theo khoản vay/Có TSBĐ'
                and r['KH KHÔNG CÓ/KHÔNG CÒN TSBĐ']=='X'
                and r['THẺ CHƯA ĐÓNG']=='X'
            )
            else '', axis=1)

    df_processed['DƯ NỢ THẺ HIỆN TẠI'] = pd.to_numeric(df_processed['DƯ NỢ THẺ HIỆN TẠI'], errors='coerce')

    df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG VÀ CÓ DƯ NỢ'] = \
        df_processed.apply(lambda r:
        'X' if r['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG']=='X'
              and r['DƯ NỢ THẺ HIỆN TẠI']>0
        else '', axis=1)

    df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'] = pd.to_numeric(df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'], errors='coerce')
    df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'] = pd.to_numeric(df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'], errors='coerce')

    df_processed['THẺ QUÁ HẠN'] = np.where(df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'].isin([2,3,4,5]),'X','')
    df_processed['KH QUÁ HẠN']  = np.where(df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'].isin([2,3,4,5]),'X','')

    # ==========================
    # 21 – 22) TKTG CKH
    # ==========================
    df_processed['PPSCRLMT'] = pd.to_numeric(df_processed['PPSCRLMT'], errors='coerce')
    df_processed['SỐ DƯ TÀI KHOẢN'] = pd.to_numeric(df_processed['SỐ DƯ TÀI KHOẢN'], errors='coerce')

    df_processed['KH KHÔNG CÓ/TẤT TOÁN TKTG CKH NHƯNG THẺ CHƯA ĐÓNG'] = np.where(
        (df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']=='Theo điều kiện về TKTG CKH') &
        (df_processed['SỐ LƯỢNG TKTG CKH'].astype(str).isin(['0','KPS'])) &
        (df_processed['THẺ CHƯA ĐÓNG']=='X'),
        'X',''
    )

    df_processed["SỐ DƯ TKTG CKH < HẠN MỨC"] = df_processed.apply(
        lambda r: 'X'
        if (
            r['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']=='Theo điều kiện về TKTG CKH' and
            r['THẺ CHƯA ĐÓNG']=='X' and
            (pd.isna(r['SỐ DƯ TÀI KHOẢN']) or r['SỐ DƯ TÀI KHOẢN'] < r['PPSCRLMT'])
        )
        else '',
        axis=1
    )

    return df_processed




# =====================================================
# MODULE UI — HÀM GỌI CHÍNH
# =====================================================
def run_the_module():

    st.header("📌 Xử lý Thẻ – 1.3.2")

    chi_nhanh = st.text_input("Nhập chi nhánh/mã SOL:", "")

    uploaded = {}

    file_labels = {
        "df_muc26": "KTNB_MUC26.xlsx",
        "df_code_tinh_trang_the": "Code Tình trạng thẻ",
        "df_code_policy": "Code Policy",
        "df_du_no_m": "Dư nợ tháng m",
        "df_du_no_m1": "Dư nợ tháng m-1",
        "df_du_no_m2": "Dư nợ tháng m-2",
        "df_crm4": "CRM4",
        "df_crm32": "CRM32",
        "df_hdv_ckh": "HDV CKH",
        "df_muc17": "Mục 17 TSTC"
    }

    for key, label in file_labels.items():
        uploaded[key] = st.file_uploader(f"📁 Upload file {label}", type=["xlsx","xls"], key=key)

    if st.button("🚀 Chạy xử lý Thẻ"):
        missing = [k for k,v in uploaded.items() if v is None]
        if missing:
            st.error(f"Thiếu file: {', '.join(missing)}")
            return

        dfs = {k: pd.read_excel(v) for k,v in uploaded.items()}

        df_result = process_the(
            dfs["df_muc26"],
            dfs["df_code_tinh_trang_the"],
            dfs["df_code_policy"],
            dfs["df_du_no_m"],
            dfs["df_du_no_m1"],
            dfs["df_du_no_m2"],
            dfs["df_crm4"],
            dfs["df_crm32"],
            dfs["df_hdv_ckh"],
            dfs["df_muc17"],
            chi_nhanh
        )

        st.success("🎉 Xử lý thành công!")

        st.dataframe(df_result.head())

        # Xuất Excel
        buffer = io.BytesIO()
        df_result.to_excel(buffer, index=False)

        st.download_button(
            "⬇ Tải file kết quả Thẻ",
            data=buffer.getvalue(),
            file_name="ket_qua_the.xlsx"
        )
