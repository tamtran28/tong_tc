# ============================================================
# module/tindung.py
# FULL MODULE – TÍN DỤNG (CRM4 – CRM32)
# ============================================================

import streamlit as st
import pandas as pd
import numpy as np
import io

from module.error_utils import UserFacingError, _should_reraise


# ============================================================
# HÀM XỬ LÝ CHÍNH (KHÔNG DÙNG STREAMLIT) – CHỈ XỬ LÝ DỮ LIỆU
# ============================================================

def process_data(
    crm4_files,
    crm32_files,
    df_muc_dich_file_upload,
    df_code_tsbd_file_upload,
    df_giai_ngan_file_upload,
    df_sol_file_upload,
    df_55_file_upload,
    df_56_file_upload,
    df_57_file_upload,
    chi_nhanh,
    ngay_danh_gia,
    dia_ban_kt
):
    # 1. Đọc tất cả file CRM4
    df_crm4_ghep = [pd.read_excel(f) for f in crm4_files]
    df_crm4 = pd.concat(df_crm4_ghep, ignore_index=True)

    # 2. Đọc tất cả file CRM32
    df_crm32_ghep = [pd.read_excel(f) for f in crm32_files]
    df_crm32 = pd.concat(df_crm32_ghep, ignore_index=True)

    # 3. Đọc bảng mã
    df_muc_dich_file = pd.read_excel(df_muc_dich_file_upload)
    df_code_tsbd_file = pd.read_excel(df_code_tsbd_file_upload)

    # =======================================================
    # Chuẩn hóa CIF_KH_VAY và CUSTSEQLN
    # =======================================================
    if "CIF_KH_VAY" in df_crm4.columns:
        # FIX: Dùng .fillna() để giữ lại các hàng, không dùng .dropna()
        df_crm4["CIF_KH_VAY"] = pd.to_numeric(df_crm4["CIF_KH_VAY"], errors="coerce")
        df_crm4["CIF_KH_VAY"] = (
            df_crm4["CIF_KH_VAY"]
            .fillna(0)  # Thay NaN bằng 0
            .astype("int64")
            .astype(str)
            .str.strip()
        )

    if "CUSTSEQLN" in df_crm32.columns:
        df_crm32["CUSTSEQLN"] = pd.to_numeric(df_crm32["CUSTSEQLN"], errors="coerce")
        df_crm32["CUSTSEQLN"] = (
            df_crm32["CUSTSEQLN"]
            .fillna(0)
            .astype("int64")
            .astype(str)
            .str.strip()
        )

    df_muc_dich = df_muc_dich_file.copy()
    df_code_tsbd = df_code_tsbd_file.copy()

    # =======================================================
    # 1. Lọc theo chi nhánh
    # =======================================================
    df_crm4_filtered = df_crm4[
        df_crm4["BRANCH_VAY"].astype(str).str.upper().str.contains(chi_nhanh, na=False)
    ].copy()
    df_crm32_filtered = df_crm32[
        df_crm32["BRCD"].astype(str).str.upper().str.contains(chi_nhanh, na=False)
    ].copy()

    # =======================================================
    # 2. GÁN LOẠI TSBD TỪ BẢNG CODE
    # =======================================================
    # FIX: Chuẩn hóa tên cột để tránh xung đột
    if "CODE CAP 2" in df_code_tsbd.columns:
        df_code_tsbd = df_code_tsbd[["CODE CAP 2", "CODE"]].copy()
        df_code_tsbd.columns = ["CAP_2", "LOAI_TS"]
    else:
        raise UserFacingError("File CODE_LOAI_TSBD thiếu cột 'CODE CAP 2'")

    df_tsbd_code = df_code_tsbd[["CAP_2", "LOAI_TS"]].drop_duplicates()

    # Đảm bảo CAP_2 tồn tại trước khi merge
    if "CAP_2" in df_crm4_filtered.columns:
        df_crm4_filtered["CAP_2"] = df_crm4_filtered["CAP_2"].astype(str).str.strip()
        df_crm4_filtered = df_crm4_filtered.merge(df_tsbd_code, how="left", on="CAP_2")
    else:
        df_crm4_filtered["LOAI_TS"] = "Không TS"

    df_crm4_filtered["LOAI_TS"] = df_crm4_filtered.apply(
        lambda row: "Không TS"
        if pd.isna(row.get("CAP_2")) or str(row.get("CAP_2", "")).strip() == ""
        else row.get("LOAI_TS", "Không TS"),
        axis=1,
    )

    df_crm4_filtered["GHI_CHU_TSBD"] = df_crm4_filtered.apply(
        lambda row: "MỚI"
        if str(row.get("CAP_2", "")).strip() != "" and pd.isna(row.get("LOAI_TS"))
        else "",
        axis=1,
    )

    df_vay_4 = df_crm4_filtered.copy()

    # Bỏ Bảo lãnh, LC
    if "LOAI" in df_vay_4.columns:
        df_vay = df_vay_4[~df_vay_4["LOAI"].isin(["Bao lanh", "LC"])].copy()
    else:
        df_vay = df_vay_4.copy()

    # Pivot giá trị TS
    if "CIF_KH_VAY" in df_vay.columns and "LOAI_TS" in df_vay.columns and "TS_KW_VND" in df_vay.columns:
        pivot_ts = (
            df_vay.pivot_table(
                index="CIF_KH_VAY",
                columns="LOAI_TS",
                values="TS_KW_VND",
                aggfunc="sum",
                fill_value=0,
            )
            .add_suffix(" (Giá trị TS)")
            .reset_index()
        )
    else:
        pivot_ts = pd.DataFrame({"CIF_KH_VAY": df_vay.get("CIF_KH_VAY", [])}).drop_duplicates()

    # Pivot dư nợ
    if "CIF_KH_VAY" in df_vay.columns and "LOAI_TS" in df_vay.columns and "DU_NO_PHAN_BO_QUY_DOI" in df_vay.columns:
        pivot_no = df_vay.pivot_table(
            index="CIF_KH_VAY",
            columns="LOAI_TS",
            values="DU_NO_PHAN_BO_QUY_DOI",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
    else:
        pivot_no = pd.DataFrame({"CIF_KH_VAY": df_vay.get("CIF_KH_VAY", [])}).drop_duplicates()

    pivot_merge = pivot_no.merge(pivot_ts, on="CIF_KH_VAY", how="left")
    pivot_merge["GIÁ TRỊ TS"] = pivot_ts.drop(columns="CIF_KH_VAY", errors="ignore").sum(axis=1)
    pivot_merge["DƯ NỢ"] = pivot_no.drop(columns="CIF_KH_VAY", errors="ignore").sum(axis=1)

    df_info = df_crm4_filtered[
        ["CIF_KH_VAY", "TEN_KH_VAY", "CUSTTPCD", "NHOM_NO"]
    ].drop_duplicates(subset="CIF_KH_VAY")

    pivot_final = df_info.merge(pivot_merge, on="CIF_KH_VAY", how="left")
    pivot_final = pivot_final.reset_index(drop=True)
    pivot_final.insert(0, "STT", range(1, len(pivot_final) + 1))

    cols_order = (
        ["STT", "CUSTTPCD", "CIF_KH_VAY", "TEN_KH_VAY", "NHOM_NO"]
        + sorted(
            [
                col
                for col in pivot_merge.columns
                if col not in ["CIF_KH_VAY", "GIÁ TRỊ TS", "DƯ NỢ"]
                and "(Giá trị TS)" not in col
            ]
        )
        + sorted([col for col in pivot_merge.columns if "(Giá trị TS)" in col])
        + ["DƯ NỢ", "GIÁ TRỊ TS"]
    )

    # Chỉ chọn cột có tồn tại
    cols_order = [c for c in cols_order if c in pivot_final.columns]
    pivot_final = pivot_final[cols_order]

    # =======================================================
    # 3. CRM32 + MỤC ĐÍCH VAY
    # =======================================================
    df_crm32_filtered = df_crm32_filtered.copy()
    
    if "CAP_PHE_DUYET" in df_crm32_filtered.columns:
        df_crm32_filtered["MA_PHE_DUYET"] = (
            df_crm32_filtered["CAP_PHE_DUYET"]
            .astype(str)
            .str.split("-")
            .str[0]
            .str.strip()
            .str.zfill(2)
        )
    else:
        df_crm32_filtered["MA_PHE_DUYET"] = ""

    ma_cap_c = [f"{i:02d}" for i in range(1, 8)] + [f"{i:02d}" for i in range(28, 32)]
    list_cif_cap_c = df_crm32_filtered[
        df_crm32_filtered["MA_PHE_DUYET"].isin(ma_cap_c)
    ]["CUSTSEQLN"].unique() if "SCHEME_CODE" in df_crm32_filtered.columns else []

    list_co_cau = [
        "ACOV1", "ACOV3", "ATT01", "ATT02", "ATT03", "ATT04",
        "BCOV1", "BCOV2", "BTT01", "BTT02", "BTT03",
        "CCOV2", "CCOV3", "CTT03", "RCOV3", "RTT03",
    ]
    
    if "SCHEME_CODE" in df_crm32_filtered.columns:
        cif_co_cau = df_crm32_filtered[
            df_crm32_filtered["SCHEME_CODE"].isin(list_co_cau)
        ]["CUSTSEQLN"].unique()
    else:
        cif_co_cau = []

    df_muc_dich_vay = df_muc_dich[["CODE_MDSDV4", "GROUP"]].copy() if "CODE_MDSDV4" in df_muc_dich.columns else pd.DataFrame()
    df_muc_dich_vay.columns = ["MUC_DICH_VAY_CAP_4", "MUC DICH"]

    if "MUC_DICH_VAY_CAP_4" in df_crm32_filtered.columns:
        df_crm32_filtered = df_crm32_filtered.merge(
            df_muc_dich_vay, how="left", on="MUC_DICH_VAY_CAP_4"
        )
    
    df_crm32_filtered["MUC DICH"] = df_crm32_filtered.get("MUC DICH", "").fillna("(blank)")
    df_crm32_filtered["GHI_CHU_TSBD"] = df_crm32_filtered.apply(
        lambda row: "MỚI"
        if str(row.get("MUC_DICH_VAY_CAP_4", "")).strip() != "" and pd.isna(row.get("MUC DICH"))
        else "",
        axis=1,
    )

    if "CUSTSEQLN" in df_crm32_filtered.columns and "DU_NO_QUY_DOI" in df_crm32_filtered.columns:
        pivot_mucdich = df_crm32_filtered.pivot_table(
            index="CUSTSEQLN",
            columns="MUC DICH",
            values="DU_NO_QUY_DOI",
            aggfunc="sum",
            fill_value=0,
        ).reset_index()
        pivot_mucdich["DƯ NỢ CRM32"] = pivot_mucdich.drop(columns="CUSTSEQLN").sum(axis=1)
    else:
        pivot_mucdich = pd.DataFrame()

    pivot_final_CRM32 = pivot_mucdich.rename(columns={"CUSTSEQLN": "CIF_KH_VAY"}) if len(pivot_mucdich) > 0 else pd.DataFrame()
    
    if len(pivot_final_CRM32) > 0:
        pivot_full = pivot_final.merge(pivot_final_CRM32, on="CIF_KH_VAY", how="left")
    else:
        pivot_full = pivot_final.copy()
    
    pivot_full = pivot_full.fillna(0)

    # Lệch dư nợ
    if "DƯ NỢ" in pivot_full.columns and "DƯ NỢ CRM32" in pivot_full.columns:
        pivot_full["LECH"] = pivot_full["DƯ NỢ"] - pivot_full["DƯ NỢ CRM32"]
        cif_lech = pivot_full[pivot_full["LECH"] != 0]["CIF_KH_VAY"].unique()
    else:
        cif_lech = []

    # Bổ sung dư nợ (blank) từ CRM4 các khoản khác
    if "LOAI" in df_crm4_filtered.columns and "DU_NO_PHAN_BO_QUY_DOI" in df_crm4_filtered.columns:
        df_crm4_blank = df_crm4_filtered[
            ~df_crm4_filtered["LOAI"].isin(["Cho vay", "Bao lanh", "LC"])
        ].copy()

        if len(df_crm4_blank) > 0:
            du_no_bosung = (
                df_crm4_blank[df_crm4_blank["CIF_KH_VAY"].isin(cif_lech)]
                .groupby("CIF_KH_VAY", as_index=False)["DU_NO_PHAN_BO_QUY_DOI"]
                .sum()
                .rename(columns={"DU_NO_PHAN_BO_QUY_DOI": "(blank)"})
            )

            pivot_full = pivot_full.merge(du_no_bosung, on="CIF_KH_VAY", how="left")
            pivot_full["(blank)"] = pivot_full["(blank)"].fillna(0)
            if "DƯ NỢ CRM32" in pivot_full.columns:
                pivot_full["DƯ NỢ CRM32"] = pivot_full["DƯ NỢ CRM32"] + pivot_full["(blank)"]

    # Nợ nhóm 2 / Nợ xấu
    if "NHOM_NO" in pivot_full.columns:
        pivot_full["Nợ nhóm 2"] = pivot_full["NHOM_NO"].apply(
            lambda x: "x" if str(x).strip() == "2" else ""
        )
        pivot_full["Nợ xấu"] = pivot_full["NHOM_NO"].apply(
            lambda x: "x" if str(x).strip() in ["3", "4", "5"] else ""
        )
    else:
        pivot_full["Nợ nhóm 2"] = ""
        pivot_full["Nợ xấu"] = ""

    # Chuyên gia PD cấp C duyệt & NỢ CƠ_CẤU
    pivot_full["Chuyên gia PD cấp C duyệt"] = pivot_full["CIF_KH_VAY"].apply(
        lambda x: "x" if x in list_cif_cap_c else ""
    )
    pivot_full["NỢ CƠ_CẤU"] = pivot_full["CIF_KH_VAY"].apply(
        lambda x: "x" if x in cif_co_cau else ""
    )

    # =======================================================
    # 4. BẢO LÃNH & LC
    # =======================================================
    if "LOAI" in df_crm4_filtered.columns and "DU_NO_PHAN_BO_QUY_DOI" in df_crm4_filtered.columns:
        df_baolanh = df_crm4_filtered[df_crm4_filtered["LOAI"] == "Bao lanh"]
        df_lc = df_crm4_filtered[df_crm4_filtered["LOAI"] == "LC"]

        df_baolanh_sum = df_baolanh.groupby("CIF_KH_VAY", as_index=False)[
            "DU_NO_PHAN_BO_QUY_DOI"
        ].sum().rename(columns={"DU_NO_PHAN_BO_QUY_DOI": "DƯ_NỢ_BẢO_LÃNH"})

        df_lc_sum = df_lc.groupby("CIF_KH_VAY", as_index=False)["DU_NO_PHAN_BO_QUY_DOI"].sum().rename(
            columns={"DU_NO_PHAN_BO_QUY_DOI": "DƯ_NỢ_LC"}
        )

        if "DƯ_NỢ_BẢO_LÃNH" in pivot_full.columns:
            pivot_full = pivot_full.drop(columns=["DƯ_NỢ_BẢO_LÃNH"])
        pivot_full = pivot_full.merge(df_baolanh_sum, on="CIF_KH_VAY", how="left")

        if "DƯ_NỢ_LC" in pivot_full.columns:
            pivot_full = pivot_full.drop(columns=["DƯ_NỢ_LC"])
        pivot_full = pivot_full.merge(df_lc_sum, on="CIF_KH_VAY", how="left")

        pivot_full["DƯ_NỢ_BẢO_LÃNH"] = pivot_full["DƯ_NỢ_BẢO_LÃNH"].fillna(0)
        pivot_full["DƯ_NỢ_LC"] = pivot_full["DƯ_NỢ_LC"].fillna(0)

    # =======================================================
    # 5. GIẢI NGÂN TIỀN MẶT
    # =======================================================
    df_giai_ngan = pd.read_excel(df_giai_ngan_file_upload)

    if "KHE_UOC" in df_crm32_filtered.columns and "FORACID" in df_giai_ngan.columns:
        df_crm32_filtered["KHE_UOC"] = df_crm32_filtered["KHE_UOC"].astype(str).str.strip()
        df_crm32_filtered["CUSTSEQLN"] = df_crm32_filtered["CUSTSEQLN"].astype(str).str.strip()
        df_giai_ngan["FORACID"] = df_giai_ngan["FORACID"].astype(str).str.strip()
        pivot_full["CIF_KH_VAY"] = pivot_full["CIF_KH_VAY"].astype(str).str.strip()

        df_match = df_crm32_filtered[
            df_crm32_filtered["KHE_UOC"].isin(df_giai_ngan["FORACID"])
        ].copy()
        ds_cif_tien_mat = df_match["CUSTSEQLN"].unique()

        pivot_full["GIẢI_NGÂN_TIEN_MAT"] = pivot_full["CIF_KH_VAY"].isin(ds_cif_tien_mat).map(
            {True: "x", False: ""}
        )

    # TSBĐ cầm cố tại TCTD khác
    if "CAP_2" in df_crm4_filtered.columns:
        df_cc_tctd = df_crm4_filtered[
            df_crm4_filtered["CAP_2"].astype(str).str.contains("TCTD", case=False, na=False)
        ]
        df_cc_flag = df_cc_tctd[["CIF_KH_VAY"]].drop_duplicates()
        df_cc_flag["Cầm cố tại TCTD khác"] = "x"

        pivot_full = pivot_full.merge(df_cc_flag, on="CIF_KH_VAY", how="left")
        pivot_full["Cầm cố tại TCTD khác"] = pivot_full["Cầm cố tại TCTD khác"].fillna("")

    # TOP 10 dư nợ KHCN / KHDN
    if "CUSTTPCD" in pivot_full.columns and "DƯ NỢ" in pivot_full.columns:
        top5_khcn = pivot_full[pivot_full["CUSTTPCD"] == "Ca nhan"].nlargest(10, "DƯ NỢ")[
            "CIF_KH_VAY"
        ]
        pivot_full["Top 10 dư nợ KHCN"] = pivot_full["CIF_KH_VAY"].apply(
            lambda x: "x" if x in top5_khcn.values else ""
        )

        top5_khdn = pivot_full[pivot_full["CUSTTPCD"] == "Doanh nghiep"].nlargest(
            10, "DƯ NỢ"
        )["CIF_KH_VAY"]
        pivot_full["Top 10 dư nợ KHDN"] = pivot_full["CIF_KH_VAY"].apply(
            lambda x: "x" if x in top5_khdn.values else ""
        )

    # =======================================================
    # 6. NGÀY ĐỊNH GIÁ TSBĐ (R34) – FIX SYNTAX
    # =======================================================
    if "LOAI_TS" in df_crm4_filtered.columns and "VALUATION_DATE" in df_crm4_filtered.columns:
        loai_ts_r34 = ["BĐS", "MMTB", "PTVT"]
        mask_r34 = df_crm4_filtered["LOAI_TS"].isin(loai_ts_r34)

        df_crm4_filtered["VALUATION_DATE"] = pd.to_datetime(
            df_crm4_filtered["VALUATION_DATE"], errors="coerce"
        )

        df_crm4_filtered.loc[mask_r34, "SO_NGAY_QUA_HAN"] = (
            ngay_danh_gia - df_crm4_filtered.loc[mask_r34, "VALUATION_DATE"]
        ).dt.days - 365

        # FIX: Đóng parentheses đúng
        df_crm4_filtered.loc[df_crm4_filtered["LOAI_TS"] == "BĐS", "SO_THANG_QUA_HAN"] = (
            (ngay_danh_gia - df_crm4_filtered.loc[df_crm4_filtered["LOAI_TS"] == "BĐS", "VALUATION_DATE"]).dt.days / 31
            - 18
        )

        df_crm4_filtered.loc[df_crm4_filtered["LOAI_TS"].isin(["MMTB", "PTVT"]), "SO_THANG_QUA_HAN"] = (
            (ngay_danh_gia - df_crm4_filtered.loc[df_crm4_filtered["LOAI_TS"].isin(["MMTB", "PTVT"]), "VALUATION_DATE"]).dt.days / 31
            - 12
        )

        cif_quahan = df_crm4_filtered[df_crm4_filtered["SO_THANG_QUA_HAN"] > 0][
            "CIF_KH_VAY"
        ].unique()

        pivot_full["KH có TSBĐ quá hạn định giá"] = pivot_full["CIF_KH_VAY"].apply(
            lambda x: "X" if x in cif_quahan else ""
        )

    # =======================================================
    # 7. TSBĐ KHÁC ĐỊA BÀN (MỤC 17)
    # =======================================================
    df_sol = pd.read_excel(df_sol_file_upload)
    
    if "SECU_SRL_NUM" in df_crm4_filtered.columns and "C01" in df_sol.columns:
        ds_secu = df_crm4_filtered["SECU_SRL_NUM"].dropna().unique()
        df_17_filtered = df_sol[df_sol["C01"].isin(ds_secu)]

        if "C02" in df_17_filtered.columns and "C19" in df_17_filtered.columns:
            df_bds = df_17_filtered[df_17_filtered["C02"].astype(str).str.strip() == "Bat dong san"].copy()
            df_bds_matched = df_bds[df_bds["C01"].isin(df_crm4["SECU_SRL_NUM"])].copy()

            def extract_tinh_thanh(diachi):
                if pd.isna(diachi):
                    return ""
                parts = str(diachi).split(",")
                return parts[-1].strip().lower() if parts else ""

            df_bds_matched["TINH_TP_TSBD"] = df_bds_matched["C19"].apply(extract_tinh_thanh)

            df_bds_matched["CANH_BAO_TS_KHAC_DIABAN"] = df_bds_matched["TINH_TP_TSBD"].apply(
                lambda x: "x" if x and x.strip().lower() not in dia_ban_kt else ""
            )

            ma_ts_canh_bao = df_bds_matched[
                df_bds_matched["CANH_BAO_TS_KHAC_DIABAN"] == "x"
            ]["C01"].unique()
            cif_canh_bao = df_crm4[df_crm4["SECU_SRL_NUM"].isin(ma_ts_canh_bao)][
                "CIF_KH_VAY"
            ].dropna().unique()

            pivot_full["KH có TSBĐ khác địa bàn"] = pivot_full["CIF_KH_VAY"].apply(
                lambda x: "x" if x in cif_canh_bao else ""
            )
        else:
            df_bds_matched = pd.DataFrame()
            pivot_full["KH có TSBĐ khác địa bàn"] = ""
    else:
        df_bds_matched = pd.DataFrame()
        pivot_full["KH có TSBĐ khác địa bàn"] = ""

    # =======================================================
    # 8. MỤC 55 & 56 – TẤT TOÁN / GIẢI NGÂN
    # =======================================================
    df_55 = pd.read_excel(df_55_file_upload)
    df_56 = pd.read_excel(df_56_file_upload)

    # Xử lý Mục 55 (Tất toán)
    cols_55_required = ["CUSTSEQLN", "NMLOC", "KHE_UOC", "SOTIENGIAINGAN", "NGAYGN", "NGAYDH", "NGAY_TT", "LOAITIEN"]
    cols_55_exist = [c for c in cols_55_required if c in df_55.columns]
    
    if cols_55_exist:
        df_tt = df_55[cols_55_exist].copy()
        df_tt.columns = ["CIF", "TEN_KHACH_HANG", "KHE_UOC", "SO_TIEN_GIAI_NGAN_VND", 
                         "NGAY_GIAI_NGAN", "NGAY_DAO_HAN", "NGAY_TT", "LOAI_TIEN_HD"][:len(cols_55_exist)]
    else:
        df_tt = pd.DataFrame()

    if len(df_tt) > 0:
        df_tt["GIAI_NGAN_TT"] = "Tất toán"
        df_tt["NGAY"] = pd.to_datetime(df_tt.get("NGAY_TT"), errors="coerce")

    # Xử lý Mục 56 (Giải ngân)
    cols_56_required = ["CIF", "TEN_KHACH_HANG", "KHE_UOC", "SO_TIEN_GIAI_NGAN_VND", "NGAY_GIAI_NGAN", "NGAY_DAO_HAN", "LOAI_TIEN_HD"]
    cols_56_exist = [c for c in cols_56_required if c in df_56.columns]
    
    if cols_56_exist:
        df_gn = df_56[cols_56_exist].copy()
    else:
        df_gn = pd.DataFrame()

    if len(df_gn) > 0:
        df_gn["GIAI_NGAN_TT"] = "Giải ngân"
        df_gn["NGAY_GIAI_NGAN"] = pd.to_datetime(df_gn["NGAY_GIAI_NGAN"], format="%Y%m%d", errors="coerce")
        df_gn["NGAY_DAO_HAN"] = pd.to_datetime(df_gn["NGAY_DAO_HAN"], format="%Y%m%d", errors="coerce")
        df_gn["NGAY"] = df_gn["NGAY_GIAI_NGAN"]

    df_gop = pd.concat([df_tt, df_gn], ignore_index=True) if len(df_tt) > 0 or len(df_gn) > 0 else pd.DataFrame()
    
    if len(df_gop) > 0:
        df_gop = df_gop[df_gop["NGAY"].notna()]
        df_gop = df_gop.sort_values(by=["CIF", "NGAY", "GIAI_NGAN_TT"])

        df_count = (
            df_gop.groupby(["CIF", "NGAY", "GIAI_NGAN_TT"])
            .size()
            .unstack(fill_value=0)
            .reset_index()
        )
        df_count["CO_CA_GN_VA_TT"] = (
            (df_count.get("Giải ngân", 0) > 0) & (df_count.get("Tất toán", 0) > 0)
        ).astype(int)

        df_count["CIF"] = df_count["CIF"].astype(str)
        df_gop["CIF"] = df_gop["CIF"].astype(str)

        ds_ca_gn_tt = df_count[df_count["CO_CA_GN_VA_TT"] == 1]["CIF"].astype(str).unique()

        pivot_full["CIF_KH_VAY"] = pivot_full["CIF_KH_VAY"].astype(str)
        pivot_full["KH có cả GNG và TT trong 1 ngày"] = pivot_full["CIF_KH_VAY"].apply(
            lambda x: "x" if x in ds_ca_gn_tt else ""
        )
    else:
        df_count = pd.DataFrame()
        pivot_full["KH có cả GNG và TT trong 1 ngày"] = ""

    # =======================================================
    # 9. MỤC 57 – CHẬM TRẢ
    # =======================================================
    df_delay = pd.read_excel(df_57_file_upload)

    if "NGAY_DEN_HAN_TT" in df_delay.columns and "NGAY_THANH_TOAN" in df_delay.columns:
        df_delay["NGAY_DEN_HAN_TT"] = pd.to_datetime(df_delay["NGAY_DEN_HAN_TT"], errors="coerce")
        df_delay["NGAY_THANH_TOAN"] = pd.to_datetime(df_delay["NGAY_THANH_TOAN"], errors="coerce")

        df_delay["NGAY_THANH_TOAN_FILL"] = df_delay["NGAY_THANH_TOAN"].fillna(ngay_danh_gia)
        df_delay["SO_NGAY_CHAM_TRA"] = (
            df_delay["NGAY_THANH_TOAN_FILL"] - df_delay["NGAY_DEN_HAN_TT"]
        ).dt.days

        mask_period = df_delay["NGAY_DEN_HAN_TT"].dt.year.between(2023, 2025)
        df_delay = df_delay[mask_period].copy()

        df_crm32_tmp = pivot_full.copy()
        df_crm32_tmp = df_crm32_tmp.rename(columns={"CIF_KH_VAY": "CIF_ID"})

        df_crm32_tmp["CIF_ID"] = df_crm32_tmp["CIF_ID"].astype(str)
        
        if "CIF_ID" in df_delay.columns:
            df_delay["CIF_ID"] = df_delay["CIF_ID"].astype(str)

            if "DƯ NỢ" in df_crm32_tmp.columns and "NHOM_NO" in df_crm32_tmp.columns:
                df_delay = df_delay.merge(
                    df_crm32_tmp[["CIF_ID", "DƯ NỢ", "NHOM_NO"]], on="CIF_ID", how="left"
                )

                df_delay = df_delay[df_delay["NHOM_NO"] == 1].copy()

        def cap_cham_tra(days):
            if pd.isna(days):
                return None
            elif days >= 10:
                return ">=10"
            elif days >= 4:
                return "4-9"
            elif days > 0:
                return "<4"
            else:
                return None

        df_delay["CAP_CHAM_TRA"] = df_delay.get("SO_NGAY_CHAM_TRA", pd.Series()).apply(cap_cham_tra)
        df_delay = df_delay.dropna(subset=["CAP_CHAM_TRA"]).copy()

        if len(df_delay) > 0:
            df_delay["NGAY"] = df_delay["NGAY_DEN_HAN_TT"].dt.date
            df_delay.sort_values(
                ["CIF_ID", "NGAY", "CAP_CHAM_TRA"],
                key=lambda s: s.map({">=10": 0, "4-9": 1, "<4": 2}),
                inplace=True,
            )
            df_unique = df_delay.drop_duplicates(subset=["CIF_ID", "NGAY"], keep="first").copy()

            df_dem = df_unique.groupby(["CIF_ID", "CAP_CHAM_TRA"]).size().unstack(fill_value=0)

            df_dem["KH Phát sinh chậm trả > 10 ngày"] = np.where(
                df_dem.get(">=10", 0) > 0, "x", ""
            )
            df_dem["KH Phát sinh chậm trả 4-9 ngày"] = np.where(
                (df_dem.get(">=10", 0) == 0) & (df_dem.get("4-9", 0) > 0), "x", ""
            )

            pivot_full["CIF_KH_VAY"] = pivot_full["CIF_KH_VAY"].astype(str)

            cols_to_merge = [
                "KH Phát sinh chậm trả > 10 ngày",
                "KH Phát sinh chậm trả 4-9 ngày",
            ]
            cols_to_merge_existing = [col for col in cols_to_merge if col in df_dem.columns]

            if cols_to_merge_existing:
                pivot_full = pivot_full.merge(
                    df_dem[cols_to_merge_existing],
                    left_on="CIF_KH_VAY",
                    right_index=True,
                    how="left",
                )

            for col in cols_to_merge_existing:
                pivot_full[col] = pivot_full[col].fillna("")

    # --------------------------------------------------------
    # TRẢ VỀ CÁC BẢNG KẾT QUẢ
    # --------------------------------------------------------
    return {
        "df_crm4_filtered": df_crm4_filtered,
        "pivot_final": pivot_final,
        "pivot_merge": pivot_merge,
        "df_crm32_filtered": df_crm32_filtered,
        "pivot_full": pivot_full,
        "pivot_mucdich": pivot_mucdich,
        "df_delay": df_delay,
        "df_gop": df_gop,
        "df_count": df_count,
        "df_bds_matched": df_bds_matched,
    }


# ============================================================
# HÀM PUBLIC – GỌI TỪ app.py
# ============================================================

def run_tin_dung():
    try:
        _run_tin_dung()
    except UserFacingError:
        raise
    except Exception as exc:
        if _should_reraise(exc):
            raise

        raise UserFacingError(
            "Đã xảy ra lỗi khi xử lý Tiêu chí tín dụng CRM4–32. Vui lòng kiểm tra file đầu vào."
        ) from exc


def _run_tin_dung():

    st.info(
        """
    **Vui lòng upload đúng loại báo cáo và đúng kỳ dữ liệu.**  
    Nếu upload sai file/mẫu cột khác hệ thống sẽ báo lỗi hoặc cho kết quả sai.
    
    **Yêu cầu từng file:**
    - **1️⃣ CRM4_Du_no_theo_tai_san_dam_bao_ALL**: xuất từ CRM4, có các cột như `CIF_KH_VAY, BRANCH_VAY, CAP_2, LOAI, TS_KW_VND, DU_NO_PHAN_BO_QUY_DOI, SECU_SRL_NUM, VALUATION_DATE...`
    - **2️⃣ RPT_CRM_32**: báo cáo CRM32, có `CUSTSEQLN, BRCD, DU_NO_QUY_DOI, SCHEME_CODE, KHE_UOC, CAP_PHE_DUYET, MUC_DICH_VAY_CAP_4...`
    - **3️⃣ CODE_MDSDV4.xlsx**: bảng mã mục đích vay (có `CODE_MDSDV4, GROUP`)
    - **4️⃣ CODE_LOAI_TSBD.xlsx**: bảng mã loại TSBD (có `CODE CAP 2, CODE`)
    - **5️⃣ Giai_ngan_tien_mat_1_ty 6**: danh sách giải ngân tiền mặt (có `FORACID`)
    - **6️⃣ Muc17_Lop2_TSTC 4**: Mục 17 tài sản (có `C01, C02, C19...`)
    - **7️⃣ Muc55_...**: Mục 55 tất toán (có `CUSTSEQLN, KHE_UOC, NGAY_TT...`)
    - **8️⃣ Muc56_...**: Mục 56 giải ngân (có `CIF, KHE_UOC, NGAY_GIAI_NGAN, NGAY_DAO_HAN...`)
    - **9️⃣ Muc57_...**: Mục 57 chậm trả (có `CIF_ID, NGAY_DEN_HAN_TT, NGAY_THANH_TOAN...`)
    
    📌 **Lưu ý:** Nếu file có nhiều sheet, hãy đảm bảo dữ liệu nằm ở **sheet đầu tiên** (hoặc chuẩn hóa lại trước khi upload).
    """
    )
    st.markdown("### 📝 Nhập tham số (phải nhập đầy đủ các thông tin theo yêu cầu)")

    colA, colB = st.columns(2)

    with colA:
        chi_nhanh = st.text_input(
            "Nhập mã SOL cần lọc",
            placeholder="Ví dụ: 1000",
        ).strip().upper()

        ngay_danh_gia_input = st.date_input(
            "Ngày đánh giá", value=pd.to_datetime("2025-09-30")
        )
        ngay_danh_gia = pd.to_datetime(ngay_danh_gia_input)

    with colB:
        dia_ban_kt_input = st.text_input(
            "Nhập tên tỉnh/thành của đơn vị (phân cách bằng dấu phẩy)",
            placeholder="VD: thanh pho ho chi minh, tinh binh duong",
        )
        dia_ban_kt = [t.strip().lower() for t in dia_ban_kt_input.split(",") if t.strip()]

    st.markdown("---")
    st.markdown("### 📂 Upload file dữ liệu")

    col1, col2 = st.columns(2)

    with col1:
        crm4_files = st.file_uploader(
            "1️⃣ CRM4_Du_no_theo_tai_san_dam_bao_ALL",
            type=["xls", "xlsx"],
            accept_multiple_files=True,
        )

        crm32_files = st.file_uploader(
            "2️⃣ RPT_CRM_32",
            type=["xls", "xlsx"],
            accept_multiple_files=True,
        )

        df_muc_dich_file_upload = st.file_uploader(
            "3️⃣ CODE_MDSDV4.xlsx (Bảng mã mục đích vay)",
            type=["xls", "xlsx"],
        )

        df_code_tsbd_file_upload = st.file_uploader(
            "4️⃣ CODE_LOAI_TSBD.xlsx (Bảng mã loại TSBD)",
            type=["xls", "xlsx"],
        )
        df_giai_ngan_file_upload = st.file_uploader(
            "5️⃣ Giai_ngan_tien_mat_1_ty 6.xls",
            type=["xls", "xlsx"],
        )

    with col2:
        df_sol_file_upload = st.file_uploader(
            "6️⃣ Muc17_Lop2_TSTC 4.xlsx (Mục 17 - Tài sản)",
            type=["xls", "xlsx"],
        )

        df_55_file_upload = st.file_uploader(
            "7️⃣ Muc55_1405.xlsx (Mục 55 - Tất toán)",
            type=["xls", "xlsx"],
        )

        df_56_file_upload = st.file_uploader(
            "8️⃣ Muc56_1405.xlsx (Mục 56 - Giải ngân)",
            type=["xls", "xlsx"],
        )

        df_57_file_upload = st.file_uploader(
            "9️⃣ Muc57_1405.xlsx (Mục 57 - Chậm trả)",
            type=["xls", "xlsx"],
        )

    run_button = st.button("▶️ Chạy xử lý dữ liệu")

    if run_button:
        missing = []
        if not crm4_files:
            missing.append("CRM4 files")
        if not crm32_files:
            missing.append("CRM32 files")
        if df_muc_dich_file_upload is None:
            missing.append("CODE_MDSDV4.xlsx")
        if df_code_tsbd_file_upload is None:
            missing.append("CODE_LOAI TSBD.xlsx")
        if df_giai_ngan_file_upload is None:
            missing.append("Giai_ngan_tien_mat_1_ty 6.xls")
        if df_sol_file_upload is None:
            missing.append("Muc17_Lop2_TSTC 4.xlsx")
        if df_55_file_upload is None:
            missing.append("Muc55_1405.xlsx")
        if df_56_file_upload is None:
            missing.append("Muc56_1405.xlsx")
        if df_57_file_upload is None:
            missing.append("Muc57_1405.xlsx")
        if chi_nhanh == "":
            missing.append("Chi nhánh (BRANCH_VAY/BRCD)")
        if not dia_ban_kt:
            missing.append("Danh sách địa bàn kiểm toán")

        if missing:
            st.error("❌ Thiếu dữ liệu/thiết lập: " + ", ".join(missing))
            return

        with st.spinner("Đang xử lý dữ liệu..."):
            results = process_data(
                crm4_files,
                crm32_files,
                df_muc_dich_file_upload,
                df_code_tsbd_file_upload,
                df_giai_ngan_file_upload,
                df_sol_file_upload,
                df_55_file_upload,
                df_56_file_upload,
                df_57_file_upload,
                chi_nhanh,
                ngay_danh_gia,
                dia_ban_kt,
            )

        st.success("✅ Đã xử lý xong!")

        df_crm4_filtered = results["df_crm4_filtered"]
        pivot_final = results["pivot_final"]
        pivot_merge = results["pivot_merge"]
        df_crm32_filtered = results["df_crm32_filtered"]
        pivot_full = results["pivot_full"]
        pivot_mucdich = results["pivot_mucdich"]
        df_delay = results["df_delay"]
        df_gop = results["df_gop"]
        df_count = results["df_count"]
        df_bds_matched = results["df_bds_matched"]

        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
            [
                "KQ_KH (pivot_full)",
                "KQ_CRM4 (pivot_final)",
                "Pivot CRM4 (pivot_merge)",
                "Pivot CRM32 (pivot_mucdich)",
                "df_crm4_LOAI_TS",
                "Cảnh báo / tiêu chí",
                "df_crm32_LOAI_TS",
            ]
        )

        with tab1:
            st.subheader("KQ_KH – Tổng hợp theo CIF (pivot_full)")
            st.dataframe(pivot_full)

        with tab2:
            st.subheader("KQ_CRM4 – Thông tin theo CIF từ CRM4")
            st.dataframe(pivot_final)

        with tab3:
            st.subheader("Pivot_crm4 – Dư nợ & Giá trị TS theo loại TS")
            st.dataframe(pivot_merge)

        with tab4:
            st.subheader("Pivot_crm32 – Dư nợ theo mục đích CRM32")
            st.dataframe(pivot_mucdich)

        with tab5:
            st.subheader("df_crm4_LOAI_TS – CRM4 sau khi gán loại TS")
            st.dataframe(df_crm4_filtered)

        with tab6:
            st.subheader("Tiêu chí 4 – Chậm trả (df_delay)")
            st.dataframe(df_delay)

            st.subheader("Tiêu chí 3_đợt 3 – Gộp GN/TT (df_gop)")
            st.dataframe(df_gop)

            st.subheader("Tiêu chí 3_đợt 3_1 – Đếm GN/TT theo ngày (df_count)")
            st.dataframe(df_count)

            st.subheader("Tiêu chí 2_đợt 3 – TSBĐ khác địa bàn (df_bds_matched)")
            st.dataframe(df_bds_matched)

        with tab7:
            st.subheader("df_crm32_LOAI_TS – CRM32 sau khi gán mục đích vay")
            st.dataframe(df_crm32_filtered)

        st.markdown("---")
        st.subheader("📤 Xuất file Excel tổng hợp")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_crm4_filtered.to_excel(writer, sheet_name="df_crm4_LOAI_TS", index=False)
            pivot_final.to_excel(writer, sheet_name="KQ_CRM4", index=False)
            pivot_merge.to_excel(writer, sheet_name="Pivot_crm4", index=False)
            df_crm32_filtered.to_excel(
                writer, sheet_name="df_crm32_LOAI_TS", index=False
            )
            pivot_full.to_excel(writer, sheet_name="KQ_KH", index=False)
            pivot_mucdich.to_excel(writer, sheet_name="Pivot_crm32", index=False)
            df_delay.to_excel(writer, sheet_name="tieu chi 4", index=False)
            df_gop.to_excel(writer, sheet_name="tieu chi 3_dot3", index=False)
            df_count.to_excel(writer, sheet_name="tieu chi 3_dot3_1", index=False)
            df_bds_matched.to_excel(writer, sheet_name="tieu chi 2_dot3", index=False)

        buffer.seek(0)

        st.download_button(
            label="⬇️ Tải file KQ_tindung.xlsx",
            data=buffer,
            file_name="KQ_tindung.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    else:
        st.info(
            "👈 Vui lòng upload đầy đủ file, nhập chi nhánh / ngày đánh giá / địa bàn, rồi bấm **Chạy xử lý dữ liệu**."
        )
