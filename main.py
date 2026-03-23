import streamlit as st
import pandas as pd
import io

# 1. CẤU HÌNH GIAO DIỆN & STYLE
st.set_page_config(page_title="Hệ thống SEO Lái Hộ - Admin", layout="wide")

# CSS để bảng hiển thị full và giao diện chuyên nghiệp
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] { width: 100%; }
    .main { background-color: #f5f7f9; }
    div[data-testid="stExpander"] { background-color: white; border-radius: 10px; border: 1px solid #e6e9ef; }
    .stButton>button { border-radius: 5px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO SESSION STATE (LƯU DỮ LIỆU TẠM THỜI)
def init_df(key, columns, data=None):
    if key not in st.session_state:
        if data:
            st.session_state[key] = pd.DataFrame(data)
        else:
            st.session_state[key] = pd.DataFrame(columns=columns)

# Khởi tạo từng bảng theo đúng ảnh bạn gửi
init_df('df_config', ["Hạng mục", "Giá trị"], [
    {"Hạng mục": "GEMINI_API_KEY", "Giá trị": ""},
    {"Hạng mục": "SERPAPI_KEY", "Giá trị": ""},
    {"Hạng mục": "SENDER_EMAIL", "Giá trị": "jundeng.po@gmail.com"},
    {"Hạng mục": "SENDER_PASSWORD", "Giá trị": ""},
    {"Hạng mục": "RECEIVER_EMAIL", "Giá trị": "jundeng.po@gmail.com"},
    {"Hạng mục": "Danh sách Keyword bài viết", "Giá trị": "thuê tài xế lái hộ, đưa người say về nhà..."},
    {"Hạng mục": "TARGET_URL", "Giá trị": "https://laiho.vn/"},
    {"Hạng mục": "Website đối thủ", "Giá trị": "lmd.vn, butl.vn"},
    {"Hạng mục": "Mục tiêu bài viết", "Giá trị": "bài viết tư vấn, hướng dẫn..."},
    {"Hạng mục": "Số lượng bài cần tạo", "Giá trị": "10"},
    {"Hạng mục": "Thiết lập số lượng chữ", "Giá trị": "900 - 1200"},
    {"Hạng mục": "Số lượng backlink/bài", "Giá trị": "3 - 4"},
    {"Hạng mục": "FOLDER_DRIVE_ID", "Giá trị": ""}
])

init_df('df_backlink', ["DatDat (Từ khóa)", "Cột B (Danh sách URL Đích)", "Cột C (Số lần đã dùng)"], [
    {"DatDat (Từ khóa)": "lái xe hộ", "Cột B (Danh sách URL Đích)": "https://laiho.vn", "Cột C (Số lần đã dùng)": 0},
    {"DatDat (Từ khóa)": "dịch vụ lái xe hộ", "Cột B (Danh sách URL Đích)": "https://laiho.vn", "Cột C (Số lần đã dùng)": 4}
])

init_df('df_website', ["ID", "Nền tảng", "URL / ID", "Tài khoản (Chỉ WP)", "Mật khẩu ứng dụng (Chỉ WP)", "Trạng thái", "Giới hạn bài/ngày"], [
    {"ID": "Blog Lái Hộ 1", "Nền tảng": "Blogger", "URL / ID": "muontaixelaxe.laiho1@...", "Trạng thái": "Bật", "Giới hạn bài/ngày": "1 - 2"}
])

init_df('df_image', ["Link Ảnh (URL)", "Số lần đã dùng"], [
    {"Link Ảnh (URL)": "https://i.postimg.cc/abc", "Số lần đã dùng": 3}
])

init_df('df_spin', ["Từ khóa gốc", "Từ đồng nghĩa (Cách nhau bằng dấu phẩy)"], [
    {"Từ khóa gốc": "chúng tôi", "Từ đồng nghĩa (Cách nhau bằng dấu phẩy)": "tụi mình, bên mình, phía chúng tôi"}
])

init_df('df_local', ["Tỉnh/Thành phố", "Quận/Huyện", "Địa điểm/Tuyến đường"], [
    {"Tỉnh/Thành phố": "Tp Hồ Chí Minh", "Quận/Huyện": "Quận 1", "Địa điểm/Tuyến đường": "Bùi Viện"}
])

init_df('df_report', ["Website", "Nền tảng", "Ngày đăng bài", "Từ khoá 1", "Link bài viết", "Trạng thái"], [
    {"Website": "Blog Lái Hộ 1", "Nền tảng": "Blogger", "Ngày đăng bài": "2026-03-23", "Từ khoá 1": "thuê tài xế", "Trạng thái": "DONE"}
])

# 3. HÀM XỬ LÝ FILE
def get_csv_download(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# 4. GIAO DIỆN CHÍNH
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống SEO Lái Hộ")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Vào hệ thống"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Sai tài khoản!")
else:
    # SIDEBAR
    with st.sidebar:
        st.header("🎮 MENU SEO")
        menu = st.radio("Chọn danh mục dữ liệu:", ["Config", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"])
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # KHÔNG GIAN LÀM VIỆC
    st.title(f"📍 Quản lý {menu}")
    
    # Khu vực Import/Export
    with st.expander("🛠️ Công cụ File (Nhập/Xuất Excel-CSV)"):
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(f"📥 Tải {menu} về máy", get_csv_download(st.session_state[f'df_{menu.lower()}']), f"{menu}.csv", "text/csv")
        with c2:
            up = st.file_uploader(f"📤 Đẩy file {menu} lên", type="csv")
            if up:
                st.session_state[f'df_{menu.lower()}'] = pd.read_csv(up)
                st.success("Đã cập nhật dữ liệu từ file!")

    st.markdown("---")

    # HIỂN THỊ BẢNG DỮ LIỆU THEO TỪNG TAB (Check đúng từng cột trong ảnh)
    key = f'df_{menu.lower()}'
    
    # Thiết lập chiều cao bảng lớn (height=1000) để hiện full không cần scroll nội bộ
    st.session_state[key] = st.data_editor(
        st.session_state[key],
        use_container_width=True,
        num_rows="dynamic", # Cho phép thêm hàng mới bằng nút (+)
        height=1000 
    )

    st.info("💡 Bạn có thể copy từ Excel rồi dán trực tiếp vào bảng trên hoặc ngược lại.")
