# =========================================================
# module/tieuchithe.py
# FULL MODULE – TIÊU CHÍ THẺ + POS (1600)
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
import glob
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io


# =========================================================
# HÀM XUẤT EXCEL -> BYTES CHO DOWNLOAD_BUTTON
# =========================================================
def df_to_excel_bytes(df: pd.DataFrame, sheet_name: str = "Sheet1") -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)
    buffer.seek(0)
    return buffer


# =========================================================
# HÀM CHUẨN HÓA FILE 6.2a (TRƯỚC & SAU 23/05)
# =========================================================
def standardize_6_2a_two_files(path_before_2305: str, path_after_2305: str) -> pd.DataFrame:
    """
    Chuẩn hóa 2 file MUC29_1600 kiểu cũ & mới về cùng format cột:
    BRANCH_CODE, MERCHANT_ID, MERCHANT_NAME, TRANS_DATE, TRANS_AMT
    """
    # ----- File TRƯỚC 23/05/2025 -----
    df_before = pd.read_excel(path_before_2305, dtype=str)

    map_before = {
        'MACN_POS': 'BRANCH_CODE',
        'IDPOS': 'MERCHANT_ID',
        'TENPOS': 'MERCHANT_NAME',
        'TRANDT': 'TRANS_DATE',
        'TRANAMT_QD': 'TRANS_AMT'
    }
    needed_before = list(map_before.keys())
    keep_before = [c for c in needed_before if c in df_before.columns]
    df_before = df_before[keep_before].rename(columns=map_before)

    # ----- File SAU / TỪ 23/05/2025 -----
    df_after = pd.read_excel(path_after_2305, dtype=str)

    map_after = {
        'BRANCH_CODE': 'BRANCH_CODE',
        'MERCHANT_ID': 'MERCHANT_ID',
        'MERCHANT_NAME': 'MERCHANT_NAME',
        'TRANS_DATE': 'TRANS_DATE',
        'TRANS_AMT': 'TRANS_AMT'
    }
    needed_after = list(map_after.keys())
    keep_after = [c for c in needed_after if c in df_after.columns]
    df_after = df_after[keep_after].rename(columns=map_after)

    # ----- Ghép & chuẩn hóa -----
    df_std = pd.concat([df_before, df_after], ignore_index=True)

    if 'TRANS_DATE' in df_std.columns:
        df_std['TRANS_DATE'] = pd.to_datetime(df_std['TRANS_DATE'], errors='coerce')

    for col in ['BRANCH_CODE', 'MERCHANT_ID', 'MERCHANT_NAME']:
        if col in df_std.columns:
            df_std[col] = df_std[col].astype(str)

    final_cols = ['BRANCH_CODE', 'MERCHANT_ID', 'MERCHANT_NAME', 'TRANS_DATE', 'TRANS_AMT']
    df_std = df_std.reindex(columns=final_cols)

    return df_std


# =========================================================
# HÀM CHẠY TOÀN BỘ PIPELINE (THẺ + POS)
# =========================================================
def run_full_pipeline(
    chi_nhanh: str,
    start_audit: datetime,
    end_audit: datetime,
):
    """
    Chạy toàn bộ logic xử lý:
      - Thẻ (Mục 1.3.2 – tiêu chí thẻ)
      - POS (Mục 6.2a, 6.2b, 7, 8)
    Trả về:
        - df_processed: bảng thẻ đã xử lý
        - df_pos      : bảng POS đã xử lý
    """

    # -----------------------------------------------------
    # 0. ĐƯỜNG DẪN FILE (GIỮ NGUYÊN NHƯ BẢN GỐC CỦA BẠN)
    #    -> Bạn chỉnh đường dẫn theo môi trường của mình.
    # -----------------------------------------------------
    file_bang_code_tinh_trang_the_path = '/content/drive/MyDrive/ChayDl/thang10_2025/Code TTD-NEW 1.xlsx'
    file_crm4_path = glob.glob('/content/drive/MyDrive/ChayDl/1500_DL_CKH/cr4/CRM4_Du_no_theo_tai_san_dam_bao_*.xls')
    file_du_no_m_path = '/content/drive/MyDrive/ChayDl/thang10_2025/EL/T9_007.EI - 07.CRM_1_DN_THE_CA_NHAN_DOANH_NGHIEP_FINCORE.xls'
    file_du_no_m1_path = '/content/drive/MyDrive/ChayDl/thang10_2025/EL/T8_007.EI - 07.CRM_1_DN_THE_CA_NHAN_DOANH_NGHIEP_FINCORE.xls'
    file_du_no_m2_path = '/content/drive/MyDrive/ChayDl/thang10_2025/EL/T7_007.EI - 07.CRM_1_DN_THE_CA_NHAN_DOANH_NGHIEP_FINCORE.xls'
    file_crm32_path = glob.glob('/content/drive/MyDrive/ChayDl/thang10_2025/RPT/RPT_CRM_32_*.xls')
    df_ckh_paths = glob.glob("/content/drive/MyDrive/ChayDl/thang10_2025/HDV/HDV_CHITIET_CKH_*xls")
    file_muc26_path = '/content/drive/MyDrive/ChayDl/thang10_2025/KTNB_MUC26.xlsx'
    file_muc17_path = '/content/drive/MyDrive/ChayDl/thang10_2025/Muc17_Lop2_TSTC 6 (1).xlsx'
    file_muc29_old_path = '/content/MUC29_1600_old.xlsx'
    file_muc29_new_path = '/content/MUC29_1600_new.xlsx'
    file_muc51_path = '/content/MUC51_1600 (1).xlsx'

    # -----------------------------------------------------
    # 1. TẢI DỮ LIỆU CKH
    # -----------------------------------------------------
    df_fx_list = [pd.read_excel(f) for f in df_ckh_paths]
    df_hdv_ckh = pd.concat(df_fx_list, ignore_index=True)

    chi_nhanh_upper = chi_nhanh.strip().upper()

    # ✅ Lọc theo chi nhánh BRCD
    df_hdv_ckh_loc = df_hdv_ckh[
        df_hdv_ckh['BRCD'].astype(str).str.upper().str.contains(chi_nhanh_upper)
    ]

    # CRM32 (dù chưa dùng nhiều – vẫn đọc để có sẵn)
    df_crm32 = pd.concat([pd.read_excel(f, dtype=str) for f in file_crm32_path], ignore_index=True)

    # Bảng code tình trạng thẻ & policy
    df_code_tinh_trang_the = pd.read_excel(
        file_bang_code_tinh_trang_the_path,
        sheet_name="Code Tình trạng thẻ"
    )
    df_code_policy = pd.read_excel(
        file_bang_code_tinh_trang_the_path,
        sheet_name="Code Policy"
    )

    # Dư nợ M-2, M-1, M
    df_du_no_m2 = pd.read_excel(file_du_no_m2_path)
    df_du_no_m1 = pd.read_excel(file_du_no_m1_path)
    df_du_no_m = pd.read_excel(file_du_no_m_path)

    # CRM4
    df_crm4 = pd.concat([pd.read_excel(f, dtype=str) for f in file_crm4_path], ignore_index=True)
    df_crm4_loc = df_crm4[
        df_crm4['BRANCH_VAY'].astype(str).str.upper().str.contains(chi_nhanh_upper)
    ]

    # -----------------------------------------------------
    # 2. MỤC 26 → df_processed (THẺ)
    # -----------------------------------------------------
    df_muc26 = pd.read_excel(file_muc26_path, dtype=str)
    cols = [
        'CUSTSEQ', 'BRCD', 'PPSCRLMT', 'FULLNM', 'CUSTNAMNE', 'ID_CARD', 'IDCARD', 'EXPDT',
        'NGAY_KICH_HOAT', 'ODACCOUNT', 'NGAY_MO', 'TRANGTHAITHE',
        'POLICY_CODE', 'POLICY_NAME', 'DU_NO'
    ]
    df_muc26 = df_muc26[[c for c in cols if c in df_muc26.columns]].copy()

    for c in ['CUSTSEQ', 'IDCARD', 'ID_CARD', 'ODACCOUNT']:
        if c in df_muc26.columns:
            df_muc26[c] = df_muc26[c].astype("string")

    for c in ['NGAY_MO', 'NGAY_KICH_HOAT', 'EXPDT']:
        if c in df_muc26.columns:
            df_muc26[c] = pd.to_datetime(df_muc26[c], errors='coerce')

    df_processed = df_muc26.copy()

    # -----------------------------------------------------
    # (1) TÌNH TRẠNG THẺ – GÁN TỪ BẢNG CODE
    # -----------------------------------------------------
    if (
        'TRANGTHAITHE' in df_processed.columns and
        'Code' in df_code_tinh_trang_the.columns and
        'Tình trạng thẻ' in df_code_tinh_trang_the.columns
    ):
        df_code_tinh_trang_the['Code_policy'] = df_code_tinh_trang_the['Code'].astype(str)

        df_processed['TRANGTHAITHE_is_blank_orig'] = (
            df_processed['TRANGTHAITHE'].isna() |
            df_processed['TRANGTHAITHE'].astype(str).str.strip().eq('')
        )
        df_processed['TRANGTHAITHE_for_merge'] = df_processed['TRANGTHAITHE'].astype(str)

        df_processed = pd.merge(
            df_processed,
            df_code_tinh_trang_the[['Code_policy', 'Tình trạng thẻ']].rename(
                columns={'Tình trạng thẻ': 'POLICY_TinhTrang'}
            ),
            left_on='TRANGTHAITHE_for_merge',
            right_on='Code_policy',
            how='left'
        )

        cond_a_blank = df_processed['TRANGTHAITHE_is_blank_orig']
        cond_c_no_match = (~df_processed['TRANGTHAITHE_is_blank_orig']) & (df_processed['Code_policy'].isna())

        df_processed['TÌNH TRẠNG THẺ'] = np.select(
            [cond_a_blank, cond_c_no_match],
            ['Hoạt động bình thường', 'Khác'],
            default=df_processed['POLICY_TinhTrang']
        )

        cols_to_drop = [
            'Code_policy', 'POLICY_TinhTrang',
            'TRANGTHAITHE_is_blank_orig', 'TRANGTHAITHE_for_merge',
            'Description', 'Unnamed: 3'
        ]
        df_processed.drop(
            columns=[col for col in cols_to_drop if col in df_processed.columns],
            inplace=True,
            errors='ignore'
        )
    else:
        df_processed['TÌNH TRẠNG THẺ'] = "Lỗi dữ liệu nguồn"

    # -----------------------------------------------------
    # Gộp Policy -> PHÂN LOẠI CẤP HM THẺ
    # -----------------------------------------------------
    if 'POLICY_CODE' in df_processed.columns and 'CODE' in df_code_policy.columns:
        df_processed['POLICY_CODE'] = df_processed['POLICY_CODE'].str.strip()
        df_code_policy['CODE'] = df_code_policy['CODE'].str.strip()

        df_processed = df_processed.merge(
            df_code_policy[['CODE', 'PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']],
            left_on='POLICY_CODE',
            right_on='CODE',
            how='left'
        )

        df_processed['PHÂN LOẠI CẤP HM THẺ'] = df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].fillna('Khác')
    else:
        df_processed['PHÂN LOẠI CẤP HM THẺ'] = 'Khác'

    # -----------------------------------------------------
    # (3) DƯ NỢ THẺ 02 THÁNG TRƯỚC
    # -----------------------------------------------------
    if (
        'ODACCOUNT' in df_processed.columns and
        'OD_ACCOUNT' in df_du_no_m2.columns and
        'DU_NO_QUY_DOI' in df_du_no_m2.columns
    ):
        df_du_no_m2['OD_ACCOUNT'] = df_du_no_m2['OD_ACCOUNT'].astype(str)
        df_processed = pd.merge(
            df_processed,
            df_du_no_m2[['OD_ACCOUNT', 'DU_NO_QUY_DOI']],
            left_on='ODACCOUNT',
            right_on='OD_ACCOUNT',
            how='left'
        )
        df_processed.rename(columns={'DU_NO_QUY_DOI': 'DƯ NỢ THẺ 02 THÁNG TRƯỚC'}, inplace=True)
        df_processed['DƯ NỢ THẺ 02 THÁNG TRƯỚC'].fillna("KPS", inplace=True)
        df_processed.drop(columns=['OD_ACCOUNT'], inplace=True, errors='ignore')
    else:
        df_processed['DƯ NỢ THẺ 02 THÁNG TRƯỚC'] = "KPS"

    # -----------------------------------------------------
    # (4) DƯ NỢ THẺ 01 THÁNG TRƯỚC
    # -----------------------------------------------------
    if (
        'ODACCOUNT' in df_processed.columns and
        'OD_ACCOUNT' in df_du_no_m1.columns and
        'DU_NO_QUY_DOI' in df_du_no_m1.columns
    ):
        df_du_no_m1['OD_ACCOUNT'] = df_du_no_m1['OD_ACCOUNT'].astype(str)
        df_processed = pd.merge(
            df_processed,
            df_du_no_m1[['OD_ACCOUNT', 'DU_NO_QUY_DOI']],
            left_on='ODACCOUNT',
            right_on='OD_ACCOUNT',
            how='left'
        )
        df_processed.rename(columns={'DU_NO_QUY_DOI': 'DƯ NỢ THẺ 01 THÁNG TRƯỚC'}, inplace=True)
        df_processed['DƯ NỢ THẺ 01 THÁNG TRƯỚC'].fillna("KPS", inplace=True)
        df_processed.drop(columns=['OD_ACCOUNT'], inplace=True, errors='ignore')
    else:
        df_processed['DƯ NỢ THẺ 01 THÁNG TRƯỚC'] = "KPS"

    # -----------------------------------------------------
    # (5) DƯ NỢ THẺ HIỆN TẠI
    # -----------------------------------------------------
    if (
        'ODACCOUNT' in df_processed.columns and
        'OD_ACCOUNT' in df_du_no_m.columns and
        'DU_NO_QUY_DOI' in df_du_no_m.columns
    ):
        df_du_no_m['OD_ACCOUNT'] = df_du_no_m['OD_ACCOUNT'].astype(str)
        df_processed = pd.merge(
            df_processed,
            df_du_no_m[['OD_ACCOUNT', 'DU_NO_QUY_DOI']],
            left_on='ODACCOUNT',
            right_on='OD_ACCOUNT',
            how='left'
        )
        df_processed.rename(columns={'DU_NO_QUY_DOI': 'DƯ NỢ THẺ HIỆN TẠI'}, inplace=True)
        df_processed['DƯ NỢ THẺ HIỆN TẠI'].fillna("KPS", inplace=True)
        df_processed.drop(columns=['OD_ACCOUNT'], inplace=True, errors='ignore')
    else:
        df_processed['DƯ NỢ THẺ HIỆN TẠI'] = "KPS"

    # -----------------------------------------------------
    # (6) NHÓM NỢ HIỆN TẠI CỦA THẺ
    # -----------------------------------------------------
    df_processed.drop(columns=['NHÓM NỢ HIỆN TẠI CỦA THẺ'], inplace=True, errors='ignore')
    if (
        'ODACCOUNT' in df_processed.columns and
        'OD_ACCOUNT' in df_du_no_m.columns and
        'NHOM_NO_OD_ACCOUNT' in df_du_no_m.columns
    ):
        df_processed = pd.merge(
            df_processed,
            df_du_no_m[['OD_ACCOUNT', 'NHOM_NO_OD_ACCOUNT']],
            left_on='ODACCOUNT',
            right_on='OD_ACCOUNT',
            how='left'
        )
        df_processed.rename(columns={'NHOM_NO_OD_ACCOUNT': 'NHÓM NỢ HIỆN TẠI CỦA THẺ'}, inplace=True)
        df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'].fillna("KPS", inplace=True)
        df_processed.drop(columns=['OD_ACCOUNT'], inplace=True, errors='ignore')
    else:
        df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'] = "KPS"

    # -----------------------------------------------------
    # (7) NHÓM NỢ HIỆN TẠI CỦA KH
    # -----------------------------------------------------
    if (
        'ODACCOUNT' in df_processed.columns and
        'OD_ACCOUNT' in df_du_no_m.columns and
        'NHOM_NO' in df_du_no_m.columns
    ):
        df_processed = pd.merge(
            df_processed,
            df_du_no_m[['OD_ACCOUNT', 'NHOM_NO']],
            left_on='ODACCOUNT',
            right_on='OD_ACCOUNT',
            how='left'
        )
        df_processed.rename(columns={'NHOM_NO': 'NHÓM NỢ HIỆN TẠI CỦA KH'}, inplace=True)
        df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'].fillna("KPS", inplace=True)
        df_processed.drop(columns=['OD_ACCOUNT'], inplace=True, errors='ignore')
    else:
        df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'] = "KPS"

    # -----------------------------------------------------
    # (8) DƯ NỢ VAY CỦA KH (từ CRM4)
    # -----------------------------------------------------
    if (
        'CUSTSEQ' in df_processed.columns and
        'CIF_KH_VAY' in df_crm4_loc.columns and
        'DU_NO_PHAN_BO_QUY_DOI' in df_crm4_loc.columns and
        'LOAI' in df_crm4_loc.columns
    ):
        df_crm4_loc['CIF_KH_VAY'] = df_crm4_loc['CIF_KH_VAY'].astype(str)
        df_crm4_cho_vay = df_crm4_loc[df_crm4_loc['LOAI'] == 'Cho vay'].copy()
        df_crm4_cho_vay['DU_NO_PHAN_BO_QUY_DOI'] = pd.to_numeric(
            df_crm4_cho_vay['DU_NO_PHAN_BO_QUY_DOI'], errors='coerce'
        ).fillna(0)

        df_tong_du_no_vay_kh = (
            df_crm4_cho_vay
            .groupby('CIF_KH_VAY')['DU_NO_PHAN_BO_QUY_DOI']
            .sum()
            .reset_index()
            .rename(columns={'DU_NO_PHAN_BO_QUY_DOI': 'DƯ NỢ VAY CỦA KH_temp'})
        )

        df_processed['CUSTSEQ'] = df_processed['CUSTSEQ'].astype(str)

        df_processed = pd.merge(
            df_processed,
            df_tong_du_no_vay_kh,
            left_on='CUSTSEQ',
            right_on='CIF_KH_VAY',
            how='left'
        )

        df_processed.rename(columns={'DƯ NỢ VAY CỦA KH_temp': 'DƯ NỢ VAY CỦA KH'}, inplace=True)
        df_processed['DƯ NỢ VAY CỦA KH'].fillna("KPS", inplace=True)
        df_processed.drop(columns=['CIF_KH_VAY'], inplace=True, errors='ignore')
    else:
        df_processed['DƯ NỢ VAY CỦA KH'] = "KPS"

    # -----------------------------------------------------
    # (9) SỐ LƯỢNG TSBĐ (Mục 17)
    # -----------------------------------------------------
    df_muc17 = pd.read_excel(file_muc17_path, dtype=str)

    if (
        'CUSTSEQ' in df_processed.columns and
        'C04' in df_muc17.columns and
        'C01' in df_muc17.columns
    ):
        df_muc17_copy = df_muc17.copy()
        df_muc17_copy['C04'] = df_muc17_copy['C04'].astype(str)
        df_processed['CUSTSEQ'] = df_processed['CUSTSEQ'].astype(str)

        df_so_luong_tsbd = (
            df_muc17_copy
            .groupby('C04')['C01']
            .nunique()
            .reset_index()
            .rename(columns={'C01': 'SỐ LƯỢNG TSBĐ_temp'})
        )

        df_processed = pd.merge(
            df_processed,
            df_so_luong_tsbd,
            left_on='CUSTSEQ',
            right_on='C04',
            how='left'
        )

        df_processed.rename(columns={'SỐ LƯỢNG TSBĐ_temp': 'SỐ LƯỢNG TSBĐ'}, inplace=True)
        df_processed['SỐ LƯỢNG TSBĐ'] = df_processed['SỐ LƯỢNG TSBĐ'].fillna("KPS")
        df_processed.drop(columns=['C04'], inplace=True, errors='ignore')
    else:
        df_processed['SỐ LƯỢNG TSBĐ'] = "KPS"

    # -----------------------------------------------------
    # (10) TRỊ GIÁ TSBĐ (CRM4 SECU_VALUE)
    # -----------------------------------------------------
    if (
        'CUSTSEQ' in df_processed.columns and
        'CIF_KH_VAY' in df_crm4_loc.columns and
        'SECU_VALUE' in df_crm4_loc.columns
    ):
        df_crm4_loc_copy = df_crm4_loc.copy()
        df_crm4_loc_copy['CIF_KH_VAY'] = df_crm4_loc_copy['CIF_KH_VAY'].astype(str)
        df_crm4_loc_copy['SECU_VALUE'] = pd.to_numeric(
            df_crm4_loc_copy['SECU_VALUE'], errors='coerce'
        ).fillna(0)

        df_tri_gia_tsbd = (
            df_crm4_loc_copy
            .groupby('CIF_KH_VAY', as_index=False)['SECU_VALUE']
            .sum()
            .rename(columns={'SECU_VALUE': 'TRỊ GIÁ TSBĐ'})
        )

        df_processed = pd.merge(
            df_processed,
            df_tri_gia_tsbd,
            left_on='CUSTSEQ',
            right_on='CIF_KH_VAY',
            how='left'
        )

        df_processed['TRỊ GIÁ TSBĐ'] = df_processed['TRỊ GIÁ TSBĐ'].fillna("KPS")
        df_processed.drop(columns=['CIF_KH_VAY'], inplace=True, errors='ignore')
    else:
        df_processed['TRỊ GIÁ TSBĐ'] = "KPS"

    # -----------------------------------------------------
    # (11) & (12) TKTG CKH – SỐ LƯỢNG & SỐ DƯ
    # -----------------------------------------------------
    df_processed['CUSTSEQ'] = df_processed['CUSTSEQ'].astype(str)
    df_hdv_ckh_loc['CUSTSEQ'] = df_hdv_ckh_loc['CUSTSEQ'].astype(str)

    # Số lượng TKTG CKH
    tktg_ckh_counts = (
        df_hdv_ckh_loc
        .groupby('CUSTSEQ')['IDXACNO']
        .count()
        .reset_index()
        .rename(columns={'IDXACNO': 'SO_LUONG_TKTG_CKH'})
    )
    df_processed = df_processed.merge(tktg_ckh_counts, on='CUSTSEQ', how='left')
    df_processed['SỐ LƯỢNG TKTG CKH'] = df_processed['SO_LUONG_TKTG_CKH'].fillna('KPS')
    df_processed.drop(columns=['SO_LUONG_TKTG_CKH'], inplace=True, errors='ignore')

    # Số dư TKTG CKH
    sodu_ckh = (
        df_hdv_ckh_loc
        .groupby('CUSTSEQ')['CURBAL_VN']
        .sum()
        .reset_index()
        .rename(columns={'CURBAL_VN': 'SỐ DƯ TÀI KHOẢN'})
    )
    df_processed = df_processed.merge(sodu_ckh, on='CUSTSEQ', how='left')
    df_processed['SỐ DƯ TÀI KHOẢN'] = df_processed['SỐ DƯ TÀI KHOẢN'].fillna('KPS')

    # -----------------------------------------------------
    # (13) THẺ CÓ HẠN MỨC CAO (>30 TRĐ)
    # -----------------------------------------------------
    if 'PPSCRLMT' in df_processed.columns:
        df_processed['PPSCRLMT_numeric'] = pd.to_numeric(
            df_processed['PPSCRLMT'], errors='coerce'
        )
        df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] = np.where(
            df_processed['PPSCRLMT_numeric'] > 30_000_000,
            'X', ''
        )
        df_processed.drop(columns=['PPSCRLMT_numeric'], inplace=True, errors='ignore')
    else:
        df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] = ''

    # -----------------------------------------------------
    # (14)–(15) TỈ LỆ DƯ NỢ / HẠN MỨC
    # -----------------------------------------------------
    df_processed['DƯ NỢ THẺ HIỆN TẠI'] = pd.to_numeric(
        df_processed['DƯ NỢ THẺ HIỆN TẠI'], errors='coerce'
    )
    df_processed['PPSCRLMT'] = pd.to_numeric(
        df_processed.get('PPSCRLMT', np.nan), errors='coerce'
    )

    df_processed['THẺ TD CÓ TL DƯ NỢ/HM CAO (>= 90%)'] = np.where(
        (df_processed['PPSCRLMT'] > 0) &
        (df_processed['DƯ NỢ THẺ HIỆN TẠI'] / df_processed['PPSCRLMT'] >= 0.9),
        'X', ''
    )

    df_processed['THẺ TD CÓ DƯ NỢ > HM'] = np.where(
        (df_processed['PPSCRLMT'] > 0) &
        (df_processed['DƯ NỢ THẺ HIỆN TẠI'] / df_processed['PPSCRLMT'] > 1),
        'X', ''
    )

    # -----------------------------------------------------
    # (16) THẺ CHƯA ĐÓNG
    # -----------------------------------------------------
    df_processed['TÌNH TRẠNG THẺ'] = df_processed['TÌNH TRẠNG THẺ'].astype(str).str.strip()
    df_processed['PHÂN LOẠI CẤP HM THẺ'] = df_processed['PHÂN LOẠI CẤP HM THẺ'].astype(str).str.strip()
    df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] = df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'].astype(str).str.strip()

    df_processed['THẺ CHƯA ĐÓNG'] = np.where(
        ~df_processed['TÌNH TRẠNG THẺ'].isin(['Chấm dứt sử dụng', 'Yêu cầu đóng thẻ']),
        'X', ''
    )

    # -----------------------------------------------------
    # (17) THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO
    # -----------------------------------------------------
    df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'] = df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].astype(str).str.strip()
    df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] = df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'].astype(str).str.strip()

    dk_17 = (
        df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].isin([
            'Theo thu nhập/tín chấp',
            'Theo điều kiện về TKTG CKH'
        ]) &
        (df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] == 'X')
    )
    df_processed['THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO'] = ''
    df_processed.loc[dk_17, 'THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO'] = 'X'

    # -----------------------------------------------------
    # (18) KH KHÔNG CÓ/KHÔNG CÒN TSBĐ
    # -----------------------------------------------------
    df_processed['KH KHÔNG CÓ/KHÔNG CÒN TSBĐ'] = df_processed['SỐ LƯỢNG TSBĐ'].apply(
        lambda x: 'X' if str(x).strip() in ['0', 'KPS'] or x == 0 else ''
    )

    df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG'] = df_processed.apply(
        lambda row: 'X' if (
            row['PHÂN LOẠI CẤP HM THẺ'] == 'Theo khoản vay/Có TSBĐ' and
            row['KH KHÔNG CÓ/KHÔNG CÒN TSBĐ'] == 'X' and
            row['THẺ CHƯA ĐÓNG'] == 'X'
        ) else '',
        axis=1
    )

    df_processed['DƯ NỢ THẺ HIỆN TẠI'] = pd.to_numeric(
        df_processed['DƯ NỢ THẺ HIỆN TẠI'], errors='coerce'
    )

    dk_20 = (
        (df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG'] == 'X') &
        (df_processed['DƯ NỢ THẺ HIỆN TẠI'].notnull()) &
        (df_processed['DƯ NỢ THẺ HIỆN TẠI'] != 0)
    )
    df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG VÀ CÓ DƯ NỢ'] = ''
    df_processed.loc[dk_20, 'KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG VÀ CÓ DƯ NỢ'] = 'X'

    df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'] = pd.to_numeric(
        df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'], errors='coerce'
    )
    df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'] = pd.to_numeric(
        df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'], errors='coerce'
    )

    df_processed['THẺ QUÁ HẠN'] = np.where(
        df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'].isin([2, 3, 4, 5]),
        'X', ''
    )
    df_processed['KH QUÁ HẠN'] = np.where(
        df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'].isin([2, 3, 4, 5]),
        'X', ''
    )

    # -----------------------------------------------------
    # (21) KH KHÔNG CÓ/TẤT TOÁN TKTG CKH NHƯNG THẺ CHƯA ĐÓNG
    # -----------------------------------------------------
    cond_a_21 = df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'] == 'Theo điều kiện về TKTG CKH'
    cond_b_21 = df_processed['SỐ LƯỢNG TKTG CKH'].astype(str).isin(['0', 'KPS'])
    cond_c_21 = df_processed['THẺ CHƯA ĐÓNG'] == 'X'

    df_processed['KH KHÔNG CÓ/TẤT TOÁN TKTG CKH NHƯNG THẺ CHƯA ĐÓNG'] = np.where(
        cond_a_21 & cond_b_21 & cond_c_21,
        'X', ''
    )

    # -----------------------------------------------------
    # (22) SỐ DƯ TKTG CKH < HẠN MỨC
    # -----------------------------------------------------
    df_processed['PPSCRLMT'] = pd.to_numeric(df_processed['PPSCRLMT'], errors='coerce')
    df_processed['SỐ DƯ TÀI KHOẢN'] = pd.to_numeric(df_processed['SỐ DƯ TÀI KHOẢN'], errors='coerce')

    df_processed['SỐ DƯ TKTG CKH < HẠN MỨC'] = df_processed.apply(
        lambda row: 'X' if (
            row['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'] == 'Theo điều kiện về TKTG CKH' and
            row['THẺ CHƯA ĐÓNG'] == 'X' and
            (
                pd.isna(row['SỐ DƯ TÀI KHOẢN']) or
                row['SỐ DƯ TÀI KHOẢN'] < row['PPSCRLMT']
            )
        ) else '',
        axis=1
    )

    # Có thể bỏ cột PHÂN LOẠI CẤP HM THẺ nếu không cần xuất
    df_processed.drop(columns=['PHÂN LOẠI CẤP HM THẺ'], inplace=True, errors='ignore')

    # =====================================================
    # POS – TIÊU CHÍ 6,7,8
    # =====================================================
    df_6_2a = standardize_6_2a_two_files(
        path_before_2305=file_muc29_old_path,
        path_after_2305=file_muc29_new_path
    )

    cols_needed = [
        'MID', 'BRANCH_LAP_DAT_MAY', 'TEN_GPKD_HKD', 'TEN_TREN_HD',
        'DAI_CHI_LAP_MAY', 'ADDRESSLINE_SUB_MERCHANT', 'MCC',
        'DATE_OPEN_MID', 'DEVICE_STATUS',
        'MERCHANT_CIF'
    ]

    df_6_2b_raw = pd.read_excel(
        file_muc51_path,
        usecols=cols_needed,
        dtype={'MID': 'string', 'MERCHANT_CIF': 'string'},
        parse_dates=['DATE_OPEN_MID']
    )
    df_pos = df_6_2b_raw.copy()

    # Làm sạch MERCHANT_CIF
    s = df_pos['MERCHANT_CIF'].fillna('').astype('string').str.strip()
    s = s.str.replace(r'^[A-Za-z]', '', regex=True)
    s = s.str.replace(r'\D+', '', regex=True).str[-9:]
    df_pos['MERCHANT_CIF'] = s.mask(s == '', None)

    for c in ['MID', 'MERCHANT_CIF']:
        if c in df_pos.columns:
            df_pos[c] = df_pos[c].astype('string')

    if 'DATE_OPEN_MID' in df_pos.columns:
        df_pos['DATE_OPEN_MID'] = pd.to_datetime(df_pos['DATE_OPEN_MID'], errors='coerce')

    df_6_2a['TRANS_AMT'] = (
        df_6_2a['TRANS_AMT']
        .astype(str)
        .str.replace(r'[^\d\.\-]', '', regex=True)
        .replace({'': '0'})
        .astype(float)
    )
    df_6_2a['TRANS_DATE'] = pd.to_datetime(df_6_2a['TRANS_DATE'], errors='coerce')
    df_6_2a['MERCHANT_ID'] = df_6_2a['MERCHANT_ID'].astype(str)
    df_pos['MID'] = df_pos['MID'].astype(str)

    def calc_revenue(df_trans, df_pos_local, start_date, end_date):
        mask = (df_trans['TRANS_DATE'] >= start_date) & (df_trans['TRANS_DATE'] <= end_date)
        g = (
            df_trans.loc[mask]
            .groupby('MERCHANT_ID', as_index=False)['TRANS_AMT']
            .sum()
            .rename(columns={'MERCHANT_ID': 'MID', 'TRANS_AMT': 'REVENUE'})
        )
        return (
            df_pos_local[['MID']]
            .merge(g, on='MID', how='left')['REVENUE']
            .fillna(0)
            .astype(float)
        )

    y = end_audit.year
    date_ranges = {
        'T-2': (datetime(y - 2, 1, 1), datetime(y - 2, 12, 31)),
        'T-1': (datetime(y - 1, 1, 1), datetime(y - 1, 12, 31)),
        'T': (datetime(y, 1, 1), datetime(y, 12, 31)),
    }

    df_pos['DSỐ_2_NĂM_TRƯỚC_T2'] = calc_revenue(df_6_2a, df_pos, *date_ranges['T-2'])
    df_pos['DSỐ_NĂM_TRƯỚC_T1'] = calc_revenue(df_6_2a, df_pos, *date_ranges['T-1'])
    df_pos['DSỐ_NĂM_NAY_T'] = calc_revenue(df_6_2a, df_pos, *date_ranges['T'])

    df_pos['TỔNG_DSỐ_3_NĂM'] = (
        df_pos['DSỐ_2_NĂM_TRƯỚC_T2'] +
        df_pos['DSỐ_NĂM_TRƯỚC_T1'] +
        df_pos['DSỐ_NĂM_NAY_T']
    )

    # 3 tháng gần nhất
    start_3m = (end_audit.replace(day=1) - relativedelta(months=2)).replace(day=1)
    end_3m = end_audit

    df_pos['DSỐ_3_THÁNG_GẦN_NHẤT'] = calc_revenue(df_6_2a, df_pos, start_3m, end_3m)
    df_pos['DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT'] = (df_pos['DSỐ_3_THÁNG_GẦN_NHẤT'] / 3).round(2)

    # Lọc trùng MID theo BRANCH_LAP_DAT_MAY
    df_pos = df_pos.drop_duplicates(subset=['MID', 'BRANCH_LAP_DAT_MAY'], keep='first').copy()

    # POS đang hoạt động
    df_pos['POS_ĐANG_HOẠT_ĐỘNG'] = df_pos['DEVICE_STATUS'].astype(str).apply(
        lambda x: 'X' if x == 'Device OK' else ''
    )

    # POS hoạt động – DS 3 năm cao nhất
    df_active = df_pos[df_pos['POS_ĐANG_HOẠT_ĐỘNG'] == 'X']
    if not df_active.empty:
        top10_total = df_active.nlargest(10, 'TỔNG_DSỐ_3_NĂM')['MID']
    else:
        top10_total = pd.Series([], dtype=str)

    df_pos['POS ĐANG HOẠT ĐỘNG CÓ TỔNG DSỐ 3 NĂM CAO'] = df_pos['MID'].apply(
        lambda x: 'X' if x in top10_total.values else ''
    )

    # POS hoạt động – DS 3 tháng gần nhất cao nhất
    if not df_active.empty:
        top10_3m = df_active.nlargest(10, 'DSỐ_3_THÁNG_GẦN_NHẤT')['MID']
    else:
        top10_3m = pd.Series([], dtype=str)

    df_pos['POS ĐANG HOẠT ĐỘNG CÓ DSỐ 3 THÁNG GẦN NHẤT CAO'] = df_pos['MID'].apply(
        lambda x: 'X' if x in top10_3m.values else ''
    )

    # POS KPS doanh số 3 tháng & chưa đóng
    df_pos['POS KPS DSỐ TRONG 3 THÁNG VÀ CHƯA ĐÓNG'] = df_pos.apply(
        lambda row: 'X' if row['POS_ĐANG_HOẠT_ĐỘNG'] == 'X' and row['DSỐ_3_THÁNG_GẦN_NHẤT'] == 0 else '',
        axis=1
    )

    # POS DS BQ 3 tháng < 20tr & chưa đóng
    df_pos['POS CÓ DSỐ BQ TRONG 3 THÁNG < 20 TRĐ VÀ CHƯA ĐÓNG'] = df_pos.apply(
        lambda row: 'X' if (
            row['POS_ĐANG_HOẠT_ĐỘNG'] == 'X' and
            row['DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT'] < 20_000_000
        ) else '',
        axis=1
    )

    # ĐVCNT có nhiều POS đang hoạt động (>2)
    active_pos = df_pos[df_pos['POS_ĐANG_HOẠT_ĐỘNG'] == 'X']
    multi_pos = active_pos.groupby('MERCHANT_CIF').filter(
        lambda g: len(g) >= 2
    )['MERCHANT_CIF'].unique()

    df_pos['ĐVCNT CÓ NHIỀU POS ĐANG HOẠT ĐỘNG (>2)'] = df_pos['MERCHANT_CIF'].apply(
        lambda x: 'X' if x in multi_pos else ''
    )

    return df_processed, df_pos


# =========================================================
# HÀM PUBLIC – GỌI TỪ app.py
# =========================================================
def run_module_the():
    """
    Giao diện Streamlit cho mô-đun TIÊU CHÍ THẺ & POS (1600)
    Gọi trong app.py:  from module.tieuchithe import run_module_the
    """

    st.title("📊 TIÊU CHÍ 1600 – THẺ & POS")

    with st.sidebar:
        st.header("⚙️ Tham số chạy")

        chi_nhanh_input = st.text_input(
            "Nhập tên chi nhánh hoặc mã SOL (VD: HANOI, 001)",
            value="HANOI"
        )

        start_audit_date = st.date_input(
            "Ngày bắt đầu thời hiệu kiểm toán",
            value=date(2025, 1, 1)
        )
        end_audit_date = st.date_input(
            "Ngày kết thúc thời hiệu kiểm toán",
            value=date(2025, 10, 31)
        )

        run_button = st.button("🚀 Chạy toàn bộ pipeline")

        if run_button:
            with st.spinner("Đang xử lý toàn bộ dữ liệu thẻ & POS..."):
                df_card, df_pos = run_full_pipeline(
                    chi_nhanh=chi_nhanh_input,
                    start_audit=datetime.combine(start_audit_date, datetime.min.time()),
                    end_audit=datetime.combine(end_audit_date, datetime.min.time()),
                )
                st.session_state['df_card'] = df_card
                st.session_state['df_pos'] = df_pos

            st.success("✅ Đã xử lý xong dữ liệu thẻ & POS!")

    tab1, tab2, tab3, tab4 = st.tabs([
        "🔍 Thông tin chạy",
        "💳 Kết quả Thẻ (1.3.2)",
        "🏧 Kết quả POS (6.2a, 6.2b, 7, 8)",
        "⬇️ Tải file Excel"
    ])

    with tab1:
        st.subheader("🔍 Thông tin tham số & trạng thái")
        st.write(f"**Chi nhánh / SOL:** `{chi_nhanh_input}`")
        st.write(f"**Thời hiệu kiểm toán:** từ `{start_audit_date}` đến `{end_audit_date}`")

        if 'df_card' in st.session_state:
            st.success("✅ Dữ liệu đã xử lý, xem ở các tab tiếp theo.")
            st.write("**Số dòng bảng Thẻ:**", len(st.session_state['df_card']))
            st.write("**Số dòng bảng POS:**", len(st.session_state['df_pos']))
        else:
            st.info("⏳ Chưa có dữ liệu. Vào Sidebar và bấm **Chạy toàn bộ pipeline**.")

    with tab2:
        st.subheader("💳 Bảng kết quả Thẻ – Mục 1.3.2")
        if 'df_card' in st.session_state:
            df_card = st.session_state['df_card']
            st.write("### Xem nhanh 20 dòng đầu")
            st.dataframe(df_card.head(20), use_container_width=True)

            with st.expander("📚 Xem toàn bộ danh sách cột"):
                st.write(list(df_card.columns))
        else:
            st.warning("⚠ Chưa có dữ liệu thẻ. Hãy chạy pipeline ở Sidebar.")

    with tab3:
        st.subheader("🏧 Bảng kết quả POS – Tiêu chí 6, 7, 8")
        if 'df_pos' in st.session_state:
            df_pos = st.session_state['df_pos']
            st.write("### Xem nhanh 20 dòng đầu")
            st.dataframe(df_pos.head(20), use_container_width=True)

            with st.expander("📚 Một số cột chính"):
                selected_cols = [c for c in [
                    'MID', 'BRANCH_LAP_DAT_MAY', 'MERCHANT_CIF',
                    'DSỐ_2_NĂM_TRƯỚC_T2', 'DSỐ_NĂM_TRƯỚC_T1', 'DSỐ_NĂM_NAY_T',
                    'TỔNG_DSỐ_3_NĂM', 'DSỐ_3_THÁNG_GẦN_NHẤT',
                    'POS_ĐANG_HOẠT_ĐỘNG',
                    'POS KPS DSỐ TRONG 3 THÁNG VÀ CHƯA ĐÓNG',
                    'POS CÓ DSỐ BQ TRONG 3 THÁNG < 20 TRĐ VÀ CHƯA ĐÓNG',
                    'ĐVCNT CÓ NHIỀU POS ĐANG HOẠT ĐỘNG (>2)'
                ] if c in df_pos.columns]
                st.dataframe(df_pos[selected_cols].head(30), use_container_width=True)
        else:
            st.warning("⚠ Chưa có dữ liệu POS. Hãy chạy pipeline ở Sidebar.")

    with tab4:
        st.subheader("⬇️ Tải file kết quả Excel")
        if 'df_card' in st.session_state:
            df_card = st.session_state['df_card']
            df_pos = st.session_state['df_pos']

            card_bytes = df_to_excel_bytes(df_card, sheet_name="THE_1600")
            pos_bytes = df_to_excel_bytes(df_pos, sheet_name="POS_1600")

            st.download_button(
                label="💳 Tải file Thẻ (1.3.2) – Excel",
                data=card_bytes,
                file_name="tieuchithe_1600_streamlit.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            st.download_button(
                label="🏧 Tải file POS (6,7,8) – Excel",
                data=pos_bytes,
                file_name="tieuchi6_7_8_1600_streamlit.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("📂 Chưa có dữ liệu để tải. Hãy chạy pipeline trước.")
