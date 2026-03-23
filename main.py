import streamlit as st
import pandas as pd
import io

# 1. CẤU HÌNH TRANG & CSS PREMIUM
st.set_page_config(page_title="SEO Lái Hộ - Premium Admin", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* Tổng thể giao diện */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"]  { font-family: 'Inter', sans-serif; }
    .main { background-color: #f4f7f6; }
    
    /* Làm bảng hiển thị Full không scroll */
    [data-testid="stDataFrame"] { width: 100% !important; height: auto !important; }
    [data-testid="stDataFrame"] > div { height: auto !important; max-height: none !important; }

    /* Card thiết kế */
    .st-emotion-cache-12w0qpk { border-radius: 12px; border: none; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); background: white; padding: 20px; }
    
    /* Nút bấm */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; transition: all 0.3s; height: 3.2em; border: none; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,123,255,0.3); }
    
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1e293b; color: white; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: white; }
    
    /* Tiêu đề */
    h1 { color: #1e293b; font-weight: 700; }
    h3 { color: #334155; font-weight: 600; padding-bottom: 10px; border-bottom: 2px solid #e2e8f0; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU CHUẨN (KHẮC PHỤC KEYERROR)
# Bản đồ ánh xạ giữa Tên Menu và Khóa Session State
MENU_MAP = {
    "Config Hệ thống": "config",
    "Data Backlink": "backlink",
    "Data Website": "website",
    "Data Image": "image",
    "Data Spin": "spin",
    "Data Local": "local",
    "Data Report": "report"
}

def init_session_state():
    for menu_name, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            # Khởi tạo đúng cột theo ảnh Google Sheets của Đăng
            if key_suffix == "config":
                cols = ["Cột A (Nội dung - Fix cứng)", "Cột B (Dữ liệu - Bạn điền vào đây)"]
                data = [["GEMINI_API_KEY", ""], ["SERPAPI_KEY", ""], ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["SENDER_PASSWORD", ""], ["RECEIVER_EMAIL", "jundeng.po@gmail.com"], ["Danh sách Keyword bài viết", "thuê tài xế lái hộ..."], ["TARGET_URL", "https://laiho.vn/"], ["Website đối thủ", "lmd.vn, butl.vn"], ["Mục tiêu bài viết", ""], ["Số lượng bài cần tạo", "10"], ["Thiết lập số lượng chữ", "900-1200"], ["Số lượng backlink/bài", "3-4"], ["FOLDER_DRIVE_ID", ""]]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                cols = ["DatDat", "Cột B (Danh sách URL Đích - cách nhau bằng dấu phẩy)", "Cột C (Số lần đã dùng)"]
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]], columns=cols)
            elif key_suffix == "website":
                cols = ["c", "Nền tảng", "URL / ID", "Tài khoản (Chỉ WP)", "Mật khẩu ứng dụng (Chỉ WP)", "Trạng thái", "Giới hạn bài/ngày"]
                st.session_state[key] = pd.DataFrame([["Blog Lái Hộ 1", "Blogger", "muontaixelaxe.laiho1@...", "", "", "Bật", "1-2"]], columns=cols)
            elif key_suffix == "image":
                cols = ["Link Ảnh (URL)", "Số lần dùng"]
                st.session_state[key] = pd.DataFrame([["https://i.postimg.cc/...", 0]], columns=cols)
            elif key_suffix == "spin":
                cols = ["Từ khóa gốc", "Từ đồng nghĩa (Cách nhau bằng dấu phẩy)"]
                st.session_state[key] = pd.DataFrame([["chúng tôi", "tụi mình, bên mình..."]], columns=cols)
            elif key_suffix == "local":
                cols = ["Tỉnh/Thành phố", "Quận/Huyện", "Địa điểm/Tuyến đường"]
                st.session_state[key] = pd.DataFrame([["Tp Hồ Chí Minh", "Quận 1", "Bùi Viện"]], columns=cols)
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)

init_session_state()

# 3. GIAO DIỆN ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center;'>🚀 SEO System Pro</h1>", unsafe_allow_html=True)
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            st.subheader("Đăng nhập")
            u = st.text_input("Tài khoản")
            p = st.text_input("Mật khẩu", type="password")
            if st.button("Truy cập hệ thống"):
                if u == "admin" and p == "123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Sai tài khoản!")
else:
    # 4. SIDEBAR CHUYÊN NGHIỆP
    with st.sidebar:
        st.markdown("## ⚙️ HỆ THỐNG SEO")
        st.caption("Dự án: Lái Hộ (Hồ Chí Minh)")
        st.markdown("---")
        choice = st.radio("Menu quản trị:", list(MENU_MAP.keys()))
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHÔNG GIAN LÀM VIỆC CHÍNH
    st.title(f"📍 {choice}")
    
    # Khu vực Card Import/Export
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### 📤 Xuất dữ liệu")
            current_key = f"df_{MENU_MAP[choice]}"
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"Tải {choice}.csv", data=csv, file_name=f"{choice}.csv", mime='text/csv')
        with col2:
            st.markdown("##### 📥 Nhập dữ liệu")
            up = st.file_uploader("Kéo file CSV vào đây", type=["csv"], key="uploader")
            if st.button("Nạp dữ liệu từ File"):
                if up:
                    st.session_state[current_key] = pd.read_csv(up)
                    st.success("✅ Đã cập nhật!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. HIỂN THỊ BẢNG DỮ LIỆU FULL
    st.subheader(f"📊 Bảng dữ liệu: {choice}")
    key = f"df_{MENU_MAP[choice]}"
    
    # Hiển thị data editor với chiều cao động (Dynamic height)
    st.session_state[key] = st.data_editor(
        st.session_state[key],
        use_container_width=True,
        num_rows="dynamic",
        # Không đặt height cố định để CSS ép nó nở ra full
        height=600 if len(st.session_state[key]) < 15 else 1200
    )

    st.caption("💡 Mẹo: Nhấn đúp chuột vào ô để sửa. Nhấn (+) ở cuối bảng để thêm hàng mới.")
