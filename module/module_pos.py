# # =========================================================
# # module_pos.py — Xử lý POS (6, 7, 8)
# # =========================================================

# import streamlit as st
# import pandas as pd

# from module.error_utils import UserFacingError, _should_reraise
# import numpy as np
# from datetime import datetime, date
# from dateutil.relativedelta import relativedelta
# import io
# from db.security import require_role


# # ------------------------------
# # Xuất file excel
# # ------------------------------
# def df_to_excel_bytes(df, sheet="DATA"):
#     buffer = io.BytesIO()
#     with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
#         df.to_excel(writer, sheet_name=sheet[:31], index=False)
#     buffer.seek(0)
#     return buffer


# # ------------------------------
# # Chuẩn hóa 6.2a
# # ------------------------------
# def standardize_6_2a_two_files(file_before, file_after):

#     # --- Đọc file trước 23/05 ---
#     df_before = pd.read_excel(file_before, dtype=str)

#     # --- Đọc file sau 23/05 ---
#     df_after = pd.read_excel(file_after, dtype=str)

#     # Mapping cho file cũ
#     map_before = {
#         "MACN_POS": "BRANCH_CODE",
#         "IDPOS": "MERCHANT_ID",
#         "TENPOS": "MERCHANT_NAME",
#         "TRANDT": "TRANS_DATE",
#         "TRANAMT_QD": "TRANS_AMT",
#     }

#     # Mapping file mới
#     map_after = {
#         "BRANCH_CODE": "BRANCH_CODE",
#         "MERCHANT_ID": "MERCHANT_ID",
#         "MERCHANT_NAME": "MERCHANT_NAME",
#         "TRANS_DATE": "TRANS_DATE",
#         "TRANS_AMT": "TRANS_AMT",
#     }

#     # Lấy đúng cột
#     df1 = df_before[[c for c in map_before if c in df_before.columns]].rename(columns=map_before)
#     df2 = df_after[[c for c in map_after if c in df_after.columns]].rename(columns=map_after)

#     # Ghép
#     df = pd.concat([df1, df2], ignore_index=True)

#     # Chuẩn hóa ngày
#     df["TRANS_DATE"] = pd.to_datetime(df["TRANS_DATE"], errors="coerce")

#     # Chuẩn hóa số doanh số
#     df["TRANS_AMT"] = (
#         df["TRANS_AMT"]
#         .astype(str)
#         .str.replace(r"[^\d\.-]", "", regex=True)
#         .replace("", "0")
#         .astype(float)
#     )

#     df["MERCHANT_ID"] = df["MERCHANT_ID"].astype(str)

#     return df


# # ------------------------------
# # XỬ LÝ POS CHÍNH
# # ------------------------------
# def process_pos_only(file_before_2305, file_after_2305, file_6_2b,
#                      start_audit, end_audit):

#     # 6.2a – doanh số POS
#     df_trans = standardize_6_2a_two_files(file_before_2305, file_after_2305)

#     # 6.2b – danh sách MID
#     df_pos = pd.read_excel(file_6_2b, dtype=str)

#     # Chuẩn hóa
#     if "MID" not in df_pos.columns:
#         raise Exception("❌ File 6.2b bị thiếu cột MID!")

#     df_pos["MID"] = df_pos["MID"].astype(str)
#     df_trans["MERCHANT_ID"] = df_trans["MERCHANT_ID"].astype(str)

#     # Chuyển Device status (nếu có)
#     if "DEVICE_STATUS" in df_pos.columns:
#         df_pos["DEVICE_STATUS"] = df_pos["DEVICE_STATUS"].astype(str)
#     else:
#         df_pos["DEVICE_STATUS"] = "Unknown"

#     # -----------------------------------------------
#     # Hàm tính doanh số theo khoảng thời gian
#     # -----------------------------------------------
#     def cal_rev(df_trans_local, df_pos_local, d1, d2):
#         mask = (df_trans_local["TRANS_DATE"] >= d1) & (df_trans_local["TRANS_DATE"] <= d2)
#         g = (
#             df_trans_local.loc[mask]
#             .groupby("MERCHANT_ID")["TRANS_AMT"]
#             .sum()
#             .reset_index()
#             .rename(columns={"MERCHANT_ID": "MID", "TRANS_AMT": "REV"})
#         )

#         # Merge đúng key MID
#         merged = df_pos_local[["MID"]].merge(g, on="MID", how="left")

#         return merged["REV"].fillna(0).astype(float)

#     # Lấy năm từ end_audit
#     y = end_audit.year

#     # Tính doanh số T-2, T-1, T
#     df_pos["DS_T2"] = cal_rev(df_trans, df_pos, datetime(y - 2, 1, 1), datetime(y - 2, 12, 31))
#     df_pos["DS_T1"] = cal_rev(df_trans, df_pos, datetime(y - 1, 1, 1), datetime(y - 1, 12, 31))
#     df_pos["DS_T"] = cal_rev(df_trans, df_pos, datetime(y, 1, 1), datetime(y, 12, 31))

#     df_pos["TONG_3N"] = df_pos["DS_T2"] + df_pos["DS_T1"] + df_pos["DS_T"]

#     # -----------------------------------------
#     # 3 tháng gần nhất
#     # -----------------------------------------
#     start_3m = (end_audit.replace(day=1) - relativedelta(months=2)).replace(day=1)
#     df_pos["DS_3T"] = cal_rev(df_trans, df_pos, start_3m, end_audit)
#     df_pos["DSBQ_3T"] = (df_pos["DS_3T"] / 3).round(2)

#     # -----------------------------------------
#     # Tiêu chí POS ĐANG HOẠT ĐỘNG
#     # -----------------------------------------
#     df_pos["POS_ACTIVE"] = np.where(df_pos["DEVICE_STATUS"] == "Device OK", "X", "")

#     # -----------------------------------------
#     # TOP POS doanh số cao nhất
#     # -----------------------------------------
#     df_active = df_pos[df_pos["POS_ACTIVE"] == "X"]

#     if not df_active.empty:
#         top10_total = df_active.nlargest(10, "TONG_3N")["MID"]
#         top10_3T = df_active.nlargest(10, "DS_3T")["MID"]
#     else:
#         top10_total = pd.Series([], dtype=str)
#         top10_3T = pd.Series([], dtype=str)

#     df_pos["TOP_3NAM"] = df_pos["MID"].apply(lambda x: "X" if x in top10_total.values else "")
#     df_pos["TOP_3THANG"] = df_pos["MID"].apply(lambda x: "X" if x in top10_3T.values else "")

#     # -----------------------------------------
#     # POS KPS doanh số 3 tháng
#     # -----------------------------------------
#     df_pos["POS_KPS_3T"] = np.where(
#         (df_pos["POS_ACTIVE"] == "X") & (df_pos["DS_3T"] == 0),
#         "X",
#         "",
#     )

#     # POS doanh số thấp
#     df_pos["POS_DS_THAP"] = np.where(
#         (df_pos["POS_ACTIVE"] == "X") & (df_pos["DSBQ_3T"] < 20_000_000),
#         "X",
#         "",
#     )

#     return df_pos


# # =========================================================
# # MODULE STREAMLIT
# # =========================================================
# def run_module_pos():
#     try:
#         _run_module_pos()
#     except UserFacingError:
#         raise
#     except Exception as exc:
#         if _should_reraise(exc):
#             raise

#         raise UserFacingError(
#             "Đã xảy ra lỗi khi xử lý Tiêu chí máy POS. Vui lòng kiểm tra file đầu vào và thử lại."
#         ) from exc


# def _run_module_pos():
    
    
#     st.markdown("**Upload 3 file:6.2a trước 23/05, 6.2a sau 23/05, 6.2b (MUC51)**")

#     start_date = st.date_input("Ngày bắt đầu THKT", value=date(2025, 1, 1))
#     end_date = st.date_input("Ngày kết thúc THKT", value=date(2025, 10, 31))

#     col1, col2 = st.columns(2)
#     with col1:
#         file_old = st.file_uploader("📂 6.2a – File TRƯỚC 23/05", type=["xls", "xlsx"])
#     with col2:
#         file_new = st.file_uploader("📂 6.2a – File SAU 23/05", type=["xls", "xlsx"])

#     file_6_2b = st.file_uploader("📂 6.2b – MUC51_sol", type=["xls", "xlsx"])

#     run_button = st.button("🚀 Chạy POS")

#     if run_button:
#         if not file_old or not file_new or not file_6_2b:
#             st.error("❌ Thiếu file POS!")
#             return

#         with st.spinner("⏳ Đang xử lý…"):
#             df_pos = process_pos_only(
#                 file_old,
#                 file_new,
#                 file_6_2b,
#                 start_audit=datetime.combine(start_date, datetime.min.time()),
#                 end_audit=datetime.combine(end_date, datetime.min.time())
#             )

#         st.success("✔ Xử lý hoàn tất!")

#         st.subheader("📊 Kết quả POS")
#         st.dataframe(df_pos, use_container_width=True)

#         st.subheader("📥 Tải xuống Excel")
#         st.download_button(
#             "⬇ Tải file KQ_POS.xlsx",
#             data=df_to_excel_bytes(df_pos, "POS"),
#             file_name="KQ_POS.xlsx"
#         )
# =========================================================
# module_pos.py — Xử lý POS
# =========================================================

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io

from module.error_utils import UserFacingError, _should_reraise
from db.security import require_role


# =========================================================
# 1. XUẤT FILE EXCEL
# =========================================================
def df_to_excel_bytes(df, sheet="DATA"):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=sheet[:31], index=False)
    buffer.seek(0)
    return buffer


# =========================================================
# 2. CLEAN MONEY VN
# =========================================================
def clean_money_vn(series):
    """
    Chuẩn hóa số tiền VN:
    - 1,000,000
    - 1.000.000
    - 1 000 000
    - text có ký tự khác
    """
    return (
        series.fillna("0")
        .astype(str)
        .str.replace(r"[^\d]", "", regex=True)
        .replace("", "0")
        .astype("int64")
    )


# =========================================================
# 3. CLEAN DATE AUTO
# =========================================================
def clean_date(series):
    """
    Tự nhận diện ngày:
    - YYYYMMDD
    - dd/mm/yyyy
    - yyyy-mm-dd
    - số serial Excel
    """
    s = series.astype(str).str.strip()

    # Trường hợp số serial Excel
    numeric_s = pd.to_numeric(s, errors="coerce")
    if numeric_s.notna().mean() > 0.8 and numeric_s.dropna().between(20000, 60000).mean() > 0.8:
        return pd.to_datetime(numeric_s, unit="D", origin="1899-12-30", errors="coerce")

    # Trường hợp YYYYMMDD
    if s.str.match(r"^\d{8}$").mean() > 0.8:
        return pd.to_datetime(s, format="%Y%m%d", errors="coerce")

    # Trường hợp dd/mm/yyyy hoặc các định dạng thường gặp
    return pd.to_datetime(s, dayfirst=True, errors="coerce")


# =========================================================
# 4. LOAD MỤC 29 - GIAO DỊCH POS
# =========================================================
def load_muc29(file_before_2305, file_after_2305):
    """
    File trước 23/05 có thể có cột:
    - MACN_POS
    - MCTID hoặc IDPOS
    - TENPOS
    - TRANDT
    - TRANAMT_QD

    File sau 23/05 có thể có cột:
    - BRANCH_CODE
    - MERCHANT_ID
    - MERCHANT_NAME
    - TRANS_DATE
    - TRANS_AMT
    """

    df_old = pd.read_excel(file_before_2305, dtype=str)
    df_new = pd.read_excel(file_after_2305, dtype=str)

    # Mapping file cũ
    map_old = {
        "MACN_POS": "BRANCH_CODE",
        "MCTID": "MERCHANT_ID",
        "IDPOS": "MERCHANT_ID",
        "TENPOS": "MERCHANT_NAME",
        "TRANDT": "TRANS_DATE",
        "TRANAMT_QD": "TRANS_AMT",
    }

    # Mapping file mới
    map_new = {
        "BRANCH_CODE": "BRANCH_CODE",
        "MERCHANT_ID": "MERCHANT_ID",
        "MERCHANT_NAME": "MERCHANT_NAME",
        "TRANS_DATE": "TRANS_DATE",
        "TRANS_AMT": "TRANS_AMT",
    }

    df_old = df_old.rename(columns=map_old)
    df_new = df_new.rename(columns=map_new)

    required_cols = ["MERCHANT_ID", "TRANS_DATE", "TRANS_AMT"]

    missing_old = [c for c in required_cols if c not in df_old.columns]
    missing_new = [c for c in required_cols if c not in df_new.columns]

    if missing_old:
        raise UserFacingError(
            f"File 6.2a trước 23/05 thiếu cột sau khi mapping: {missing_old}. "
            f"Vui lòng kiểm tra các cột MCTID/IDPOS, TRANDT, TRANAMT_QD."
        )

    if missing_new:
        raise UserFacingError(
            f"File 6.2a sau 23/05 thiếu cột sau khi mapping: {missing_new}. "
            f"Vui lòng kiểm tra các cột MERCHANT_ID, TRANS_DATE, TRANS_AMT."
        )

    df_old = df_old[required_cols].copy()
    df_new = df_new[required_cols].copy()

    df_all = pd.concat([df_old, df_new], ignore_index=True)

    df_all["TRANS_DATE"] = clean_date(df_all["TRANS_DATE"])
    df_all["TRANS_AMT"] = clean_money_vn(df_all["TRANS_AMT"])

    df_all["MERCHANT_ID"] = (
        df_all["MERCHANT_ID"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    df_all = df_all[df_all["MERCHANT_ID"].notna()]
    df_all = df_all[df_all["MERCHANT_ID"] != ""]
    df_all = df_all[df_all["MERCHANT_ID"].str.lower() != "nan"]

    return df_all


# =========================================================
# 5. LOAD MỤC 51 - DANH SÁCH POS / MID
# =========================================================
def load_muc51(file_6_2b):
    df_pos = pd.read_excel(file_6_2b, dtype=str)

    if "MID" not in df_pos.columns:
        raise UserFacingError("File 6.2b / Mục 51 bị thiếu cột MID.")

    df_pos["MID"] = (
        df_pos["MID"]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )

    # Nếu thiếu DEVICE_STATUS thì tự tạo để không lỗi
    if "DEVICE_STATUS" not in df_pos.columns:
        df_pos["DEVICE_STATUS"] = "Unknown"
    else:
        df_pos["DEVICE_STATUS"] = df_pos["DEVICE_STATUS"].astype(str).str.strip()

    # Clean MERCHANT_CIF nếu có
    if "MERCHANT_CIF" in df_pos.columns:
        s = df_pos["MERCHANT_CIF"].fillna("").astype(str).str.strip()
        s = s.str.replace(r"^[A-Za-z]", "", regex=True)
        s = s.str.replace(r"\D+", "", regex=True).str[-9:]
        df_pos["MERCHANT_CIF"] = s.mask(s == "", None)

    # Chuẩn hóa DATE_OPEN_MID nếu có
    if "DATE_OPEN_MID" in df_pos.columns:
        df_pos["DATE_OPEN_MID"] = clean_date(df_pos["DATE_OPEN_MID"])

    return df_pos


# =========================================================
# 6. TÍNH DOANH SỐ 3 NĂM
# =========================================================
def calculate_3years(df_trans, df_pos, end_audit):
    """
    Tính doanh số theo 3 năm:
    - T-2
    - T-1
    - T

    Trong đó T = năm của ngày kết thúc thời hiệu kiểm toán.
    """

    df_trans = df_trans.copy()
    df_pos = df_pos.copy()

    y = end_audit.year

    df_trans["YEAR"] = df_trans["TRANS_DATE"].dt.year

    revenue = (
        df_trans.groupby(["MERCHANT_ID", "YEAR"])["TRANS_AMT"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
        .rename(columns={"MERCHANT_ID": "MID"})
    )

    df_pos = df_pos.merge(revenue, on="MID", how="left")

    df_pos["DSỐ_2_NĂM_TRƯỚC_T2"] = df_pos[y - 2] if y - 2 in df_pos.columns else 0
    df_pos["DSỐ_NĂM_TRƯỚC_T1"] = df_pos[y - 1] if y - 1 in df_pos.columns else 0
    df_pos["DSỐ_NĂM_NAY_T"] = df_pos[y] if y in df_pos.columns else 0

    df_pos["DSỐ_2_NĂM_TRƯỚC_T2"] = df_pos["DSỐ_2_NĂM_TRƯỚC_T2"].fillna(0)
    df_pos["DSỐ_NĂM_TRƯỚC_T1"] = df_pos["DSỐ_NĂM_TRƯỚC_T1"].fillna(0)
    df_pos["DSỐ_NĂM_NAY_T"] = df_pos["DSỐ_NĂM_NAY_T"].fillna(0)

    df_pos["TỔNG_DSỐ_3_NĂM"] = (
        df_pos["DSỐ_2_NĂM_TRƯỚC_T2"]
        + df_pos["DSỐ_NĂM_TRƯỚC_T1"]
        + df_pos["DSỐ_NĂM_NAY_T"]
    )

    # Xóa các cột năm phát sinh từ pivot nếu muốn bảng gọn
    year_cols = [c for c in df_pos.columns if isinstance(c, int)]
    df_pos = df_pos.drop(columns=year_cols, errors="ignore")

    return df_pos


# =========================================================
# 7. TÍNH DOANH SỐ 3 THÁNG GẦN NHẤT
# =========================================================
def calculate_3months(df_trans, df_pos, start_3m, end_3m):
    df_trans = df_trans.copy()
    df_pos = df_pos.copy()

    df_3m = df_trans[
        (df_trans["TRANS_DATE"] >= start_3m)
        & (df_trans["TRANS_DATE"] <= end_3m)
    ]

    rev_3m = (
        df_3m.groupby("MERCHANT_ID")["TRANS_AMT"]
        .sum()
        .reset_index()
        .rename(
            columns={
                "MERCHANT_ID": "MID",
                "TRANS_AMT": "DSỐ_3_THÁNG_GẦN_NHẤT",
            }
        )
    )

    df_pos = df_pos.merge(rev_3m, on="MID", how="left")

    df_pos["DSỐ_3_THÁNG_GẦN_NHẤT"] = (
        df_pos["DSỐ_3_THÁNG_GẦN_NHẤT"]
        .fillna(0)
        .astype(float)
    )

    df_pos["DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT"] = (
        df_pos["DSỐ_3_THÁNG_GẦN_NHẤT"] / 3
    ).round(0)

    return df_pos


# =========================================================
# 8. ĐÁNH DẤU TIÊU CHÍ POS
# =========================================================
def apply_flags(df_pos):
    df_pos = df_pos.copy()

    df_pos["POS_ĐANG_HOẠT_ĐỘNG"] = np.where(
        df_pos["DEVICE_STATUS"].astype(str).str.strip() == "Device OK",
        "X",
        "",
    )

    df_active = df_pos[df_pos["POS_ĐANG_HOẠT_ĐỘNG"] == "X"].copy()

    if not df_active.empty:
        top10_total = df_active.nlargest(10, "TỔNG_DSỐ_3_NĂM")["MID"]
    else:
        top10_total = pd.Series([], dtype=str)

    df_pos["POS TOP10 3 NĂM"] = df_pos["MID"].apply(
        lambda x: "X" if x in top10_total.values else ""
    )

    df_pos["POS KPS 3 THÁNG"] = np.where(
        (df_pos["POS_ĐANG_HOẠT_ĐỘNG"] == "X")
        & (df_pos["DSỐ_3_THÁNG_GẦN_NHẤT"] == 0),
        "X",
        "",
    )

    df_pos["POS BQ <20TR"] = np.where(
        (df_pos["POS_ĐANG_HOẠT_ĐỘNG"] == "X")
        & (df_pos["DSỐ BQ/THÁNG TRONG 3 THÁNG GẦN NHẤT"] < 20_000_000),
        "X",
        "",
    )

    return df_pos


# =========================================================
# 9. XỬ LÝ POS CHÍNH
# =========================================================
def process_pos_only(file_before_2305, file_after_2305, file_6_2b, start_audit, end_audit):

    if start_audit > end_audit:
        raise UserFacingError("Ngày bắt đầu thời hiệu không được lớn hơn ngày kết thúc thời hiệu.")

    # Load Mục 29
    df_trans = load_muc29(file_before_2305, file_after_2305)

    # Load Mục 51
    df_pos = load_muc51(file_6_2b)

    # Tính 3 tháng gần nhất theo end_audit
    start_3m = (end_audit.replace(day=1) - relativedelta(months=2)).replace(day=1)
    end_3m = end_audit

    # Tính doanh số 3 năm
    df_pos = calculate_3years(df_trans, df_pos, end_audit)

    # Tính doanh số 3 tháng
    df_pos = calculate_3months(df_trans, df_pos, start_3m, end_3m)

    # Đánh dấu tiêu chí
    df_pos = apply_flags(df_pos)

    # Thêm thông tin thời hiệu để dễ kiểm tra
    df_pos["THKT_TỪ_NGÀY"] = start_audit.date()
    df_pos["THKT_ĐẾN_NGÀY"] = end_audit.date()
    df_pos["KHOẢNG_3_THÁNG_TỪ"] = start_3m.date()
    df_pos["KHOẢNG_3_THÁNG_ĐẾN"] = end_3m.date()

    return df_pos


# =========================================================
# 10. MODULE STREAMLIT
# =========================================================
def run_module_pos():
    try:
        _run_module_pos()
    except UserFacingError:
        raise
    except Exception as exc:
        if _should_reraise(exc):
            raise

        raise UserFacingError(
            "Đã xảy ra lỗi khi xử lý Tiêu chí máy POS. "
            "Vui lòng kiểm tra file đầu vào, tên cột và định dạng ngày/số tiền."
        ) from exc


def _run_module_pos():

    st.markdown("## 🧾 Xử lý POS")
    st.markdown("**Upload 3 file: 6.2a trước 23/05, 6.2a sau 23/05, 6.2b / Mục 51**")

    start_date = st.date_input("Ngày bắt đầu THKT", value=date(2025, 1, 1))
    end_date = st.date_input("Ngày kết thúc THKT", value=date(2025, 10, 31))

    start_3m_preview = (
        datetime.combine(end_date, datetime.min.time()).replace(day=1)
        - relativedelta(months=2)
    ).replace(day=1)

    st.info(
        f"Khoảng 3 tháng gần nhất sẽ tính từ "
        f"**{start_3m_preview.date()}** đến **{end_date}**."
    )

    col1, col2 = st.columns(2)

    with col1:
        file_old = st.file_uploader(
            "📂 6.2a – File TRƯỚC 23/05",
            type=["xls", "xlsx"],
        )

    with col2:
        file_new = st.file_uploader(
            "📂 6.2a – File SAU 23/05",
            type=["xls", "xlsx"],
        )

    file_6_2b = st.file_uploader(
        "📂 6.2b – Mục 51 / Danh sách MID",
        type=["xls", "xlsx"],
    )

    run_button = st.button("🚀 Chạy POS")

    if run_button:

        if not file_old or not file_new or not file_6_2b:
            st.error("❌ Thiếu file POS. Vui lòng upload đủ 3 file.")
            return

        with st.spinner("⏳ Đang xử lý POS..."):
            df_pos = process_pos_only(
                file_old,
                file_new,
                file_6_2b,
                start_audit=datetime.combine(start_date, datetime.min.time()),
                end_audit=datetime.combine(end_date, datetime.min.time()),
            )

        st.success("✔ Xử lý hoàn tất!")

        st.subheader("📊 Kết quả POS")
        st.dataframe(df_pos, use_container_width=True)

        # Tổng hợp nhanh
        st.subheader("📌 Tổng hợp nhanh")

        col_a, col_b, col_c, col_d = st.columns(4)

        with col_a:
            st.metric(
                "POS đang hoạt động",
                int((df_pos["POS_ĐANG_HOẠT_ĐỘNG"] == "X").sum()),
            )

        with col_b:
            st.metric(
                "POS TOP10 3 năm",
                int((df_pos["POS TOP10 3 NĂM"] == "X").sum()),
            )

        with col_c:
            st.metric(
                "POS KPS 3 tháng",
                int((df_pos["POS KPS 3 THÁNG"] == "X").sum()),
            )

        with col_d:
            st.metric(
                "POS BQ <20TR",
                int((df_pos["POS BQ <20TR"] == "X").sum()),
            )

        st.subheader("📥 Tải xuống Excel")

        st.download_button(
            "⬇ Tải file KQ_POS.xlsx",
            data=df_to_excel_bytes(df_pos, "POS"),
            file_name="KQ_POS.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
