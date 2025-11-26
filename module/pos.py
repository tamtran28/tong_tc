# =========================================================
# module_pos.py — Xử lý POS (6, 7, 8)
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io


# ------------------------------
# Xuất file excel
# ------------------------------
def df_to_excel_bytes(df, sheet="DATA"):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet[:31], index=False)
    buffer.seek(0)
    return buffer


# ------------------------------
# Chuẩn hóa 6.2a
# ------------------------------
def standardize_6_2a_two_files(file_before, file_after):

    df_before = pd.read_excel(file_before, dtype=str)
    df_after = pd.read_excel(file_after, dtype=str)

    map_before = {
        "MACN_POS":"BRANCH_CODE",
        "IDPOS":"MERCHANT_ID",
        "TENPOS":"MERCHANT_NAME",
        "TRANDT":"TRANS_DATE",
        "TRANAMT_QD":"TRANS_AMT"
    }

    map_after = {
        "BRANCH_CODE":"BRANCH_CODE",
        "MERCHANT_ID":"MERCHANT_ID",
        "MERCHANT_NAME":"MERCHANT_NAME",
        "TRANS_DATE":"TRANS_DATE",
        "TRANS_AMT":"TRANS_AMT"
    }

    df1 = df_before[[c for c in map_before if c in df_before.columns]].rename(columns=map_before)
    df2 = df_after[[c for c in map_after if c in df_after.columns]].rename(columns=map_after)

    df = pd.concat([df1, df2], ignore_index=True)
    df["TRANS_DATE"] = pd.to_datetime(df["TRANS_DATE"], errors="coerce")
    return df


# ------------------------------
# XỬ LÝ POS CHÍNH
# ------------------------------
def process_pos_only(file_before_2305, file_after_2305, file_6_2b,
                     start_audit, end_audit):

    df_trans = standardize_6_2a_two_files(file_before_2305, file_after_2305)

    df_62b = pd.read_excel(file_6_2b)

    df_62b["MID"] = df_62b["MID"].astype(str)
    df_trans["MERCHANT_ID"] = df_trans["MERCHANT_ID"].astype(str)

    def cal_rev(df, df_pos, d1, d2):
        mask = (df["TRANS_DATE"] >= d1) & (df["TRANS_DATE"] <= d2)
        g = df.loc[mask].groupby("MERCHANT_ID")["TRANS_AMT"].sum().reset_index()
        g = g.rename(columns={"MERCHANT_ID":"MID", "TRANS_AMT":"REV"})
        return df_pos[["MID"]].merge(g, on="MID", how="left")["REV"].fillna(0)

    y = end_audit.year
    df_62b["DS_T2"] = cal_rev(df_trans, df_62b, datetime(y-2,1,1), datetime(y-2,12,31))
    df_62b["DS_T1"] = cal_rev(df_trans, df_62b, datetime(y-1,1,1), datetime(y-1,12,31))
    df_62b["DS_T"] = cal_rev(df_trans, df_62b, datetime(y,1,1), datetime(y,12,31))
    df_62b["TONG_3N"] = df_62b["DS_T2"] + df_62b["DS_T1"] + df_62b["DS_T"]

    # 3 tháng gần nhất
    start_3m = (end_audit.replace(day=1) - relativedelta(months=2)).replace(day=1)
    df_62b["DS_3T"] = cal_rev(df_trans, df_62b, start_3m, end_audit)
    df_62b["DSBQ_3T"] = df_62b["DS_3T"] / 3

    df_62b["POS_ACTIVE"] = np.where(df_62b["DEVICE_STATUS"]=="Device OK","X","")

    return df_62b


# =========================================================
# MODULE STREAMLIT
# =========================================================
def run_module_pos():

    st.title("🏧 TIÊU CHÍ POS – 6,7,8")

    start_date = st.date_input("Ngày bắt đầu THKT", value=date(2025,1,1))
    end_date = st.date_input("Ngày kết thúc THKT", value=date(2025,10,31))

    col1,col2 = st.columns(2)
    with col1:
        file_old = st.file_uploader("6.2a – File TRƯỚC 23/05", type=["xls","xlsx"])
    with col2:
        file_new = st.file_uploader("6.2a – File SAU 23/05", type=["xls","xlsx"])

    file_6_2b = st.file_uploader("6.2b – MUC51_1600", type=["xls","xlsx"])

    run_button = st.button("🚀 Chạy POS")

    if run_button:
        if not file_old or not file_new or not file_6_2b:
            st.error("Thiếu file POS!")
            return

        with st.spinner("Đang xử lý…"):
            df_pos = process_pos_only(
                file_old, file_new, file_6_2b,
                start_audit=datetime.combine(start_date, datetime.min.time()),
                end_audit=datetime.combine(end_date, datetime.min.time())
            )

        st.success("✔ Xong")
        st.dataframe(df_pos, use_container_width=True)

        st.download_button(
            "⬇ Tải Excel POS",
            data=df_to_excel_bytes(df_pos, "POS"),
            file_name="KQ_POS.xlsx"
        )
