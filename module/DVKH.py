# module/DVKH.py
"""
Module DVKH cho Streamlit
Bao gồm: 2 tab
- Tab A: Tiêu chí 1,2,3 (Ủy quyền + SMS + SCM010)
- Tab B: Tiêu chí 4 (HDV KKH + chargelevel + nhân sự) và Tiêu chí 5 (Mapping/1405)
Ghi audit vào CSV dvkh_audit.csv trong working dir (không thay DB).
"""

import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import glob
import zipfile
import os
from datetime import datetime
from typing import List, Optional

# Cố gắng lấy user hiện tại từ hệ thống auth (nếu project của bạn có)
try:
    from db.auth_jwt import get_current_user
except Exception:
    def get_current_user():
        return {"username": "unknown", "full_name": "unknown", "role": "unknown"}


# ---------------------------
# Utilities
# ---------------------------
AUDIT_FILE = "dvkh_audit.csv"

def audit_log(action: str, note: str = "", user: Optional[dict] = None):
    """Ghi log hoạt động (append CSV)."""
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    if user is None:
        user = get_current_user() if callable(get_current_user) else {"username": "unknown"}
    username = user.get("username", "unknown") if isinstance(user, dict) else str(user)
    row = {"timestamp": ts, "username": username, "action": action, "note": note}
    df_row = pd.DataFrame([row])
    header = not os.path.exists(AUDIT_FILE)
    df_row.to_csv(AUDIT_FILE, mode="a", header=header, index=False, encoding="utf-8-sig")


@st.cache_data(show_spinner=False)
def read_excel_file_bytesio(uploaded_file) -> pd.DataFrame:
    """Đọc file uploaded (pandas) với dtype=str an toàn."""
    return pd.read_excel(uploaded_file, dtype=str)


@st.cache_data(show_spinner=False)
def read_text_file_bytesio(uploaded_file, sep='\t') -> pd.DataFrame:
    return pd.read_csv(uploaded_file, sep=sep, dtype=str, on_bad_lines='skip')


def safe_to_datetime(series, fmt=None):
    if fmt:
        return pd.to_datetime(series, format=fmt, errors='coerce')
    return pd.to_datetime(series, errors='coerce')


def to_excel_bytes(dfs: dict) -> bytes:
    """Trả về bytes của Excel (multi-sheet)."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in dfs.items():
            # truncate sheet name to 31 chars
            sheet = name[:31]
            df.to_excel(writer, sheet_name=sheet, index=False)
    output.seek(0)
    return output.getvalue()


# ---------------------------
# XỬ LÝ TIÊU CHÍ 1-3 (Ủy quyền + SMS + SCM010)
# ---------------------------
def process_uyquyen_sms_scm(
    uploaded_ckh_files: List,
    uploaded_kkh_files: List,
    uploaded_muc30_file,
    uploaded_sms_txt_file,
    uploaded_scm10_xlsx_file,
    filter_chi_nhanh: Optional[str] = None
):
    """Trả về df_uyquyen, df_tc3 (final display for tab1)."""
    # 1. ghép CKH + KKH
    df_b_CKH = pd.concat([read_excel_file_bytesio(f) for f in uploaded_ckh_files], ignore_index=True) if uploaded_ckh_files else pd.DataFrame()
    df_b_KKH = pd.concat([read_excel_file_bytesio(f) for f in uploaded_kkh_files], ignore_index=True) if uploaded_kkh_files else pd.DataFrame()
    df_b = pd.concat([df_b_CKH, df_b_KKH], ignore_index=True) if not df_b_CKH.empty or not df_b_KKH.empty else pd.DataFrame()

    # 2. đọc MUC30 (df_a)
    df_a = read_excel_file_bytesio(uploaded_muc30_file)

    # filter DESCRIPTION chứa chu ky
    df_a = df_a[df_a["DESCRIPTION"].str.contains(r"chu\s*ky|chuky|cky", case=False, na=False)].copy()

    # chuyển ngày
    # một số file cung cấp YYYYMMDD, một số đã ở dạng khác -> dùng coerce
    df_a["EXPIRYDATE"] = safe_to_datetime(df_a.get("EXPIRYDATE", pd.Series(dtype=str)))
    df_a["EFFECTIVEDATE"] = safe_to_datetime(df_a.get("EFFECTIVEDATE", pd.Series(dtype=str)))
    # format mm/dd/YYYY để nhất quán
    df_a["EXPIRYDATE_str"] = df_a["EXPIRYDATE"].dt.strftime("%m/%d/%Y")
    df_a["EFFECTIVEDATE_str"] = df_a["EFFECTIVEDATE"].dt.strftime("%m/%d/%Y")

    # filter loại doanh nghiệp
    keywords = ["CONG TY", "CTY", "CONGTY", "CÔNG TY", "CÔNGTY"]
    df_a = df_a[~df_a["NGUOI_UY_QUYEN"].astype(str).str.upper().str.contains("|".join(keywords), na=False)].copy()

    # extract name
    def extract_name(value):
        parts = re.split(r'[-,]', str(value))
        for part in parts:
            name = part.strip()
            if re.fullmatch(r'[A-Z ]{3,}', name):
                return name
        return value

    df_a["NGUOI_DUOC_UY_QUYEN"] = df_a["NGUOI_DUOC_UY_QUYEN"].apply(extract_name)
    df_a = df_a.drop_duplicates(subset=["PRIMARY_SOL_ID", "TK_DUOC_UY_QUYEN", "NGUOI_DUOC_UY_QUYEN"], keep='first')

    # 3. merge TK_DUOC_UY_QUYEN vs df_b IDXACNO -> get CUSTSEQ (CIF)
    if not df_b.empty and "IDXACNO" in df_b.columns:
        df_a["TK_DUOC_UY_QUYEN"] = df_a["TK_DUOC_UY_QUYEN"].astype(str)
        df_b["IDXACNO"] = df_b["IDXACNO"].astype(str)
        merged = df_a.merge(df_b[["IDXACNO", "CUSTSEQ"]], left_on="TK_DUOC_UY_QUYEN", right_on="IDXACNO", how="left")
    else:
        merged = df_a.copy()
        merged["CUSTSEQ"] = np.nan

    # CIF người ủy quyền
    merged["CIF_NGUOI_UY_QUYEN"] = merged["CUSTSEQ"].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).strip() != "" and str(x) != "nan" else "NA")

    # bổ sung CIF nếu cùng NGUOI_UY_QUYEN
    cif_nguoi_uy_quyen_updated = merged["CIF_NGUOI_UY_QUYEN"].copy()
    for nguoi_uq, group in merged.groupby("NGUOI_UY_QUYEN"):
        if len(group) >= 2:
            cif_values = group["CIF_NGUOI_UY_QUYEN"]
            has_na = "NA" in cif_values.unique()
            actual_cifs = [c for c in cif_values.unique() if c != "NA"]
            if has_na and actual_cifs:
                cif_to_fill = actual_cifs[0]
                indices_to_update = group[group["CIF_NGUOI_UY_QUYEN"] == "NA"].index
                cif_nguoi_uy_quyen_updated.loc[indices_to_update] = cif_to_fill
    merged["CIF_NGUOI_UY_QUYEN"] = cif_nguoi_uy_quyen_updated

    # remove helper columns if exist
    for drop_col in ["IDXACNO", "CUSTSEQ"]:
        if drop_col in merged.columns:
            merged.drop(columns=[drop_col], inplace=True, errors='ignore')

    # classify account type using CKH/KKH sets
    set_ckh = set(df_b_CKH["CUSTSEQ"].astype(str).dropna()) if not df_b.empty and 'CUSTSEQ' in df_b_CKH.columns else set()
    set_kkh = set(df_b_KKH["IDXACNO"].astype(str).dropna()) if not df_b.empty and 'IDXACNO' in df_b_KKH.columns else set()
    def phan_loai_tk(tk):
        if str(tk) in set_ckh:
            return "CKH"
        if str(tk) in set_kkh:
            return "KKH"
        return "NA"
    merged["LOAI_TK"] = merged["TK_DUOC_UY_QUYEN"].astype(str).apply(phan_loai_tk)

    # time calculations
    merged["EXPIRYDATE_dt"] = safe_to_datetime(merged.get("EXPIRYDATE_str") if "EXPIRYDATE_str" in merged.columns else merged.get("EXPIRYDATE"))
    merged["EFFECTIVEDATE_dt"] = safe_to_datetime(merged.get("EFFECTIVEDATE_str") if "EFFECTIVEDATE_str" in merged.columns else merged.get("EFFECTIVEDATE"))
    merged["YEAR_DIFF"] = merged["EXPIRYDATE_dt"].dt.year - merged["EFFECTIVEDATE_dt"].dt.year
    merged["KHONG_NHAP_TGIAN_UQ"] = ""
    merged.loc[merged["YEAR_DIFF"].fillna(-1) == 99, "KHONG_NHAP_TGIAN_UQ"] = "X"
    merged["UQ_TREN_50_NAM"] = ""
    merged.loc[merged["YEAR_DIFF"].fillna(-1) >= 50, "UQ_TREN_50_NAM"] = "X"
    merged.drop(columns=["EXPIRYDATE_dt", "EFFECTIVEDATE_dt", "YEAR_DIFF"], inplace=True, errors='ignore')

    # 4. SMS + SCM010 processing
    df_sms_raw = read_text_file_bytesio(uploaded_sms_txt_file)  # expects tab separated
    df_sms = df_sms_raw.copy()
    for col in ["FORACID", "ORGKEY", "C_MOBILE_NO"]:
        if col in df_sms.columns:
            df_sms[col] = df_sms[col].astype(str)
    # normalize date
    if "CRE_DATE" in df_sms.columns:
        df_sms["CRE_DATE_parsed"] = safe_to_datetime(df_sms["CRE_DATE"])
        df_sms["CRE_DATE_str"] = df_sms["CRE_DATE_parsed"].dt.strftime("%m/%d/%Y")
    # filter
    if "FORACID" in df_sms.columns:
        df_sms = df_sms[df_sms["FORACID"].str.match(r'^\d+$', na=False)]
    if "CUSTTPCD" in df_sms.columns:
        df_sms = df_sms[df_sms["CUSTTPCD"].str.upper() != "KHDN"]

    df_scm10 = read_excel_file_bytesio(uploaded_scm10_xlsx_file)
    df_scm10 = df_scm10.rename(columns=lambda x: x.strip())
    if "CIF_ID" in df_scm10.columns:
        df_scm10["CIF_ID"] = df_scm10["CIF_ID"].astype(str)
    df_sms["PL DICH VU"] = "SMS"
    df_scm10["ORGKEY"] = df_scm10.get("CIF_ID", pd.Series(dtype=str))
    df_scm10["PL DICH VU"] = "SCM010"
    df_merged_sms_scm10 = pd.concat([df_sms, df_scm10[["ORGKEY", "PL DICH VU"]].drop_duplicates()], ignore_index=True, axis=0)

    # mark accounts registered for SMS and CIF registered for SCM010
    df_sms_only = df_merged_sms_scm10[df_merged_sms_scm10["PL DICH VU"] == "SMS"] if "PL DICH VU" in df_merged_sms_scm10.columns else pd.DataFrame()
    tk_sms_set = set(df_sms_only["FORACID"].astype(str).dropna()) if not df_sms_only.empty else set()
    df_scm10_only = df_merged_sms_scm10[df_merged_sms_scm10["PL DICH VU"] == "SCM010"] if "PL DICH VU" in df_merged_sms_scm10.columns else pd.DataFrame()
    cif_scm10_set = set(df_scm10_only["ORGKEY"].astype(str).dropna()) if not df_scm10_only.empty else set()

    merged["TK có đăng ký SMS"] = merged["TK_DUOC_UY_QUYEN"].astype(str).apply(lambda x: "X" if str(x) in tk_sms_set else "")
    merged["CIF có đăng ký SCM010"] = merged["CIF_NGUOI_UY_QUYEN"].astype(str).apply(lambda x: "X" if str(x) in cif_scm10_set else "")

    # 5. 1 người nhận nhiều UQ
    df_tc3 = merged.copy()
    grouped = df_tc3.groupby("NGUOI_DUOC_UY_QUYEN")["NGUOI_UY_QUYEN"].nunique().reset_index()
    grouped = grouped[grouped["NGUOI_UY_QUYEN"] >= 2]
    nguoi_nhan_nhieu_uq = set(grouped["NGUOI_DUOC_UY_QUYEN"].astype(str).dropna())
    df_tc3["1 người nhận UQ của nhiều người"] = df_tc3["NGUOI_DUOC_UY_QUYEN"].astype(str).apply(lambda x: "X" if x in nguoi_nhan_nhieu_uq else "")

    return merged, df_tc3


# ---------------------------
# XỬ LÝ TIÊU CHÍ 4-5 (42a, mapping)
# ---------------------------
def process_tieuchi_4_5(
    files_42a_upload: List,
    file_42b_upload,
    file_42c_upload,
    file_42d_upload,
    file_mapping_upload,
    chi_nhanh: str
):
    """Trả về df_42a_processed, df_mapping_final"""
    # 1) ghép file 42a (HDV_CHITIET_KKH_*)
    df_ghep42a = pd.concat([read_excel_file_bytesio(f) for f in files_42a_upload], ignore_index=True) if files_42a_upload else pd.DataFrame()
    df_42a = df_ghep42a[df_ghep42a["BRCD"].astype(str).str.upper().str.contains(chi_nhanh)].copy() if not df_ghep42a.empty else pd.DataFrame()

    # keep columns
    columns_needed_42a = ['BRCD', 'DEPTCD', 'CUST_TYPE', 'CUSTSEQ', 'NMLOC', 'BIRTH_DAY',
                          'IDXACNO', 'SCHM_NAME', 'CCYCD', 'CURBAL_VN', 'OPNDT_FIRST', 'OPNDT_EFFECT']
    df_42a = df_42a[[c for c in columns_needed_42a if c in df_42a.columns]].copy()

    # KHCN
    if 'CUST_TYPE' in df_42a.columns:
        df_42a = df_42a[df_42a['CUST_TYPE'].str.upper() == 'KHCN'].copy()
    if 'CURBAL_VN' in df_42a.columns:
        df_42a['CURBAL_VN'] = df_42a['CURBAL_VN'].astype(str)

    exclude_keywords = ['KY QUY', 'GIAI NGAN', 'CHI LUONG', 'TKTT THE', 'TRUNG GIAN']
    if 'SCHM_NAME' in df_42a.columns:
        mask_exclude = df_42a['SCHM_NAME'].astype(str).str.upper().str.contains('|'.join(exclude_keywords), na=False)
        df_42a = df_42a[~mask_exclude].copy()

    # 2) df_42b (chargelevel)
    df_ghep42b = read_excel_file_bytesio(file_42b_upload)
    df_42b = df_ghep42b[df_ghep42b['CN_MO_TK'].astype(str).str.upper().str.contains(chi_nhanh)].copy() if 'CN_MO_TK' in df_ghep42b.columns else df_ghep42b.copy()

    # merge MACIF -> CHARGELEVELCODE_CIF
    if 'CUSTSEQ' in df_42a.columns and 'MACIF' in df_42b.columns:
        df_42a['CUSTSEQ'] = df_42a['CUSTSEQ'].astype(str)
        df_42b['MACIF'] = df_42b['MACIF'].astype(str)
        df_42b_unique_macif = df_42b.drop_duplicates(subset=['MACIF'], keep='first')
        df_42a = df_42a.merge(df_42b_unique_macif[['MACIF', 'CHARGELEVELCODE_CIF']], how='left', left_on='CUSTSEQ', right_on='MACIF')
        df_42a.rename(columns={'CHARGELEVELCODE_CIF': 'CHARGELEVELCODE_CUA_CIF'}, inplace=True)
        df_42a.drop(columns=['MACIF'], inplace=True, errors='ignore')

    # merge STKKH -> CHARGELEVELCODE_TK
    if 'IDXACNO' in df_42a.columns and 'STKKH' in df_42b.columns:
        df_42a['IDXACNO'] = df_42a['IDXACNO'].astype(str)
        df_42b['STKKH'] = df_42b['STKKH'].astype(str)
        df_42b_unique_stkkh = df_42b.drop_duplicates(subset=['STKKH'], keep='first')
        df_42a = df_42a.merge(df_42b_unique_stkkh[['STKKH', 'CHARGELEVELCODE_TK']], how='left', left_on='IDXACNO', right_on='STKKH')
        df_42a.rename(columns={'CHARGELEVELCODE_TK': 'CHARGELEVELCODE_CUA_TK'}, inplace=True)
        df_42a.drop(columns=['STKKH'], inplace=True, errors='ignore')

    # (3) TK gắn code ưu đãi CBNV
    if 'CHARGELEVELCODE_CUA_TK' in df_42a.columns:
        df_42a['TK_GAN_CODE_UU_DAI_CBNV'] = np.where(df_42a['CHARGELEVELCODE_CUA_TK'] == 'NVEIB', 'X', '')

    # (4) nhân sự nghỉ việc
    df_42d = read_excel_file_bytesio(file_42d_upload)
    if 'CUSTSEQ' in df_42a.columns and 'CIF' in df_42d.columns:
        df_42a["CBNV_NGHI_VIEC"] = df_42a["CUSTSEQ"].isin(df_42d["CIF"]).map({True: "X", False: ""})
        df_42a = df_42a.merge(df_42d[['CIF', 'Ngày thôi việc']], how='left', left_on='CUSTSEQ', right_on='CIF')
        df_42a['CBNV_NGHI_VIEC'] = np.where(df_42a['CIF'].notna(), 'X', '')
        df_42a.rename(columns={'Ngày thôi việc': 'NGAY_NGHI_VIEC'}, inplace=True)
        df_42a['NGAY_NGHI_VIEC'] = safe_to_datetime(df_42a['NGAY_NGHI_VIEC']).dt.strftime('%m/%d/%Y')

    # 5) Mapping_1405 -> tiêu chí 5
    df_mapping = read_excel_file_bytesio(file_mapping_upload)
    df_mapping.columns = df_mapping.columns.str.lower()
    cols_needed_mapping = [
        'brcd', 'semaacount', 'cardnbr', 'token', 'relation', 'uploaddt',
        'odaccount', 'acctcd', 'dracctno', 'drratio', 'adduser', 'updtuser',
        'expiredate', 'custnm', 'cif', 'xpcode', 'xpcodedt', 'remark', 'oldxpcode'
    ]
    existing_cols_mapping = [c for c in cols_needed_mapping if c in df_mapping.columns]
    df_mapping_final = df_mapping[existing_cols_mapping].copy()
    if 'xpcodedt' in df_mapping_final.columns:
        df_mapping_final['xpcodedt'] = safe_to_datetime(df_mapping_final['xpcodedt'])
    if 'uploaddt' in df_mapping_final.columns:
        df_mapping_final['uploaddt'] = safe_to_datetime(df_mapping_final['uploaddt'])

    if 'xpcodedt' in df_mapping_final.columns and 'uploaddt' in df_mapping_final.columns:
        df_mapping_final['SO_NGAY_MO_THE'] = (df_mapping_final['xpcodedt'] - df_mapping_final['uploaddt']).dt.days
        df_mapping_final['MO_DONG_TRONG_6_THANG'] = df_mapping_final.apply(
            lambda row: 'X' if (
                pd.notnull(row.get('SO_NGAY_MO_THE')) and
                row.get('SO_NGAY_MO_THE') >= 0 and
                row.get('SO_NGAY_MO_THE') < 180 and
                pd.notnull(row.get('uploaddt')) and
                row.get('uploaddt') > pd.to_datetime('2023-05-31')
            ) else '', axis=1
        )

    return df_42a, df_mapping_final


# ---------------------------
# STREAMLIT UI PUBLIC FUNCTION
# ---------------------------
def run_dvkh_5_tieuchi():
    st.title("👥 DVKH — 5 tiêu chí (Ủy quyền, SMS/SCM, HDV, Mapping)")

    user = get_current_user() or {"username": "unknown"}

    tab1, tab2 = st.tabs(["Tiêu chí 1-3 (Ủy quyền + SMS/SCM)", "Tiêu chí 4-5 (42a & Mapping)"])

    # ---- TAB 1 ----
    # with tab1:
    #     st.header("A. Tiêu chí 1-3: Ủy quyền + SMS + SCM010")
    #     st.info("Upload: HDV_CHITIET_CKH (nhiều file), HDV_CHITIET_KKH (nhiều file), MUC30, Muc14_DKSMS.txt, Muc14_SCM010.xlsx")

    #     uploaded_ckh_files = st.file_uploader("HDV_CHITIET_CKH (CKH) - multiple", type=["xls", "xlsx"], accept_multiple_files=True, key="dvkh_ckh")
    #     uploaded_kkh_files = st.file_uploader("HDV_CHITIET_KKH (KKH) - multiple", type=["xls", "xlsx"], accept_multiple_files=True, key="dvkh_kkh")
    #     uploaded_muc30_file = st.file_uploader("MUC 30 (Muc30) - single", type=["xls", "xlsx", "xlsx"], key="dvkh_muc30")
    #     uploaded_sms_txt_file = st.file_uploader("Muc14_DKSMS.txt (tab-separated)", type=["txt", "csv"], key="dvkh_sms")
    #     uploaded_scm10_xlsx_file = st.file_uploader("Muc14_SCM010.xlsx", type=["xls", "xlsx"], key="dvkh_scm10")

    #     if st.button("Chạy Tiêu chí 1-3"):
    #         if not (uploaded_ckh_files and uploaded_kkh_files and uploaded_muc30_file and uploaded_sms_txt_file and uploaded_scm10_xlsx_file):
    #             st.error("Vui lòng tải lên đầy đủ các file yêu cầu cho Tiêu chí 1-3.")
    #             audit_log("run_tieuchi_1_3_failed", "missing files", user)
    #         else:
    #             try:
    #                 audit_log("run_tieuchi_1_3_start", f"files: CKH={len(uploaded_ckh_files)}, KKH={len(uploaded_kkh_files)}", user)
    #                 merged, df_tc3 = process_uyquyen_sms_scm(uploaded_ckh_files, uploaded_kkh_files, uploaded_muc30_file, uploaded_sms_txt_file, uploaded_scm10_xlsx_file)
    #                 st.success("Xử lý xong Tiêu chí 1-3")
    #                 st.subheader("Kết quả — preview (Tiêu chí 3)")
    #                 st.dataframe(df_tc3.head(200), use_container_width=True)

    #                 # Download both sheets
    #                 out_bytes = to_excel_bytes({
    #                     "UyQuyen": merged,
    #                     "UyQuyen_TC3": df_tc3
    #                 })
    #                 st.download_button("Tải Excel Tiêu chí 1-3", data=out_bytes, file_name="DVKH_TC1_3.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    #                 audit_log("run_tieuchi_1_3_success", f"rows:{len(df_tc3)}", user)
    #             except Exception as e:
    #                 st.error("Đã xảy ra lỗi trong quá trình xử lý Tiêu chí 1-3.")
    #                 st.exception(e)
    #                 audit_log("run_tieuchi_1_3_error", str(e), user)


        def extract_excel_from_zip(uploaded_zip):
        """Trả về list các (filename, BytesIO) của file .xls/.xlsx trong ZIP."""
        result = []
        try:
            z = zipfile.ZipFile(uploaded_zip)
            for name in z.namelist():
                if name.lower().endswith((".xls", ".xlsx")):
                    result.append((name, io.BytesIO(z.read(name))))
            return result
        except:
            return []
    
    
        # =============================
        # GIẢI NÉN 1 FILE TXT TỪ ZIP
        # =============================
        def extract_sms_txt_from_zip(uploaded_zip_file):
            """Trích xuất file Muc14_DKSMS.txt từ ZIP (trong bộ nhớ)."""
            try:
                z = zipfile.ZipFile(uploaded_zip_file)
                for name in z.namelist():
                    if name.lower().endswith(".txt"):
                        return io.BytesIO(z.read(name)), name
                return None, None
            except:
                return None, None
        
        
        
        # =============================
        # UI TAB 1
        # =============================
        with tab1:
            st.header("A. Tiêu chí 1-3: Ủy quyền + SMS + SCM010")
            st.info("Upload: CKH.zip, KKH.zip, MUC30.xlsx, ZIP chứa Muc14_DKSMS.txt, SCM010.xlsx")
        
            # CKH ZIP
            uploaded_ckh_zip = st.file_uploader(
                "HDV_CHITIET_CKH.zip (nhiều file Excel bên trong)",
                type=["zip"],
                key="dvkh_ckh"
            )
        
            # KKH ZIP
            uploaded_kkh_zip = st.file_uploader(
                "HDV_CHITIET_KKH.zip (nhiều file Excel bên trong)",
                type=["zip"],
                key="dvkh_kkh"
            )
        
            # MUC30
            uploaded_muc30_file = st.file_uploader(
                "MUC 30 (Muc30)",
                type=["xls", "xlsx"],
                key="dvkh_muc30"
            )
        
            # SMS ZIP
            uploaded_sms_zip = st.file_uploader(
                "Muc14_DKSMS.zip (bên trong phải có 1 file .txt)",
                type=["zip"],
                key="dvkh_sms_zip"
            )
        
            # SCM010
            uploaded_scm10_xlsx_file = st.file_uploader(
                "Muc14_SCM010.xlsx",
                type=["xls", "xlsx"],
                key="dvkh_scm10"
            )
        
        
            # ========================================
            # BUTTON
            # ========================================
            if st.button("Chạy Tiêu chí 1-3"):
        
                # ----- kiểm tra upload -----
                if not uploaded_ckh_zip:
                    st.error("Bạn phải upload file ZIP CKH.")
                    st.stop()
        
                if not uploaded_kkh_zip:
                    st.error("Bạn phải upload file ZIP KKH.")
                    st.stop()
        
                if not uploaded_sms_zip:
                    st.error("Bạn phải upload file ZIP chứa Muc14_DKSMS.txt.")
                    st.stop()
        
                # ========================================
                # GIẢI NÉN CKH ZIP
                # ========================================
                ckh_files = extract_excel_from_zip(uploaded_ckh_zip)
                if len(ckh_files) == 0:
                    st.error("ZIP CKH không chứa file Excel (.xls/.xlsx).")
                    st.stop()
        
                # convert -> danh sách BytesIO để truyền vào xử lý
                ckh_streams = [f[1] for f in ckh_files]
        
        
                # ========================================
                # GIẢI NÉN KKH ZIP
                # ========================================
                kkh_files = extract_excel_from_zip(uploaded_kkh_zip)
                if len(kkh_files) == 0:
                    st.error("ZIP KKH không chứa file Excel (.xls/.xlsx).")
                    st.stop()
        
                kkh_streams = [f[1] for f in kkh_files]
        
        
                # ========================================
                # GIẢI NÉN SMS.TXT TỪ ZIP
                # ========================================
                sms_txt_bytes, sms_filename = extract_sms_txt_from_zip(uploaded_sms_zip)
        
                if sms_txt_bytes is None:
                    st.error("Không tìm thấy file .txt trong ZIP SMS. Vui lòng kiểm tra lại!")
                    st.stop()
        
        
                # ========================================
                # XỬ LÝ DỮ LIỆU
                # ========================================
                try:
                    merged, df_tc3 = process_uyquyen_sms_scm(
                        ckh_streams,
                        kkh_streams,
                        uploaded_muc30_file,
                        sms_txt_bytes,
                        uploaded_scm10_xlsx_file
                    )
        
                    st.success("Xử lý xong Tiêu chí 1-3")
        
                    st.subheader("Kết quả — preview (Tiêu chí 3)")
                    st.dataframe(df_tc3.head(200), use_container_width=True)
        
                    out_bytes = to_excel_bytes({
                        "UyQuyen": merged,
                        "UyQuyen_TC3": df_tc3
                    })
        
                    st.download_button(
                        "📥 Tải Excel Tiêu chí 1-3",
                        data=out_bytes,
                        file_name="DVKH_TC1_3.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        
                except Exception as e:
                    st.error("Lỗi khi xử lý Tiêu chí 1-3.")
                    st.exception(e)

    # ---- TAB 2 ----
    with tab2:
        st.header("B. Tiêu chí 4 & 5 (42a / Mapping)")
        st.info("Upload files: HDV_CHITIET_KKH (list), BC_LAY_CHARGELEVELCODE..., 10_Danh sach nhan su..., DS nghi viec..., Mapping_1405.xlsx")

        files_42a_upload = st.file_uploader("HDV_CHITIET_KKH_*.xls (multiple)", type=["xls", "xlsx"], accept_multiple_files=True, key="dvkh_42a")
        file_42b_upload = st.file_uploader("BC_LAY_CHARGELEVELCODE_THEO_KHCN.xlsx", type=["xls", "xlsx"], key="dvkh_42b")
        file_42c_upload = st.file_uploader("10_Danh sach nhan su_T*.xlsx", type=["xls", "xlsx"], key="dvkh_42c")
        file_42d_upload = st.file_uploader("2.DS..._nghi_viec.xlsx", type=["xls", "xlsx"], key="dvkh_42d")
        file_mapping_upload = st.file_uploader("Mapping_1405.xlsx", type=["xls", "xlsx"], key="dvkh_map")
        chi_nhanh = st.text_input("Nhập tên chi nhánh hoặc mã SOL để lọc (VD: HANOI hoặc 1405)").strip().upper()

        if st.button("Chạy Tiêu chí 4-5"):
            if not (files_42a_upload and file_42b_upload and file_42c_upload and file_42d_upload and file_mapping_upload and chi_nhanh):
                st.error("Vui lòng tải đầy đủ file và nhập chi nhánh để chạy Tiêu chí 4-5.")
                audit_log("run_tieuchi_4_5_failed", "missing inputs", user)
            else:
                try:
                    audit_log("run_tieuchi_4_5_start", f"chi_nhanh={chi_nhanh}", user)
                    df_42a_processed, df_mapping_final = process_tieuchi_4_5(files_42a_upload, file_42b_upload, file_42c_upload, file_42d_upload, file_mapping_upload, chi_nhanh)
                    st.success("Xử lý xong Tiêu chí 4-5")
                    st.subheader("Preview Tiêu chí 4 (42a)")
                    st.dataframe(df_42a_processed.head(200), use_container_width=True)
                    st.subheader("Preview Tiêu chí 5 (Mapping)")
                    st.dataframe(df_mapping_final.head(200), use_container_width=True)

                    # xuất Excel 2 sheet
                    out_bytes = to_excel_bytes({
                        "Tieu_chi_4": df_42a_processed,
                        "Tieu_chi_5": df_mapping_final
                    })
                    st.download_button("Tải Excel Tiêu chí 4-5", data=out_bytes, file_name="DVKH_TC4_5.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    audit_log("run_tieuchi_4_5_success", f"rows4:{len(df_42a_processed)} rows5:{len(df_mapping_final)}", user)
                except Exception as e:
                    st.error("Đã xảy ra lỗi trong quá trình xử lý Tiêu chí 4-5.")
                    st.exception(e)
                    audit_log("run_tieuchi_4_5_error", str(e), user)

    # ---- Audit viewer & quick exports ----
    st.markdown("---")
    st.header("Audit & Logs")
    st.write("Nhật ký hoạt động DVKH (local file):")
    if os.path.exists(AUDIT_FILE):
        try:
            df_audit = pd.read_csv(AUDIT_FILE)
            st.dataframe(df_audit.sort_values("timestamp", ascending=False).head(200))
            csv_bytes = df_audit.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Tải Log Audit (CSV)", data=csv_bytes, file_name="dvkh_audit.csv", mime="text/csv")
        except Exception as e:
            st.error("Không thể đọc file audit.")
            st.exception(e)
    else:
        st.info("Chưa có log hoạt động (file dvkh_audit.csv chưa tồn tại).")

    # footer
    st.markdown("---")
    st.info("Module DVKH — hoàn tất. Liên hệ admin khi cần thêm các cột/out rule bổ sung.")
