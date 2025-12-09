import streamlit as st
import pandas as pd
import numpy as np
import glob
import re
from io import BytesIO

# ==========================================================
#                 MODULE DVKH – FULL VERSION
# ==========================================================

def run_dvkh():
    st.title("📌 Hệ thống kiểm tra DVKH – TC1 → TC5")

    st.info("Vui lòng nhập đủ dữ liệu để hệ thống xử lý tất cả tiêu chí.")

    # ============================
    #  UPLOAD FILE / INPUT
    # ============================
    folder_CKH = st.text_input("📁 Thư mục CKH:", "")
    folder_KKH = st.text_input("📁 Thư mục KKH:", "")
    file_muc30 = st.file_uploader("📄 File Mục 30:", type=["xlsx"])

    file_sms = st.file_uploader("📄 File DK_SMS:", type=["txt"])
    file_scm10 = st.file_uploader("📄 File SCM010:", type=["xlsx"])

    file_ns = st.file_uploader("📄 Danh sách nhân sự:", type=["xlsx"])
    file_ns_nghi = st.file_uploader("📄 Danh sách nhân sự nghỉ:", type=["xlsx"])

    file_mapping = st.file_uploader("📄 Mapping 1405:", type=["xlsx"])

    chi_nhanh = st.text_input("Nhập mã chi nhánh lọc FTP:", "").upper().strip()

    if st.button("🚀 Chạy DVKH"):
        try:
            st.success("Đang chạy xử lý... vui lòng đợi...")

            # =============================================================
            #                  TIÊU CHÍ 1 – XỬ LÝ UỶ QUYỀN
            # =============================================================
            CKH = glob.glob(f"{folder_CKH}/HDV_CHITIET_CKH_*.xls*")
            KKH = glob.glob(f"{folder_KKH}/HDV_CHITIET_KKH_*.xls*")

            df_b_CKH = pd.concat([pd.read_excel(f, dtype=str) for f in CKH])
            df_b_KKH = pd.concat([pd.read_excel(f, dtype=str) for f in KKH])
            df_b = pd.concat([df_b_CKH, df_b_KKH])

            df_a = pd.read_excel(file_muc30, dtype=str)

            df_a = df_a[df_a["DESCRIPTION"].str.contains(r"chu\s*ky|chuky|cky", case=False, na=False)]

            df_a["EXPIRYDATE"] = pd.to_datetime(df_a["EXPIRYDATE"], format='%Y%m%d', errors='coerce')
            df_a["EFFECTIVEDATE"] = pd.to_datetime(df_a["EFFECTIVEDATE"], format='%Y%m%d', errors='coerce')

            df_a["EXPIRYDATE"] = df_a["EXPIRYDATE"].dt.strftime('%m/%d/%Y')
            df_a["EFFECTIVEDATE"] = df_a["EFFECTIVEDATE"].dt.strftime('%m/%d/%Y')

            keywords = ["CONG TY", "CTY", "CONGTY", "CÔNG TY"]
            df_a = df_a[~df_a["NGUOI_UY_QUYEN"].str.upper().str.contains("|".join(keywords))]

            # Tách tên UQ
            def extract_name(value):
                parts = re.split(r'[-,]', str(value))
                for part in parts:
                    name = part.strip()
                    if re.fullmatch(r'[A-Z ]{3,}', name):
                        return name
                return value

            df_a["NGUOI_DUOC_UY_QUYEN"] = df_a["NGUOI_DUOC_UY_QUYEN"].apply(extract_name)
            df_a.drop_duplicates(subset=["PRIMARY_SOL_ID", "TK_DUOC_UY_QUYEN", "NGUOI_DUOC_UY_QUYEN"], inplace=True)

            df_a['TK_DUOC_UY_QUYEN'] = df_a['TK_DUOC_UY_QUYEN'].astype(str)
            df_b['IDXACNO'] = df_b['IDXACNO'].astype(str)

            merged = df_a.merge(df_b[["IDXACNO", "CUSTSEQ"]], left_on="TK_DUOC_UY_QUYEN", right_on="IDXACNO", how="left")

            merged["CIF_NGUOI_UY_QUYEN"] = merged["CUSTSEQ"].apply(lambda x: str(int(x)) if pd.notna(x) else "NA")

            # Xử lý NA
            updated = merged["CIF_NGUOI_UY_QUYEN"].copy()
            for nguoi, group in merged.groupby("NGUOI_DUOC_UY_QUYEN"):
                if "NA" in group["CIF_NGUOI_UY_QUYEN"].unique():
                    valid = [x for x in group["CIF_NGUOI_UY_QUYEN"].unique() if x != "NA"]
                    if valid:
                        updated.loc[group[group["CIF_NGUOI_UY_QUYEN"] == "NA"].index] = valid[0]
            merged["CIF_NGUOI_UY_QUYEN"] = updated

            set_ckh = set(df_b_CKH['CUSTSEQ'].astype(str))
            set_kkh = set(df_b_KKH['IDXACNO'].astype(str))

            def classify(tk):
                if tk in set_ckh:
                    return "CKH"
                if tk in set_kkh:
                    return "KKH"
                return "NA"

            merged["LOAI_TK"] = merged["TK_DUOC_UY_QUYEN"].astype(str).apply(classify)

            # =============================================================
            #                       TIÊU CHÍ 2 – SMS / SCM010
            # =============================================================
            df_sms = pd.read_csv(file_sms, sep="\t", on_bad_lines="skip", dtype=str)
            df_sms['FORACID'] = df_sms['FORACID'].astype(str)
            df_sms = df_sms[df_sms['FORACID'].str.match(r'^\d+$')]

            df_scm10 = pd.read_excel(file_scm10, dtype=str)
            df_scm10['ORGKEY'] = df_scm10['CIF_ID']

            df_uyquyen = merged.copy()
            df_uyquyen["TK có đăng ký SMS"] = df_uyquyen["TK_DUOC_UY_QUYEN"].isin(df_sms["FORACID"]).map({True:"X",False:""})
            df_uyquyen["CIF có đăng ký SCM010"] = df_uyquyen["CIF_NGUOI_UY_QUYEN"].isin(df_scm10["ORGKEY"]).map({True:"X",False:""})

            # =============================================================
            #                 TIÊU CHÍ 3 – NGƯỜI NHẬN UQ NHIỀU LẦN
            # =============================================================
            df_tc3 = df_uyquyen.copy()

            grouped = df_tc3.groupby('NGUOI_DUOC_UY_QUYEN')['NGUOI_UY_QUYEN'].nunique()
            many = set(grouped[grouped >= 2].index)

            df_tc3['1 người nhận UQ của nhiều người'] = df_tc3['NGUOI_DUOC_UY_QUYEN'].apply(
                lambda x: "X" if x in many else ""
            )

            # =============================================================
            #                    TIÊU CHÍ 4 – FTP
            # =============================================================
            files_42a = glob.glob(f"{folder_KKH}/HDV_CHITIET_KKH_*.xls")
            df_ghep42a = pd.concat([pd.read_excel(f, dtype=str) for f in files_42a])

            df_42a = df_ghep42a[df_ghep42a['BRCD'].str.upper().str.contains(chi_nhanh)]
            df_42a = df_42a[df_42a['CUST_TYPE'] == 'KHCN']

            # Code ưu đãi CBNV
            df_42b = pd.read_excel(file_ns, dtype=str)
            df_42d = pd.read_excel(file_ns_nghi, dtype=str)

            df_42a['CUSTSEQ'] = df_42a['CUSTSEQ'].astype(str)
            df_42b['MACIF'] = df_42b['MACIF'].astype(str)

            df_42b_macif = df_42b.drop_duplicates(subset=['MACIF'])

            df_42a = df_42a.merge(df_42b_macif[['MACIF', 'CHARGELEVELCODE_CIF']],
                                  left_on='CUSTSEQ', right_on='MACIF', how='left')
            df_42a['TK_GAN_CODE_UU_DAI_CBNV'] = np.where(df_42a['CHARGELEVELCODE_CIF'] == 'NVEIB', 'X', '')

            # CBNV nghỉ việc
            df_42a["CBNV_NGHI_VIEC"] = df_42a["CUSTSEQ"].isin(df_42d["CIF"]).map({True: "X", False: ""})

            # =============================================================
            #                  TIÊU CHÍ 5 – MAPPING 1405
            # =============================================================
            df_map = pd.read_excel(file_mapping, dtype=str)
            df_map.columns = df_map.columns.str.lower()

            df_map['xpcodedt'] = pd.to_datetime(df_map['xpcodedt'], errors='coerce')
            df_map['uploaddt'] = pd.to_datetime(df_map['uploaddt'], errors='coerce')

            df_map['SO_NGAY_MO_THE'] = (df_map['xpcodedt'] - df_map['uploaddt']).dt.days

            df_map['MO_DONG_TRONG_6_THANG'] = df_map.apply(
                lambda r: "X" if (pd.notna(r['SO_NGAY_MO_THE']) and 0 <= r['SO_NGAY_MO_THE'] < 180) else "",
                axis=1
            )

            # =============================================================
            #               XUẤT FILE EXCEL → 5 SHEET
            # =============================================================
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                merged.to_excel(writer, sheet_name="TC1", index=False)
                df_uyquyen.to_excel(writer, sheet_name="TC2", index=False)
                df_tc3.to_excel(writer, sheet_name="TC3", index=False)
                df_42a.to_excel(writer, sheet_name="TC4", index=False)
                df_map.to_excel(writer, sheet_name="TC5", index=False)

            st.success("🎉 Hoàn thành xử lý DVKH!")

            st.download_button(
                label="📥 Tải file kết quả DVKH",
                data=output.getvalue(),
                file_name="DVKH_Result.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Lỗi xảy ra: {e}")
