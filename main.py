import streamlit as st
import pandas as pd
import io

# 1. CẤU HÌNH TRANG & GIAO DIỆN (UI/UX)
st.set_page_config(page_title="Hệ thống SEO Quản trị - Lái Hộ", layout="wide")

# Custom CSS để làm bảng hiển thị full, không bị cuộn nội dung bên trong
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] { width: 100%; }
    /* Tối ưu hóa khoảng cách và màu sắc */
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    div[data-testid="stExpander"] { border: 1px solid #dee2e6; border-radius: 8px; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (SESSION STATE) - Để lưu thông tin khi Import hoặc sửa
def init_data(key, default_df):
    if key not in st.session_state:
        st.session_state[key] = default_df

# Dữ liệu mẫu dựa trên template của bạn
init_data('df_config', pd.DataFrame({
    "Hạng mục": ["GEMINI_API_KEY", "SERPAPI_KEY", "SENDER_EMAIL", "TARGET_URL", "Số lượng bài/ngày"],
    "Giá trị": ["", "", "jundeng.po@gmail.com", "https://laiho.vn/", "10"]
}))

init_data('df_backlink', pd.DataFrame({
    "Từ khóa": ["lái xe hộ", "thuê tài xế"],
    "URL Đích": ["https://laiho.vn", "https://laiho.vn"],
    "Đã dùng": [0, 5]
}))

# 3. HÀM TIỆN ÍCH: IMPORT & EXPORT
def export_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

def import_csv(uploaded_file, key):
    if uploaded_file is not None:
        st.session_state[key] = pd.read_csv(uploaded_file)
        st.success("Đã nạp dữ liệu từ file thành công!")

# 4. KIỂM TRA ĐĂNG NHẬP
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Hệ thống SEO Nội bộ")
    with st.container(border=True):
        user = st.text_input("Tài khoản")
        pw = st.text_input("Mật khẩu", type="password")
        if st.button("Đăng nhập"):
            if (user == "admin" and pw == "123"):
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Sai thông tin!")
else:
    # 5. SIDEBAR NAVIGATION
    with st.sidebar:
        st.title("🎮 ĐIỀU HÀNH")
        project = st.selectbox("Dự án", ["Lái Hộ", "Giúp Việc Nhanh"])
        menu = st.radio("Danh mục", ["Config", "Data_Backlink", "Data_Website", "Data_Local", "Data_Report"])
        st.markdown("---")
        if st.button("🚪 Đăng xuất", key="logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.title(f"🚀 {project} - {menu}")

    # --- CÔNG CỤ CHUNG: IMPORT / EXPORT ---
    with st.expander("📥 Thao tác File (Import/Export)"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("📤 Xuất dữ liệu")
            current_df = st.session_state.get(f'df_{menu.lower()}', pd.DataFrame())
            st.download_button(
                label=f"Tải file {menu}.csv",
                data=export_csv(current_df),
                file_name=f"{menu}_export.csv",
                mime='text/csv'
            )
        with col2:
            st.write("📥 Nhập dữ liệu")
            up_file = st.file_uploader(f"Chọn file CSV cho {menu}", type=["csv"])
            if st.button(f"Nạp dữ liệu {menu}"):
                import_csv(up_file, f'df_{menu.lower()}')

    st.markdown("---")

    # --- HIỂN THỊ NỘI DUNG THEO MENU ---
    if menu == "Config":
        st.subheader("⚙️ Cài đặt hệ thống")
        # height=400 và use_container_width giúp bảng hiển thị full không scroll
        st.session_state.df_config = st.data_editor(
            st.session_state.df_config, 
            use_container_width=True, 
            num_rows="fixed",
            height=300 
        )

    elif menu == "Data_Backlink":
        st.subheader("🔗 Quản lý Link & Từ khóa")
        st.session_state.df_backlink = st.data_editor(
            st.session_state.df_backlink,
            use_container_width=True,
            num_rows="dynamic",
            height=500 # Tăng chiều cao để hiện hết các hàng
        )

    elif menu == "Data_Website":
        st.subheader("🌐 Hệ thống Website vệ tinh")
        init_data('df_website', pd.DataFrame({
            "ID Blog": ["Blog 1", "Blog 2"],
            "Nền tảng": ["Blogger", "Blogger"],
            "Trạng thái": ["Bật", "Bật"]
        }))
        st.session_state.df_website = st.data_editor(
            st.session_state.df_website,
            use_container_width=True,
            num_rows="dynamic",
            height=500
        )

    elif menu == "Data_Local":
        st.subheader("📍 Phủ sóng địa phương")
        init_data('df_local', pd.DataFrame({
            "Tỉnh/Thành": ["TP.HCM", "Hà Nội"],
            "Quận/Huyện": ["Quận 1", "Cầu Giấy"],
            "Địa danh": ["Bùi Viện", "Duy Tân"]
        }))
        st.session_state.df_local = st.data_editor(
            st.session_state.df_local,
            use_container_width=True,
            num_rows="dynamic",
            height=600
        )

    elif menu == "Data_Report":
        st.subheader("📊 Nhật ký thực thi (Logs)")
        init_data('df_report', pd.DataFrame({
            "Ngày": ["2026-03-23"],
            "Website": ["Blog 1"],
            "Từ khóa": ["lái xe hộ"],
            "Trạng thái": ["DONE"]
        }))
        st.session_state.df_report = st.data_editor(
            st.session_state.df_report,
            use_container_width=True,
            num_rows="dynamic",
            height=800
        )

    st.success("✅ Mọi thay đổi trên bảng đều được tự động ghi nhận trong phiên làm việc này.")
