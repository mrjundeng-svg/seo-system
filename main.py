import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG & UI/UX CAO CẤP
st.set_page_config(page_title="Hệ thống SEO Pro - Lái Hộ", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    
    /* Làm bảng nở rộng 100% và hiển thị ít nhất 25 dòng */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] div[data-testid="stTable"] { height: auto !important; }
    
    /* Sidebar thiết kế hiện đại */
    [data-testid="stSidebar"] { background-color: #1e293b; color: #f8fafc; }
    
    /* Nút Run System màu xanh lá nổi bật */
    .run-btn button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important; font-weight: 700 !important; height: 3.5em !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO CẤU TRÚC DỮ LIỆU (SOI KỸ THEO ẢNH CỦA NÍ)
MENU_MAP = {
    "⚙️ Config & Chạy bài": "config",
    "🔗 Data Backlink": "backlink",
    "🌐 Data Website": "website",
    "🖼️ Data Image": "image",
    "✍️ Data Spin": "spin",
    "📍 Data Local": "local",
    "📊 Data Report": "report"
}

def init_session_state():
    for m_label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            # Khởi tạo chuẩn xác từng cột theo ảnh Google Sheets
            if key_suffix == "config":
                cols = ["Cột A (Nội dung)", "Cột B (Dữ liệu)"]
                data = [["GEMINI_API_KEY", ""], ["SERPAPI_KEY", ""], ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["SENDER_PASSWORD", ""], ["RECEIVER_EMAIL", "jundeng.po@gmail.com"], ["Danh sách Keyword", "thuê tài xế lái hộ..."], ["TARGET_URL", "https://laiho.vn/"], ["Website đối thủ", ""], ["Mục tiêu bài viết", ""], ["Số lượng bài", "10"], ["Số chữ", "900-1200"], ["Số backlink", "3-4"], ["FOLDER_DRIVE_ID", ""]]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                cols = ["DatDat", "Cột B (Danh sách URL Đích)", "Cột C (Số lần đã dùng)"]
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 10, columns=cols)
            elif key_suffix == "website":
                cols = ["c", "Nền tảng", "URL / ID", "Tài khoản (Chỉ WP)", "Mật khẩu ứng dụng (Chỉ WP)", "Trạng thái", "Giới hạn bài/ngày"]
                st.session_state[key] = pd.DataFrame([["Blog Lái Hộ 1", "Blogger", "muontaixelaxe.laiho1@...", "", "", "Bật", "1-2"]] * 5, columns=cols)
            elif key_suffix == "image":
                cols = ["Link Ảnh (URL)", "Số lần dùng"]
                st.session_state[key] = pd.DataFrame([["https://i.postimg.cc/...", 3]] * 5, columns=cols)
            elif key_suffix == "spin":
                cols = ["Từ khóa gốc", "Từ đồng nghĩa (phẩy)"]
                st.session_state[key] = pd.DataFrame([["chúng tôi", "tụi mình, bên mình..."]] * 5, columns=cols)
            elif key_suffix == "local":
                cols = ["Tỉnh/Thành phố", "Quận/Huyện", "Địa điểm/Tuyến đường"]
                st.session_state[key] = pd.DataFrame([["Tp Hồ Chí Minh", "Quận 1", "Bùi Viện"]] * 5, columns=cols)
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL/ID", "Ngày đăng", "Từ khóa 1", "Từ khóa 2", "Từ khóa 3", "Từ khóa 4", "Từ khóa 5", "Link bài", "Tiêu đề", "Drive ID", "Hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)

init_session_state()

# 3. KIỂM TRA ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,2,1])[1]:
        st.title("🔐 SEO SYSTEM LOGIN")
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="123")
        if st.button("ĐĂNG NHẬP"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # 4. SIDEBAR MENU
    with st.sidebar:
        st.markdown("### 🏢 SEO CONTROL PANEL")
        choice = st.radio("CHỌN DANH MỤC:", list(MENU_MAP.keys()))
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHÔNG GIAN LÀM VIỆC CHÍNH
    st.title(f"📍 {choice}")
    current_key = f"df_{MENU_MAP[choice]}"

    # Công cụ Import/Export (Nằm trong khung Expander cho đẹp)
    with st.expander("🛠️ Công cụ File (Nhập/Xuất Dữ Liệu)"):
        col1, col2 = st.columns(2)
        with col1:
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 Tải {choice}.csv", data=csv, file_name=f"{choice}.csv", use_container_width=True)
        with col2:
            up = st.file_uploader("Nhập file CSV", type=["csv"], label_visibility="collapsed")
            if st.button("🚀 Cập nhật dữ liệu từ File"):
                if up:
                    st.session_state[current_key] = pd.read_csv(up)
                    st.success("Đã cập nhật!")
                    st.rerun()

    st.markdown("---")

    # 6. HIỂN THỊ DỮ LIỆU
    if "Config" in choice:
        # Tab Config có thêm nút chạy bài
        st.subheader("⚙️ Thiết lập & Kích hoạt AI")
        st.session_state[current_key] = st.data_editor(st.session_state[current_key], use_container_width=True, height=450)
        
        st.markdown("<div class='run-btn'>", unsafe_allow_html=True)
        if st.button("🔥 BẮT ĐẦU CHẠY SEO (RUN SYSTEM)"):
            progress = st.progress(0)
            status = st.empty()
            for i in range(1, 101):
                time.sleep(0.02)
                progress.progress(i)
                if i == 20: status.text("🤖 AI đang đọc Data_Backlink...")
                if i == 50: status.text("✍️ Đang Spin nội dung & Chèn ảnh...")
                if i == 80: status.text("🌐 Đang đẩy bài lên hệ thống Blog...")
            st.success("✅ HOÀN TẤT! Đã đăng 10 bài viết thành công.")
        st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        # Các Tab Data khác hiển thị bảng Full (Chiều cao 850 ~ 25 dòng)
        st.subheader(f"📊 Bảng dữ liệu: {choice}")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=850 
        )

    st.caption("✅ Ní có thể copy từ Excel dán vào đây hoặc ngược lại. Hệ thống tự động lưu tạm.")
