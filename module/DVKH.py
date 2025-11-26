import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ======================================================
#   MODULE DVKH – 5 TIÊU CHÍ
# ======================================================

def run_dvkh_5_tieuchi():

    st.title("📌 ỨNG DỤNG XỬ LÝ DỮ LIỆU DVKH – 5 TIÊU CHÍ")

    tab1, tab2 = st.tabs(["📥 Nhập & Xử lý dữ liệu", "📤 Xuất kết quả"])

    # ================= TAB 1 ===========================================
    with tab1:
        st.header("1️⃣ Upload dữ liệu đầu vào")

        file_dksms = st.file_uploader("Upload Muc14_DKSMS.txt,xlsx", type=["txt", "xlsx"])
        file_scm10 = st.file_uploader("Upload Muc14_SCM010.xlsx", type=["xlsx"])
        file_42a = st.file_uploader("Upload HDV_CHITIET_KKH_*.xls (4.2.a)", type=["xls"], accept_multiple_files=True)
        file_42b = st.file_uploader("Upload BC_LAY_CHARGELEVELCODE_THEO_KHCN.xlsx", type=["xlsx"])
        file_42c = st.file_uploader("Upload 10_DanhSachNhanSu.xlsx", type=["xlsx"])
        file_42d = st.file_uploader("Upload DS Nghi Viec.xlsx", type=["xlsx"])
        file_mapping = st.file_uploader("Upload Mapping_1405.xlsx", type=["xlsx"])

        chi_nhanh = st.text_input("Nhập tên chi nhánh hoặc mã SOL (VD: HANOI, 001)").upper()

        run_btn = st.button("▶️ CHẠY XỬ LÝ")

        if run_btn:
            if not all([file_dksms, file_scm10, file_42a, file_42b, file_42c, file_42d, file_mapping]):
                st.error("⚠️ Bạn phải upload đầy đủ tất cả các file!")
                st.stop()

            st.success("⏳ Đang xử lý dữ liệu...")

            # ================= TIÊU CHÍ 1,2,3 ==================================
            df_sms = pd.read_csv(file_dksms, sep="\t", on_bad_lines="skip", dtype=str)

            df_sms["FORACID"] = df_sms["FORACID"].astype(str)
            df_sms["ORGKEY"] = df_sms["ORGKEY"].astype(str)
            df_sms["C_MOBILE_NO"] = df_sms["C_MOBILE_NO"].astype(str)
            df_sms["CRE DATE"] = pd.to_datetime(df_sms["CRE_DATE"], errors="coerce").dt.strftime("%m/%d/%Y")
            df_sms = df_sms[df_sms["FORACID"].str.match(r"^\d+$")]
            df_sms = df_sms[df_sms["CUSTTPCD"].str.upper() != "KHDN"]

            df_scm10 = pd.read_excel(file_scm10, dtype=str)
            df_scm10.columns = df_scm10.columns.str.strip()
            df_scm10["CIF_ID"] = df_scm10["CIF_ID"].astype(str)

            df_sms["PL DICH VU"] = "SMS"
            df_scm10["ORGKEY"] = df_scm10["CIF_ID"]
            df_scm10["PL DICH VU"] = "SCM010"

            df_merged = pd.concat(
                [df_sms, df_scm10[["ORGKEY", "PL DICH VU"]].drop_duplicates()],
                ignore_index=True
            )

            df_uyquyen = df_merged.copy()

            # --- Đánh dấu ---
            tk_sms = set(df_merged[df_merged["PL DICH VU"] == "SMS"]["FORACID"])
            df_uyquyen["TK có đăng ký SMS"] = df_uyquyen["FORACID"].apply(lambda x: "X" if x in tk_sms else "")

            cif_scm10 = set(df_merged[df_merged["PL DICH VU"] == "SCM010"]["ORGKEY"])
            df_uyquyen["CIF có đăng ký SCM010"] = df_uyquyen["ORGKEY"].apply(lambda x: "X" if x in cif_scm10 else "")

            # --- Tiêu chí 3 ---
            df_tc3 = df_uyquyen.copy()
            grouped = df_tc3.groupby("NGUOI_DUOC_UY_QUYEN")["NGUOI_UY_QUYEN"].nunique().reset_index()
            many = set(grouped[grouped["NGUOI_UY_QUYEN"] >= 2]["NGUOI_DUOC_UY_QUYEN"])
            df_tc3["1 người nhận UQ của nhiều người"] = df_tc3["NGUOI_DUOC_UY_QUYEN"].apply(
                lambda x: "X" if x in many else ""
            )

            # ================= TIÊU CHÍ 4 ==================================
            df_ghep42a = pd.concat([pd.read_excel(f, dtype=str) for f in file_42a], ignore_index=True)
            df_42a = df_ghep42a[df_ghep42a["BRCD"].astype(str).str.upper().str.contains(chi_nhanh)]

            cols_42a = ['BRCD', 'DEPTCD', 'CUST_TYPE', 'CUSTSEQ', 'NMLOC', 'BIRTH_DAY',
                        'IDXACNO', 'SCHM_NAME', 'CCYCD', 'CURBAL_VN', 'OPNDT_FIRST', 'OPNDT_EFFECT']

            df_42a = df_42a[cols_42a]
            df_42a = df_42a[df_42a["CUST_TYPE"] == "KHCN"]
            df_42a = df_42a[~df_42a["SCHM_NAME"].str.upper().str.contains(
                "KY QUY|GIAI NGAN|CHI LUONG|TKTT THE|TRUNG GIAN"
            )]

            df_ghep42b = pd.read_excel(file_42b, dtype=str)
            df_42b = df_ghep42b[df_ghep42b["CN_MO_TK"].astype(str).str.upper().str.contains(chi_nhanh)]

            df_42c = pd.read_excel(file_42c, dtype=str)
            df_42d = pd.read_excel(file_42d, dtype=str)

            df_42a["CUSTSEQ"] = df_42a["CUSTSEQ"].astype(str)
            df_42b["MACIF"] = df_42b["MACIF"].astype(str)

            df_42a = df_42a.merge(
                df_42b.drop_duplicates("MACIF")[["MACIF", "CHARGELEVELCODE_CIF"]],
                left_on="CUSTSEQ",
                right_on="MACIF",
                how="left"
            ).drop(columns=["MACIF"])

            df_42b["STKKH"] = df_42b["STKKH"].astype(str)
            df_42a["IDXACNO"] = df_42a["IDXACNO"].astype(str)

            df_42a = df_42a.merge(
                df_42b.drop_duplicates("STKKH")[["STKKH", "CHARGELEVELCODE_TK"]],
                left_on="IDXACNO",
                right_on="STKKH",
                how="left"
            ).drop(columns=["STKKH"])

            df_42a["TK_GAN_CODE_UU_DAI_CBNV"] = np.where(df_42a["CHARGELEVELCODE_TK"] == "NVEIB", "X", "")

            df_42a = df_42a.merge(
                df_42c[["Mã số CIF", "Mã NV"]],
                left_on="CUSTSEQ",
                right_on="Mã số CIF",
                how="left"
            )

            df_42a = df_42a.merge(
                df_42d[["CIF", "Ngày thôi việc"]],
                how="left",
                left_on="CUSTSEQ",
                right_on="CIF"
            )

            df_42a["CBNV_NGHI_VIEC"] = np.where(df_42a["CIF"].notna(), "X", "")
            df_42a["NGAY_NGHI_VIEC"] = pd.to_datetime(df_42a["Ngày thôi việc"], errors="coerce").dt.strftime("%m/%d/%Y")

            # ================= TIÊU CHÍ 5 ==================================
            df_map = pd.read_excel(file_mapping, dtype=str)
            df_map.columns = df_map.columns.str.lower()

            df_map["xpcodedt"] = pd.to_datetime(df_map["xpcodedt"], errors="coerce")
            df_map["uploaddt"] = pd.to_datetime(df_map["uploaddt"], errors="coerce")
            df_map["SO_NGAY_MO_THE"] = (df_map["xpcodedt"] - df_map["uploaddt"]).dt.days

            df_map["MO_DONG_TRONG_6_THANG"] = df_map.apply(
                lambda r: "X" if (
                    pd.notnull(r["SO_NGAY_MO_THE"]) and
                    0 <= r["SO_NGAY_MO_THE"] < 180 and
                    r["uploaddt"] > pd.to_datetime("2023-05-31")
                ) else "",
                axis=1
            )

            st.success("🎉 Hoàn tất xử lý tất cả 5 tiêu chí!")

            # Lưu session
            st.session_state["DF_SMS"] = df_sms
            st.session_state["DF_UYQUYEN"] = df_uyquyen
            st.session_state["DF_TC3"] = df_tc3
            st.session_state["DF_42A"] = df_42a
            st.session_state["DF_MAP"] = df_map

    # ================= TAB 2 ===========================================
    with tab2:

        st.header("📤 Xuất file Excel theo 5 tiêu chí")

        if "DF_SMS" not in st.session_state:
            st.warning("⚠️ Bạn cần chạy xử lý ở tab 1 trước!")
            return

        df_sms = st.session_state["DF_SMS"]
        df_uyquyen = st.session_state["DF_UYQUYEN"]
        df_tc3 = st.session_state["DF_TC3"]
        df_42a = st.session_state["DF_42A"]
        df_map = st.session_state["DF_MAP"]

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_sms.to_excel(writer, "TieuChi1", index=False)
            df_uyquyen.to_excel(writer, "TieuChi2", index=False)
            df_tc3.to_excel(writer, "TieuChi3", index=False)
            df_42a.to_excel(writer, "TieuChi4", index=False)
            df_map.to_excel(writer, "TieuChi5", index=False)

        st.download_button(
            label="📥 Tải xuống file Excel 5 tiêu chí",
            data=output.getvalue(),
            file_name="DVKH_5_TIEU_CHI.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
