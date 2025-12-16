def tong_hop_chuyen_tien(df: pd.DataFrame, so_nam: int = 3):

    if df.empty:
        raise DataValidationError("File không có dữ liệu.")

    # Chuẩn hóa USD
    df["QUY_DOI_USD"] = pd.to_numeric(df["QUY_DOI_USD"], errors="coerce").fillna(0)

    # Parse ngày
    df["TRAN_DATE"] = pd.to_datetime(df["TRAN_DATE"], errors="coerce")
    invalid_dates = int(df["TRAN_DATE"].isna().sum())

    df["YEAR"] = df["TRAN_DATE"].dt.year
    if df["YEAR"].notna().sum() == 0:
        raise DataValidationError("Không xác định được YEAR từ TRAN_DATE.")

    nam_max = int(df["YEAR"].max())
    cac_nam = [nam_max - i for i in range(so_nam - 1, -1, -1)]

    # Drop duplicate
    df = df.drop_duplicates(
        subset=["PART_NAME", "PURPOSE_OF_REMITTANCE", "TRAN_DATE", "TRAN_ID"]
    )

    ket_qua = pd.DataFrame()
    ds_muc_dich = df["PURPOSE_OF_REMITTANCE"].dropna().unique()

    if len(ds_muc_dich) == 0:
        raise DataValidationError("Không có PURPOSE_OF_REMITTANCE hợp lệ.")

    for muc_dich in ds_muc_dich:
        for nam in cac_nam:
            df_nam = df[
                (df["PURPOSE_OF_REMITTANCE"] == muc_dich) & (df["YEAR"] == nam)
            ]
            if df_nam.empty:
                continue

            pivot = (
                df_nam.groupby("PART_NAME")
                .agg(
                    tong_lan_nhan=("TRAN_ID", "count"),
                    tong_tien_usd=("QUY_DOI_USD", "sum"),
                )
                .reset_index()
            )

            pivot.rename(
                columns={
                    "tong_lan_nhan": f"{muc_dich}_LAN_{nam}",
                    "tong_tien_usd": f"{muc_dich}_TIEN_{nam}",
                },
                inplace=True,
            )

            ket_qua = pivot if ket_qua.empty else ket_qua.merge(
                pivot, on="PART_NAME", how="outer"
            )

    if ket_qua.empty:
        raise DataValidationError("Không có dữ liệu sau khi tổng hợp.")

    # Fill NA
    for col in ket_qua.columns:
        if "_LAN_" in col:
            ket_qua[col] = ket_qua[col].fillna(0).astype(int)
        elif "_TIEN_" in col:
            ket_qua[col] = ket_qua[col].fillna(0).astype(float)

    meta = {
        "nam_max": nam_max,
        "cac_nam": cac_nam,
        "invalid_dates": invalid_dates,
        "so_muc_dich": len(ds_muc_dich),
    }

    return ket_qua, meta
def run_chuyen_tien():
    st.title("Tổng hợp chuyển tiền")

    uploaded_file = st.file_uploader("Upload file Excel", type=["xlsx", "xls"])
    so_nam = st.number_input("Số năm gần nhất", 1, 10, 3)

    if not uploaded_file:
        st.info("📤 Vui lòng upload file Excel.")
        return

    try:
        df = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error("❌ Không đọc được file Excel.")
        st.exception(e)
        return

    # Kiểm tra cột
    missing_cols = REQUIRED_COLS - set(df.columns)
    if missing_cols:
        st.error("❌ File thiếu cột bắt buộc:")
        st.code("\n".join(missing_cols))
        return

    if st.button("Chạy tổng hợp", type="primary"):
        try:
            with st.spinner("Đang xử lý dữ liệu..."):
                ket_qua, meta = tong_hop_chuyen_tien(df, so_nam)

            # Warning mềm
            if meta["invalid_dates"] > 0:
                st.warning(
                    f"⚠️ Có {meta['invalid_dates']} dòng TRAN_DATE không parse được."
                )

            st.success(
                f"✅ Hoàn thành! Năm lớn nhất: {meta['nam_max']} | "
                f"Các năm: {meta['cac_nam']}"
            )

            st.dataframe(ket_qua, use_container_width=True)

        except DataValidationError as e:
            st.warning(f"⚠️ {str(e)}")

        except Exception as e:
            st.error("🔥 Lỗi hệ thống không mong muốn.")
            st.exception(e)
