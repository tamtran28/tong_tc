import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

# ======================================================================
# MODULE XỬ LÝ TIÊU CHÍ TÍN DỤNG – CRM4 / CRM32 / TSBD / CHẬM TRẢ / GN-TT
# ======================================================================

def run_tin_dung():

    st.header("📘 PHÂN HỆ TÍN DỤNG – CRM4 / CRM32 / TSBD / MỤC 17–57")

    st.markdown("""
    Hệ thống xử lý toàn bộ:
    - **CRM4 → TSBD / Dư nợ**
    - **CRM32 → Mục đích vay / Dư nợ**
    - **Mục 17 → TS khác địa bàn**
    - **Mục 55–56 → Giải ngân / tất toán cùng ngày**
    - **Mục 57 → Chậm trả**
    """)

    # ============================================================
    # NHẬP THÔNG TIN
    # ============================================================

    chi_nhanh = st.text_input("Nhập mã chi nhánh (BRANCH_VAY / BRCD)", "").upper().strip()
    ngay_danh_gia = st.date_input("Ngày đánh giá", pd.to_datetime("2025-09-30"))

    dia_ban_kt = st.text_input(
        "Nhập địa bàn kiểm toán (ngăn cách bằng dấu phẩy)",
        "Hồ Chí Minh, Long An"
    )
    dia_ban_kt = [t.strip().lower() for t in dia_ban_kt.split(",") if t.strip()]

    st.subheader("📂 Upload file dữ liệu")
    crm4_files = st.file_uploader("Upload file CRM4", type=["xls", "xlsx"], accept_multiple_files=True)
    crm32_files = st.file_uploader("Upload file CRM32", type=["xls", "xlsx"], accept_multiple_files=True)
    df_mucdich_file = st.file_uploader("Upload CODE_MDSDV4.xlsx", type=["xls", "xlsx"])
    df_tsbd_file = st.file_uploader("Upload CODE_LOAI TSBD.xlsx", type=["xls", "xlsx"])

    df_giai_ngan = st.file_uploader("Upload file GN tiền mặt (Mục 56)", type=["xls", "xlsx"])
    df_tt_55 = st.file_uploader("Upload file Mục 55 (Tất toán)", type=["xls", "xlsx"])
    df_56_file = st.file_uploader("Upload file Mục 56", type=["xls", "xlsx"])
    df_57_file = st.file_uploader("Upload file Mục 57 (Chậm trả)", type=["xls", "xlsx"])
    df_17_file = st.file_uploader("Upload file Mục 17 – TSBD", type=["xls", "xlsx"])

    if st.button("🚀 Chạy phân hệ Tín Dụng"):

        missing = []
        if not crm4_files: missing.append("CRM4")
        if not crm32_files: missing.append("CRM32")
        if df_mucdich_file is None: missing.append("CODE_MDSDV4")
        if df_tsbd_file is None: missing.append("CODE TSBD")
        if df_giai_ngan is None: missing.append("Giải ngân tiền mặt")
        if df_tt_55 is None: missing.append("Mục 55")
        if df_56_file is None: missing.append("Mục 56")
        if df_57_file is None: missing.append("Mục 57")
        if df_17_file is None: missing.append("Mục 17")

        if missing:
            st.error("❌ Thiếu: " + ", ".join(missing))
            return

        with st.spinner("⏳ Đang xử lý dữ liệu…"):

            # --------------------------------------------------------
            # GỘP CRM4
            # --------------------------------------------------------
            df4 = pd.concat([pd.read_excel(f) for f in crm4_files], ignore_index=True)
            df4['CIF_KH_VAY'] = df4['CIF_KH_VAY'].astype(str).str.strip()
            df4 = df4[df4['BRANCH_VAY'].astype(str).str.contains(chi_nhanh)]

            # --------------------------------------------------------
            # GỘP CRM32
            # --------------------------------------------------------
            df32 = pd.concat([pd.read_excel(f) for f in crm32_files], ignore_index=True)
            df32['CUSTSEQLN'] = df32['CUSTSEQLN'].astype(str).str.strip()
            df32 = df32[df32['BRCD'].astype(str).str.contains(chi_nhanh)]

            # --------------------------------------------------------
            # MAP TSBD
            # --------------------------------------------------------
            df_tsbd = pd.read_excel(df_tsbd_file)[['CODE CAP 2', 'CODE']]
            df_tsbd.columns = ['CAP_2', 'LOAI_TS']

            df4 = df4.merge(df_tsbd, how="left", on="CAP_2")
            df4['LOAI_TS'] = df4['LOAI_TS'].fillna("Không TS")

            # --------------------------------------------------------
            # PIVOT DƯ NỢ – CRM4
            # --------------------------------------------------------
            pivot_no = df4.pivot_table(
                index="CIF_KH_VAY",
                columns="LOAI_TS",
                values="DU_NO_PHAN_BO_QUY_DOI",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            df_info = df4[['CIF_KH_VAY', 'TEN_KH_VAY', 'CUSTTPCD', 'NHOM_NO']].drop_duplicates()
            df_crm4_final = df_info.merge(pivot_no, on="CIF_KH_VAY", how="left")

            df_crm4_final["DƯ NỢ"] = df_crm4_final[pivot_no.columns[1:]].sum(axis=1)

            # --------------------------------------------------------
            # MỤC ĐÍCH VAY – CRM32
            # --------------------------------------------------------
            df_mucdich = pd.read_excel(df_mucdich_file)
            df_mucdich = df_mucdich[['CODE_MDSDV4', 'GROUP']]
            df_mucdich.columns = ['MUC_DICH', 'NHOM_MUC_DICH']

            df32 = df32.merge(df_mucdich, how="left", on="MUC_DICH_VAY_CAP_4")
            df32['NHOM_MUC_DICH'] = df32['NHOM_MUC_DICH'].fillna("(blank)")

            pivot_md = df32.pivot_table(
                index="CUSTSEQLN",
                columns="NHOM_MUC_DICH",
                values="DU_NO_QUY_DOI",
                aggfunc="sum",
                fill_value=0
            ).reset_index()

            pivot_md["DƯ NỢ CRM32"] = pivot_md.drop(columns=["CUSTSEQLN"]).sum(axis=1)
            pivot_md.rename(columns={"CUSTSEQLN": "CIF_KH_VAY"}, inplace=True)

            # --------------------------------------------------------
            # GHÉP CRM4 + CRM32
            # --------------------------------------------------------
            pivot_full = df_crm4_final.merge(pivot_md, on="CIF_KH_VAY", how="left")
            pivot_full.fillna(0, inplace=True)

            # --------------------------------------------------------
            # NỢ XẤU – NỢ NHÓM 2
            # --------------------------------------------------------
            pivot_full["Nợ nhóm 2"] = pivot_full["NHOM_NO"].apply(lambda x: "X" if str(x) == "2" else "")
            pivot_full["Nợ xấu"] = pivot_full["NHOM_NO"].apply(lambda x: "X" if str(x) in ["3", "4", "5"] else "")

            # --------------------------------------------------------
            # GIẢI NGÂN – TẤT TOÁN (MỤC 55 – 56)
            # --------------------------------------------------------
            df_55 = pd.read_excel(df_tt_55)
            df_56 = pd.read_excel(df_56_file)

            df_55['CIF'] = df_55['CUSTSEQLN'].astype(str)
            df_56['CIF'] = df_56['CIF'].astype(str)

            df_gop = pd.concat([df_55, df_56], ignore_index=True)
            df_gop['NGAY'] = pd.to_datetime(df_gop['NGAY'], errors='coerce')
            df_ca = df_gop.groupby(['CIF', 'NGAY']).size().reset_index(name="SL")
            ds_ca = df_ca[df_ca['SL'] >= 2]['CIF'].unique()

            pivot_full["GN – TT cùng ngày"] = pivot_full["CIF_KH_VAY"].apply(lambda x: "X" if x in ds_ca else "")

            # --------------------------------------------------------
            # MỤC 57 – CHẬM TRẢ
            # --------------------------------------------------------
            df_57 = pd.read_excel(df_57_file)
            df_57['CIF_ID'] = df_57['CIF_ID'].astype(str)

            df_57['NGAY_DEN_HAN_TT'] = pd.to_datetime(df_57['NGAY_DEN_HAN_TT'], errors='coerce')
            df_57['NGAY_THANH_TOAN'] = pd.to_datetime(df_57['NGAY_THANH_TOAN'], errors='coerce')

            df_57['SO_NGAY'] = (df_57['NGAY_THANH_TOAN'].fillna(pd.to_datetime(ngay_danh_gia)) - df_57['NGAY_DEN_HAN_TT']).dt.days

            df_57['MUC'] = df_57['SO_NGAY'].apply(
                lambda x: '>=10' if x >= 10 else ('4-9' if x >= 4 else ('<4' if x > 0 else None))
            )

            df_57 = df_57.dropna(subset=['MUC'])

            df_ct = df_57.groupby(['CIF_ID', 'MUC']).size().unstack(fill_value=0)

            df_ct['Chậm trả >=10 ngày'] = np.where(df_ct.get('>=10', 0) > 0, 'X', '')
            df_ct['Chậm trả 4-9 ngày'] = np.where(
                (df_ct.get('>=10', 0) == 0) & (df_ct.get('4-9', 0) > 0), 'X', ''
            )

            pivot_full = pivot_full.merge(
                df_ct[['Chậm trả >=10 ngày', 'Chậm trả 4-9 ngày']],
                left_on="CIF_KH_VAY",
                right_index=True,
                how="left"
            ).fillna("")

            # --------------------------------------------------------
            # MỤC 17 – TSBD KHÁC ĐỊA BÀN
            # --------------------------------------------------------
            df_17 = pd.read_excel(df_17_file)

            df_17['C01'] = df_17['C01'].astype(str)
            df4['SECU_SRL_NUM'] = df4['SECU_SRL_NUM'].astype(str)

            ds_ts = df4['SECU_SRL_NUM'].unique()
            df_17_f = df_17[df_17['C01'].isin(ds_ts)]

            df_17_f['TINH_TP'] = df_17_f['C19'].astype(str).apply(lambda x: x.split(",")[-1].strip().lower())

            df_17_f['KHAC_DIABAN'] = df_17_f['TINH_TP'].apply(
                lambda x: "X" if x not in dia_ban_kt else ""
            )

            ds_canhbao = df_17_f[df_17_f['KHAC_DIABAN']=="X"]['C01'].unique()
            ds_cif_canhbao = df4[df4['SECU_SRL_NUM'].isin(ds_canhbao)]['CIF_KH_VAY'].unique()

            pivot_full["TSBD khác địa bàn"] = pivot_full["CIF_KH_VAY"].apply(
                lambda x: "X" if x in ds_cif_canhbao else ""
            )

        # ============================================================
        # HIỂN THỊ KẾT QUẢ
        # ============================================================

        st.success("🎯 ĐÃ XỬ LÝ THÀNH CÔNG!")

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📌 Tổng hợp CIF",
            "📌 CRM4 – TSBD",
            "📌 CRM32 – Mục đích vay",
            "📌 GN/TT – TS khác địa bàn – Chậm trả",
            "📌 Xuất Excel"
        ])

        with tab1:
            st.dataframe(pivot_full, use_container_width=True)

        with tab2:
            st.dataframe(df_crm4_final, use_container_width=True)

        with tab3:
            st.dataframe(pivot_md, use_container_width=True)

        with tab4:
            st.write("Mục 55–56–57 / TS khác địa bàn")
            st.dataframe(df_ct, use_container_width=True)

        # --------------------------------------------------------
        # EXPORT
        # --------------------------------------------------------
        with tab5:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_crm4_final.to_excel(writer, sheet_name="CRM4_TSBD", index=False)
                pivot_md.to_excel(writer, sheet_name="CRM32_MUCDICH", index=False)
                pivot_full.to_excel(writer, sheet_name="TONG_HOP_CIF", index=False)
                df_ct.to_excel(writer, sheet_name="CHAM_TRA", index=False)

            st.download_button(
                "📥 Tải file KQ_Tin_dung.xlsx",
                buffer.getvalue(),
                "KQ_Tin_dung.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

