import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import datetime

from module.error_utils import ensure_required_columns, render_error, UserFacingError

# ==========================================================
#      MODULE XỬ LÝ HDV – 3 TIÊU CHÍ
# ==========================================================

def download_excel(df, filename):
    buffer = BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    st.download_button(
        label="📥 Tải xuống " + filename,
        data=buffer,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def run_hdv():

    st.header("💳 PHÂN HỆ HDV – 3 TIÊU CHÍ")

    st.markdown("""
    Gồm:
    - **TC1**: HDV CKH + so sánh FTP + LS thực trả  
    - **TC2**: Xếp hạng KH theo số dư  
    - **TC3**: Giao dịch tiền gửi rút – mở/rút trong ngày  
    """)

    tab1, tab2, tab3 = st.tabs(["📌 TIÊU CHÍ 1", "📌 TIÊU CHÍ 2", "📌 TIÊU CHÍ 3"])

    # ================================================================
    #                        TIÊU CHÍ 1
    # ================================================================
    with tab1:
        st.subheader("📌 TIÊU CHÍ 1 – HDV CKH + FTP + LS THỰC TRẢ")

        hdv_files = st.file_uploader("📁 Tải các file HDV CKH (*.xls, *.xlsx)", type=['xls', 'xlsx'], accept_multiple_files=True)
        ftp_files = st.file_uploader("📁 Tải các file FTP (*.xls, *.xlsx)", type=['xls','xlsx'], accept_multiple_files=True)
        tt_file = st.file_uploader("📁 Tải file Lãi suất thực trả", type=['xls','xlsx'])

        chi_nhanh_tc1 = st.text_input("🔍 Nhập mã SOL", "").upper().strip()

        if st.button("🚀 Chạy TIÊU CHÍ 1"):
            if not (hdv_files and ftp_files and tt_file):
                st.error("⚠ Vui lòng tải đầy đủ 3 loại file!")
            else:
                try:
                    # Các cột cần dùng
                    cols_ckh = [
                        'BRCD','DEPTCD','CUST_TYPE','NMLOC','CUSTSEQ','BIRTH_DAY','IDXACNO',
                        'SCHM_NAME','TERM_DAYS','GL_SUB','CCYCD','CURBAL_NT','CURBAL_VN',
                        'OPNDT_FIRST','OPNDT_EFFECT','MATDT','LS_GHISO','LS_CONG_BO',
                        'PROMO_CD','KH_VIP','CIF_OPNDT','DP_MTHS','DP_DAYS','PROMO_NM','PHANKHUC_KH'
                    ]

                    df_ckh = pd.concat([pd.read_excel(f, dtype=str) for f in hdv_files], ignore_index=True)
                    ensure_required_columns(df_ckh, cols_ckh)
                    df_ckh = df_ckh[cols_ckh]

                    cols_ftp = ['CUSTSEQ','NMLOC','IDXACNO','KY_HAN','LS_FTP']
                    df_ftp = pd.concat([pd.read_excel(f, dtype=str) for f in ftp_files], ignore_index=True)
                    ensure_required_columns(df_ftp, cols_ftp)
                    df_ftp = df_ftp[cols_ftp]

                    # Lọc đúng chi nhánh
                    df_filtered = df_ckh[df_ckh['BRCD'].str.upper().str.contains(chi_nhanh_tc1)]

                    df_tt_raw = pd.read_excel(tt_file, dtype=str)
                    ensure_required_columns(
                        df_tt_raw,
                        [
                            'Số tài khoản',
                            'Lãi suất thực trả',
                        ],
                    )

                    df_tt = df_tt_raw.rename(
                        columns={'Số tài khoản':'IDXACNO','Lãi suất thực trả':'LS_THUC_TRA'}
                    )

                    df_merge = df_filtered.merge(
                        df_ftp[['IDXACNO','LS_FTP']].drop_duplicates(),
                        on="IDXACNO",
                        how="left"
                    )
                    df_merge = df_merge.merge(df_tt, on="IDXACNO", how="left")

                    df_merge["LS_GHISO"] = pd.to_numeric(df_merge["LS_GHISO"], errors="coerce")
                    df_merge["LS_CONG_BO"] = pd.to_numeric(df_merge["LS_CONG_BO"], errors="coerce")
                    df_merge["LS_THUC_TRA"] = pd.to_numeric(df_merge["LS_THUC_TRA"], errors="coerce")
                    df_merge["LS_FTP"] = pd.to_numeric(df_merge["LS_FTP"], errors="coerce")

                    df_merge["LSGS ≠ LSCB"] = (df_merge["LS_GHISO"] != df_merge["LS_CONG_BO"]).map({True:"X",False:""})
                    df_merge["Không có LS trình duyệt"] = df_merge["LS_THUC_TRA"].isna().map({True:"X",False:""})

                    df_merge["LSGS > FTP"] = (
                        df_merge["LS_GHISO"] > df_merge["LS_FTP"]
                    ).map({True:"X",False:""})

                    st.success("✔ Tiêu chí 1 hoàn tất!")
                    st.dataframe(df_merge, use_container_width=True)

                    download_excel(df_merge, "TC1.xlsx")
                except UserFacingError as exc:
                    render_error(str(exc))
                except Exception as exc:
                    render_error(
                        "Không thể xử lý Tiêu chí 1. Vui lòng kiểm tra định dạng và cột dữ liệu trong các file CKH/FTP/LS.",
                        exc,
                    )

    # ================================================================
    #                        TIÊU CHÍ 2
    # ================================================================
    with tab2:
        st.subheader("📌 TIÊU CHÍ 2 – Xếp hạng KH theo số dư")

        ckh_tc2 = st.file_uploader("📁 Tải file HDV CHI TIẾT CKH", type=['xls','xlsx'], accept_multiple_files=True)
        kkh_tc2 = st.file_uploader("📁 Tải file HDV CHI TIẾT KKH", type=['xls','xlsx'], accept_multiple_files=True)

        chi_nhanh_tc2 = st.text_input("🔍 Nhập mã SOL hoặc tên chi nhánh (TC2)", "").upper().strip()

        if st.button("🚀 Chạy TIÊU CHÍ 2"):
            if not (ckh_tc2 and kkh_tc2):
                st.error("⚠ Vui lòng tải file CKH và KKH!")
            else:
                try:
                    cols = [
                        'BRCD','DEPTCD','CUST_TYPE','CUSTSEQ','NMLOC','BIRTH_DAY','IDXACNO',
                        'SCHM_NAME','TERM_DAYS','GL_SUB','CCYCD','CURBAL_NT','CURBAL_VN',
                        'OPNDT_FIRST','OPNDT_EFFECT','MATDT','LS_GHISO','LS_CONG_BO','PROMO_CD',
                        'KH_VIP','CIF_OPNDT'
                    ]

                    df_ckh2 = pd.concat([pd.read_excel(f, dtype=str) for f in ckh_tc2], ignore_index=True)
                    df_kkh2 = pd.concat([pd.read_excel(f, dtype=str) for f in kkh_tc2], ignore_index=True)

                    ensure_required_columns(df_ckh2, cols)
                    ensure_required_columns(df_kkh2, cols)

                    df_ckh2 = df_ckh2[cols]
                    df_kkh2 = df_kkh2[cols]

                    df_all = pd.concat([df_ckh2, df_kkh2], ignore_index=True)
                    df_filtered = df_all[df_all["BRCD"].str.upper().str.contains(chi_nhanh_tc2)]

                    df_filtered["CURBAL_VN"] = pd.to_numeric(df_filtered["CURBAL_VN"], errors='coerce')

                    df_sum = df_filtered.groupby("CUSTSEQ", as_index=False)["CURBAL_VN"].sum().rename(columns={"CURBAL_VN":"SỐ DƯ"})
                    df_tonghop = df_filtered.drop_duplicates("CUSTSEQ").merge(df_sum, on="CUSTSEQ", how="left")

                    today = pd.Timestamp.today().normalize()
                    df_tonghop["BIRTH_DAY"] = pd.to_datetime(df_tonghop["BIRTH_DAY"], errors='coerce')

                    mask = df_tonghop["CUST_TYPE"]=="KHCN"
                    df_tonghop.loc[mask,"ĐỘ TUỔI"] = df_tonghop.loc[mask,"BIRTH_DAY"].apply(
                        lambda x: today.year - x.year - ((today.month, today.day) < (x.month, x.day)) if pd.notnull(x) else None
                    )

                    df_tonghop["RANK_RAW"] = df_tonghop.groupby("CUST_TYPE")["SỐ DƯ"].rank(method="min", ascending=False)

                    for t in ["KHDN","KHCN"]:
                        for n in [10,15,20]:
                            df_tonghop[f"TOP{n}_{t}"] = df_tonghop.apply(
                                lambda x: "X" if x["CUST_TYPE"]==t and x["RANK_RAW"]<=n else "", axis=1
                            )

                    df_tonghop["RANK"] = df_tonghop["RANK_RAW"].apply(lambda x: int(x) if x<=20 else "")

                    df_final = df_tonghop.rename(columns={
                        "BRCD":"SOL","CUST_TYPE":"LOAI KH","CUSTSEQ":"CIF","NMLOC":"HO TEN",
                        "BIRTH_DAY":"NGAY SINH/NGAY TL","KH_VIP":"KH VIP"
                    })

                    st.success("✔ Tiêu chí 2 hoàn tất!")
                    st.dataframe(df_final, use_container_width=True)

                    download_excel(df_final, "TC2.xlsx")
                except UserFacingError as exc:
                    render_error(str(exc))
                except Exception as exc:
                    render_error(
                        "Không thể xử lý Tiêu chí 2. Vui lòng kiểm tra định dạng và cột dữ liệu trong file CKH/KKH.",
                        exc,
                    )

    # ================================================================
    #                        TIÊU CHÍ 3
    # ================================================================
    with tab3:
        st.subheader("📌 TIÊU CHÍ 3 – Giao dịch tiền gửi rút")

        tc3_file = st.file_uploader("📁 Tải file giao dịch (Mục 11)", type=['xls','xlsx'])
        chi_nhanh_tc3 = st.text_input("🔍 Nhập mã SOL hoặc tên chi nhánh (TC3)", "").upper().strip()

        if st.button("🚀 Chạy TIÊU CHÍ 3"):
            if not tc3_file:
                st.error("⚠ Vui lòng tải file TC3!")
            else:
                try:
                    df = pd.read_excel(tc3_file, dtype=str)
                    ensure_required_columns(
                        df,
                        [
                            "NGAY_HACH_TOAN",
                            "ACCT_OPN_DATE",
                            "PART_CLOSE_AMT",
                            "SOL_ID",
                        ],
                    )

                    df["NGAY_HACH_TOAN"] = pd.to_datetime(df["NGAY_HACH_TOAN"], errors='coerce')
                    df["ACCT_OPN_DATE"] = pd.to_datetime(df["ACCT_OPN_DATE"], errors='coerce')
                    df["PART_CLOSE_AMT"] = pd.to_numeric(df["PART_CLOSE_AMT"], errors='coerce')

                    df = df[df["SOL_ID"].str.upper().str.contains(chi_nhanh_tc3)]

                    df["CHENH_LECH_NGAY"] = (df["NGAY_HACH_TOAN"] - df["ACCT_OPN_DATE"]).dt.days

                    df["MO_RUT_CUNG_NGAY"] = df["CHENH_LECH_NGAY"].apply(lambda x: "X" if x==0 else "")
                    df["MO_RUT_1_3_NGAY"] = df["CHENH_LECH_NGAY"].apply(lambda x: "X" if 0<x<=3 else "")
                    df["MO_RUT_4_7_NGAY"] = df["CHENH_LECH_NGAY"].apply(lambda x: "X" if 4<=x<=7 else "")
                    df["GD_LON_HON_1TY"] = df["PART_CLOSE_AMT"].apply(lambda x: "X" if x>1_000_000_000 else "")

                    today = pd.Timestamp.today().normalize()
                    df["TRONG_THOI_HIEU_CAMERA"] = df["NGAY_HACH_TOAN"].apply(lambda x: "X" if (today-x).days<=90 else "")

                    st.success("✔ Tiêu chí 3 hoàn tất!")
                    st.dataframe(df, use_container_width=True)

                    download_excel(df, "TC3.xlsx")
                except UserFacingError as exc:
                    render_error(str(exc))
                except Exception as exc:
                    render_error(
                        "Không thể xử lý Tiêu chí 3. Vui lòng kiểm tra định dạng file Mục 11 và các cột ngày/số tiền.",
                        exc,
                    )

