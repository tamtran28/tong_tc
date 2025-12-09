import streamlit as st
import pandas as pd
import numpy as np
import glob
import re
from io import BytesIO

# ===============================
# MODULE DVKH – CHẠY TƯƠNG TỰ COLAB
# ===============================

def run_dvkh():
    st.header("📌 DVKH – Chạy dữ liệu CKH / KKH / Mục 30 / SMS / SCM010")

    st.info("Hãy tải lên các file theo yêu cầu bên dưới. Tất cả phải đúng định dạng!")

    # --- Upload file CKH & KKH ---
    uploaded_ckh = st.file_uploader("Tải lên các file CKH (HDV_CHITIET_CKH_*.xlsx)", accept_multiple_files=True)
    uploaded_kkh = st.file_uploader("Tải lên các file KKH (HDV_CHITIET_KKH_*.xlsx)", accept_multiple_files=True)

    # --- Upload file Mức 30 ---
    file_muc30 = st.file_uploader("Tải lên file Mục 30", type=["xls", "xlsx"])

    # --- Upload file SMS ---
    file_sms = st.file_uploader("Tải lên file Mục 14 – DK_SMS (.txt)", type=["txt"])

    # --- Upload file SCM010 ---
    file_scm10 = st.file_uploader("Tải lên file SCM010 (.xlsx)", type=["xlsx"])

    if st.button("▶️ CHẠY XỬ LÝ DVKH"):
        if not uploaded_ckh or not uploaded_kkh or not file_muc30 or not file_sms or not file_scm10:
            st.error("⚠️ Bạn phải tải lên đầy đủ tất cả file!")
            return

        st.success("⏳ Đang xử lý... vui lòng đợi...")

        # ==========================================
        # 1) Đọc file CKH – KKH
        # ==========================================
        df_b_CKH = pd.concat([pd.read_excel(f, dtype=str) for f in uploaded_ckh], ignore_index=True)
        df_b_KKH = pd.concat([pd.read_excel(f, dtype=str) for f in uploaded_kkh], ignore_index=True)
        df_b = pd.concat([df_b_CKH, df_b_KKH], ignore_index=True)

        # ==========================================
        # 2) Đọc file Mục 30
        # ==========================================
        df_a = pd.read_excel(file_muc30, dtype=str)

        # Lọc mô tả có chữ "chu ky"
        df_a = df_a[df_a["DESCRIPTION"].str.contains(r"chu\s*ky|chuky|cky", case=False, na=False)]

        # Convert ngày
        df_a["EXPIRYDATE"] = pd.to_datetime(df_a["EXPIRYDATE"], format='%Y%m%d', errors='coerce')
        df_a["EFFECTIVEDATE"] = pd.to_datetime(df_a["EFFECTIVEDATE"], format='%Y%m%d', errors='coerce')

        df_a["EXPIRYDATE"] = df_a["EXPIRYDATE"].dt.strftime('%m/%d/%Y')
        df_a["EFFECTIVEDATE"] = df_a["EFFECTIVEDATE"].dt.strftime('%m/%d/%Y')

        # Lọc doanh nghiệp
        keywords = ["CONG TY", "CTY", "CONGTY", "CÔNG TY", "CÔNGTY"]
        df_a = df_a[~df_a["NGUOI_UY_QUYEN"].str.upper().str.contains("|".join(keywords))]

        # Tách tên người được ủy quyền
        def extract_name(value):
            parts = re.split(r'[-,]', str(value))
            for part in parts:
                name = part.strip()
                if re.fullmatch(r'[A-Z ]{3,}', name):
                    return name
            return value

        df_a["NGUOI_DUOC_UY_QUYEN"] = df_a["NGUOI_DUOC_UY_QUYEN"].apply(extract_name)

        # ==========================================
        # 3) MERGE CKH–KKH
        # ==========================================
        df_a['TK_DUOC_UY_QUYEN'] = df_a['TK_DUOC_UY_QUYEN'].astype(str)
        df_b['IDXACNO'] = df_b['IDXACNO'].astype(str)

        merged = df_a.merge(
            df_b[["IDXACNO", "CUSTSEQ"]],
            left_on="TK_DUOC_UY_QUYEN",
            right_on="IDXACNO",
            how="left"
        )

        merged["CIF_NGUOI_UY_QUYEN"] = merged["CUSTSEQ"].apply(
            lambda x: str(int(x)) if pd.notna(x) else "NA"
        )

        # Loại TK CKH / KKH
        set_ckh = set(df_b_CKH['CUSTSEQ'].astype(str))
        set_kkh = set(df_b_KKH['IDXACNO'].astype(str))

        def phan_loai_tk(tk):
            if tk in set_ckh:
                return 'CKH'
            elif tk in set_kkh:
                return 'KKH'
            else:
                return 'NA'

        merged['LOAI_TK'] = merged['TK_DUOC_UY_QUYEN'].astype(str).apply(phan_loai_tk)

        # ==========================================
        # 4) Xử lý mục 14 SMS
        # ==========================================
        df_sms = pd.read_csv(file_sms, sep='\t', on_bad_lines='skip', dtype=str)

        df_sms = df_sms[df_sms["FORACID"].str.match(r"^\d+$")]
        df_sms = df_sms[df_sms["CUSTTPCD"].str.upper() != 'KHDN']

        df_sms["CRE_DATE"] = pd.to_datetime(df_sms["CRE_DATE"], errors='coerce').dt.strftime('%m/%d/%Y')

        # SCM010
        df_scm10 = pd.read_excel(file_scm10, dtype=str)
        df_scm10['ORGKEY'] = df_scm10['CIF_ID'].astype(str)

        df_sms['PL DICH VU'] = "SMS"
        df_scm10['PL DICH VU'] = "SCM010"

        df_all_service = pd.concat([
            df_sms[['FORACID', 'ORGKEY', 'PL DICH VU']],
            df_scm10[['ORGKEY', 'PL DICH VU']]
        ], ignore_index=True)

        # ==========================================
        # 5) Kết hợp Uy quyền
        # ==========================================
        df_uyquyen = merged.copy()
        df_uyquyen['TK có đăng ký SMS'] = df_uyquyen['TK_DUOC_UY_QUYEN'].apply(
            lambda x: "X" if str(x) in set(df_sms['FORACID']) else ""
        )

        df_uyquyen['CIF có đăng ký SCM010'] = df_uyquyen['CIF_NGUOI_UY_QUYEN'].apply(
            lambda x: "X" if str(x) in set(df_scm10['ORGKEY']) else ""
        )

        # ==========================================
        # 6) TÌM "1 người nhận UQ của nhiều người"
        # ==========================================
        df_tc3 = df_uyquyen.copy()

        group = df_tc3.groupby("NGUOI_DUOC_UY_QUYEN")["NGUOI_UY_QUYEN"].nunique()
        nhieu_uq = set(group[group >= 2].index)

        df_tc3["1 người nhận UQ của nhiều người"] = df_tc3["NGUOI_DUOC_UY_QUYEN"].apply(
            lambda x: "X" if x in nhieu_uq else ""
        )

        # ==========================================
        # 7) Xuất Excel
        # ==========================================
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            merged.to_excel(writer, sheet_name="tieu chi 1", index=False)
            df_uyquyen.to_excel(writer, sheet_name="tieu chi 2", index=False)
            df_tc3.to_excel(writer, sheet_name="tieu chi 3", index=False)

        st.success("🎉 Hoàn tất DVKH!")

        st.download_button(
            label="⬇️ Tải về DVKH.xlsx",
            data=output.getvalue(),
            file_name="DVKH.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
