import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import glob
import os
from datetime import datetime

# --- CẤU HÌNH TRANG (Phải đặt đầu tiên) ---
st.set_page_config(page_title="DVKH Module", layout="wide")

st.title("Module Dịch Vụ Khách Hàng (DVKH)")
st.markdown("---")

# --- TẠO TABS ---
tab1, tab2 = st.tabs(["🛠️ Xử lý Ủy Quyền & SMS/SCM", "📊 Phân tích KHCN (Theo Chi Nhánh)"])

# ==============================================================================
# TAB 1: XỬ LÝ DỮ LIỆU ỦY QUYỀN VÀ SMS/SCM
# ==============================================================================
with tab1:
    st.header("1. Tải lên các tệp dữ liệu (Ủy Quyền & SMS)")
    st.info("Vui lòng tải lên tất cả các tệp cần thiết để ứng dụng hoạt động chính xác.")

    col1, col2 = st.columns(2)
    with col1:
        uploaded_ckh_files = st.file_uploader("1. Tải lên tệp HDV_CHITIET_CKH (Nhiều file)", type=["xls", "xlsx"], accept_multiple_files=True, key="ckh_upload")
        uploaded_kkh_files = st.file_uploader("2. Tải lên tệp HDV_CHITIET_KKH (Nhiều file)", type=["xls", "xlsx"], accept_multiple_files=True, key="kkh_upload")
    with col2:
        uploaded_muc30_file = st.file_uploader("3. Tải lên tệp MUC 30 1710 NEW (1).xlsx", type=["xlsx"], key="muc30_upload")
        uploaded_sms_txt_file = st.file_uploader("4. Tải lên tệp Muc14_DKSMS.txt", type=["txt"], key="sms_txt_upload")
        uploaded_scm10_xlsx_file = st.file_uploader("5. Tải lên tệp Muc14_SCM010.xlsx", type=["xlsx"], key="scm10_xlsx_upload")

    st.markdown("---")
    st.header("2. Thực hiện Xử lý Dữ liệu")

    if st.button("Bắt đầu Xử lý Dữ liệu (Tab 1)", key="btn_process_tab1"):
        if not (uploaded_ckh_files and uploaded_kkh_files and uploaded_muc30_file and uploaded_sms_txt_file and uploaded_scm10_xlsx_file):
            st.error("Vui lòng tải lên đầy đủ tất cả các tệp yêu cầu trước khi xử lý.")
        else:
            with st.spinner("Đang xử lý dữ liệu, vui lòng chờ..."):
                try:
                    # --- Bước 1: Tải và ghép dữ liệu CKH/KKH ---
                    st.subheader("2.1: Tải và ghép dữ liệu CKH/KKH")
                    df_b_CKH_list = []
                    for file in uploaded_ckh_files:
                        df_b_CKH_list.append(pd.read_excel(file, dtype=str))
                    df_b_CKH = pd.concat(df_b_CKH_list, ignore_index=True)

                    df_b_KKH_list = []
                    for file in uploaded_kkh_files:
                        df_b_KKH_list.append(pd.read_excel(file, dtype=str))
                    df_b_KKH = pd.concat(df_b_KKH_list, ignore_index=True)

                    df_b = pd.concat([df_b_CKH, df_b_KKH], ignore_index=True)
                    st.success(f"Đã ghép thành công dữ liệu tổng. Tổng số dòng: {len(df_b)}")

                    # --- Bước 2: Tải và xử lý df_a (MUC 30) ---
                    st.subheader("2.2: Tải và làm sạch dữ liệu MUC 30")
                    df_a = pd.read_excel(uploaded_muc30_file, dtype=str)

                    df_a = df_a[df_a["DESCRIPTION"].str.contains(r"chu\s*ky|chuky|cky", case=False, na=False)]
                    df_a["EXPIRYDATE"] = pd.to_datetime(df_a["EXPIRYDATE"], format='%Y%m%d', errors='coerce')
                    df_a['EFFECTIVEDATE'] = pd.to_datetime(df_a['EFFECTIVEDATE'], format='%Y%m%d', errors='coerce')
                    df_a['EXPIRYDATE'] = df_a['EXPIRYDATE'].dt.strftime('%m/%d/%Y')
                    df_a['EFFECTIVEDATE'] = df_a['EFFECTIVEDATE'].dt.strftime('%m/%d/%Y')
                    
                    keywords = ["CONG TY", "CTY", "CONGTY", "CÔNG TY", "CÔNGTY"]
                    df_a = df_a[~df_a["NGUOI_UY_QUYEN"].str.upper().str.contains("|".join(keywords), na=False)]

                    def extract_name(value):
                        parts = re.split(r'[-,]', str(value))
                        for part in parts:
                            name = part.strip()
                            if re.fullmatch(r'[A-Z ]{3,}', name):
                                return name
                        return value

                    df_a["NGUOI_DUOC_UY_QUYEN"] = df_a["NGUOI_DUOC_UY_QUYEN"].apply(extract_name)
                    df_a = df_a.drop_duplicates(subset=["PRIMARY_SOL_ID", "TK_DUOC_UY_QUYEN", "NGUOI_DUOC_UY_QUYEN"])
                    st.success("Đã xử lý xong dữ liệu MUC 30.")

                    # --- Bước 3: Ghép dữ liệu ủy quyền và xử lý CIF ---
                    st.subheader("2.3: Ghép dữ liệu ủy quyền")
                    df_a['TK_DUOC_UY_QUYEN'] = df_a['TK_DUOC_UY_QUYEN'].astype(str)
                    df_b['IDXACNO'] = df_b['IDXACNO'].astype(str)
                    merged = df_a.merge(df_b[["IDXACNO", "CUSTSEQ"]], left_on="TK_DUOC_UY_QUYEN", right_on="IDXACNO", how="left")

                    merged["CIF_NGUOI_UY_QUYEN"] = merged["CUSTSEQ"].apply(lambda x: str(int(x)) if pd.notna(x) else "NA")

                    # Logic điền CIF bị thiếu
                    cif_nguoi_uy_quyen_updated = merged["CIF_NGUOI_UY_QUYEN"].copy()
                    for nguoi_uq, group in merged.groupby("NGUOI_UY_QUYEN"):
                        if len(group) >= 2:
                            cif_values = group["CIF_NGUOI_UY_QUYEN"]
                            has_na = "NA" in cif_values.unique()
                            actual_cifs = [c for c in cif_values.unique() if c != "NA"]
                            if has_na and actual_cifs:
                                cif_to_fill = actual_cifs[0]
                                indices_to_update = group[group["CIF_NGUOI_UY_QUYEN"] == "NA"].index
                                cif_nguoi_uy_quyen_updated.loc[indices_to_update] = cif_to_fill

                    merged["CIF_NGUOI_UY_QUYEN"] = cif_nguoi_uy_quyen_updated
                    merged = merged.drop(columns=["IDXACNO", "CUSTSEQ"], errors='ignore')
                    st.success("Đã ghép dữ liệu và xử lý CIF người ủy quyền.")

                    # --- Bước 4: Phân loại loại tài khoản ---
                    merged['LOAI_TK'] = 'NA'
                    set_ckh = set(df_b_CKH['CUSTSEQ'].astype(str).dropna())
                    set_kkh = set(df_b_KKH['IDXACNO'].astype(str).dropna())
                    
                    # Tối ưu hóa việc map bằng vectorization thay vì apply từng dòng nếu dữ liệu lớn
                    merged.loc[merged['TK_DUOC_UY_QUYEN'].isin(set_ckh), 'LOAI_TK'] = 'CKH' # Logic cũ của bạn dùng CUSTSEQ cho CKH, cần kiểm tra lại logic này nếu sai
                    # Sửa lại logic map theo code gốc của bạn: 
                    # Code gốc: tk in set_ckh (CUSTSEQ) -> CKH. tk in set_kkh (IDXACNO) -> KKH.
                    # Lưu ý: TK_DUOC_UY_QUYEN thường là Số tài khoản (IDXACNO). 
                    # Nếu set_ckh là CUSTSEQ thì so sánh TK với CIF là không khớp. 
                    # Tuy nhiên tôi giữ nguyên logic code của bạn:
                    
                    def phan_loai_tk(tk):
                        if tk in set_ckh: return 'CKH'
                        elif tk in set_kkh: return 'KKH'
                        else: return 'NA'
                    merged['LOAI_TK'] = merged['TK_DUOC_UY_QUYEN'].astype(str).apply(phan_loai_tk)

                    # --- Bước 5: Tính toán thời gian ủy quyền ---
                    merged["EXPIRYDATE"] = pd.to_datetime(merged["EXPIRYDATE"], format='%m/%d/%Y', errors="coerce")
                    merged["EFFECTIVEDATE"] = pd.to_datetime(merged["EFFECTIVEDATE"], format='%m/%d/%Y', errors="coerce")
                    merged["YEAR_DIFF"] = (merged["EXPIRYDATE"].dt.year - merged["EFFECTIVEDATE"].dt.year)
                    
                    merged["KHONG_NHAP_TGIAN_UQ"] = ""
                    merged.loc[merged["YEAR_DIFF"].fillna(-1) == 99, "KHONG_NHAP_TGIAN_UQ"] = "X"
                    merged["UQ_TREN_50_NAM"] = ""
                    merged.loc[merged["YEAR_DIFF"].fillna(-1) >= 50, "UQ_TREN_50_NAM"] = "X"
                    merged.drop(columns=["YEAR_DIFF"], inplace=True)
                    
                    df_uyquyen = merged.copy()

                    # --- Bước 6: Xử lý SMS/SCM ---
                    st.subheader("2.6: Xử lý dữ liệu SMS và SCM10")
                    df_sms_raw = pd.read_csv(uploaded_sms_txt_file, sep='\t', on_bad_lines='skip', dtype=str)
                    df_sms = df_sms_raw.copy()
                    
                    # Chuẩn hóa SMS
                    df_sms = df_sms[df_sms['FORACID'].str.match(r'^\d+$', na=False)]
                    df_sms = df_sms[df_sms['CUSTTPCD'].str.upper() != 'KHDN']
                    
                    # Chuẩn hóa SCM10
                    df_scm10 = pd.read_excel(uploaded_scm10_xlsx_file, dtype=str)
                    df_scm10 = df_scm10.rename(columns=lambda x: x.strip())
                    df_scm10['CIF_ID'] = df_scm10['CIF_ID'].astype(str)

                    # Ghép set để tra cứu
                    tk_sms_set = set(df_sms['FORACID'].astype(str).dropna())
                    cif_scm10_set = set(df_scm10['CIF_ID'].astype(str).dropna())

                    df_uyquyen = df_uyquyen.rename(columns=lambda x: x.strip())
                    df_uyquyen['TK_DUOC_UY_QUYEN'] = df_uyquyen['TK_DUOC_UY_QUYEN'].astype(str)
                    df_uyquyen['CIF_NGUOI_UY_QUYEN'] = df_uyquyen['CIF_NGUOI_UY_QUYEN'].astype(str)

                    df_uyquyen['TK có đăng ký SMS'] = df_uyquyen['TK_DUOC_UY_QUYEN'].apply(lambda x: 'X' if x in tk_sms_set else '')
                    df_uyquyen['CIF có đăng ký SCM010'] = df_uyquyen['CIF_NGUOI_UY_QUYEN'].apply(lambda x: 'X' if x in cif_scm10_set else '')
                    st.success("Đã đối chiếu xong SMS và SCM10.")

                    # --- Bước 7: Tiêu chí 3 ---
                    df_tc3 = df_uyquyen.copy()
                    grouped = df_tc3.groupby('NGUOI_DUOC_UY_QUYEN')['NGUOI_UY_QUYEN'].nunique().reset_index()
                    grouped = grouped[grouped['NGUOI_UY_QUYEN'] >= 2]
                    nguoi_nhan_nhieu_uq = set(grouped['NGUOI_DUOC_UY_QUYEN'].astype(str).dropna())
                    
                    df_tc3['1 người nhận UQ của nhiều người'] = df_tc3['NGUOI_DUOC_UY_QUYEN'].apply(lambda x: 'X' if x in nguoi_nhan_nhieu_uq else '')

                    # --- Bước 8: Xuất kết quả ---
                    st.markdown("---")
                    st.header("3. Kết quả")
                    st.dataframe(df_tc3.head(50))

                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df_tc3.to_excel(writer, sheet_name='UyQuyen_SMS_SCM', index=False)
                    output.seek(0)
                    
                    st.download_button(
                        label="📥 Tải xuống kết quả (Excel)",
                        data=output,
                        file_name="UyQuyen_Final_Streamlit.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

                except Exception as e:
                    st.error(f"Lỗi xử lý: {e}")
                    st.exception(e)

# ==============================================================================
# TAB 2: PHÂN TÍCH DỮ LIỆU KHÁCH HÀNG CÁ NHÂN (THEO CHI NHÁNH)
# ==============================================================================
with tab2:
    st.header("Phân tích dữ liệu KHCN theo Chi Nhánh")
    
    # Cấu hình đường dẫn dữ liệu
    st.info("Module này sử dụng dữ liệu từ thư mục trên máy (hoặc Google Drive mounted).")
    
    # Default path từ code cũ của bạn
    default_path = '/content/drive/MyDrive/ChayDl/thang10_2025/'
    BASE_PATH = st.text_input("Nhập đường dẫn thư mục dữ liệu gốc:", value=default_path)
    
    if not BASE_PATH.endswith('/'):
        BASE_PATH += '/'

    # 1. Nhập liệu chi nhánh/SOL
    chi_nhanh = st.text_input("Nhập tên chi nhánh hoặc mã SOL cần lọc (ví dụ: HANOI hoặc 1405): ", key="input_chinhanh").strip().upper()

    if st.button("Chạy phân tích Chi Nhánh", key="btn_run_tab2"):
        if not chi_nhanh:
            st.warning("Vui lòng nhập mã chi nhánh.")
        elif not os.path.exists(BASE_PATH) and not BASE_PATH.startswith('/content/drive'): 
            # Note: startswith check is loose to allow running if user thinks they are on colab but file check will fail later safely
            st.error(f"Đường dẫn không tồn tại: {BASE_PATH}. Vui lòng kiểm tra lại.")
        else:
            st.write(f"Đang xử lý dữ liệu cho chi nhánh: **{chi_nhanh}** tại thư mục `{BASE_PATH}`")
            
            try:
                with st.spinner("Đang tải và lọc dữ liệu..."):
                    # --- 2. Xử lý file HDV_CHITIET_KKH_*.xls ---
                    st.subheader("1. Dữ liệu HDV Chi Tiết KKH (4.2.a)")
                    hdv_path = os.path.join(BASE_PATH, 'HDV/HDV_CHITIET_KKH_*.xls')
                    files_42a = glob.glob(hdv_path)
                    
                    if not files_42a:
                        st.error(f"Không tìm thấy file theo mẫu `{hdv_path}`")
                        st.stop()

                    # Đọc và gộp file
                    df_list = []
                    for f in files_42a:
                        try:
                            df_temp = pd.read_excel(f, dtype=str)
                            df_list.append(df_temp)
                        except Exception as ex:
                            st.warning(f"Không thể đọc file {f}: {ex}")
                    
                    if not df_list:
                        st.stop()
                        
                    df_ghep42a = pd.concat(df_list, ignore_index=True)
                    
                    # Lọc Chi Nhánh
                    df_42a = df_ghep42a[df_ghep42a['BRCD'].astype(str).str.upper().str.contains(chi_nhanh, na=False)].copy()
                    st.write(f"Số dòng sau khi lọc chi nhánh '{chi_nhanh}': {len(df_42a)}")

                    columns_needed_42a = ['BRCD', 'DEPTCD', 'CUST_TYPE', 'CUSTSEQ', 'NMLOC', 'BIRTH_DAY',
                                          'IDXACNO', 'SCHM_NAME', 'CCYCD', 'CURBAL_VN', 'OPNDT_FIRST', 'OPNDT_EFFECT']
                    # Chỉ giữ cột nếu tồn tại trong file
                    valid_cols = [c for c in columns_needed_42a if c in df_42a.columns]
                    df_42a = df_42a[valid_cols].copy()

                    # Lọc KHCN & Loại trừ
                    if 'CUST_TYPE' in df_42a.columns:
                        df_42a = df_42a[df_42a['CUST_TYPE'].str.upper() == 'KHCN'].copy()
                    
                    exclude_keywords = ['KY QUY', 'GIAI NGAN', 'CHI LUONG', 'TKTT THE', 'TRUNG GIAN']
                    if 'SCHM_NAME' in df_42a.columns:
                        mask_exclude = df_42a['SCHM_NAME'].str.upper().str.contains('|'.join(exclude_keywords), na=False)
                        df_42a = df_42a[~mask_exclude].copy()
                    
                    st.dataframe(df_42a.head())

                    # --- 3. Dữ liệu Charge Level Code ---
                    st.subheader("2. Dữ liệu Charge Level Code (4.2.b)")
                    file_42b = os.path.join(BASE_PATH, 'fin2/BC_LAY_CHARGELEVELCODE_THEO_KHCN 3.xlsx')
                    try:
                        df_ghep42b = pd.read_excel(file_42b, dtype=str)
                        df_42b = df_ghep42b[df_ghep42b['CN_MO_TK'].astype(str).str.upper().str.contains(chi_nhanh, na=False)].copy()
                        
                        # Merge Logic
                        df_42a['CUSTSEQ'] = df_42a['CUSTSEQ'].astype(str)
                        df_42b['MACIF'] = df_42b['MACIF'].astype(str)
                        df_42b_unique_macif = df_42b.drop_duplicates(subset=['MACIF'], keep='first')
                        
                        df_42a = df_42a.merge(df_42b_unique_macif[['MACIF', 'CHARGELEVELCODE_CIF']], how='left', left_on='CUSTSEQ', right_on='MACIF')
                        df_42a.rename(columns={'CHARGELEVELCODE_CIF': 'CHARGELEVELCODE_CUA_CIF'}, inplace=True)
                        df_42a.drop(columns='MACIF', inplace=True, errors='ignore')

                        df_42a['IDXACNO'] = df_42a['IDXACNO'].astype(str)
                        df_42b['STKKH'] = df_42b['STKKH'].astype(str)
                        df_42b_unique_stkkh = df_42b.drop_duplicates(subset=['STKKH'], keep='first')
                        
                        df_42a = df_42a.merge(df_42b_unique_stkkh[['STKKH', 'CHARGELEVELCODE_TK']], how='left', left_on='IDXACNO', right_on='STKKH')
                        df_42a.rename(columns={'CHARGELEVELCODE_TK': 'CHARGELEVELCODE_CUA_TK'}, inplace=True)
                        df_42a.drop(columns='STKKH', inplace=True, errors='ignore')
                        
                        df_42a['TK_GAN_CODE_UU_DAI_CBNV'] = np.where(df_42a['CHARGELEVELCODE_CUA_TK'] == 'NVEIB', 'X', '')
                        st.success("Đã merge Charge Level Code.")

                    except FileNotFoundError:
                        st.error(f"Không tìm thấy file: {file_42b}")
                    except Exception as e:
                        st.error(f"Lỗi xử lý file 4.2.b: {e}")

                    # --- 4. Danh sách nhân sự ---
                    st.subheader("3. Dữ liệu Nhân sự & Nghỉ việc (4.2.c & 4.2.d)")
                    file_42c = os.path.join(BASE_PATH, 'fin2/10_Danh sach nhan su_T09-2025.xlsx')
                    try:
                        df_42c = pd.read_excel(file_42c, dtype=str)
                        df_42a = df_42a.merge(df_42c[["Mã số CIF", "Mã NV"]], left_on="CUSTSEQ", right_on="Mã số CIF", how="left")
                    except Exception as e:
                        st.warning(f"Bỏ qua bước nhân sự (Lỗi: {e})")

                    file_42d = os.path.join(BASE_PATH, 'fin2/2.DS nhân sự nghị việc FULL đến T9. 2025 1.xlsx')
                    try:
                        df_42d = pd.read_excel(file_42d, dtype=str)
                        df_42a = df_42a.merge(df_42d[['CIF', 'Ngày thôi việc']], how='left', left_on='CUSTSEQ', right_on='CIF')
                        df_42a['CBNV_NGHI_VIEC'] = np.where(df_42a['CIF'].notna(), 'X', '')
                        df_42a.rename(columns={'Ngày thôi việc': 'NGAY_NGHI_VIEC'}, inplace=True)
                        df_42a['NGAY_NGHI_VIEC'] = pd.to_datetime(df_42a['NGAY_NGHI_VIEC'], errors='coerce').dt.strftime('%m/%d/%Y')
                        # Cleanup duplicate columns
                        df_42a.drop(columns=['CIF', 'Mã số CIF'], inplace=True, errors='ignore')
                    except Exception as e:
                        st.warning(f"Bỏ qua bước nhân sự nghỉ việc (Lỗi: {e})")

                    # --- 5. Mapping ---
                    st.subheader("4. Dữ liệu Mapping (Tiêu chí 5)")
                    file_mapping = os.path.join(BASE_PATH, 'fin2/Mapping_1405.xlsx')
                    df_mapping_final = pd.DataFrame() # Init empty
                    
                    try:
                        df_mapping = pd.read_excel(file_mapping, engine='openpyxl', dtype=str)
                        df_mapping.columns = df_mapping.columns.str.lower()
                        
                        cols_needed_mapping = [
                            'brcd', 'semaacount', 'cardnbr', 'token', 'relation', 'uploaddt',
                            'odaccount', 'acctcd', 'dracctno', 'drratio', 'adduser', 'updtuser',
                            'expiredate', 'custnm', 'cif', 'xpcode', 'xpcodedt', 'remark', 'oldxpcode'
                        ]
                        existing_cols = [c for c in cols_needed_mapping if c in df_mapping.columns]
                        df_mapping_final = df_mapping[existing_cols].copy()
                        
                        # Logic tính ngày
                        df_mapping_final['xpcodedt'] = pd.to_datetime(df_mapping_final['xpcodedt'], format='%m/%d/%Y', errors='coerce')
                        df_mapping_final['uploaddt'] = pd.to_datetime(df_mapping_final['uploaddt'], format='%m/%d/%Y', errors='coerce')
                        df_mapping_final['SO_NGAY_MO_THE'] = (df_mapping_final['xpcodedt'] - df_mapping_final['uploaddt']).dt.days

                        df_mapping_final['MO_DONG_TRONG_6_THANG'] = df_mapping_final.apply(
                            lambda row: 'X' if (
                                pd.notnull(row['SO_NGAY_MO_THE']) and
                                row['SO_NGAY_MO_THE'] >= 0 and
                                row['SO_NGAY_MO_THE'] < 180 and
                                row['uploaddt'] > pd.to_datetime('2023-05-31')
                            ) else '', axis=1
                        )
                        st.success("Xử lý xong Mapping.")
                    except Exception as e:
                        st.error(f"Lỗi Mapping: {e}")

                    # --- KẾT QUẢ CUỐI CÙNG ---
                    st.markdown("---")
                    st.header("Kết quả cuối cùng Tab 2")
                    
                    output2 = io.BytesIO()
                    with pd.ExcelWriter(output2, engine='openpyxl') as writer:
                        df_42a.to_excel(writer, sheet_name='tieu chi 4', index=False)
                        if not df_mapping_final.empty:
                            df_mapping_final.to_excel(writer, sheet_name='tieu chi 5', index=False)
                    output2.seek(0)
                    
                    st.download_button(
                        label="📥 Tải về file Excel kết quả (Tab 2)",
                        data=output2,
                        file_name=f"DVKH_{chi_nhanh}_Output.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

            except Exception as e:
                st.error(f"Có lỗi không mong muốn xảy ra: {e}")
                st.exception(e)

# # module/DVKH.py
# import streamlit as st
# import pandas as pd
# import numpy as np
# import glob
# import re
# import io
# from datetime import datetime



# # --- Helper: Excel bytes for download
# def dfs_to_excel_bytes(dfs: dict):
#     """
#     dfs: dict of sheet_name -> DataFrame
#     returns BytesIO buffer
#     """
#     buffer = io.BytesIO()
#     with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
#         for sheet, df in dfs.items():
#             # sheet name max 31 chars
#             df.to_excel(writer, sheet_name=sheet[:31], index=False)
#     buffer.seek(0)
#     return buffer

# # --- Helper: parse date with flexible formats
# def try_parse_date(series, possible_formats=None):
#     """
#     Try to parse a pd.Series of dates using given formats, fallback to pd.to_datetime.
#     Returns datetime64 series (or NaT).
#     """
#     if possible_formats is None:
#         possible_formats = ['%Y%m%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d']
#     # try formats one-by-one
#     for fmt in possible_formats:
#         try:
#             parsed = pd.to_datetime(series, format=fmt, errors='coerce')
#             # if many parsed notna, use it
#             if parsed.notna().sum() > 0:
#                 return parsed
#         except Exception:
#             continue
#     # final fallback
#     return pd.to_datetime(series, errors='coerce')


# def _safe_read_excel(f, dtype=None, parse_dates=None, engine=None):
#     """
#     Safe helper to read Excel-like input which can be:
#     - path (str)
#     - file-like object (UploadedFile)
#     Returns DataFrame or raises Exception.
#     """
#     try:
#         if engine:
#             return pd.read_excel(f, dtype=dtype, parse_dates=parse_dates, engine=engine)
#         else:
#             return pd.read_excel(f, dtype=dtype, parse_dates=parse_dates)
#     except Exception as e:
#         # try reading with engine openpyxl if xlsx, else xlrd
#         raise

# # ===========================
# # MAIN function exposed to app
# # ===========================
# def run_dvkh_5_tieuchi():
#     st.header("👥 Module DVKH — Xử lý tiêu chí (Uỷ quyền, CKH, SMS, SCM010, 4.2.a/4.2.b ...)")
#     st.markdown("Upload các file đầu vào hoặc để trống và dùng đường dẫn mặc định (tùy môi trường).")

#     # ---------- DEFAULT PATHS (thay đổi khi cần) ----------
#     # DEFAULT_CKH_GLOB = "/content/drive/MyDrive/ChayDl/1500_DL_CKH/CKH/HDV_CHITIET_CKH_*.xls*"
#     # DEFAULT_KKH_GLOB = "/content/drive/MyDrive/ChayDl/1500_DL_CKH/KKH/HDV_CHITIET_KKH_*.xls*"
#     # DEFAULT_MUC30_PATH = "/content/drive/MyDrive/ChayDl/1500_DL_CKH/muc30/MUC 30 1710 NEW (1).xlsx"
#     # DEFAULT_MUC14_SMS = "/content/drive/MyDrive/ChayDl/1500_DL_CKH/sms/Muc14_DKSMS.txt"
#     # DEFAULT_MUC14_SCM010 = "/content/drive/MyDrive/ChayDl/1500_DL_CKH/sms/Muc14_SCM010.xlsx"
#     # DEFAULT_42A_GLOB = "/content/drive/MyDrive/ChayDl/thang10_2025/HDV/HDV_CHITIET_KKH_*.xls"
#     # DEFAULT_42B = "/content/drive/MyDrive/ChayDl/thang10_2025/fin2/BC_LAY_CHARGELEVELCODE_THEO_KHCN 3.xlsx"
#     # DEFAULT_42C = "/content/drive/MyDrive/ChayDl/thang10_2025/fin2/10_Danh sach nhan su_T09-2025.xlsx"
#     # DEFAULT_42D = "/content/drive/MyDrive/ChayDl/thang10_2025/fin2/2.DS nhân sự nghỉ việc FULL đến T9. 2025 1.xlsx"
#     # DEFAULT_MAPPING = "/content/drive/MyDrive/ChayDl/thang10_2025/fin2/Mapping_1405.xlsx"

#     # ---------- Upload widgets ----------
#     st.subheader("1) Tệp danh sách CKH / KKH (HDV_CHITIET_CKH_*, HDV_CHITIET_KKH_*)")
#     use_upload_ckh = st.radio("Chọn nguồn CKH/KKH", ["Upload files", "Dùng đường dẫn mặc định"], index=1)
#     ckh_files = []
#     kkh_files = []
#     if use_upload_ckh == "Upload files":
#         uploaded_ckh = st.file_uploader("Upload các file CKH (HDV_CHITIET_CKH_*.xls/xlsx)", accept_multiple_files=True, type=['xls','xlsx'])
#         uploaded_kkh = st.file_uploader("Upload các file KKH (HDV_CHITIET_KKH_*.xls/xlsx)", accept_multiple_files=True, type=['xls','xlsx'])
#         ckh_files = uploaded_ckh or []
#         kkh_files = uploaded_kkh or []
#     else:
#         # try to glob
#         ckh_files = glob.glob(DEFAULT_CKH_GLOB)
#         kkh_files = glob.glob(DEFAULT_KKH_GLOB)

#     st.subheader("2) File Mục 30 (ủy quyền)")
#     use_upload_muc30 = st.radio("Chọn nguồn Mục 30", ["Upload file", "Dùng đường dẫn mặc định"], index=1, key="muc30_radio")
#     muc30_file = None
#     if use_upload_muc30 == "Upload file":
#         muc30_file = st.file_uploader("Upload file Mục 30 (MUC 30 ...xlsx)", type=['xls','xlsx'])
#     else:
#         muc30_file = DEFAULT_MUC30_PATH

#     st.subheader("3) File SMS (Mục14) và SCM010")
#     use_upload_sms = st.radio("Chọn nguồn SMS/SCM010", ["Upload files", "Dùng đường dẫn mặc định"], index=1, key="sms_radio")
#     sms_file = None
#     scm10_file = None
#     if use_upload_sms == "Upload files":
#         sms_file = st.file_uploader("Upload Muc14_DKSMS (txt/txt tab) or csv", type=['txt','csv','xls','xlsx'])
#         scm10_file = st.file_uploader("Upload Muc14_SCM010.xlsx", type=['xls','xlsx'])
#     else:
#         sms_file = DEFAULT_MUC14_SMS
#         scm10_file = DEFAULT_MUC14_SCM010

#     st.subheader("4) File 4.2a/4.2b và bảng nhân sự / mapping")
#     use_upload_42 = st.radio("Chọn nguồn 4.2a/4.2b/nhân sự", ["Upload files", "Dùng đường dẫn mặc định"], index=1, key="42_radio")
#     files_42a = []
#     file_42b = None
#     file_42c = None
#     file_42d = None
#     mapping_file = None
#     if use_upload_42 == "Upload files":
#         files_42a = st.file_uploader("Upload file(s) 4.2a (HDV_CHITIET_KKH_*.xls...)", accept_multiple_files=True, type=['xls','xlsx'])
#         file_42b = st.file_uploader("Upload 4.2b (BC_LAY_CHARGELEVELCODE...xlsx)", type=['xls','xlsx'])
#         file_42c = st.file_uploader("Upload danh sách nhân sự (10_Danh sach ...xlsx)", type=['xls','xlsx'])
#         file_42d = st.file_uploader("Upload danh sách nghỉ việc (2.DS ...xlsx)", type=['xls','xlsx'])
#         mapping_file = st.file_uploader("Upload Mapping_1405.xlsx", type=['xls','xlsx'])
#     else:
#         files_42a = glob.glob(DEFAULT_42A_GLOB)
#         file_42b = DEFAULT_42B
#         file_42c = DEFAULT_42C
#         file_42d = DEFAULT_42D
#         mapping_file = DEFAULT_MAPPING

#     st.markdown("---")
#     col1, col2 = st.columns([1,3])
#     with col1:
#         chi_nhanh = st.text_input("Nhập tên chi nhánh hoặc mã SOL để lọc (ví dụ HANOI hoặc 001)", value="").strip().upper()
#     with col2:
#         run_btn = st.button("🚀 Chạy xử lý DVKH (4.2a, SMS, SCM010, Mapping...)")

#     if not run_btn:
#         st.info("Bấm nút để bắt đầu xử lý.")
#         return

#     # ---------- Validation & Read files ----------
#     st.info("⏳ Bắt đầu đọc file...")

#     # helper to read multiple possibly uploaded files
#     def read_multiple(files_or_paths, dtype=None):
#         items = []
#         if not files_or_paths:
#             return []
#         for f in files_or_paths:
#             try:
#                 if hasattr(f, "read"):  # uploaded file
#                     df = pd.read_excel(f, dtype=dtype)
#                 else:
#                     df = pd.read_excel(f, dtype=dtype)
#                 items.append(df)
#             except Exception as e:
#                 st.error(f"Lỗi đọc file: {f} — {e}")
#         return items

#     # Read CKH and KKH
#     try:
#         if isinstance(ckh_files, (list, tuple)) and len(ckh_files) > 0 and hasattr(ckh_files[0], "read"):
#             df_ckh_list = [pd.read_excel(f, dtype=str) for f in ckh_files]
#         else:
#             df_ckh_list = [pd.read_excel(p, dtype=str) for p in ckh_files] if ckh_files else []
#         if isinstance(kkh_files, (list, tuple)) and len(kkh_files) > 0 and hasattr(kkh_files[0], "read"):
#             df_kkh_list = [pd.read_excel(f, dtype=str) for f in kkh_files]
#         else:
#             df_kkh_list = [pd.read_excel(p, dtype=str) for p in kkh_files] if kkh_files else []
#         df_b_CKH = pd.concat(df_ckh_list, ignore_index=True) if df_ckh_list else pd.DataFrame()
#         df_b_KKH = pd.concat(df_kkh_list, ignore_index=True) if df_kkh_list else pd.DataFrame()
#     except Exception as e:
#         st.error(f"Lỗi đọc CKH/KKH: {e}")
#         return

#     # Read Muc30 (ủy quyền)
#     try:
#         if hasattr(muc30_file, "read"):
#             df_a = pd.read_excel(muc30_file, dtype=str)
#         else:
#             df_a = pd.read_excel(muc30_file, dtype=str)
#     except Exception as e:
#         st.error(f"Lỗi đọc file Mục 30: {e}")
#         return

#     # Read SMS file (txt or excel) and SCM010
#     try:
#         # SMS: may be tab-separated txt
#         if hasattr(sms_file, "read"):
#             # inspect name
#             name = getattr(sms_file, "name", "")
#             if str(name).lower().endswith(".txt") or str(name).lower().endswith(".csv"):
#                 df_sms = pd.read_csv(sms_file, sep=None, engine='python', on_bad_lines='skip')
#             else:
#                 df_sms = pd.read_excel(sms_file, dtype=str)
#         else:
#             # path
#             if str(sms_file).lower().endswith(".txt") or str(sms_file).lower().endswith(".csv"):
#                 df_sms = pd.read_csv(sms_file, sep=None, engine='python', on_bad_lines='skip')
#             else:
#                 df_sms = pd.read_excel(sms_file, dtype=str)
#     except Exception as e:
#         st.error(f"Lỗi đọc file SMS: {e}")
#         df_sms = pd.DataFrame()

#     try:
#         if hasattr(scm10_file, "read"):
#             df_scm10 = pd.read_excel(scm10_file, dtype=str)
#         else:
#             df_scm10 = pd.read_excel(scm10_file, dtype=str)
#     except Exception as e:
#         st.error(f"Lỗi đọc SCM010: {e}")
#         df_scm10 = pd.DataFrame()

#     # Read 4.2a files
#     try:
#         if isinstance(files_42a, (list, tuple)) and len(files_42a) > 0 and hasattr(files_42a[0], "read"):
#             df_42a_list = [pd.read_excel(f, dtype=str) for f in files_42a]
#         else:
#             df_42a_list = [pd.read_excel(p, dtype=str) for p in files_42a] if files_42a else []
#         df_ghep42a = pd.concat(df_42a_list, ignore_index=True) if df_42a_list else pd.DataFrame()
#     except Exception as e:
#         st.error(f"Lỗi đọc file 4.2a: {e}")
#         df_ghep42a = pd.DataFrame()

#     # Read 4.2b and staff files and mapping
#     try:
#         if hasattr(file_42b, "read"):
#             df_42b = pd.read_excel(file_42b, dtype=str)
#         else:
#             df_42b = pd.read_excel(file_42b, dtype=str)
#     except Exception as e:
#         st.error(f"Lỗi đọc file 4.2b: {e}")
#         df_42b = pd.DataFrame()

#     try:
#         if hasattr(file_42c, "read"):
#             df_42c = pd.read_excel(file_42c, dtype=str)
#         else:
#             df_42c = pd.read_excel(file_42c, dtype=str)
#     except Exception as e:
#         st.error(f"Lỗi đọc file nhân sự (42c): {e}")
#         df_42c = pd.DataFrame()

#     try:
#         if hasattr(file_42d, "read"):
#             df_42d = pd.read_excel(file_42d, dtype=str)
#         else:
#             df_42d = pd.read_excel(file_42d, dtype=str)
#     except Exception as e:
#         st.error(f"Lỗi đọc file nghỉ việc (42d): {e}")
#         df_42d = pd.DataFrame()

#     try:
#         if hasattr(mapping_file, "read"):
#             df_map = pd.read_excel(mapping_file, engine='openpyxl', dtype=str)
#         else:
#             df_map = pd.read_excel(mapping_file, engine='openpyxl', dtype=str)
#     except Exception as e:
#         st.warning(f"Cảnh báo: không đọc được Mapping_1405: {e}")
#         df_map = pd.DataFrame()

#     st.success("✅ Đã đọc xong file (nếu có). Bắt đầu xử lý dữ liệu...")

#     # ---------- PROCESS MUC30 (ủy quyền) ----------
#     try:
#         # Step: filter DESCRIPTION containing chu ky / chuky / cky
#         if 'DESCRIPTION' in df_a.columns:
#             df_a = df_a[df_a["DESCRIPTION"].astype(str).str.contains(r"chu\s*ky|chuky|cky", case=False, na=False)].copy()
#         else:
#             st.warning("Cột DESCRIPTION không tồn tại trong Mục 30; bỏ qua lọc DESCRIPTION.")

#         # Parse dates flexible
#         if 'EXPIRYDATE' in df_a.columns:
#             df_a['EXPIRYDATE_parsed'] = try_parse_date(df_a['EXPIRYDATE'])
#         else:
#             df_a['EXPIRYDATE_parsed'] = pd.NaT

#         if 'EFFECTIVEDATE' in df_a.columns:
#             df_a['EFFECTIVEDATE_parsed'] = try_parse_date(df_a['EFFECTIVEDATE'])
#         else:
#             df_a['EFFECTIVEDATE_parsed'] = pd.NaT

#         # Normalize to mm/dd/YYYY strings where possible
#         df_a['EXPIRYDATE_norm'] = df_a['EXPIRYDATE_parsed'].dt.strftime('%m/%d/%Y')
#         df_a['EFFECTIVEDATE_norm'] = df_a['EFFECTIVEDATE_parsed'].dt.strftime('%m/%d/%Y')

#         # Filter out corporate NGUOI_UY_QUYEN by keywords (if column exists)
#         if 'NGUOI_UY_QUYEN' in df_a.columns:
#             keywords = ["CONG TY", "CTY", "CONGTY", "CÔNG TY", "CÔNGTY"]
#             df_a = df_a[~df_a["NGUOI_UY_QUYEN"].astype(str).str.upper().str.contains("|".join(keywords), na=False)].copy()
#         else:
#             st.warning("Cột NGUOI_UY_QUYEN không tồn tại trong Mục30; sẽ dùng nguyên dữ liệu.")

#         # Extract NGUOI_DUOC_UY_QUYEN names (your heuristic)
#         if 'NGUOI_DUOC_UY_QUYEN' in df_a.columns:
#             def extract_name(value):
#                 parts = re.split(r'[-,]', str(value))
#                 for part in parts:
#                     name = part.strip()
#                     if re.fullmatch(r'[A-Z ]{3,}', name):
#                         return name
#                 return str(value)
#             df_a['NGUOI_DUOC_UY_QUYEN'] = df_a['NGUOI_DUOC_UY_QUYEN'].apply(extract_name)
#         else:
#             st.warning("Cột NGUOI_DUOC_UY_QUYEN không có; một số tiêu chí có thể thiếu.")
#     except Exception as e:
#         st.error(f"Lỗi xử lý Mục30 (ủy quyền): {e}")
#         return

#     # ---------- PROCESS CKH/KKH merges ----------
#     try:
#         # Make sure df_b_CKH/df_b_KKH exist
#         df_b = pd.concat([df_b_CKH, df_b_KKH], ignore_index=True) if (not df_b_CKH.empty or not df_b_KKH.empty) else pd.DataFrame()

#         # Ensure column names exist for merge: TK_DUOC_UY_QUYEN -> IDXACNO mapping
#         # Normalize types to str for join keys
#         if 'TK_DUOC_UY_QUYEN' in df_a.columns and 'IDXACNO' in df_b.columns and 'CUSTSEQ' in df_b.columns:
#             df_a['TK_DUOC_UY_QUYEN'] = df_a['TK_DUOC_UY_QUYEN'].astype(str)
#             df_b['IDXACNO'] = df_b['IDXACNO'].astype(str)
#             merged = df_a.merge(df_b[['IDXACNO','CUSTSEQ']], left_on='TK_DUOC_UY_QUYEN', right_on='IDXACNO', how='left')
#         else:
#             # If columns missing, create merged with NaNs to keep flow
#             merged = df_a.copy()
#             merged['CUSTSEQ'] = np.nan
#             merged['IDXACNO'] = np.nan

#         # CIF_NGUOI_UY_QUYEN convert
#         merged['CIF_NGUOI_UY_QUYEN'] = merged['CUSTSEQ'].apply(lambda x: str(int(float(x))) if pd.notna(x) and str(x).strip()!='' and str(x)!='nan' else "NA")

#         # Try to fill missing CIF for same NGUOI_UY_QUYEN
#         if 'NGUOI_UY_QUYEN' in merged.columns:
#             cif_series = merged['CIF_NGUOI_UY_QUYEN'].copy()
#             for name, grp in merged.groupby('NGUOI_UY_QUYEN'):
#                 actual = [v for v in grp['CIF_NGUOI_UY_QUYEN'].unique() if v != "NA"]
#                 if actual:
#                     fill = actual[0]
#                     mask = (merged['NGUOI_UY_QUYEN'] == name) & (merged['CIF_NGUOI_UY_QUYEN'] == "NA")
#                     cif_series.loc[mask] = fill
#             merged['CIF_NGUOI_UY_QUYEN'] = cif_series

#         # Drop helper columns if exist
#         for col in ['MODIFIEDDATE_NEW','IDXACNO','CUSTSEQ']:
#             if col in merged.columns:
#                 try:
#                     merged.drop(columns=[col], inplace=True)
#                 except Exception:
#                     pass

#         # Create sets for CKH and KKH to classify accounts
#         set_ckh = set(df_b_CKH['CUSTSEQ'].astype(str)) if not df_b_CKH.empty else set()
#         set_kkh = set(df_b_KKH['IDXACNO'].astype(str)) if not df_b_KKH.empty else set()

#         def phan_loai_tk(tk):
#             tk = str(tk)
#             if tk in set_ckh:
#                 return 'CKH'
#             elif tk in set_kkh:
#                 return 'KKH'
#             else:
#                 return 'NA'

#         if 'TK_DUOC_UY_QUYEN' in merged.columns:
#             merged['LOAI_TK'] = merged['TK_DUOC_UY_QUYEN'].astype(str).apply(phan_loai_tk)
#         else:
#             merged['LOAI_TK'] = 'NA'

#         # Normalize expiry/effective dates
#         merged['EXPIRYDATE_dt'] = try_parse_date(merged.get('EXPIRYDATE', pd.Series([pd.NaT]*len(merged))))
#         merged['EFFECTIVEDATE_dt'] = try_parse_date(merged.get('EFFECTIVEDATE', pd.Series([pd.NaT]*len(merged))))

#         # Compute year diff and flags
#         merged['YEAR_DIFF'] = merged['EXPIRYDATE_dt'].dt.year - merged['EFFECTIVEDATE_dt'].dt.year
#         merged['KHONG_NHAP_TGIAN_UQ'] = np.where(merged['YEAR_DIFF'] == 99, 'X', '')
#         merged['UQ_TREN_50_NAM'] = np.where(merged['YEAR_DIFF'] >= 50, 'X', '')
#         merged.drop(columns=['YEAR_DIFF'], inplace=True, errors='ignore')
#     except Exception as e:
#         st.error(f"Lỗi xử lý merge ủy quyền-CKH: {e}")
#         return

#     # ---------- PROCESS SMS & SCM010 ----------
#     try:
#         # Normalize SMS df
#         if not df_sms.empty:
#             # ensure columns exist; try common column names
#             if 'FORACID' not in df_sms.columns:
#                 # attempt to find similar col
#                 possible = [c for c in df_sms.columns if 'for' in c.lower() or 'acid' in c.lower()]
#                 if possible:
#                     df_sms.rename(columns={possible[0]:'FORACID'}, inplace=True)
#             if 'C_MOBILE_NO' not in df_sms.columns:
#                 poss = [c for c in df_sms.columns if 'mobile' in c.lower() or 'phone' in c.lower()]
#                 if poss:
#                     df_sms.rename(columns={poss[0]:'C_MOBILE_NO'}, inplace=True)

#             df_sms['FORACID'] = df_sms['FORACID'].astype(str)
#             # if CRE_DATE col absent, try CRE_DATE/CREDATE/CRE DATE
#             if 'CRE_DATE' not in df_sms.columns and 'CRE DATE' in df_sms.columns:
#                 df_sms['CRE_DATE'] = df_sms['CRE DATE']
#             if 'CRE_DATE' in df_sms.columns:
#                 # try parsing
#                 df_sms['CRE_DATE_dt'] = try_parse_date(df_sms['CRE_DATE'])
#                 df_sms['CRE_DATE_norm'] = df_sms['CRE_DATE_dt'].dt.strftime('%m/%d/%Y')
#         else:
#             df_sms = pd.DataFrame()

#         # SCM010 normalization
#         if not df_scm10.empty:
#             df_scm10 = df_scm10.rename(columns=lambda x: x.strip())
#             if 'CIF_ID' in df_scm10.columns:
#                 df_scm10['CIF_ID'] = df_scm10['CIF_ID'].astype(str)
#             if 'ORGKEY' not in df_scm10.columns and 'CIF_ID' in df_scm10.columns:
#                 df_scm10['ORGKEY'] = df_scm10['CIF_ID']
#             df_scm10['PL DICH VU'] = 'SCM010'
#             df_scm10_small = df_scm10[['ORGKEY','PL DICH VU']].drop_duplicates() if 'ORGKEY' in df_scm10.columns else pd.DataFrame()
#         else:
#             df_scm10_small = pd.DataFrame()

#         # merge SMS + SCM010 into one small table of registrations
#         df_sms_copy = df_sms.copy()
#         if not df_sms_copy.empty:
#             df_sms_copy['PL DICH VU'] = 'SMS'
#             if 'FORACID' in df_sms_copy.columns:
#                 df_sms_small = df_sms_copy[['FORACID','PL DICH VU']].drop_duplicates()
#             else:
#                 df_sms_small = pd.DataFrame()
#         else:
#             df_sms_small = pd.DataFrame()

#         df_merged_reg = pd.concat([df_sms_small.rename(columns={'FORACID':'ORGKEY'}), df_scm10_small], axis=0, ignore_index=True, sort=False).drop_duplicates()
#     except Exception as e:
#         st.error(f"Lỗi xử lý SMS/SCM010: {e}")
#         df_merged_reg = pd.DataFrame()

#     # ---------- APPLY REGISTRATION FLAGS to merged ủy quyền ----------
#     try:
#         if not df_merged_reg.empty:
#             sms_keys = set(df_merged_reg[df_merged_reg['PL DICH VU']=='SMS']['ORGKEY'].astype(str))
#             scm_keys = set(df_merged_reg[df_merged_reg['PL DICH VU']=='SCM010']['ORGKEY'].astype(str))
#         else:
#             sms_keys = set()
#             scm_keys = set()

#         # Ensure CIF_NGUOI_UY_QUYEN and TK_DUOC_UY_QUYEN exist
#         merged['TK_DUOC_UY_QUYEN'] = merged.get('TK_DUOC_UY_QUYEN', merged.get('TK_DUOC_UY_QUYEN','')).astype(str)
#         merged['CIF_NGUOI_UY_QUYEN'] = merged.get('CIF_NGUOI_UY_QUYEN', '').astype(str)

#         merged['TK có đăng ký SMS'] = merged['TK_DUOC_UY_QUYEN'].apply(lambda x: 'X' if str(x) in sms_keys else '')
#         merged['CIF có đăng ký SCM010'] = merged['CIF_NGUOI_UY_QUYEN'].apply(lambda x: 'X' if str(x) in scm_keys else '')
#     except Exception as e:
#         st.error(f"Lỗi gán flag SMS/SCM010: {e}")

#     # ---------- Additional rule: 1 người nhận UQ của nhiều người ----------
#     try:
#         if 'NGUOI_DUOC_UY_QUYEN' in merged.columns and 'NGUOI_UY_QUYEN' in merged.columns:
#             grouped = merged.groupby('NGUOI_DUOC_UY_QUYEN')['NGUOI_UY_QUYEN'].nunique().reset_index()
#             multiple = set(grouped[grouped['NGUOI_UY_QUYEN']>=2]['NGUOI_DUOC_UY_QUYEN'])
#             merged['1 người nhận UQ của nhiều người'] = merged['NGUOI_DUOC_UY_QUYEN'].apply(lambda x: 'X' if x in multiple else '')
#         else:
#             merged['1 người nhận UQ của nhiều người'] = ''
#     except Exception as e:
#         st.error(f"Lỗi đánh dấu 1 người nhận UQ của nhiều người: {e}")

#     # ---------- PROCESS 4.2a (accounts) ----------
#     try:
#         df_42a = df_ghep42a.copy() if not df_ghep42a.empty else pd.DataFrame()
#         if not df_42a.empty:
#             # filter branch if provided
#             if chi_nhanh:
#                 mask = df_42a['BRCD'].astype(str).str.upper().str.contains(chi_nhanh)
#                 df_42a = df_42a[mask].copy()

#             # select needed columns if exist
#             columns_needed_42a = ['BRCD', 'DEPTCD', 'CUST_TYPE', 'CUSTSEQ', 'NMLOC', 'BIRTH_DAY',
#                                   'IDXACNO', 'SCHM_NAME', 'CCYCD', 'CURBAL_VN', 'OPNDT_FIRST', 'OPNDT_EFFECT']
#             cols_exist = [c for c in columns_needed_42a if c in df_42a.columns]
#             df_42a = df_42a[cols_exist].copy()

#             # Filter KHCN
#             if 'CUST_TYPE' in df_42a.columns:
#                 df_42a = df_42a[df_42a['CUST_TYPE'].astype(str).str.upper() == 'KHCN'].copy()

#             # ensure CURBAL_VN as numeric or string
#             if 'CURBAL_VN' in df_42a.columns:
#                 df_42a['CURBAL_VN'] = df_42a['CURBAL_VN'].astype(str)

#             # exclude unwanted schema names
#             if 'SCHM_NAME' in df_42a.columns:
#                 exclude_keywords = ['KY QUY', 'GIAI NGAN', 'CHI LUONG', 'TKTT THE', 'TRUNG GIAN']
#                 mask_exclude = df_42a['SCHM_NAME'].astype(str).str.upper().str.contains('|'.join(exclude_keywords), na=False)
#                 df_42a = df_42a[~mask_exclude].copy()
#         else:
#             df_42a = pd.DataFrame()
#     except Exception as e:
#         st.error(f"Lỗi xử lý 4.2a: {e}")
#         df_42a = pd.DataFrame()

#     # ---------- Merge 4.2b data (charge level code) ----------
#     try:
#         if not df_42b.empty and not df_42a.empty:
#             # normalize types
#             if 'MACIF' in df_42b.columns:
#                 df_42b['MACIF'] = df_42b['MACIF'].astype(str)
#             if 'CUSTSEQ' in df_42a.columns:
#                 df_42a['CUSTSEQ'] = df_42a['CUSTSEQ'].astype(str)

#             # unique MACIF
#             df_42b_unique_macif = df_42b.drop_duplicates(subset=['MACIF'], keep='first') if 'MACIF' in df_42b.columns else pd.DataFrame()
#             if not df_42b_unique_macif.empty:
#                 df_42a = df_42a.merge(df_42b_unique_macif[['MACIF','CHARGELEVELCODE_CIF']], how='left', left_on='CUSTSEQ', right_on='MACIF')
#                 df_42a.rename(columns={'CHARGELEVELCODE_CIF':'CHARGELEVELCODE_CUA_CIF'}, inplace=True)
#                 df_42a.drop(columns=['MACIF'], inplace=True, errors='ignore')

#             # now merge by STKKH -> IDXACNO
#             if 'IDXACNO' in df_42a.columns and 'STKKH' in df_42b.columns:
#                 df_42b_unique_stkkh = df_42b.drop_duplicates(subset=['STKKH'], keep='first')
#                 df_42a = df_42a.merge(df_42b_unique_stkkh[['STKKH','CHARGELEVELCODE_TK']], how='left', left_on='IDXACNO', right_on='STKKH')
#                 df_42a.rename(columns={'CHARGELEVELCODE_TK':'CHARGELEVELCODE_CUA_TK'}, inplace=True)
#                 df_42a.drop(columns=['STKKH'], inplace=True, errors='ignore')

#             # flag TK gắn code ưu đãi CBNV example
#             df_42a['TK_GAN_CODE_UU_DAI_CBNV'] = np.where(df_42a.get('CHARGELEVELCODE_CUA_TK','') == 'NVEIB','X','')
#         else:
#             # create placeholders
#             if df_42a.empty:
#                 df_42a = pd.DataFrame()
#     except Exception as e:
#         st.error(f"Lỗi merge 4.2b: {e}")

#     # ---------- Staff / resigned processing ----------
#     try:
#         if not df_42c.empty:
#             # df_42c used for later; ensure columns exist
#             # (no fixed operations in your pasted script except merges)
#             pass
#         if not df_42d.empty:
#             # convert CIF column name possibilities
#             possible_cif_cols = [c for c in df_42d.columns if c.strip().upper() in ['CIF','CIF_ID','CIFID']]
#             if possible_cif_cols:
#                 df_42d.rename(columns={possible_cif_cols[0]:'CIF'}, inplace=True)
#             # ensure CIF string
#             if 'CIF' in df_42d.columns:
#                 df_42d['CIF'] = df_42d['CIF'].astype(str)
#             # map to 42a
#             if 'CUSTSEQ' in df_42a.columns and 'CIF' in df_42d.columns:
#                 df_42a = df_42a.merge(df_42d[['CIF','Ngày thôi việc'] if 'Ngày thôi việc' in df_42d.columns else ['CIF']], how='left', left_on='CUSTSEQ', right_on='CIF')
#                 df_42a['CBNV_NGHI_VIEC'] = np.where(df_42a['CIF'].notna(),'X','')
#                 if 'Ngày thôi việc' in df_42a.columns:
#                     df_42a['NGAY_NGHI_VIEC'] = try_parse_date(df_42a['Ngày thôi việc']).dt.strftime('%m/%d/%Y')
#                 df_42a.drop(columns=['CIF'], inplace=True, errors='ignore')
#     except Exception as e:
#         st.error(f"Lỗi xử lý nhân sự/nghỉ việc: {e}")

#     # ---------- Mapping_1405 logic (tiêu chí 5) ----------
#     try:
#         df_map_out = pd.DataFrame()
#         if not df_map.empty:
#             # normalize lower-case columns
#             df_map.columns = df_map.columns.str.lower()
#             # pick existing needed
#             cols_needed = [
#                 'brcd', 'semaacount', 'cardnbr', 'token', 'relation', 'uploaddt',
#                 'odaccount', 'acctcd', 'dracctno', 'drratio', 'adduser', 'updtuser',
#                 'expiredate', 'custnm', 'cif', 'xpcode', 'xpcodedt', 'remark', 'oldxpcode'
#             ]
#             existing = [c for c in cols_needed if c in df_map.columns]
#             if existing:
#                 df_map_out = df_map[existing].copy()
#                 # parse dates safely if exist
#                 if 'xpcodedt' in df_map_out.columns:
#                     df_map_out['xpcodedt_dt'] = try_parse_date(df_map_out['xpcodedt'])
#                 if 'uploaddt' in df_map_out.columns:
#                     df_map_out['uploaddt_dt'] = try_parse_date(df_map_out['uploaddt'])
#                 # compute days open if both exist
#                 if 'xpcodedt_dt' in df_map_out.columns and 'uploaddt_dt' in df_map_out.columns:
#                     df_map_out['SO_NGAY_MO_THE'] = (df_map_out['xpcodedt_dt'] - df_map_out['uploaddt_dt']).dt.days
#                     df_map_out['MO_DONG_TRONG_6_THANG'] = df_map_out.apply(lambda r: 'X' if pd.notna(r.get('SO_NGAY_MO_THE')) and r['SO_NGAY_MO_THE'] >= 0 and r['SO_NGAY_MO_THE'] < 180 and (pd.isna(r.get('uploaddt_dt')) == False and r['uploaddt_dt'] > pd.to_datetime('2023-05-31')) else '', axis=1)
#             else:
#                 st.warning("Mapping file không chứa cột cần thiết; bỏ qua bước này.")
#         else:
#             df_map_out = pd.DataFrame()
#     except Exception as e:
#         st.error(f"Lỗi xử lý Mapping file: {e}")
#         df_map_out = pd.DataFrame()

#     # ---------- FINAL: prepare outputs and download ----------
#     try:
#         out_merged = merged.copy()
#         out_42a = df_42a.copy()
#         out_map = df_map_out.copy()

#         # give user previews
#         st.subheader("Kết quả — preview")
#         st.write("👉 Bảng ủy quyền (tieu chi 1) — preview")
#         st.dataframe(out_merged.head(50))
#         st.write("👉 Bảng 4.2a (tieu chi 4) — preview")
#         st.dataframe(out_42a.head(50))
#         st.write("👉 Bảng Mapping / tiêu chí 5 — preview")
#         st.dataframe(out_map.head(50))

#         # prepare excel
#         sheets = {
#             "tieu chi 1 (uy quyen)": out_merged,
#             "tieu chi 4 (42a)": out_42a,
#             "tieu chi 5 (mapping)": out_map
#         }
#         excel_bytes = dfs_to_excel_bytes(sheets)
#         st.download_button("⬇️ Tải Excel kết quả DVKH (3 sheet)", data=excel_bytes, file_name="DVKH_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

#         st.success("Hoàn tất xử lý DVKH. Kiểm tra file tải xuống hoặc xem preview.")
#     except Exception as e:
#         st.error(f"Lỗi xuất kết quả: {e}")
#         return
