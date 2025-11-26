# import streamlit as st
# import pandas as pd
# import numpy as np
# from datetime import datetime, date
# import io

# st.set_page_config(page_title="TIÊU CHÍ THẺ & POS", layout="wide")

# # ===================================================================
# # HÀM XUẤT EXCEL
# # ===================================================================
# def df_to_excel_bytes(df, sheet="DATA"):
#     buffer = io.BytesIO()
#     with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
#         df.to_excel(writer, index=False, sheet_name=sheet)
#     buffer.seek(0)
#     return buffer


# # ===================================================================
# # =====================   MODULE THẺ 1.3.2   ========================
# # ===================================================================
# def process_the(df_muc26, df_du_no_m, df_du_no_m1, df_du_no_m2,
#                 df_code_tinh_trang_the, df_code_policy, df_hdv_ckh):
#     """ Xử lý full tiêu chí thẻ """

#     df = df_muc26.copy()

#     # Chuẩn hóa ngày
#     for c in ["NGAY_MO", "NGAY_KICH_HOAT", "EXPDT"]:
#         if c in df.columns:
#             df[c] = pd.to_datetime(df[c], errors="coerce")

#     # ============================================
#     # (1) TÌNH TRẠNG THẺ
#     # ============================================
#     df_code_tinh_trang_the["Code_policy"] = df_code_tinh_trang_the["Code"].astype(str)
#     df["TRANGTHAITHE"] = df["TRANGTHAITHE"].astype(str)

#     df = df.merge(
#         df_code_tinh_trang_the[["Code_policy", "Tình trạng thẻ"]].rename(
#             columns={"Tình trạng thẻ": "POLICY_TinhTrang"}
#         ),
#         left_on="TRANGTHAITHE",
#         right_on="Code_policy",
#         how="left"
#     )

#     df["TÌNH TRẠNG THẺ"] = df["POLICY_TinhTrang"].fillna("Khác")

#     # ============================================
#     # (2) GỘP POLICY
#     # ============================================
#     df["POLICY_CODE"] = df["POLICY_CODE"].astype(str)
#     df_code_policy["CODE"] = df_code_policy["CODE"].astype(str)

#     df = df.merge(
#         df_code_policy[["CODE", "PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"]],
#         left_on="POLICY_CODE",
#         right_on="CODE",
#         how="left"
#     )

#     df["PHÂN LOẠI CẤP HM THẺ"] = df["PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"].fillna("Khác")

#     # ============================================
#     # (3)–(7) DƯ NỢ VÀ NHÓM NỢ
#     # ============================================
#     def merge_du_no(df, df_du, col_new):
#         if df_du is not None and "DU_NO_QUY_DOI" in df_du.columns:
#             df_du["OD_ACCOUNT"] = df_du["OD_ACCOUNT"].astype(str)
#             df = df.merge(
#                 df_du[["OD_ACCOUNT", "DU_NO_QUY_DOI"]],
#                 left_on="ODACCOUNT",
#                 right_on="OD_ACCOUNT",
#                 how="left"
#             )
#             df[col_new] = df["DU_NO_QUY_DOI"].fillna("KPS")
#             df.drop(columns=["DU_NO_QUY_DOI", "OD_ACCOUNT"], inplace=True)
#         else:
#             df[col_new] = "KPS"
#         return df

#     df = merge_du_no(df, df_du_no_m2, "DƯ NỢ THẺ 02 THÁNG TRƯỚC")
#     df = merge_du_no(df, df_du_no_m1, "DƯ NỢ THẺ 01 THÁNG TRƯỚC")
#     df = merge_du_no(df, df_du_no_m,  "DƯ NỢ THẺ HIỆN TẠI")

#     # ============================================
#     # (11)-(12) TKTG CKH
#     # ============================================
#     df["CUSTSEQ"] = df["CUSTSEQ"].astype(str)
#     df_hdv_ckh["CUSTSEQ"] = df_hdv_ckh["CUSTSEQ"].astype(str)

#     # Số lượng
#     count_ckh = df_hdv_ckh.groupby("CUSTSEQ")["IDXACNO"].count().reset_index()
#     count_ckh.columns = ["CUSTSEQ", "SO_LUONG"]

#     df = df.merge(count_ckh, on="CUSTSEQ", how="left")
#     df["SỐ LƯỢNG TKTG CKH"] = df["SO_LUONG"].fillna("KPS")
#     df.drop(columns=["SO_LUONG"], inplace=True)

#     # Số dư
#     sodu = df_hdv_ckh.groupby("CUSTSEQ")["CURBAL_VN"].sum().reset_index()
#     sodu.columns = ["CUSTSEQ", "SODU"]

#     df = df.merge(sodu, on="CUSTSEQ", how="left")
#     df["SỐ DƯ TÀI KHOẢN"] = df["SODU"].fillna("KPS")
#     df.drop(columns=["SODU"], inplace=True)

#     # ============================================
#     # TIÊU CHÍ CHÍNH
#     # ============================================
#     df["THẺ CHƯA ĐÓNG"] = np.where(
#         ~df["TÌNH TRẠNG THẺ"].isin(["Chấm dứt sử dụng", "Yêu cầu đóng thẻ"]),
#         "X", ""
#     )

#     df["PPSCRLMT"] = pd.to_numeric(df["PPSCRLMT"], errors="ignore")
#     df["DƯ NỢ THẺ HIỆN TẠI"] = pd.to_numeric(df["DƯ NỢ THẺ HIỆN TẠI"], errors="ignore")

#     df["THẺ CÓ HẠN MỨC CAO (>30TR)"] = np.where(df["PPSCRLMT"] > 30_000_000, "X", "")

#     df["THẺ TD CÓ TL DƯ NỢ/HM CAO (>=90%)"] = np.where(
#         (df["PPSCRLMT"] > 0) & (df["DƯ NỢ THẺ HIỆN TẠI"]/df["PPSCRLMT"] >= 0.9),
#         "X", ""
#     )

#     return df


# # ===================================================================
# # =====================   MODULE POS (6–7–8)   ======================
# # ===================================================================
# def process_pos(df_62a, df_62b, start_audit, end_audit):
#     """ Xử lý full tiêu chí POS """

#     df_a = df_62a.copy()
#     df_b = df_62b.copy()

#     df_a["TRANS_DATE"] = pd.to_datetime(df_a["TRANS_DATE"], errors="coerce")
#     df_a["TRANS_AMT"] = pd.to_numeric(df_a["TRANS_AMT"], errors="coerce").fillna(0)

#     df_b["DATE_OPEN_MID"] = pd.to_datetime(df_b["DATE_OPEN_MID"], errors="coerce")

#     # ===== Revenue by Year =====
#     y = end_audit.year
#     ranges = {
#         "T-2": (datetime(y-2,1,1), datetime(y-2,12,31)),
#         "T-1": (datetime(y-1,1,1), datetime(y-1,12,31)),
#         "T":   (datetime(y,1,1),   datetime(y,12,31)),
#     }

#     def cal_rev(df, m1, m2):
#         mask = (df["TRANS_DATE"] >= m1) & (df["TRANS_DATE"] <= m2)
#         rev = df.loc[mask].groupby("MID")["TRANS_AMT"].sum().reset_index()
#         rev.columns = ["MID", "REV"]
#         return rev

#     for k, (d1, d2) in ranges.items():
#         rev = cal_rev(df_a, d1, d2)
#         df_b = df_b.merge(rev, on="MID", how="left")
#         df_b[f"DOANH_SO_{k}"] = df_b["REV"].fillna(0)
#         df_b.drop(columns=["REV"], inplace=True)

#     # ===== 3 tháng gần nhất =====
#     start_3m = (end_audit.replace(day=1) - pd.DateOffset(months=2)).replace(day=1)
#     end_3m = end_audit

#     rev3 = cal_rev(df_a, start_3m, end_3m)
#     df_b = df_b.merge(rev3, on="MID", how="left")
#     df_b["DS_3_THANG"] = df_b["REV"].fillna(0)
#     df_b.drop(columns=["REV"], inplace=True)

#     df_b["BQ_3_THANG"] = (df_b["DS_3_THANG"]/3).round(2)

#     # TIÊU CHÍ
#     df_b["POS_ĐANG_HOẠT_ĐỘNG"] = np.where(df_b["DEVICE_STATUS"] == "Device OK", "X","")
#     df_b["POS_KHONG_DOANH_SO_3T"] = np.where(
#         (df_b["POS_ĐANG_HOẠT_ĐỘNG"] == "X") & (df_b["DS_3_THANG"] == 0), "X", ""
#     )
#     df_b["POS_DOANH_SO_BQ_THAP"] = np.where(
#         (df_b["POS_ĐANG_HOẠT_ĐỘNG"] == "X") & (df_b["BQ_3_THANG"] < 20_000_000), "X", ""
#     )

#     return df_b


# # ===================================================================
# # =======================   GIAO DIỆN STREAMLIT   ===================
# # ===================================================================

# st.title("📌 TIÊU CHÍ THẺ 1.3.2 & POS 6-7-8 (TÁCH RIÊNG)")

# tab_the, tab_pos = st.tabs(["💳 MODULE THẺ", "🏧 MODULE POS"])

# # ===================================================================
# # TAB THẺ
# # ===================================================================
# with tab_the:
#     st.subheader("💳 Xử lý tiêu chí Thẻ (1.3.2)")

#     col1, col2, col3, col4 = st.columns(4)

#     with col1:
#         file_muc26 = st.file_uploader("Mục 26", type=["xls","xlsx"])
#     with col2:
#         file_du_no_m   = st.file_uploader("Dư nợ tháng M",   type=["xls","xlsx"])
#     with col3:
#         file_du_no_m1  = st.file_uploader("Dư nợ tháng M-1", type=["xls","xlsx"])
#     with col4:
#         file_du_no_m2  = st.file_uploader("Dư nợ tháng M-2", type=["xls","xlsx"])

#     col5, col6, col7 = st.columns(3)

#     with col5:
#         file_code_tinh = st.file_uploader("Code tình trạng thẻ", type=["xls","xlsx"])
#     with col6:
#         file_code_policy = st.file_uploader("Code Policy thẻ", type=["xls","xlsx"])
#     with col7:
#         file_ckh = st.file_uploader("HDV CKH", type=["xls","xlsx"])

#     run_the = st.button("🚀 Chạy THẺ")

#     if run_the:
#         if not all([file_muc26, file_du_no_m, file_du_no_m1, file_du_no_m2,
#                     file_code_tinh, file_code_policy, file_ckh]):
#             st.error("⚠ Vui lòng upload đầy đủ tất cả file thẻ!")
#         else:
#             df_muc26 = pd.read_excel(file_muc26)
#             df_du_no_m = pd.read_excel(file_du_no_m)
#             df_du_no_m1 = pd.read_excel(file_du_no_m1)
#             df_du_no_m2 = pd.read_excel(file_du_no_m2)
#             df_code_tinh = pd.read_excel(file_code_tinh)
#             df_code_policy = pd.read_excel(file_code_policy)
#             df_ckh = pd.read_excel(file_ckh)

#             df_the = process_the(df_muc26, df_du_no_m, df_du_no_m1, df_du_no_m2,
#                                  df_code_tinh, df_code_policy, df_ckh)

#             st.success("✔ Xử lý thẻ hoàn tất!")
#             st.dataframe(df_the.head(20), use_container_width=True)

#             st.download_button(
#                 "⬇ Tải Excel Thẻ",
#                 data=df_to_excel_bytes(df_the, "THE"),
#                 file_name="KQ_THE.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#             )

# # ===================================================================
# # TAB POS
# # ===================================================================
# with tab_pos:
#     st.subheader("🏧 Xử lý tiêu chí POS (6–7–8)")

#     colp1, colp2 = st.columns(2)

#     with colp1:
#         file_62a = st.file_uploader("Upload 6.2a (Giao dịch POS)", type=["xls","xlsx"])
#     with colp2:
#         file_62b = st.file_uploader("Upload 6.2b (Thông tin MID)", type=["xls","xlsx"])

#     start_date = st.date_input("Ngày bắt đầu THKT", value=date(2025,1,1))
#     end_date   = st.date_input("Ngày kết thúc THKT", value=date(2025,10,31))

#     run_pos = st.button("🚀 Chạy POS")

#     if run_pos:
#         if not all([file_62a, file_62b]):
#             st.error("⚠ Thiếu file 6.2a hoặc 6.2b!")
#         else:
#             df_62a = pd.read_excel(file_62a)
#             df_62b = pd.read_excel(file_62b)

#             df_pos = process_pos(df_62a, df_62b,
#                                  start_audit=datetime.combine(start_date, datetime.min.time()),
#                                  end_audit=datetime.combine(end_date, datetime.min.time()))

#             st.success("✔ Xử lý POS hoàn tất!")
#             st.dataframe(df_pos.head(20), use_container_width=True)

#             st.download_button(
#                 "⬇ Tải Excel POS",
#                 data=df_to_excel_bytes(df_pos, "POS"),
#                 file_name="KQ_POS.xlsx",
#                 mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#             )

# # =========================================================
# # module/tieuchithe.py
# # FULL MODULE – TIÊU CHÍ THẺ (THẺ TD + POS)
# # =========================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io


# =========================================================
# HÀM PHỤ – XUẤT EXCEL RA BYTES
# =========================================================
def df_to_excel_bytes(df_dict: dict):
    """
    df_dict: {sheet_name: dataframe}
    Trả về: buffer BytesIO để dùng cho st.download_button
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    buffer.seek(0)
    return buffer


# =========================================================
# HÀM CHUẨN HÓA FILE 6.2a (TRƯỚC & SAU 23/05)
# =========================================================
def standardize_6_2a_two_files(file_before_2305, file_after_2305):
    """
    Chuẩn hóa 2 file POS 6.2a (trước & sau 23/05):
    - File trước 23/05: MACN_POS, IDPOS, TENPOS, TRANDT, TRANAMT_QD
    - File sau 23/05: BRANCH_CODE, MERCHANT_ID, MERCHANT_NAME, TRANS_DATE, TRANS_AMT
    """
    # ----- File TRƯỚC 23/05/2025 -----
    df_before = pd.read_excel(file_before_2305, dtype=str)

    map_before = {
        "MACN_POS": "BRANCH_CODE",
        "IDPOS": "MERCHANT_ID",
        "TENPOS": "MERCHANT_NAME",
        "TRANDT": "TRANS_DATE",
        "TRANAMT_QD": "TRANS_AMT",
    }
    needed_before = list(map_before.keys())
    keep_before = [c for c in needed_before if c in df_before.columns]
    df_before = df_before[keep_before].rename(columns=map_before)

    # ----- File SAU 23/05/2025 -----
    df_after = pd.read_excel(file_after_2305, dtype=str)

    map_after = {
        "BRANCH_CODE": "BRANCH_CODE",
        "MERCHANT_ID": "MERCHANT_ID",
        "MERCHANT_NAME": "MERCHANT_NAME",
        "TRANS_DATE": "TRANS_DATE",
        "TRANS_AMT": "TRANS_AMT",
    }
    needed_after = list(map_after.keys())
    keep_after = [c for c in needed_after if c in df_after.columns]
    df_after = df_after[keep_after].rename(columns=map_after)

    # ----- Ghép & chuẩn hóa -----
    df_std = pd.concat([df_before, df_after], ignore_index=True)

    if "TRANS_DATE" in df_std.columns:
        df_std["TRANS_DATE"] = pd.to_datetime(df_std["TRANS_DATE"], errors="coerce")

    for col in ["BRANCH_CODE", "MERCHANT_ID", "MERCHANT_NAME"]:
        if col in df_std.columns:
            df_std[col] = df_std[col].astype(str)

    final_cols = ["BRANCH_CODE", "MERCHANT_ID", "MERCHANT_NAME", "TRANS_DATE", "TRANS_AMT"]
    df_std = df_std.reindex(columns=final_cols)

    return df_std


# =========================================================
# HÀM XỬ LÝ CHÍNH – THẺ + POS
# =========================================================
def process_the_pos(
    file_muc26,
    file_code_ttd_policy,
    files_du_no_m,
    files_du_no_m1,
    files_du_no_m2,
    files_crm4,
    files_crm32,
    files_ckh,
    file_muc17,
    file_muc29_old,
    file_muc29_new,
    file_muc51,
    chi_nhanh: str,
    start_audit: datetime,
    end_audit: datetime,
):
    """
    Nhận toàn bộ file upload + tham số, xử lý & trả:
      - df_card: kết quả Thẻ
      - df_pos : kết quả POS
    """

    chi_nhanh_upper = chi_nhanh.strip().upper()

    # -------------------------------
    # LOAD DỮ LIỆU NHÓM THẺ
    # -------------------------------

    # Mục 26
    df_muc26 = pd.read_excel(file_muc26, dtype=str)

    # Code tình trạng thẻ & Code Policy (trong cùng 1 file – 2 sheet)
    df_code_tinh_trang_the = pd.read_excel(
        file_code_ttd_policy, sheet_name="Code Tình trạng thẻ"
    )
    df_code_policy = pd.read_excel(file_code_ttd_policy, sheet_name="Code Policy")

    # Dư nợ M, M-1, M-2 (ghép nếu nhiều file)
    df_du_no_m = pd.concat(
        [pd.read_excel(f) for f in files_du_no_m], ignore_index=True
    )
    df_du_no_m1 = pd.concat(
        [pd.read_excel(f) for f in files_du_no_m1], ignore_index=True
    )
    df_du_no_m2 = pd.concat(
        [pd.read_excel(f) for f in files_du_no_m2], ignore_index=True
    )

    # CRM4 & CRM32
    df_crm4 = pd.concat([pd.read_excel(f, dtype=str) for f in files_crm4], ignore_index=True)
    df_crm32 = pd.concat([pd.read_excel(f, dtype=str) for f in files_crm32], ignore_index=True)

    # CKH chi tiết (HDV)
    df_hdv_ckh = pd.concat([pd.read_excel(f) for f in files_ckh], ignore_index=True)

    # Mục 17
    df_muc17 = pd.read_excel(file_muc17, dtype=str)

    # Lọc CRM4 & CKH theo chi nhánh
    df_crm4_loc = df_crm4[
        df_crm4["BRANCH_VAY"].astype(str).str.upper().str.contains(chi_nhanh_upper)
    ].copy()

    df_hdv_ckh_loc = df_hdv_ckh[
        df_hdv_ckh["BRCD"].astype(str).str.upper().str.contains(chi_nhanh_upper)
    ].copy()

    # -------------------------------
    # XỬ LÝ MỤC 26 → df_processed (Thẻ)
    # -------------------------------
    cols_keep = [
        "CUSTSEQ",
        "BRCD",
        "PPSCRLMT",
        "FULLNM",
        "CUSTNAMNE",
        "ID_CARD",
        "IDCARD",
        "EXPDT",
        "NGAY_KICH_HOAT",
        "ODACCOUNT",
        "NGAY_MO",
        "TRANGTHAITHE",
        "POLICY_CODE",
        "POLICY_NAME",
        "DU_NO",
    ]
    cols_exist = [c for c in cols_keep if c in df_muc26.columns]
    df_processed = df_muc26[cols_exist].copy()

    # Chuẩn hóa kiểu dữ liệu
    for c in ["CUSTSEQ", "IDCARD", "ID_CARD", "ODACCOUNT"]:
        if c in df_processed.columns:
            df_processed[c] = df_processed[c].astype("string")

    for c in ["NGAY_MO", "NGAY_KICH_HOAT", "EXPDT"]:
        if c in df_processed.columns:
            df_processed[c] = pd.to_datetime(df_processed[c], errors="coerce")

    # -------------------------------
    # (1) TÌNH TRẠNG THẺ
    # -------------------------------
    if (
        "TRANGTHAITHE" in df_processed.columns
        and "Code" in df_code_tinh_trang_the.columns
        and "Tình trạng thẻ" in df_code_tinh_trang_the.columns
    ):
        df_code_tinh_trang_the["Code_policy"] = df_code_tinh_trang_the["Code"].astype(
            str
        )

        df_processed["TRANGTHAITHE_is_blank_orig"] = (
            df_processed["TRANGTHAITHE"].isna()
            | df_processed["TRANGTHAITHE"].astype(str).str.strip().eq("")
        )
        df_processed["TRANGTHAITHE_for_merge"] = df_processed["TRANGTHAITHE"].astype(
            str
        )

        df_processed = pd.merge(
            df_processed,
            df_code_tinh_trang_the[["Code_policy", "Tình trạng thẻ"]].rename(
                columns={"Tình trạng thẻ": "POLICY_TinhTrang"}
            ),
            left_on="TRANGTHAITHE_for_merge",
            right_on="Code_policy",
            how="left",
        )

        cond_a_blank = df_processed["TRANGTHAITHE_is_blank_orig"]
        cond_c_no_match = (~df_processed["TRANGTHAITHE_is_blank_orig"]) & (
            df_processed["Code_policy"].isna()
        )

        df_processed["TÌNH TRẠNG THẺ"] = np.select(
            [cond_a_blank, cond_c_no_match],
            ["Hoạt động bình thường", "Khác"],
            default=df_processed["POLICY_TinhTrang"],
        )

        cols_to_drop = [
            "Code_policy",
            "POLICY_TinhTrang",
            "TRANGTHAITHE_is_blank_orig",
            "TRANGTHAITHE_for_merge",
            "Description",
            "Unnamed: 3",
        ]
        df_processed.drop(
            columns=[c for c in cols_to_drop if c in df_processed.columns],
            inplace=True,
            errors="ignore",
        )
    else:
        df_processed["TÌNH TRẠNG THẺ"] = "Lỗi dữ liệu nguồn"

    # -------------------------------
    # Gộp Policy → PHÂN LOẠI CẤP HM THẺ
    # -------------------------------
    df_processed["POLICY_CODE"] = df_processed["POLICY_CODE"].astype(str).str.strip()
    df_code_policy["CODE"] = df_code_policy["CODE"].astype(str).str.strip()

    df_processed = df_processed.merge(
        df_code_policy[["CODE", "PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"]],
        left_on="POLICY_CODE",
        right_on="CODE",
        how="left",
    )

    df_processed["PHÂN LOẠI CẤP HM THẺ"] = df_processed[
        "PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"
    ].fillna("Khác")

    # -------------------------------
    # (3) DƯ NỢ THẺ 02 THÁNG TRƯỚC (M-2)
    # -------------------------------
    if (
        "ODACCOUNT" in df_processed.columns
        and "OD_ACCOUNT" in df_du_no_m2.columns
        and "DU_NO_QUY_DOI" in df_du_no_m2.columns
    ):
        df_du_no_m2["OD_ACCOUNT"] = df_du_no_m2["OD_ACCOUNT"].astype(str)
        df_processed = pd.merge(
            df_processed,
            df_du_no_m2[["OD_ACCOUNT", "DU_NO_QUY_DOI"]],
            left_on="ODACCOUNT",
            right_on="OD_ACCOUNT",
            how="left",
        )
        df_processed.rename(
            columns={"DU_NO_QUY_DOI": "DƯ NỢ THẺ 02 THÁNG TRƯỚC"}, inplace=True
        )
        df_processed["DƯ NỢ THẺ 02 THÁNG TRƯỚC"].fillna("KPS", inplace=True)
        df_processed.drop(columns=["OD_ACCOUNT"], inplace=True, errors="ignore")
    else:
        df_processed["DƯ NỢ THẺ 02 THÁNG TRƯỚC"] = "KPS"

    # -------------------------------
    # (4) DƯ NỢ THẺ 01 THÁNG TRƯỚC (M-1)
    # -------------------------------
    if (
        "ODACCOUNT" in df_processed.columns
        and "OD_ACCOUNT" in df_du_no_m1.columns
        and "DU_NO_QUY_DOI" in df_du_no_m1.columns
    ):
        df_du_no_m1["OD_ACCOUNT"] = df_du_no_m1["OD_ACCOUNT"].astype(str)
        df_processed = pd.merge(
            df_processed,
            df_du_no_m1[["OD_ACCOUNT", "DU_NO_QUY_DOI"]],
            left_on="ODACCOUNT",
            right_on="OD_ACCOUNT",
            how="left",
        )
        df_processed.rename(
            columns={"DU_NO_QUY_DOI": "DƯ NỢ THẺ 01 THÁNG TRƯỚC"}, inplace=True
        )
        df_processed["DƯ NỢ THẺ 01 THÁNG TRƯỚC"].fillna("KPS", inplace=True)
        df_processed.drop(columns=["OD_ACCOUNT"], inplace=True, errors="ignore")
    else:
        df_processed["DƯ NỢ THẺ 01 THÁNG TRƯỚC"] = "KPS"

    # -------------------------------
    # (5) DƯ NỢ THẺ HIỆN TẠI (M)
    # -------------------------------
    if (
        "ODACCOUNT" in df_processed.columns
        and "OD_ACCOUNT" in df_du_no_m.columns
        and "DU_NO_QUY_DOI" in df_du_no_m.columns
    ):
        df_du_no_m["OD_ACCOUNT"] = df_du_no_m["OD_ACCOUNT"].astype(str)
        df_processed = pd.merge(
            df_processed,
            df_du_no_m[["OD_ACCOUNT", "DU_NO_QUY_DOI"]],
            left_on="ODACCOUNT",
            right_on="OD_ACCOUNT",
            how="left",
        )
        df_processed.rename(
            columns={"DU_NO_QUY_DOI": "DƯ NỢ THẺ HIỆN TẠI"}, inplace=True
        )
        df_processed["DƯ NỢ THẺ HIỆN TẠI"].fillna("KPS", inplace=True)
        df_processed.drop(columns=["OD_ACCOUNT"], inplace=True, errors="ignore")
    else:
        df_processed["DƯ NỢ THẺ HIỆN TẠI"] = "KPS"

    # -------------------------------
    # (6) NHÓM NỢ HIỆN TẠI CỦA THẺ (NHOM_NO_OD_ACCOUNT)
    # -------------------------------
    if (
        "ODACCOUNT" in df_processed.columns
        and "OD_ACCOUNT" in df_du_no_m.columns
        and "NHOM_NO_OD_ACCOUNT" in df_du_no_m.columns
    ):
        temp = df_du_no_m[["OD_ACCOUNT", "NHOM_NO_OD_ACCOUNT"]].copy()
        temp.rename(columns={"NHOM_NO_OD_ACCOUNT": "NHÓM NỢ HIỆN TẠI CỦA THẺ"}, inplace=True)
        temp["OD_ACCOUNT"] = temp["OD_ACCOUNT"].astype(str)

        df_processed = pd.merge(
            df_processed, temp, left_on="ODACCOUNT", right_on="OD_ACCOUNT", how="left"
        )
        df_processed["NHÓM NỢ HIỆN TẠI CỦA THẺ"].fillna("KPS", inplace=True)
        df_processed.drop(columns=["OD_ACCOUNT"], inplace=True, errors="ignore")
    else:
        df_processed["NHÓM NỢ HIỆN TẠI CỦA THẺ"] = "KPS"

    # -------------------------------
    # (7) NHÓM NỢ HIỆN TẠI CỦA KH (NHOM_NO)
    # -------------------------------
    if (
        "ODACCOUNT" in df_processed.columns
        and "OD_ACCOUNT" in df_du_no_m.columns
        and "NHOM_NO" in df_du_no_m.columns
    ):
        temp = df_du_no_m[["OD_ACCOUNT", "NHOM_NO"]].copy()
        temp.rename(columns={"NHOM_NO": "NHÓM NỢ HIỆN TẠI CỦA KH"}, inplace=True)
        temp["OD_ACCOUNT"] = temp["OD_ACCOUNT"].astype(str)

        df_processed = pd.merge(
            df_processed, temp, left_on="ODACCOUNT", right_on="OD_ACCOUNT", how="left"
        )
        df_processed["NHÓM NỢ HIỆN TẠI CỦA KH"].fillna("KPS", inplace=True)
        df_processed.drop(columns=["OD_ACCOUNT"], inplace=True, errors="ignore")
    else:
        df_processed["NHÓM NỢ HIỆN TẠI CỦA KH"] = "KPS"

    # -------------------------------
    # (8) DƯ NỢ VAY CỦA KH (từ CRM4)
    # -------------------------------
    if (
        "CUSTSEQ" in df_processed.columns
        and "CIF_KH_VAY" in df_crm4_loc.columns
        and "DU_NO_PHAN_BO_QUY_DOI" in df_crm4_loc.columns
        and "LOAI" in df_crm4_loc.columns
    ):
        df_crm4_loc["CIF_KH_VAY"] = df_crm4_loc["CIF_KH_VAY"].astype(str)
        df_crm4_cho_vay = df_crm4_loc[df_crm4_loc["LOAI"] == "Cho vay"].copy()

        df_crm4_cho_vay["DU_NO_PHAN_BO_QUY_DOI"] = pd.to_numeric(
            df_crm4_cho_vay["DU_NO_PHAN_BO_QUY_DOI"], errors="coerce"
        ).fillna(0)

        df_tong_du_no_vay_kh = (
            df_crm4_cho_vay.groupby("CIF_KH_VAY")["DU_NO_PHAN_BO_QUY_DOI"]
            .sum()
            .reset_index()
            .rename(columns={"DU_NO_PHAN_BO_QUY_DOI": "DƯ NỢ VAY CỦA KH"})
        )

        df_processed["CUSTSEQ"] = df_processed["CUSTSEQ"].astype(str)

        df_processed = pd.merge(
            df_processed,
            df_tong_du_no_vay_kh,
            left_on="CUSTSEQ",
            right_on="CIF_KH_VAY",
            how="left",
        )

        df_processed["DƯ NỢ VAY CỦA KH"].fillna("KPS", inplace=True)
        df_processed.drop(columns=["CIF_KH_VAY"], inplace=True, errors="ignore")
    else:
        df_processed["DƯ NỢ VAY CỦA KH"] = "KPS"

    # -------------------------------
    # (9) SỐ LƯỢNG TSBĐ (Mục 17)
    # -------------------------------
    if "CUSTSEQ" in df_processed.columns and "C04" in df_muc17.columns and "C01" in df_muc17.columns:
        df_muc17_copy = df_muc17.copy()
        df_muc17_copy["C04"] = df_muc17_copy["C04"].astype(str)
        df_processed["CUSTSEQ"] = df_processed["CUSTSEQ"].astype(str)

        df_so_luong_tsbd = (
            df_muc17_copy.groupby("C04")["C01"].nunique().reset_index()
        )
        df_so_luong_tsbd.rename(columns={"C01": "SỐ LƯỢNG TSBĐ"}, inplace=True)

        df_processed = pd.merge(
            df_processed, df_so_luong_tsbd, left_on="CUSTSEQ", right_on="C04", how="left"
        )

        df_processed["SỐ LƯỢNG TSBĐ"] = df_processed["SỐ LƯỢNG TSBĐ"].fillna("KPS")

        df_processed.drop(columns=["C04"], inplace=True, errors="ignore")
    else:
        df_processed["SỐ LƯỢNG TSBĐ"] = "KPS"

    # -------------------------------
    # (10) TRỊ GIÁ TSBĐ (CRM4 – SECU_VALUE)
    # -------------------------------
    if (
        "CUSTSEQ" in df_processed.columns
        and "CIF_KH_VAY" in df_crm4_loc.columns
        and "SECU_VALUE" in df_crm4_loc.columns
    ):
        df_crm4_loc_copy = df_crm4_loc.copy()
        df_crm4_loc_copy["CIF_KH_VAY"] = df_crm4_loc_copy["CIF_KH_VAY"].astype(str)
        df_crm4_loc_copy["SECU_VALUE"] = pd.to_numeric(
            df_crm4_loc_copy["SECU_VALUE"], errors="coerce"
        ).fillna(0)

        df_tri_gia_tsbd = (
            df_crm4_loc_copy.groupby("CIF_KH_VAY", as_index=False)["SECU_VALUE"]
            .sum()
            .rename(columns={"SECU_VALUE": "TRỊ GIÁ TSBĐ"})
        )

        df_processed = pd.merge(
            df_processed,
            df_tri_gia_tsbd,
            left_on="CUSTSEQ",
            right_on="CIF_KH_VAY",
            how="left",
        )

        df_processed["TRỊ GIÁ TSBĐ"] = df_processed["TRỊ GIÁ TSBĐ"].fillna("KPS")
        df_processed.drop(columns=["CIF_KH_VAY"], inplace=True, errors="ignore")
    else:
        df_processed["TRỊ GIÁ TSBĐ"] = "KPS"

    # -------------------------------
    # (11) & (12) SỐ LƯỢNG / SỐ DƯ TKTG CKH
    # -------------------------------
    df_processed["CUSTSEQ"] = df_processed["CUSTSEQ"].astype(str)
    df_hdv_ckh_loc["CUSTSEQ"] = df_hdv_ckh_loc["CUSTSEQ"].astype(str)

    # Số lượng
    if "IDXACNO" in df_hdv_ckh_loc.columns:
        tktg_ckh_counts = (
            df_hdv_ckh_loc.groupby("CUSTSEQ")["IDXACNO"].count().reset_index()
        )
        tktg_ckh_counts.columns = ["CUSTSEQ", "SO_LUONG_TKTG_CKH"]

        df_processed = df_processed.merge(tktg_ckh_counts, on="CUSTSEQ", how="left")
        df_processed["SỐ LƯỢNG TKTG CKH"] = df_processed["SO_LUONG_TKTG_CKH"].fillna(
            "KPS"
        )
        df_processed.drop(columns=["SO_LUONG_TKTG_CKH"], inplace=True)
    else:
        df_processed["SỐ LƯỢNG TKTG CKH"] = "KPS"

    # Số dư
    if "CURBAL_VN" in df_hdv_ckh_loc.columns:
        sodu_ckh = (
            df_hdv_ckh_loc.groupby("CUSTSEQ")["CURBAL_VN"].sum().reset_index()
        )
        sodu_ckh.columns = ["CUSTSEQ", "SỐ DƯ TÀI KHOẢN"]

        df_processed = df_processed.merge(sodu_ckh, on="CUSTSEQ", how="left")
        df_processed["SỐ DƯ TÀI KHOẢN"] = df_processed["SỐ DƯ TÀI KHOẢN"].fillna("KPS")
    else:
        df_processed["SỐ DƯ TÀI KHOẢN"] = "KPS"

    # -------------------------------
    # (13) THẺ CÓ HẠN MỨC CAO
    # -------------------------------
    if "PPSCRLMT" in df_processed.columns:
        df_processed["PPSCRLMT_numeric"] = pd.to_numeric(
            df_processed["PPSCRLMT"], errors="coerce"
        )
        df_processed["THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)"] = np.where(
            df_processed["PPSCRLMT_numeric"] > 30_000_000, "X", ""
        )
        df_processed.drop(columns=["PPSCRLMT_numeric"], inplace=True)
    else:
        df_processed["THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)"] = ""

    # -------------------------------
    # (14) & (15) TL DƯ NỢ/HM
    # -------------------------------
    df_processed["DƯ NỢ THẺ HIỆN TẠI"] = pd.to_numeric(
        df_processed["DƯ NỢ THẺ HIỆN TẠI"], errors="coerce"
    )
    df_processed["PPSCRLMT"] = pd.to_numeric(
        df_processed["PPSCRLMT"], errors="coerce"
    )

    df_processed["THẺ TD CÓ TL DƯ NỢ/HM CAO (>= 90%)"] = np.where(
        (df_processed["PPSCRLMT"] > 0)
        & (df_processed["DƯ NỢ THẺ HIỆN TẠI"] / df_processed["PPSCRLMT"] >= 0.9),
        "X",
        "",
    )

    df_processed["THẺ TD CÓ DƯ NỢ > HM"] = np.where(
        (df_processed["PPSCRLMT"] > 0)
        & (df_processed["DƯ NỢ THẺ HIỆN TẠI"] / df_processed["PPSCRLMT"] > 1),
        "X",
        "",
    )

    # -------------------------------
    # (16) THẺ CHƯA ĐÓNG
    # -------------------------------
    df_processed["TÌNH TRẠNG THẺ"] = (
        df_processed["TÌNH TRẠNG THẺ"].astype(str).str.strip()
    )
    df_processed["THẺ CHƯA ĐÓNG"] = np.where(
        ~df_processed["TÌNH TRẠNG THẺ"].isin(["Chấm dứt sử dụng", "Yêu cầu đóng thẻ"]),
        "X",
        "",
    )

    # -------------------------------
    # (17) THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO
    # -------------------------------
    df_processed["PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"] = df_processed[
        "PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"
    ].astype(str).str.strip()
    df_processed["THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)"] = df_processed[
        "THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)"
    ].astype(str).str.strip()

    dk_17 = (
        df_processed["PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"].isin(
            ["Theo thu nhập/tín chấp", "Theo điều kiện về TKTG CKH"]
        )
        & (df_processed["THẺ CÓ HẠN MỨC CAO (> 30 TRĐ)"] == "X")
    )

    df_processed["THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO"] = ""
    df_processed.loc[dk_17, "THẺ MỞ THEO THU NHẬP/TÍN CHẤP CÓ HM CAO"] = "X"

    # -------------------------------
    # (18) KH KHÔNG CÓ/KHÔNG CÒN TSBĐ + biến thể
    # -------------------------------
    df_processed["KH KHÔNG CÓ/KHÔNG CÒN TSBĐ"] = df_processed["SỐ LƯỢNG TSBĐ"].apply(
        lambda x: "X" if str(x).strip() in ["0", "KPS"] or x == 0 else ""
    )

    df_processed["KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG"] = df_processed.apply(
        lambda row: "X"
        if (
            row["PHÂN LOẠI CẤP HM THẺ"] == "Theo khoản vay/Có TSBĐ"
            and row["KH KHÔNG CÓ/KHÔNG CÒN TSBĐ"] == "X"
            and row["THẺ CHƯA ĐÓNG"] == "X"
        )
        else "",
        axis=1,
    )

    df_processed["DƯ NỢ THẺ HIỆN TẠI"] = pd.to_numeric(
        df_processed["DƯ NỢ THẺ HIỆN TẠI"], errors="coerce"
    )

    dk_20 = (
        (df_processed["KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG"] == "X")
        & (df_processed["DƯ NỢ THẺ HIỆN TẠI"].notnull())
        & (df_processed["DƯ NỢ THẺ HIỆN TẠI"] != 0)
    )

    df_processed[
        "KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG VÀ CÓ DƯ NỢ"
    ] = ""
    df_processed.loc[
        dk_20, "KH GIẢI CHẤP TSBĐ NHƯNG THẺ CHƯA ĐÓNG VÀ CÓ DƯ NỢ"
    ] = "X"

    df_processed["NHÓM NỢ HIỆN TẠI CỦA THẺ"] = pd.to_numeric(
        df_processed["NHÓM NỢ HIỆN TẠI CỦA THẺ"], errors="coerce"
    )
    df_processed["NHÓM NỢ HIỆN TẠI CỦA KH"] = pd.to_numeric(
        df_processed["NHÓM NỢ HIỆN TẠI CỦA KH"], errors="coerce"
    )

    df_processed["THẺ QUÁ HẠN"] = np.where(
        df_processed["NHÓM NỢ HIỆN TẠI CỦA THẺ"].isin([2, 3, 4, 5]), "X", ""
    )
    df_processed["KH QUÁ HẠN"] = np.where(
        df_processed["NHÓM NỢ HIỆN TẠI CỦA KH"].isin([2, 3, 4, 5]), "X", ""
    )

    # -------------------------------
    # (21) KH KHÔNG CÓ/TẤT TOÁN TKTG CKH NHƯNG THẺ CHƯA ĐÓNG
    # -------------------------------
    cond_a_21 = df_processed["PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"] == "Theo điều kiện về TKTG CKH"
    cond_b_21 = df_processed["SỐ LƯỢNG TKTG CKH"].astype(str).isin(["0", "KPS"])
    cond_c_21 = df_processed["THẺ CHƯA ĐÓNG"] == "X"

    df_processed[
        "KH KHÔNG CÓ/TẤT TOÁN TKTG CKH NHƯNG THẺ CHƯA ĐÓNG"
    ] = np.where(
        cond_a_21 & cond_b_21 & cond_c_21,
        "X",
        "",
    )

    # -------------------------------
    # (22) SỐ DƯ TKTG CKH < HẠN MỨC
    # -------------------------------
    df_processed["PPSCRLMT"] = pd.to_numeric(df_processed["PPSCRLMT"], errors="coerce")
    df_processed["SỐ DƯ TÀI KHOẢN"] = pd.to_numeric(
        df_processed["SỐ DƯ TÀI KHOẢN"], errors="coerce"
    )

    df_processed["SỐ DƯ TKTG CKH < HẠN MỨC"] = df_processed.apply(
        lambda row: "X"
        if (
            row["PHÂN LOẠI ĐỐI TƯỢNG MỞ THẺ"] == "Theo điều kiện về TKTG CKH"
            and row["THẺ CHƯA ĐÓNG"] == "X"
            and (
                pd.isna(row["SỐ DƯ TÀI KHOẢN"])
                or row["SỐ DƯ TÀI KHOẢN"] < row["PPSCRLMT"]
            )
        )
        else "",
        axis=1,
    )

    # -------------------------------
    # XỬ LÝ POS – MỤC 6.2a, 6.2b, 7, 8
    # -------------------------------

    # Chuẩn hóa 6.2a
    df_6_2a = standardize_6_2a_two_files(
        file_before_2305=file_muc29_old,
        file_after_2305=file_muc29_new,
    )

    # Đọc 6.2b (MUC51_1600)
    cols_needed = [
        "MID",
        "BRANCH_LAP_DAT_MAY",
        "TEN_GPKD_HKD",
        "TEN_TREN_HD",
        "DAI_CHI_LAP_MAY",
        "ADDRESSLINE_SUB_MERCHANT",
        "MCC",
        "DATE_OPEN_MID",
        "DEVICE_STATUS",
        "MERCHANT_CIF",
    ]

    df_6_2b_raw = pd.read_excel(
        file_muc51,
        usecols=lambda c: c in cols_needed,
        dtype={"MID": "string", "MERCHANT_CIF": "string"},
        parse_dates=["DATE_OPEN_MID"],
    )

    df_pos = df_6_2b_raw.copy()

    # Làm sạch MERCHANT_CIF
    s = df_pos["MERCHANT_CIF"].fillna("").astype("string").str.strip()
    s = s.str.replace(r"^[A-Za-z]", "", regex=True)
    s = s.str.replace(r"\D+", "", regex=True).str[-9:]
    df_pos["MERCHANT_CIF"] = s.mask(s == "", None)

    for c in ["MID", "MERCHANT_CIF"]:
        if c in df_pos.columns:
            df_pos[c] = df_pos[c].astype("string")

    if "DATE_OPEN_MID" in df_pos.columns:
        df_pos["DATE_OPEN_MID"] = pd.to_datetime(
            df_pos["DATE_OPEN_MID"], errors="coerce"
        )

    # Chuẩn hoá nguồn giao dịch df_6_2a
    df_6_2a["TRANS_AMT"] = (
        df_6_2a["TRANS_AMT"]
        .astype(str)
        .str.replace(r"[^\d\.\-]", "", regex=True)
        .replace({"": "0"})
        .astype(float)
    )
    df_6_2a["TRANS_DATE"] = pd.to_datetime(df_6_2a["TRANS_DATE"], errors="coerce")
    df_6_2a["MERCHANT_ID"] = df_6_2a["MERCHANT_ID"].astype(str)
    df_pos["MID"] = df_pos["MID"].astype(str)

    # Hàm tổng doanh số theo MID trong một khoảng thời gian
    def calc_revenue(df_trans, df_pos_local, start_date, end_date):
        mask = (df_trans["TRANS_DATE"] >= start_date) & (
            df_trans["TRANS_DATE"] <= end_date
        )
        g = (
            df_trans.loc[mask]
            .groupby("MERCHANT_ID", as_index=False)["TRANS_AMT"]
            .sum()
            .rename(columns={"MERCHANT_ID": "MID", "TRANS_AMT": "REVENUE"})
        )
        return (
            df_pos_local[["MID"]].merge(g, on="MID", how="left")["REVENUE"]
            .fillna(0)
            .astype(float)
        )

    # Lấy năm hiện tại từ ngày kết thúc thời hiệu kiểm toán
    y = end_audit.year

    date_ranges = {
        "T-2": (datetime(y - 2, 1, 1), datetime(y - 2, 12, 31)),
        "T-1": (datetime(y - 1, 1, 1), datetime(y - 1, 12, 31)),
        "T": (datetime(y, 1, 1), datetime(y, 12, 31)),
    }

    df_pos["DSỐ_2_NĂM_TRƯỚC_T2"] = calc_revenue(df_6_2a, df_pos, *date_ranges["T-2"])
    df_pos["DSỐ_NĂM_TRƯỚC_T1"] = calc_revenue(df_6_2a, df_pos, *date_ranges["T-1"])
    df_pos["DSỐ_NĂM_NAY_T"] = calc_revenue(df_6_2a, df_pos, *date_ranges["T"])

    df_pos["TỔNG_DSỐ_3_NĂM"] = (
        df_pos["DSỐ_2_NĂM_TRƯỚC_T2"]
        + df_pos["DSỐ_NĂM_TRƯỚC_T1"]
        + df_pos["DSỐ_NĂM_NAY_T"]
    )

    # 3 tháng gần nhất
    start_3m = (end_audit.replace(day=1) - relativedelta(months=2)).replace(day=1)
    end_3m = end_audit

    df_pos["DSỐ_3_THÁNG_GẦN_NHẤT"] = calc_revenue(df_6_2a, df_pos, start_3m, end_3m)
    df_pos["DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT"] = (
        df_pos["DSỐ_3_THÁNG_GẦN_NHẤT"] / 3
    ).round(2)

    df_pos = df_pos.drop_duplicates(subset=["MID", "BRANCH_LAP_DAT_MAY"], keep="first")

    # POS đang hoạt động
    df_pos["POS_ĐANG_HOẠT_ĐỘNG"] = df_pos["DEVICE_STATUS"].astype(str).apply(
        lambda x: "X" if x == "Device OK" else ""
    )

    # POS hoạt động có tổng doanh số 3 năm cao nhất (top 10)
    df_active = df_pos[df_pos["POS_ĐANG_HOẠT_ĐỘNG"] == "X"]
    if not df_active.empty:
        top10_total = df_active.nlargest(10, "TỔNG_DSỐ_3_NĂM")["MID"]
    else:
        top10_total = pd.Series([], dtype=str)

    df_pos["POS ĐANG HOẠT ĐỘNG CÓ TỔNG DSỐ 3 NĂM CAO"] = df_pos["MID"].apply(
        lambda x: "X" if x in top10_total.values else ""
    )

    # POS hoạt động có DS 3 tháng gần nhất cao nhất (top 10)
    if not df_active.empty:
        top10_3m = df_active.nlargest(10, "DSỐ_3_THÁNG_GẦN_NHẤT")["MID"]
    else:
        top10_3m = pd.Series([], dtype=str)

    df_pos["POS ĐANG HOẠT ĐỘNG CÓ DSỐ 3 THÁNG GẦN NHẤT CAO"] = df_pos["MID"].apply(
        lambda x: "X" if x in top10_3m.values else ""
    )

    # POS KPS doanh số 3 tháng & chưa đóng
    df_pos["POS KPS DSỐ TRONG 3 THÁNG VÀ CHƯA ĐÓNG"] = df_pos.apply(
        lambda row: "X"
        if row["POS_ĐANG_HOẠT_ĐỘNG"] == "X"
        and row["DSỐ_3_THÁNG_GẦN_NHẤT"] == 0
        else "",
        axis=1,
    )

    # POS có DS BQ/3 tháng < 20 triệu & chưa đóng
    df_pos[
        "POS CÓ DSỐ BQ TRONG 3 THÁNG < 20 TRĐ VÀ CHƯA ĐÓNG"
    ] = df_pos.apply(
        lambda row: "X"
        if row["POS_ĐANG_HOẠT_ĐỘNG"] == "X"
        and row["DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT"] < 20_000_000
        else "",
        axis=1,
    )

    # ĐVCNT có nhiều POS đang hoạt động (>= 2)
    active_pos = df_pos[df_pos["POS_ĐANG_HOẠT_ĐỘNG"] == "X"]
    multi_pos = (
        active_pos.groupby("MERCHANT_CIF")
        .filter(lambda g: len(g) >= 2)["MERCHANT_CIF"]
        .unique()
    )

    df_pos["ĐVCNT CÓ NHIỀU POS ĐANG HOẠT ĐỘNG (>2)"] = df_pos["MERCHANT_CIF"].apply(
        lambda x: "X" if x in multi_pos else ""
    )

    return df_processed, df_pos


# =========================================================
# HÀM PUBLIC – GỌI TỪ app.py
# =========================================================
def run_module_the():
    st.title("📊 TIÊU CHÍ THẺ & POS – 1600")

    st.markdown(
        """
Ứng dụng này xử lý **toàn bộ tiêu chí thẻ (1.3.2) và POS (6,7,8)**.

**Bước 1:** Nhập tham số kiểm toán  
**Bước 2:** Upload file nhóm *Thẻ* và nhóm *POS*  
**Bước 3:** Bấm **Chạy xử lý** để xem kết quả & tải Excel.
"""
    )

    # =========================
    # THAM SỐ CHUNG
    # =========================
    col_param1, col_param2 = st.columns(2)

    with col_param1:
        chi_nhanh = st.text_input(
            "Nhập tên chi nhánh hoặc mã SOL (VD: HANOI, 007)",
            value="HANOI",
        ).strip()

    with col_param2:
        c1, c2 = st.columns(2)
        with c1:
            start_audit_date = st.date_input(
                "Ngày bắt đầu thời hiệu kiểm toán",
                value=date(2025, 1, 1),
            )
        with c2:
            end_audit_date = st.date_input(
                "Ngày kết thúc thời hiệu kiểm toán",
                value=date(2025, 10, 31),
            )

    st.markdown("---")

    # =========================
    # NHÓM UPLOAD – THẺ
    # =========================
    with st.expander("💳 Upload nhóm file THẺ (Mục 26 + CRM + EL + CKH + M17)", expanded=True):
        st.markdown("**Vui lòng upload đầy đủ các file sau (xls hoặc xlsx):**")

        col_t1, col_t2 = st.columns(2)

        with col_t1:
            file_muc26 = st.file_uploader(
                "1️⃣ Mục 26 – Danh sách thẻ",
                type=["xls", "xlsx"],
                key="muc26",
            )

            file_code_ttd_policy = st.file_uploader(
                "2️⃣ Code TTD-NEW (chứa cả sheet 'Code Tình trạng thẻ' và 'Code Policy')",
                type=["xls", "xlsx"],
                key="code_ttd",
            )

            files_du_no_m = st.file_uploader(
                "3️⃣ Dư nợ THẺ tháng M (có cột OD_ACCOUNT, DU_NO_QUY_DOI, NHOM_NO, NHOM_NO_OD_ACCOUNT)",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="el_m",
            )

            files_du_no_m1 = st.file_uploader(
                "4️⃣ Dư nợ THẺ tháng M-1",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="el_m1",
            )

            files_du_no_m2 = st.file_uploader(
                "5️⃣ Dư nợ THẺ tháng M-2",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="el_m2",
            )

        with col_t2:
            files_crm4 = st.file_uploader(
                "6️⃣ CRM4_Du_no_theo_tai_san_dam_bao_ALL",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="crm4",
            )

            files_crm32 = st.file_uploader(
                "7️⃣ RPT_CRM_32_* (có thể nhiều file)",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="crm32",
            )

            files_ckh = st.file_uploader(
                "8️⃣ HDV_CHITIET_CKH_* (chi tiết TKTG CKH – nhiều file)",
                type=["xls", "xlsx"],
                accept_multiple_files=True,
                key="ckh",
            )

            file_muc17 = st.file_uploader(
                "9️⃣ Mục 17 – TSTC (Muc17_Lop2_TSTC...)",
                type=["xls", "xlsx"],
                key="muc17",
            )

    # =========================
    # NHÓM UPLOAD – POS
    # =========================
    with st.expander("🏧 Upload nhóm file POS (6.2a + 6.2b)", expanded=True):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            file_muc29_old = st.file_uploader(
                "🔹 POS 6.2a – File TRƯỚC 23/05 (MUC29_1600_old...)",
                type=["xls", "xlsx"],
                key="muc29_old",
            )
        with col_p2:
            file_muc29_new = st.file_uploader(
                "🔹 POS 6.2a – File SAU 23/05 (MUC29_1600_new...)",
                type=["xls", "xlsx"],
                key="muc29_new",
            )

        file_muc51 = st.file_uploader(
            "🔹 POS 6.2b – MUC51_1600",
            type=["xls", "xlsx"],
            key="muc51",
        )

    st.markdown("---")

    # =========================
    # NÚT CHẠY & XỬ LÝ
    # =========================
    run_button = st.button("🚀 Chạy xử lý THẺ + POS")

    if run_button:
        # Kiểm tra missing
        missing = []

        if not chi_nhanh:
            missing.append("Chi nhánh")

        if file_muc26 is None:
            missing.append("Mục 26")
        if file_code_ttd_policy is None:
            missing.append("Code TTD-NEW (Code tình trạng thẻ + Code Policy)")
        if not files_du_no_m:
            missing.append("Dư nợ tháng M")
        if not files_du_no_m1:
            missing.append("Dư nợ tháng M-1")
        if not files_du_no_m2:
            missing.append("Dư nợ tháng M-2")
        if not files_crm4:
            missing.append("CRM4")
        if not files_crm32:
            missing.append("CRM32")
        if not files_ckh:
            missing.append("HDV_CHITIET_CKH")
        if file_muc17 is None:
            missing.append("Mục 17")

        if file_muc29_old is None:
            missing.append("POS 6.2a – file TRƯỚC 23/05")
        if file_muc29_new is None:
            missing.append("POS 6.2a – file SAU 23/05")
        if file_muc51 is None:
            missing.append("POS 6.2b – MUC51_1600")

        if missing:
            st.error("❌ Thiếu dữ liệu: " + ", ".join(missing))
            return

        with st.spinner("⏳ Đang xử lý dữ liệu thẻ & POS..."):
            df_card, df_pos = process_the_pos(
                file_muc26=file_muc26,
                file_code_ttd_policy=file_code_ttd_policy,
                files_du_no_m=files_du_no_m,
                files_du_no_m1=files_du_no_m1,
                files_du_no_m2=files_du_no_m2,
                files_crm4=files_crm4,
                files_crm32=files_crm32,
                files_ckh=files_ckh,
                file_muc17=file_muc17,
                file_muc29_old=file_muc29_old,
                file_muc29_new=file_muc29_new,
                file_muc51=file_muc51,
                chi_nhanh=chi_nhanh,
                start_audit=datetime.combine(start_audit_date, datetime.min.time()),
                end_audit=datetime.combine(end_audit_date, datetime.min.time()),
            )

            st.session_state["df_card"] = df_card
            st.session_state["df_pos"] = df_pos

        st.success("✅ Đã xử lý xong! Xem kết quả ở các tab bên dưới.")

    # =========================
    # TAB HIỂN THỊ KẾT QUẢ
    # =========================
    tab1, tab2, tab3 = st.tabs(
        [
            "💳 Kết quả Thẻ (1.3.2)",
            "🏧 Kết quả POS (6,7,8)",
            "⬇️ Tải file Excel",
        ]
    )

    with tab1:
        st.subheader("💳 Bảng kết quả Thẻ – tiêu chí 1.3.2")
        if "df_card" in st.session_state:
            df_card = st.session_state["df_card"]
            st.write(f"Số dòng: **{len(df_card)}**")
            st.dataframe(df_card.head(50), use_container_width=True)
        else:
            st.info("Chưa có dữ liệu. Hãy chạy xử lý ở phía trên.")

    with tab2:
        st.subheader("🏧 Bảng kết quả POS – tiêu chí 6,7,8")
        if "df_pos" in st.session_state:
            df_pos = st.session_state["df_pos"]
            st.write(f"Số dòng: **{len(df_pos)}**")
            st.dataframe(df_pos.head(50), use_container_width=True)
        else:
            st.info("Chưa có dữ liệu. Hãy chạy xử lý ở phía trên.")

    with tab3:
        st.subheader("⬇️ Tải file Excel tổng hợp")

        if "df_card" in st.session_state:
            df_card = st.session_state["df_card"]
            df_pos = st.session_state["df_pos"]

            excel_bytes = df_to_excel_bytes(
                {
                    "THE_1600": df_card,
                    "POS_1600": df_pos,
                }
            )

            st.download_button(
                label="📥 Tải file Excel KQ_Tieu_chi_the_POS.xlsx",
                data=excel_bytes,
                file_name="KQ_Tieu_chi_the_POS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.info("Chưa có dữ liệu để tải. Hãy chạy xử lý trước.")
