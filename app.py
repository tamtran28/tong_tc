import io
import re
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

# =========================================================
# CẤU HÌNH CHUNG
# =========================================================
st.set_page_config(
    page_title="Hệ thống KTNB tổng hợp",
    layout="wide"
)

st.sidebar.title("📁 Chọn phân hệ")
module = st.sidebar.selectbox(
    "Phân hệ:",
    [
        "[1] Phôi thẻ – GTCG",
        "[2] Mục 09 – Chuyển tiền",
        "[3] Tờ khai Hải quan",
        "[4] Thẻ (1.3.2)",
        "[5] POS (6.2)",
        "[6] DVKH – 5 tiêu chí",
    ]
)

# =========================================================
# =============== [1] PHÔI THẺ – GTCG =====================
# =========================================================
def run_phoi_the():
    st.title("📘 Phân hệ Phôi Thẻ – GTCG")
   

st.set_page_config(page_title="GTCG - Xử lý phôi thẻ", layout="wide")

st.title("📘 Hệ thống xử lý dữ liệu Phôi Thẻ – GTCG")


# ======================
# 1) USER INPUT
# ======================
sol_kiem_toan = st.text_input("Nhập mã SOL kiểm toán (ví dụ: 1002):", "")

uploaded_file1 = st.file_uploader("Tải file GTCG1_<sol>.xlsx", type=["xlsx"])
uploaded_file2 = st.file_uploader("Tải file GTCG2_<sol>.xlsx", type=["xlsx"])

if sol_kiem_toan and uploaded_file1 and uploaded_file2:
    st.success("✔ Đã nhập mã SOL & tải đủ 2 file.")

    if st.button("🚀 Xử lý dữ liệu"):
        prefix_tbl = f"{sol_kiem_toan}G"

        # ================================================================
        # 2) XỬ LÝ FILE GTCG1 (TIÊU CHÍ 1 & 2)
        # ================================================================
        df = pd.read_excel(uploaded_file1, dtype={"ACC_NO": str})

        df["ACC_NO"] = df["ACC_NO"].astype(str)
        df["INVT_TRAN_DATE"] = pd.to_datetime(df["INVT_TRAN_DATE"])
        df.sort_values(by="INVT_SRL_NUM", ascending=True, inplace=True)
        df.reset_index(drop=True, inplace=True)

        # (1) Số lần in hỏng
        failure_mask = (df["PASSBOOK_STATUS"] == "F") & (df["INVT_LOCN_CODE_TO"] == "IS")
        total_failure_counts = df.loc[failure_mask, "ACC_NO"].map(
            df.loc[failure_mask, "ACC_NO"].value_counts()
        )
        df["Số lần in hỏng"] = total_failure_counts.fillna(0).astype(int)

        # (2) In hỏng nhiều lần 1 ngày
        df["daily_failures"] = df[failure_mask].groupby(
            ["ACC_NO", df["INVT_TRAN_DATE"].dt.date]
        ).transform("size")
        df["TTK in hỏng nhiều lần trong 01 ngày"] = np.where(
            df["daily_failures"] >= 2, "X", ""
        )
        df.drop(columns=["daily_failures"], inplace=True)

        # (3) In hết dòng
        df["TRAN_DATE_ONLY"] = df["INVT_TRAN_DATE"].dt.date
        hetdong_mask = (df["PASSBOOK_STATUS"] == "U") & (df["INVT_LOCN_CODE_TO"] == "IS")

        df["Số lần in hết dòng"] = (
            df.loc[hetdong_mask, "ACC_NO"]
            .map(df.loc[hetdong_mask, "ACC_NO"].value_counts())
            .fillna(0)
            .astype(int)
        )

        df["daily_het_dong"] = df[hetdong_mask].groupby(
            ["ACC_NO", "TRAN_DATE_ONLY"]
        )["ACC_NO"].transform("count")
        df["TTK in hết dòng nhiều lần trong 01 ngày"] = np.where(
            df["daily_het_dong"] >= 2, "X", ""
        )
        df.drop(columns=["daily_het_dong"], inplace=True)

        # (4) Vừa in hỏng + hết dòng
        df_temp = df.groupby(["ACC_NO", "TRAN_DATE_ONLY"]).agg({
            "Số lần in hỏng": "sum",
            "Số lần in hết dòng": "sum",
        }).reset_index()

        df_temp["TTK vừa in hỏng vừa in hết dòng trong 01 ngày"] = np.where(
            (df_temp["Số lần in hỏng"] > 0) & (df_temp["Số lần in hết dòng"] > 0),
            "X",
            "",
        )

        df = df.merge(
            df_temp[
                ["ACC_NO", "TRAN_DATE_ONLY", "TTK vừa in hỏng vừa in hết dòng trong 01 ngày"]
            ],
            on=["ACC_NO", "TRAN_DATE_ONLY"],
            how="left",
        )

        df.drop(columns=["TRAN_DATE_ONLY"], inplace=True)
        df["INVT_TRAN_DATE"] = df["INVT_TRAN_DATE"].dt.strftime("%m/%d/%Y")

        # ================================================================
        # 3) XỬ LÝ FILE GTCG2 (TIÊU CHÍ 3)
        # ================================================================
        df_muc18 = pd.read_excel(uploaded_file2)

        df_muc18["TBL"] = df_muc18["INVT_XFER_PARTICULAR"].astype(str).str.extract(
            f"({prefix_tbl}[^\\s/]*)"
        )[0]

        df_muc18["Phôi hỏng không gắn số"] = (
            df_muc18["INVT_LOCN_CODE_TO"]
            .astype(str)
            .str.contains("FAIL PRINT|FAIL", na=False)
            & ~df_muc18["INVT_XFER_PARTICULAR"].astype(str).str.contains(prefix_tbl)
        ).map({True: "X", False: ""})

        # (2) Số lần phát hành
        mask_ph = (df_muc18["INVT_LOCN_CODE_TO"] == "IS") & df_muc18["TBL"].notna()
        df_ph = df_muc18[mask_ph]
        ph_counts = df_ph["TBL"].value_counts().to_dict()
        df_muc18["Số lần phát hành"] = df_muc18["TBL"].map(ph_counts).fillna(0).astype(int)

        # (3) PH nhiều lần trong 1 ngày
        df_muc18["INVT_TRAN_DATE_ONLY"] = pd.to_datetime(
            df_muc18["INVT_TRAN_DATE"]
        ).dt.date

        df_muc18["PH nhiều lần trong 1 ngày"] = ""
        df_is = df_muc18[df_muc18["INVT_LOCN_CODE_TO"] == "IS"]

        df_count = df_is.groupby(["TBL", "INVT_TRAN_DATE_ONLY"]).size().reset_index(name="count")
        multi_groups = df_count[df_count["count"] >= 2]
        multi_keys = set(zip(multi_groups["TBL"], multi_groups["INVT_TRAN_DATE_ONLY"]))

        df_muc18["PH nhiều lần trong 1 ngày"] = df_muc18.apply(
            lambda r: "X"
            if (r["INVT_LOCN_CODE_TO"] == "IS"
                and (r["TBL"], r["INVT_TRAN_DATE_ONLY"]) in multi_keys)
            else "",
            axis=1,
        )

        # (4) Số lần in hỏng
        mask_hong = (
            df_muc18["INVT_LOCN_CODE_TO"].isin(["FAIL", "FAIL PRINT"])
            & df_muc18["TBL"].notna()
        )
        df_hong = df_muc18[mask_hong]
        hong_counts = df_hong["TBL"].value_counts().to_dict()
        df_muc18["Số lần in hỏng"] = df_muc18["TBL"].map(hong_counts).fillna(0).astype(int)

        # (5) In hỏng nhiều lần trong 1 ngày
        df_muc18["(5) In hỏng nhiều lần trong 1 ngày"] = ""

        mask_h2 = (
            (df_muc18["INVT_LOCN_CODE_TO"] == "FAIL PRINT")
            & (df_muc18["Số lần in hỏng"] >= 2)
        )
        df_fail2 = df_muc18[mask_h2]

        fail_groups = (
            df_fail2.groupby(["TBL", "INVT_TRAN_DATE_ONLY"])
            .filter(lambda g: len(g) >= 2)
        )

        df_muc18.loc[fail_groups.index, "(5) In hỏng nhiều lần trong 1 ngày"] = "X"

        # (6) PH nhiều lần + có in hỏng
        df_muc18["PH nhiều lần + có in hỏng"] = df_muc18.apply(
            lambda r: "X"
            if (r["Số lần phát hành"] > 1 and r["Số lần in hỏng"] > 0)
            else "",
            axis=1,
        )

        df_muc18.drop(columns=["INVT_TRAN_DATE_ONLY", "TBL"], inplace=True)

        # ================================================================
        # 4) XUẤT FILE KẾT QUẢ
        # ================================================================
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="tieu chi 1,2", index=False)
            df_muc18.to_excel(writer, sheet_name="tieu chi 3", index=False)

        st.success("🎯 Đã xử lý dữ liệu thành công!")

        st.download_button(
            label="📥 Tải file kết quả (Phoi_the.xlsx)",
            data=output.getvalue(),
            file_name=f"Phoi_the_{sol_kiem_toan}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.info("Vui lòng nhập mã SOL và tải cả 2 file Excel.")
    # uploaded_file1 = st.file_uploader("Tải file GTCG1_1002.xlsx", type=["xlsx"])
    # uploaded_file2 = st.file_uploader("Tải file GTCG2_1002.xlsx", type=["xlsx"])

    # if uploaded_file1 and uploaded_file2:
    #     st.success("✔ Đã tải đủ 2 file. Bấm **Xử lý dữ liệu** để tiếp tục.")

    #     if st.button("🚀 Xử lý dữ liệu"):
    #         # ==============================
    #         # 1. XỬ LÝ FILE 1
    #         # ==============================
    #         df = pd.read_excel(uploaded_file1, dtype={'ACC_NO': str})

    #         df["ACC_NO"] = df["ACC_NO"].astype(str)
    #         df["INVT_TRAN_DATE"] = pd.to_datetime(df["INVT_TRAN_DATE"])
    #         df.sort_values(by="INVT_SRL_NUM", ascending=True, inplace=True)
    #         df.reset_index(drop=True, inplace=True)

    #         # (1) Số lần in hỏng
    #         failure_mask = (df["PASSBOOK_STATUS"] == "F") & (df["INVT_LOCN_CODE_TO"] == "IS")
    #         total_failure_counts = df.loc[failure_mask, "ACC_NO"].map(
    #             df.loc[failure_mask, "ACC_NO"].value_counts()
    #         )
    #         df["Số lần in hỏng"] = total_failure_counts.fillna(0).astype(int)

    #         # (2) TTK in hỏng nhiều lần trong 1 ngày
    #         df["TRAN_DATE_ONLY"] = df["INVT_TRAN_DATE"].dt.date
    #         df["daily_failures"] = 0
    #         df.loc[failure_mask, "daily_failures"] = (
    #             df[failure_mask]
    #             .groupby(["ACC_NO", "TRAN_DATE_ONLY"])["ACC_NO"]
    #             .transform("count")
    #         )
    #         df["TTK in hỏng nhiều lần trong 01 ngày"] = np.where(
    #             df["daily_failures"] >= 2, "X", ""
    #         )
    #         df.drop(columns=["daily_failures"], inplace=True)

    #         # (3) In hết dòng
    #         hetdong_mask = (df["PASSBOOK_STATUS"] == "U") & (df["INVT_LOCN_CODE_TO"] == "IS")
    #         df["Số lần in hết dòng"] = (
    #             df.loc[hetdong_mask, "ACC_NO"]
    #             .map(df.loc[hetdong_mask, "ACC_NO"].value_counts())
    #             .fillna(0)
    #             .astype(int)
    #         )

    #         df["daily_het_dong"] = 0
    #         df.loc[hetdong_mask, "daily_het_dong"] = (
    #             df[hetdong_mask]
    #             .groupby(["ACC_NO", "TRAN_DATE_ONLY"])["ACC_NO"]
    #             .transform("count")
    #         )

    #         df["TTK in hết dòng nhiều lần trong 01 ngày"] = np.where(
    #             df["daily_het_dong"] >= 2, "X", ""
    #         )
    #         df.drop(columns=["daily_het_dong"], inplace=True)

    #         # (4) In hỏng + hết dòng cùng ngày
    #         df_temp = df.groupby(["ACC_NO", "TRAN_DATE_ONLY"]).agg({
    #             "Số lần in hỏng": "sum",
    #             "Số lần in hết dòng": "sum",
    #         }).reset_index()

    #         df_temp["TTK vừa in hỏng vừa in hết dòng trong 01 ngày"] = np.where(
    #             (df_temp["Số lần in hỏng"] > 0) & (df_temp["Số lần in hết dòng"] > 0),
    #             "X",
    #             "",
    #         )

    #         df = pd.merge(
    #             df,
    #             df_temp[
    #                 ["ACC_NO", "TRAN_DATE_ONLY", "TTK vừa in hỏng vừa in hết dòng trong 01 ngày"]
    #             ],
    #             on=["ACC_NO", "TRAN_DATE_ONLY"],
    #             how="left",
    #         )

    #         df.drop(columns=["TRAN_DATE_ONLY"], inplace=True)
    #         df["INVT_TRAN_DATE"] = df["INVT_TRAN_DATE"].dt.strftime("%m/%d/%Y")

    #         # ==============================
    #         # 2. XỬ LÝ FILE 2
    #         # ==============================
    #         sol_kiem_toan = "1002"
    #         prefix_tbl = f"{sol_kiem_toan}G"

    #         df_muc18 = pd.read_excel(uploaded_file2)
    #         df_muc18["TBL"] = df_muc18["INVT_XFER_PARTICULAR"].astype(str).str.extract(
    #             f"({prefix_tbl}[^\\s/]*)"
    #         )[0]

    #         df_muc18["Phôi hỏng không gắn số"] = (
    #             df_muc18["INVT_LOCN_CODE_TO"]
    #             .astype(str)
    #             .str.contains("FAIL PRINT|FAIL", na=False)
    #             & ~df_muc18["INVT_XFER_PARTICULAR"].astype(str).str.contains(prefix_tbl)
    #         ).map({True: "X", False: ""})

    #         # (2) Số lần phát hành
    #         mask_ph = (df_muc18["INVT_LOCN_CODE_TO"] == "IS") & df_muc18["TBL"].notna()
    #         df_ph = df_muc18[mask_ph]
    #         ph_counts = df_ph["TBL"].value_counts().to_dict()
    #         df_muc18["Số lần phát hành"] = df_muc18["TBL"].map(ph_counts).fillna(0).astype(int)

    #         # (3) PH nhiều lần trong 1 ngày
    #         df_muc18["INVT_TRAN_DATE_ONLY"] = pd.to_datetime(
    #             df_muc18["INVT_TRAN_DATE"]
    #         ).dt.date

    #         df_is = df_muc18[df_muc18["INVT_LOCN_CODE_TO"] == "IS"]

    #         count_by_tbl_date = (
    #             df_is.groupby(["TBL", "INVT_TRAN_DATE_ONLY"])
    #             .size()
    #             .reset_index(name="count")
    #         )
    #         multiple_ph = count_by_tbl_date[count_by_tbl_date["count"] >= 2]
    #         multiple_keys = set(zip(multiple_ph["TBL"], multiple_ph["INVT_TRAN_DATE_ONLY"]))

    #         df_muc18["PH nhiều lần trong 1 ngày"] = df_muc18.apply(
    #             lambda row: "X"
    #             if (
    #                 row["INVT_LOCN_CODE_TO"] == "IS"
    #                 and (row["TBL"], row["INVT_TRAN_DATE_ONLY"]) in multiple_keys
    #             )
    #             else "",
    #             axis=1,
    #         )

    #         # (4) Số lần in hỏng
    #         mask_hong = (
    #             df_muc18["INVT_LOCN_CODE_TO"].isin(["FAIL", "FAIL PRINT"])
    #             & df_muc18["TBL"].notna()
    #         )
    #         df_hong = df_muc18[mask_hong]
    #         hong_counts = df_hong["TBL"].value_counts().to_dict()

    #         df_muc18["Số lần in hỏng"] = (
    #             df_muc18["TBL"].map(hong_counts).fillna(0).astype(int)
    #         )

    #         # (5) In hỏng nhiều lần trong 1 ngày
    #         df_muc18["(5) In hỏng nhiều lần trong 1 ngày"] = ""

    #         mask_hong_2plus = (
    #             (df_muc18["INVT_LOCN_CODE_TO"] == "FAIL PRINT")
    #             & (df_muc18["Số lần in hỏng"] >= 2)
    #         )
    #         df_fail_print = df_muc18[mask_hong_2plus]

    #         hong_groups = (
    #             df_fail_print.groupby(["TBL", "INVT_TRAN_DATE_ONLY"])
    #             .filter(lambda g: len(g) >= 2)
    #         )

    #         df_muc18.loc[hong_groups.index, "(5) In hỏng nhiều lần trong 1 ngày"] = "X"

    #         # (6) PH nhiều lần + có in hỏng
    #         df_muc18["PH nhiều lần + có in hỏng"] = df_muc18.apply(
    #             lambda row: "X"
    #             if (row["Số lần phát hành"] > 1 and row["Số lần in hỏng"] > 0)
    #             else "",
    #             axis=1,
    #         )

    #         df_muc18.drop(columns=["INVT_TRAN_DATE_ONLY", "TBL"], inplace=True)

    #         # ==============================
    #         # 3. TẠO FILE KẾT QUẢ
    #         # ==============================
    #         output = io.BytesIO()
    #         with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
    #             df.to_excel(writer, sheet_name="tieu chi 1,2", index=False)
    #             df_muc18.to_excel(writer, sheet_name="tieu chi 3", index=False)

    #         st.success("🎯 Hoàn thành xử lý dữ liệu!")

    #         st.download_button(
    #             label="📥 Tải về file kết quả (Phoi_the_1002.xlsx)",
    #             data=output.getvalue(),
    #             file_name="Phoi_the_1002.xlsx",
    #             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    #         )
    # else:
    #     st.info("Vui lòng tải lên cả 2 file để bắt đầu.")


# =========================================================
# =========== [2] MỤC 09 – CHUYỂN TIỀN ====================
# =========================================================
def run_muc09():
    st.title("📊 Mục 09 — Tổng hợp theo PART_NAME & Mục đích (3 năm gần nhất)")
    st.caption("Chỉ hỗ trợ .xlsx (engine openpyxl).")

    DEFAULT_COLS = {
        "date":  "TRAN_DATE",
        "id":    "TRAN_ID",
        "party": "PART_NAME",
        "purpose": "PURPOSE_OF_REMITTANCE",
        "amount": "QUY_DOI_USD",
    }

    with st.expander("⚙️ Tuỳ chỉnh tên cột (nếu file của bạn khác)"):
        col_date   = st.text_input("Cột ngày giao dịch", DEFAULT_COLS["date"])
        col_id     = st.text_input("Cột mã giao dịch", DEFAULT_COLS["id"])
        col_part   = st.text_input("Cột PART_NAME", DEFAULT_COLS["party"])
        col_purp   = st.text_input("Cột PURPOSE_OF_REMITTANCE", DEFAULT_COLS["purpose"])
        col_amt    = st.text_input("Cột QUY_DOI_USD (số tiền)", DEFAULT_COLS["amount"])

    uploaded = st.file_uploader("Tải file Excel (.xlsx)", type=["xlsx"])
    run = st.button("▶️ Chạy tổng hợp")

    def read_xlsx_openpyxl(uploaded_file):
        if not uploaded_file:
            return None
        name = uploaded_file.name.lower()
        if not name.endswith(".xlsx"):
            st.error("❌ Chỉ hỗ trợ .xlsx. Hãy lưu file .xls thành .xlsx rồi tải lên.")
            return None
        try:
            return pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"Không đọc được file .xlsx: {e}")
            return None

    def build_output(df: pd.DataFrame):
        df = df.copy()
        df[col_date] = pd.to_datetime(df[col_date], errors="coerce")
        df["YEAR"]   = df[col_date].dt.year
        df[col_amt]  = pd.to_numeric(df[col_amt], errors="coerce")

        df = df.dropna(subset=[col_date, "YEAR"])
        if df.empty:
            return pd.DataFrame(), []

        df = df.drop_duplicates(subset=[col_part, col_purp, col_date, col_id])

        years = sorted(df["YEAR"].dropna().astype(int).unique())
        nam_T = years[-1]
        cac_nam = [y for y in years if y >= nam_T - 2][-3:]

        ket_qua = pd.DataFrame()
        ds_muc_dich = df[col_purp].dropna().astype(str).unique()

        for muc_dich in ds_muc_dich:
            df_md = df[df[col_purp] == muc_dich]
            for nam in cac_nam:
                df_y = df_md[df_md["YEAR"] == nam]
                if df_y.empty:
                    continue

                pivot = (
                    df_y.groupby(col_part, dropna=False)
                        .agg(
                            tong_lan_nhan=(col_id, "count"),
                            tong_tien_usd=(col_amt, "sum"),
                        )
                        .reset_index()
                )

                col_lan  = f"{muc_dich}_LAN_{nam}"
                col_tien = f"{muc_dich}_TIEN_{nam}"
                pivot.rename(
                    columns={"tong_lan_nhan": col_lan, "tong_tien_usd": col_tien},
                    inplace=True,
                )

                ket_qua = pivot if ket_qua.empty else ket_qua.merge(pivot, on=col_part, how="outer")

        if ket_qua.empty:
            return ket_qua, cac_nam

        for c in ket_qua.columns:
            if c == col_part:
                continue
            if "_LAN_" in c:
                ket_qua[c] = pd.to_numeric(ket_qua[c], errors="coerce").fillna(0).astype(int)
            elif "_TIEN_" in c:
                ket_qua[c] = pd.to_numeric(ket_qua[c], errors="coerce").fillna(0.0).astype(float)

        ket_qua = ket_qua[[col_part] + [c for c in ket_qua.columns if c != col_part]]
        return ket_qua, cac_nam

    if run:
        if not uploaded:
            st.warning("Hãy tải file .xlsx trước.")
            return

        df_raw = read_xlsx_openpyxl(uploaded)
        if df_raw is None:
            return

        required = [col_date, col_id, col_part, col_purp, col_amt]
        missing = [c for c in required if c not in df_raw.columns]
        if missing:
            st.error(f"Thiếu các cột bắt buộc: {missing}")
            return

        ket_qua, years_used = build_output(df_raw)

        if ket_qua.empty:
            st.info("Không có dữ liệu phù hợp để tổng hợp.")
        else:
            st.success(
                "Tổng hợp xong"
                + (f" cho các năm: {', '.join(map(str, years_used))}" if years_used else "")
            )
            st.dataframe(ket_qua, use_container_width=True)

            bio = io.BytesIO()
            with pd.ExcelWriter(bio, engine="openpyxl") as writer:
                ket_qua.to_excel(writer, sheet_name="tong_hop", index=False)
            st.download_button(
                "⬇️ Tải Excel tổng hợp",
                data=bio.getvalue(),
                file_name="tong_hop_chuyen_tien_Muc09.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )


# =========================================================
# =========== [3] TỜ KHAI HẢI QUAN (TKHQ) =================
# =========================================================
def smart_date_parse(series):
    """Tự động nhận diện định dạng dd-mm-yyyy hoặc mm-dd-yyyy"""
    series = series.astype(str).str.strip()

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

    return pd.to_datetime(series, errors='coerce', dayfirst=dayfirst_detected, infer_datetime_format=True)


def process_tkhq_data(df, ngay_kiem_toan):
    df.columns = df.columns.str.strip().str.upper()

    df['DECLARATION_DUE_DATE'] = smart_date_parse(df.get('DECLARATION_DUE_DATE'))
    df['DECLARATION_RECEIVED_DATE'] = smart_date_parse(df.get('DECLARATION_RECEIVED_DATE'))

    df['KHÔNG NHẬP NGÀY ĐẾN HẠN TKHQ'] = df['DECLARATION_DUE_DATE'].isna().map(lambda x: 'X' if x else '')

    df['SỐ NGÀY QUÁ HẠN TKHQ'] = df.apply(
        lambda row: (ngay_kiem_toan - row['DECLARATION_DUE_DATE']).days
        if pd.notnull(row['DECLARATION_DUE_DATE'])
        and pd.isnull(row['DECLARATION_RECEIVED_DATE'])
        and (ngay_kiem_toan - row['DECLARATION_DUE_DATE']).days > 0
        else '',
        axis=1
    )

    so_ngay_qua_han_numeric = pd.to_numeric(df['SỐ NGÀY QUÁ HẠN TKHQ'], errors='coerce')
    df['QUÁ HẠN CHƯA NHẬP TKHQ'] = so_ngay_qua_han_numeric.apply(lambda x: 'X' if pd.notnull(x) and x > 0 else '')
    df['QUÁ HẠN > 90 NGÀY CHƯA NHẬP TKHQ'] = so_ngay_qua_han_numeric.apply(lambda x: 'X' if pd.notnull(x) and x > 90 else '')

    def check_gia_han(row):
        if 'AUDIT_DATE2' in row.index and pd.notnull(row['AUDIT_DATE2']):
            return 'X'
        if 'DECLARATION_REF_NO' in row.index and isinstance(row['DECLARATION_REF_NO'], str):
            text = row['DECLARATION_REF_NO'].lower().replace(" ", "")
            if 'giahan' in text:
                return 'X'
        return ''

    df['CÓ PHÁT SINH GIA HẠN TKHQ'] = df.apply(check_gia_han, axis=1)

    return df


def run_tkhq():
    st.title("📊 Ứng dụng Phân tích Tờ khai Hải quan (TKHQ)")

    with st.sidebar:
        st.subheader("Cài đặt TKHQ (riêng phân hệ này)")
        uploaded_file = st.file_uploader("📁 Chọn file Excel TKHQ", type=['xlsx'], key="tkhq_file")
        audit_date = st.date_input("📅 Ngày kiểm toán (TKHQ)", value=datetime(2025, 5, 31), key="tkhq_date")

    if uploaded_file is not None:
        st.info(f"Đã tải lên file: **{uploaded_file.name}**")

        if st.button("🚀 Bắt đầu xử lý TKHQ", type="primary"):
            with st.spinner("Đang đọc và xử lý dữ liệu..."):
                try:
                    df_raw = pd.read_excel(uploaded_file)
                    ngay_kiem_toan_pd = pd.to_datetime(audit_date)

                    df_processed = process_tkhq_data(df_raw, ngay_kiem_toan_pd)

                    st.success("✅ Xử lý hoàn tất!")
                    st.subheader("📋 Kết quả phân tích")
                    st.dataframe(df_processed)

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
        st.info("⬆️ Vui lòng tải lên một file Excel TKHQ để bắt đầu.")


# =========================================================
# ============== [4] THẺ (1.3.2) – TIÊU CHÍ ===============
# =========================================================
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

    for c in ['NGAY_MO','NGAY_KICH_HOAT','EXPDT']:
        if c in df_muc26.columns:
            df_muc26[c] = pd.to_datetime(df_muc26[c], errors='coerce')

    df_processed = df_muc26.copy()

    # 1) TÌNH TRẠNG THẺ
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

    df_processed.drop(columns=[
        'Code_policy','POLICY_TinhTrang','TRANGTHAITHE_is_blank_orig','TRANGTHAITHE_for_merge'
    ], errors='ignore', inplace=True)

    # 2) PHÂN LOẠI CẤP HM THẺ
    df_code_policy['CODE'] = df_code_policy['CODE'].astype(str)
    df_processed['POLICY_CODE'] = df_processed['POLICY_CODE'].astype(str)

    df_processed = df_processed.merge(
        df_code_policy[['CODE','PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']],
        left_on='POLICY_CODE', right_on='CODE', how='left'
    )

    df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'] = \
        df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].fillna('Khác')

    # 3–5) DƯ NỢ THẺ (m-2, m-1, m)
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
        df_processed.drop(columns=['DU_NO_QUY_DOI','OD_ACCOUNT'], errors='ignore', inplace=True)

    # 6–7) NHÓM NỢ
    df_du_no_m['OD_ACCOUNT'] = df_du_no_m['OD_ACCOUNT'].astype(str)
    df_processed = df_processed.merge(
        df_du_no_m[['OD_ACCOUNT','NHOM_NO_OD_ACCOUNT','NHOM_NO']],
        left_on='ODACCOUNT', right_on='OD_ACCOUNT', how='left'
    )

    df_processed["NHÓM NỢ HIỆN TẠI CỦA THẺ"] = df_processed["NHOM_NO_OD_ACCOUNT"].fillna("KPS")
    df_processed["NHÓM NỢ HIỆN TẠI CỦA KH"]   = df_processed["NHOM_NO"].fillna("KPS")

    df_processed.drop(columns=['NHOM_NO_OD_ACCOUNT','NHOM_NO','OD_ACCOUNT'], errors='ignore', inplace=True)

    # 8) DƯ NỢ VAY CỦA KH
    df_crm4 = df_crm4.copy()
    df_crm4['CIF_KH_VAY'] = df_crm4['CIF_KH_VAY'].astype(str)
    df_processed['CUSTSEQ'] = df_processed['CUSTSEQ'].astype(str)

    df_crm4_cho_vay = df_crm4[df_crm4['LOAI'] == 'Cho vay'].copy()
    df_crm4_cho_vay['DU_NO_PHAN_BO_QUY_DOI'] = pd.to_numeric(
        df_crm4_cho_vay['DU_NO_PHAN_BO_QUY_DOI'], errors='coerce'
    ).fillna(0)

    df_tong_du_no = (
        df_crm4_cho_vay.groupby('CIF_KH_VAY')['DU_NO_PHAN_BO_QUY_DOI']
        .sum().reset_index().rename(columns={'DU_NO_PHAN_BO_QUY_DOI':'DƯ NỢ VAY CỦA KH'})
    )

    df_processed = df_processed.merge(df_tong_du_no, left_on='CUSTSEQ', right_on='CIF_KH_VAY', how='left')
    df_processed['DƯ NỢ VAY CỦA KH'] = df_processed['DƯ NỢ VAY CỦA KH'].fillna("KPS")
    df_processed.drop(columns=['CIF_KH_VAY'], errors='ignore', inplace=True)

    # 9) SỐ LƯỢNG TSBĐ – Mục 17
    df_muc17['C04'] = df_muc17['C04'].astype(str)
    df_muc17['C01'] = df_muc17['C01'].astype(str)
    df_processed['CUSTSEQ'] = df_processed['CUSTSEQ'].astype(str)

    tsbd_count = df_muc17.groupby('C04')['C01'].nunique().reset_index()
    tsbd_count.columns = ['C04','SL_tam']

    df_processed = df_processed.merge(tsbd_count, left_on='CUSTSEQ', right_on='C04', how='left')
    df_processed['SỐ LƯỢNG TSBĐ'] = df_processed['SL_tam'].fillna("KPS")
    df_processed.drop(columns=['SL_tam','C04'], inplace=True, errors='ignore')

    # 10) TRỊ GIÁ TSBĐ – CRM4
    df_crm4['SECU_VALUE'] = pd.to_numeric(df_crm4['SECU_VALUE'], errors='coerce').fillna(0)
    giatri = df_crm4.groupby('CIF_KH_VAY')['SECU_VALUE'].sum().reset_index()
    giatri.columns = ['CIF_KH_VAY','TRỊ GIÁ TSBĐ']

    df_processed = df_processed.merge(giatri, left_on='CUSTSEQ', right_on='CIF_KH_VAY', how='left')
    df_processed['TRỊ GIÁ TSBĐ'] = df_processed['TRỊ GIÁ TSBĐ'].fillna("KPS")
    df_processed.drop(columns=['CIF_KH_VAY'], inplace=True, errors='ignore')

    # 11–12) SỐ LƯỢNG TKTG CKH – SỐ DƯ
    df_hdv_ckh['CUSTSEQ'] = df_hdv_ckh['CUSTSEQ'].astype(str)

    g1 = df_hdv_ckh.groupby('CUSTSEQ')['IDXACNO'].count().reset_index()
    g1.columns = ['CUSTSEQ','SỐ LƯỢNG TKTG CKH']
    df_processed = df_processed.merge(g1, on='CUSTSEQ', how='left')
    df_processed['SỐ LƯỢNG TKTG CKH'] = df_processed['SỐ LƯỢNG TKTG CKH'].fillna('KPS')

    g2 = df_hdv_ckh.groupby('CUSTSEQ')['CURBAL_VN'].sum().reset_index()
    g2.columns = ['CUSTSEQ','SỐ DƯ TÀI KHOẢN']
    df_processed = df_processed.merge(g2, on='CUSTSEQ', how='left')
    df_processed['SỐ DƯ TÀI KHOẢN'] = df_processed['SỐ DƯ TÀI KHOẢN'].fillna('KPS')

    # 13) THẺ CÓ HẠN MỨC CAO
    df_processed['PPSCRLMT_numeric'] = pd.to_numeric(df_processed['PPSCRLMT'], errors='coerce')
    df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)'] = np.where(
        df_processed['PPSCRLMT_numeric'] > 30000000, 'X',''
    )

    # 16) THẺ CHƯA ĐÓNG
    df_processed['THẺ CHƯA ĐÓNG'] = np.where(
        ~df_processed['TÌNH TRẠNG THẺ'].isin(['Chấm dứt sử dụng','Yêu cầu đóng thẻ']),
        'X',''
    )

    # 17)
    df_processed['THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO'] = ''
    dk17 = (
        df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ'].isin(
            ['Theo thu nhập/tín chấp','Theo điều kiện về TKTG CKH']
        )
        &
        (df_processed['THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)']=='X')
    )
    df_processed.loc[dk17, 'THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO'] = 'X'

    # 18–20
    df_processed['KH KHÔNG CÓ/KHÔNG CÒN TSBĐ'] = \
        df_processed['SỐ LƯỢNG TSBĐ'].apply(lambda x: 'X' if str(x) in ['0','KPS'] else '')

    df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG'] = \
        df_processed.apply(lambda r:
                           'X' if (
                               r['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']=='Theo khoản vay/Có TSBĐ'
                               and r['KH KHÔNG CÓ/KHÔNG CÒN TSBĐ']=='X'
                               and r['THẺ CHƯA ĐÓNG']=='X'
                           ) else '', axis=1)

    df_processed['DƯ NỢ THẺ HIỆN TẠI'] = pd.to_numeric(df_processed['DƯ NỢ THẺ HIỆN TẠI'], errors='coerce')

    df_processed['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG VÀ CÓ DƯ NỢ'] = \
        df_processed.apply(lambda r:
        'X' if r['KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG']=='X'
              and r['DƯ NỢ THẺ HIỆN TẠI']>0
        else '', axis=1)

    df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'] = pd.to_numeric(
        df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'], errors='coerce'
    )
    df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'] = pd.to_numeric(
        df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'], errors='coerce'
    )

    df_processed['THẺ QUÁ HẠN'] = \
        np.where(df_processed['NHÓM NỢ HIỆN TẠI CỦA THẺ'].isin([2,3,4,5]),'X','')

    df_processed['KH QUÁ HẠN'] = \
        np.where(df_processed['NHÓM NỢ HIỆN TẠI CỦA KH'].isin([2,3,4,5]),'X','')

    # 21–22
    df_processed["PPSCRLMT"] = pd.to_numeric(df_processed["PPSCRLMT"], errors="coerce")
    df_processed["SỐ DƯ TÀI KHOẢN"] = pd.to_numeric(df_processed["SỐ DƯ TÀI KHOẢN"], errors="coerce")

    df_processed['KH KHÔNG CÓ/TẤT TOÁN TKTG CKH NHƯNG THẺ CHƯA ĐÓNG'] = \
        np.where(
            (df_processed['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']=='Theo điều kiện về TKTG CKH')
            &
            (df_processed['SỐ LƯỢNG TKTG CKH'].astype(str).isin(['0','KPS']))
            &
            (df_processed['THẺ CHƯA ĐÓNG']=='X'),
            'X',''
        )

    df_processed["SỐ DƯ TKTG CKH < HẠN MỨC"] = \
        df_processed.apply(lambda r:
        'X' if (
            r['PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ']=='Theo điều kiện về TKTG CKH'
            and r['THẺ CHƯA ĐÓNG']=='X'
            and (
                pd.isna(r['SỐ DƯ TÀI KHOẢN']) or
                r['SỐ DƯ TÀI KHOẢN'] < r['PPSCRLMT']
            )
        )
        else '', axis=1)

    return df_processed


def run_the():
    st.title("📌 Tiêu chí Thẻ (1.3.2)")

    chi_nhanh = st.text_input("Nhập chi nhánh hoặc mã SOL:", "")

    uploaded_files_the = {}

    file_list = {
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

    for key, label in file_list.items():
        uploaded_files_the[key] = st.file_uploader(
            f"Upload file {label}", type=["xlsx","xls"], key=f"the_{key}"
        )

    if st.button("▶ Chạy xử lý Thẻ (1.3.2)"):
        missing = [k for k,v in uploaded_files_the.items() if v is None]
        if missing:
            st.error(f"Thiếu file: {', '.join(missing)}")
        else:
            dfs = {k: pd.read_excel(v) for k,v in uploaded_files_the.items()}
            df_the_result = process_the(
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
            st.success("✔ Xử lý Thẻ hoàn tất!")
            st.dataframe(df_the_result.head(200), use_container_width=True)

            buf = io.BytesIO()
            df_the_result.to_excel(buf, index=False)
            st.download_button(
                "⬇ Tải file kết quả Thẻ (1.3.2)",
                data=buf.getvalue(),
                file_name="ket_qua_the_132.xlsx"
            )


# =========================================================
# ================ [5] POS (6.2) – TIÊU CHÍ ===============
# =========================================================
def process_pos(df_pos_raw, df_trans_raw, start_date, end_date):
    df_pos = df_pos_raw.copy()
    df_trans = df_trans_raw.copy()

    # Làm sạch MERCHANT_CIF
    s = df_pos['MERCHANT_CIF'].fillna('').astype(str).str.strip()
    s = s.str.replace(r'^[A-Za-z]', '', regex=True)
    s = s.str.replace(r'\D+', '', regex=True).str[-9:]
    df_pos['MERCHANT_CIF'] = s.mask(s == '', None)

    df_pos['MID'] = df_pos['MID'].astype(str)

    df_pos['DATE_OPEN_MID'] = pd.to_datetime(df_pos['DATE_OPEN_MID'], errors='coerce')

    df_trans['TRANS_AMT'] = (
        df_trans['TRANS_AMT'].astype(str)
        .str.replace(r'[^\d\.\-]', '', regex=True)
        .replace({'': '0'})
        .astype(float)
    )
    df_trans['TRANS_DATE'] = pd.to_datetime(df_trans['TRANS_DATE'], errors='coerce')
    df_trans['MERCHANT_ID'] = df_trans['MERCHANT_ID'].astype(str)

    df_3m = df_trans[
        (df_trans['TRANS_DATE'] >= start_date)
        &
        (df_trans['TRANS_DATE'] <= end_date)
    ]

    g3 = df_3m.groupby('MERCHANT_ID')['TRANS_AMT'].sum().reset_index()
    g3.columns = ['MID','DSỐ_3_THÁNG_GẦN_NHẤT']

    df_pos = df_pos.merge(g3, on='MID', how='left')
    df_pos['DSỐ_3_THÁNG_GẦN_NHẤT'] = df_pos['DSỐ_3_THÁNG_GẦN_NHẤT'].fillna(0)

    df_pos['DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT'] = df_pos['DSỐ_3_THÁNG_GẦN_NHẤT'] / 3

    df_pos['POS_ĐANG_HOẠT_ĐỘNG'] = df_pos['DEVICE_STATUS'].apply(
        lambda x: 'X' if str(x)=='Device OK' else ''
    )

    df_pos['POS KPS DSỐ TRONG 3 THÁNG VÀ CHƯA ĐÓNG'] = df_pos.apply(
        lambda r: 'X' if r['POS_ĐANG_HOẠT_ĐỘNG']=='X' and r['DSỐ_3_THÁNG_GẦN_NHẤT']==0
        else '', axis=1
    )

    df_pos['POS CÓ DSỐ BQ TRONG 3 THÁNG < 20 TRĐ VÀ CHƯA ĐÓNG'] = df_pos.apply(
        lambda r: 'X' if r['POS_ĐANG_HOẠT_ĐỘNG']=='X' and r['DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT'] < 20000000
        else '', axis=1
    )

    active = df_pos[df_pos['POS_ĐANG_HOẠT_ĐỘNG']=='X']
    multi = active.groupby('MERCHANT_CIF').filter(lambda g: len(g)>=2)['MERCHANT_CIF'].unique()

    df_pos['ĐVCNT CÓ NHIỀU POS ĐANG HOẠT ĐỘNG (>2)'] = \
        df_pos['MERCHANT_CIF'].apply(lambda x: 'X' if x in multi else '')

    return df_pos


def run_pos():
    st.title("📌 Tiêu chí POS (6.2)")

    df_pos_raw = st.file_uploader("Upload file POS (MUC51_1600)", type=["xlsx","xls"], key="pos_pos")
    df_trans_raw = st.file_uploader("Upload file giao dịch POS (6.2a)", type=["xlsx","xls","csv"], key="pos_trans")

    colA, colB = st.columns(2)
    with colA:
        start_date = st.date_input("Ngày bắt đầu thời hiệu kiểm toán", key="pos_start")
    with colB:
        end_date = st.date_input("Ngày kết thúc thời hiệu kiểm toán", key="pos_end")

    if st.button("▶ Chạy xử lý POS (6.2)"):
        if df_pos_raw is None or df_trans_raw is None:
            st.error("Thiếu file POS hoặc giao dịch!")
        else:
            df_pos_df = pd.read_excel(df_pos_raw)
            df_trans_df = pd.read_excel(df_trans_raw)

            df_pos_result = process_pos(
                df_pos_df,
                df_trans_df,
                pd.Timestamp(start_date),
                pd.Timestamp(end_date)
            )

            st.success("✔ Xử lý POS hoàn tất!")
            st.dataframe(df_pos_result.head(200), use_container_width=True)

            buf2 = io.BytesIO()
            df_pos_result.to_excel(buf2, index=False)
            st.download_button(
                "⬇ Tải file kết quả POS (6.2)",
                data=buf2.getvalue(),
                file_name="ket_qua_pos_62.xlsx"
            )


# =========================================================
# ============= [6] DVKH – 5 TIÊU CHÍ =====================
# =========================================================
def run_dvkh():
    st.title("📌 ỨNG DỤNG XỬ LÝ DỮ LIỆU DVKH – 5 TIÊU CHÍ")

    tab1, tab2 = st.tabs(["📥 Nhập & Xử lý dữ liệu", "📤 Xuất kết quả"])

    # ================= TAB 1 ===========================================
    with tab1:
        st.header("1️⃣ Upload dữ liệu đầu vào")

        file_dksms = st.file_uploader("Upload Muc14_DKSMS.txt", type=["txt"])
        file_scm10 = st.file_uploader("Upload Muc14_SCM010.xlsx", type=["xlsx"])
        file_42a = st.file_uploader(
            "Upload HDV_CHITIET_KKH_*.xls (4.2.a)",
            type=["xls"],
            accept_multiple_files=True,
        )
        file_42b = st.file_uploader("Upload BC_LAY_CHARGELEVELCODE_THEO_KHCN.xlsx", type=["xlsx"])
        file_42c = st.file_uploader("Upload 10_DanhSachNhanSu.xlsx", type=["xlsx"])
        file_42d = st.file_uploader("Upload DS Nghi Viec.xlsx", type=["xlsx"])
        file_mapping = st.file_uploader("Upload Mapping_1405.xlsx", type=["xlsx"])

        chi_nhanh = st.text_input(
            "Nhập tên chi nhánh hoặc mã SOL (VD: HANOI, 001)"
        ).upper()

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

            st.session_state["df_sms"] = df_sms
            st.session_state["df_uyquyen"] = df_uyquyen
            st.session_state["df_tc3"] = df_tc3
            st.session_state["df_42a"] = df_42a
            st.session_state["df_map"] = df_map

    # ================= TAB 2 – EXPORT ==================================
    with tab2:
        st.header("📤 Xuất file Excel theo 5 tiêu chí")

        if "df_sms" not in st.session_state:
            st.warning("⚠️ Bạn cần chạy xử lý ở tab 1 trước!")
            return

        df_sms = st.session_state["df_sms"]
        df_uyquyen = st.session_state["df_uyquyen"]
        df_tc3 = st.session_state["df_tc3"]
        df_42a = st.session_state["df_42a"]
        df_map = st.session_state["df_map"]

        output = io.BytesIO()

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


# =========================================================
# CHỌN MODULE & CHẠY
# =========================================================
if module.startswith("[1]"):
    run_phoi_the()
elif module.startswith("[2]"):
    run_muc09()
elif module.startswith("[3]"):
    run_tkhq()
elif module.startswith("[4]"):
    run_the()
elif module.startswith("[5]"):
    run_pos()
elif module.startswith("[6]"):
    run_dvkh()
