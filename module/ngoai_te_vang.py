import io
import numpy as np
import pandas as pd
import streamlit as st

# ======================================================
#   MODULE: NGOẠI TỆ & VÀNG (FULL TIÊU CHÍ 1 → 6)
# ======================================================

def run_ngoai_te_vang():

    st.header("💱 NGHIỆP VỤ MUA BÁN NGOẠI TỆ / VÀNG – FULL 6 TIÊU CHÍ")

    st.caption("Tải đủ 4 file MUC49 – MUC19 – MUC20 – MUC21 rồi bấm **Chạy**")

    # ------------ UPLOAD FILES ------------
    c1, c2 = st.columns(2)
    with c1:
        f_fx   = st.file_uploader("📁 MUC49_1201.xlsx (FX gốc)", type=["xlsx"])
        f_a    = st.file_uploader("📁 Muc20_1201.xlsx (Rate Request – bảng A)", type=["xlsx"])
    with c2:
        f_b    = st.file_uploader("📁 Muc21_1201.xlsx (Forward – bảng B)", type=["xlsx"])
        f_m19  = st.file_uploader("📁 Muc19_1201.xlsx (Gốc lãi/lỗ)", type=["xlsx"])

    run = st.button("▶️ Chạy xử lý NT & Vàng", type="primary")

    if not run:
        return

    # --------------------------------------------------
    # Kiểm tra file upload
    # --------------------------------------------------
    missing = []
    if not f_fx: missing.append("MUC49 (FX)")
    if not f_a: missing.append("Mục 20")
    if not f_b: missing.append("Mục 21")
    if not f_m19: missing.append("Mục 19")

    if missing:
        st.error("❌ Thiếu file: " + ", ".join(missing))
        return

    # ======================================================
    # HÀM ĐỌC FILE
    # ======================================================
    def read_xlsx(file):
        return pd.read_excel(file, engine="openpyxl")

    df_fx   = read_xlsx(f_fx)
    df_a    = read_xlsx(f_a)
    df_b    = read_xlsx(f_b)
    df_m19  = read_xlsx(f_m19)

    # ======================================================
    # 1) TIÊU CHÍ 1 – 4 (FX GỐC)
    # ======================================================

    df_filtered = df_fx.copy()

    df_filtered = df_filtered[
        (df_filtered['CRNCY_PURCHSD'] != 'GD1') &
        (df_filtered['CRNCY_SOLD'] != 'GD1')
    ].copy()

    filter_dot = df_filtered['DEALER'].astype(str).str.contains('.', regex=False, na=False)
    filter_not_robot = ~df_filtered['DEALER'].astype(str).str.contains('ROBOT', case=False, regex=False, na=False)

    df_filtered = df_filtered[filter_dot & filter_not_robot].copy()

    # P/S
    df_filtered['P/S'] = np.where(df_filtered['PURCHASED_AMOUNT'].fillna(0) != 0, 'P',
                                  np.where(df_filtered['SOLD_AMOUNT'].fillna(0) != 0, 'S', ''))

    df_filtered['AMOUNT'] = np.where(df_filtered['P/S'] == 'P', df_filtered['PURCHASED_AMOUNT'], df_filtered['SOLD_AMOUNT'])
    df_filtered['Rate'] = np.where(df_filtered['P/S'] == 'P', df_filtered['PURCHASED_RATE'], df_filtered['SOLD_RATE'])
    df_filtered['Treasury Rate'] = np.where(df_filtered['P/S'] == 'P', df_filtered['TREASURY_BUY_RATE'], df_filtered['TREASURY_SELL_RATE'])

    # Info
    df_filtered['SOL'] = df_filtered['SOL_ID']
    df_filtered['Đơn vị'] = df_filtered['SOL_DESC']
    df_filtered['CIF'] = df_filtered['CIF_ID']
    df_filtered['Tên KH'] = df_filtered['CUST_NAME']

    df_filtered['DEAL_DATE'] = pd.to_datetime(df_filtered['DEAL_DATE'], errors='coerce')
    df_filtered['DUE_DATE'] = pd.to_datetime(df_filtered['DUE_DATE'], errors='coerce')
    df_filtered['TRANSACTION_NO'] = df_filtered['TRANSACTION_NO'].astype(str).str.strip()

    df_filtered['Quy đổi VND'] = df_filtered['VALUE_VND']
    df_filtered['Quy đổi USD'] = df_filtered['VALUE_USD']
    df_filtered['Mục đích'] = df_filtered['PURPOSE_OF_TRANSACTION']
    df_filtered['Kết quả Lãi/lỗ'] = df_filtered['KETQUA']
    df_filtered['Số tiền Lãi lỗ'] = df_filtered['SOTIEN_LAI_LO']

    # Maker – Checker
    df_filtered['Maker'] = df_filtered['DEALER'].apply(
        lambda x: str(x).strip() if pd.notnull(x) and 'ROBOT' not in str(x).upper() else ''
    )
    df_filtered['Maker Date'] = pd.to_datetime(df_filtered['MAKER_DATE'], errors='coerce')
    df_filtered['Checker'] = df_filtered['VERIFY_ID']
    df_filtered['Verify Date'] = pd.to_datetime(df_filtered['VERIFY_DATE'], errors='coerce')

    # ================= TIÊU CHÍ PHÂN LOẠI =================

    def contains(text, keys):
        if pd.isna(text):
            return False
        text = str(text).upper()
        return any(k in text for k in keys)

    df_filtered['GD bán ngoại tệ CK'] = df_filtered.apply(
        lambda x: 'X' if x['P/S'] == 'S' and contains(x['Mục đích'], ['CK']) else '', axis=1)

    df_filtered['GD bán ngoại tệ mặt'] = df_filtered.apply(
        lambda x: 'X' if x['P/S'] == 'S' and contains(x['Mục đích'], ['MAT']) else '', axis=1)

    df_filtered['Bán NT - Trợ cấp'] = df_filtered.apply(
        lambda x: 'X' if x['P/S'] == 'S' and contains(x['Mục đích'], ['TRO CAP']) else '', axis=1)

    df_filtered['Bán NT - Du học'] = df_filtered.apply(
        lambda x: 'X' if x['P/S'] == 'S' and contains(x['Mục đích'], ['DU HOC']) else '', axis=1)

    df_filtered['Bán NT - Du lịch'] = df_filtered.apply(
        lambda x: 'X' if x['P/S'] == 'S' and contains(x['Mục đích'], ['DU LICH']) else '', axis=1)

    df_filtered['Nhập sai mục đích'] = df_filtered.apply(
        lambda x: 'X' if (x['P/S'] == 'P' and contains(x['Mục đích'], ['BAN'])) or
                         (x['P/S'] == 'S' and contains(x['Mục đích'], ['MUA'])) else '',
        axis=1
    )

    # Lỗ > 100k
    df_filtered['GD lỗ >100.000đ'] = df_filtered.apply(
        lambda x: 'X' if x['Kết quả Lãi/lỗ'] == 'LO' and abs(x['Số tiền Lãi lỗ']) >= 100_000 else '',
        axis=1
    )

    # Duyệt trễ > 30p
    tre = df_filtered['Verify Date'] - df_filtered['Maker Date']
    df_filtered['GD duyệt trễ >30p'] = tre.apply(
        lambda x: 'X' if pd.notnull(x) and x.total_seconds() > 30 * 60 else ''
    )

    # ======================================================
    # 2) TIÊU CHÍ 5–6 (M19 – M20 – M21)
    # ======================================================

    df_m19['SOTIEN_LAI_LO'] = pd.to_numeric(df_m19['SOTIEN_LAI_LO'], errors='coerce')
    df_m19['GD lỗ >100k'] = df_m19['SOTIEN_LAI_LO'].apply(
        lambda x: 'X' if x <= -100_000 else ''
    )

    df_m19['MAKER_DATE'] = pd.to_datetime(df_m19['MAKER_DATE'], errors='coerce')
    df_m19['VERIFY_DATE'] = pd.to_datetime(df_m19['VERIFY_DATE'], errors='coerce')

    df_m19['DUYỆT_TRỄ_>20P'] = (
        (df_m19['VERIFY_DATE'] - df_m19['MAKER_DATE'])
            .dt.total_seconds()
            .apply(lambda x: 'X' if x > 20 * 60 else '')
    )

    # GHÉP RATE REQUEST
    df_a['FRWRD_CNTRCT_NUM'] = df_a['FRWRD_CNTRCT_NUM'].astype(str).str.strip()
    df_b['TRAN_ID'] = df_b['TRAN_ID'].astype(str).str.strip()

    set_rate = set(df_a['FRWRD_CNTRCT_NUM'].dropna()) | set(df_b['TRAN_ID'].dropna())

    df_m19['TRANSACTION_NO'] = df_m19['TRANSACTION_NO'].astype(str).str.strip()

    df_m19['GD Rate Request'] = df_m19['TRANSACTION_NO'].apply(
        lambda x: 'X' if x in set_rate else ''
    )

    # ======================================================
    # 3) HIỂN THỊ KẾT QUẢ
    # ======================================================

    t1, t2, t3, t4 = st.tabs([
        "📌 FX – Tiêu chí 1 → 4",
        "📌 Mục 19",
        "📌 Mục 20 + 21",
        "📌 Tổng hợp"
    ])

    with t1:
        st.dataframe(df_filtered)

    with t2:
        st.dataframe(df_m19)

    with t3:
        st.dataframe(df_a.merge(df_b, left_on="FRWRD_CNTRCT_NUM", right_on="TRAN_ID", how="left"))

    with t4:
        st.success("🎉 Đã xử lý đầy đủ 6 tiêu chí!")

    # ======================================================
    # 4) XUẤT EXCEL
    # ======================================================
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_filtered.to_excel(writer, sheet_name="TC1_4_FX", index=False)
        df_m19.to_excel(writer, sheet_name="TC5_6_Muc19", index=False)
        df_a.to_excel(writer, sheet_name="Muc20", index=False)
        df_b.to_excel(writer, sheet_name="Muc21", index=False)

    st.download_button(
        "⬇️ Tải file NT_Vang_Full.xlsx",
        data=out.getvalue(),
        file_name="NT_Vang_Full.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

