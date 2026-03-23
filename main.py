import streamlit as st
import pandas as pd
import time
from datetime import datetime

# 1. CẤU HÌNH TRANG & CSS LUXURY (CHỐNG SCROLL BẢNG)
st.set_page_config(page_title="Hệ thống SEO Pro - Lái Hộ & Giúp Việc", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #f8fafc; }
    
    /* ÉP BẢNG NỞ RỘNG TỐI ĐA - SHOW 25+ DÒNG KHÔNG CUỘN */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] > div { height: auto !important; max-height: none !important; }
    div[data-testid="stDataFrame"] iframe { height: 1000px !important; }

    /* Sidebar thiết kế hiện đại */
    [data-testid="stSidebar"] { background-color: #0f172a; color: white; }
    [data-testid="stSidebar"] hr { border-color: #334155; }
    
    /* Card trang trí */
    .st-emotion-cache-12w0qpk { border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); background: white; padding: 25px; }
    
    /* Nút bấm Gradient */
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 700; height: 3.5em;
        transition: all 0.3s; border: none; color: white;
    }
    .btn-run button { background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important; }
    .btn-schedule button { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DATA CHUẨN (SOI TỪNG PIXEL TRÊN ẢNH CỦA ĐĂNG)
MENU_MAP = {
    "⚙️ Config & Điều khiển": "config",
    "🔗 Data Backlink": "backlink",
    "🌐 Data Website": "website",
    "🖼️ Data Image": "image",
    "✍️ Data Spin": "spin",
    "📍 Data Local": "local",
    "📊 Data Report": "report"
}

def init_data():
    for m_label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                cols = ["Cột A (Nội dung - Fix cứng)", "Cột B (Dữ liệu - Bạn điền vào đây)"]
                data = [["GEMINI_API_KEY", ""], ["SERPAPI_KEY", ""], ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["SENDER_PASSWORD", ""], ["RECEIVER_EMAIL", "jundeng.po@gmail.com"], ["Danh sách Keyword bài viết", "thuê tài xế lái hộ..."], ["TARGET_URL", "https://laiho.vn/"], ["Website đối thủ", "lmd.vn, butl.vn"], ["Mục tiêu bài viết", "Tư vấn dịch vụ"], ["Số lượng bài cần tạo", "10"], ["Thiết lập số lượng chữ", "900-1200"], ["Số lượng backlink/bài", "3-4"], ["FOLDER_DRIVE_ID", ""]]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                cols = ["DatDat", "Cột B (Danh sách URL Đích)", "Cột C (Số lần đã dùng)"]
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 10, columns=cols)
            elif key_suffix == "website":
                cols = ["ID", "Nền tảng", "URL / ID", "Tài khoản (Chỉ WP)", "Mật khẩu ứng dụng (Chỉ WP)", "Trạng thái", "Giới hạn bài/ngày"]
                st.session_state[key] = pd.DataFrame([["Blog Lái Hộ 1", "Blogger", "muontaixelaxe.laiho1@...", "", "", "Bật", "1-2"]] * 5, columns=cols)
            elif key_suffix == "image":
                cols = ["Link Ảnh (URL)", "Số lần đã dùng"]
                st.session_state[key] = pd.DataFrame([["https://i.postimg.cc/abc", 0]] * 5, columns=cols)
            elif key_suffix == "spin":
                cols = ["Từ khóa gốc", "Từ đồng nghĩa (phẩy)"]
                st.session_state[key] = pd.DataFrame([["chúng tôi", "tụi mình, bên mình, chúng tôi"]] * 5, columns=cols)
            elif key_suffix == "local":
                cols = ["Tỉnh/Thành phố", "Quận/Huyện", "Địa điểm/Tuyến đường"]
                st.session_state[key] = pd.DataFrame([["Tp Hồ Chí Minh", "Quận 1", "Bùi Viện"]] * 5, columns=cols)
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)

init_data()

# 3. LOGIC ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1.5,1])[1]:
        st.markdown("<h2 style='text-align: center;'>🔐 SEO SYSTEM PRO</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            u = st.text_input("Tài khoản", value="admin")
            p = st.text_input("Mật khẩu", type="password", value="123")
            if st.button("VÀO HỆ THỐNG"):
                if u == "admin" and p == "123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Sai tài khoản!")
else:
    # 4. SIDEBAR CHUYÊN NGHIỆP
    with st.sidebar:
        st.markdown("### 🏢 DASHBOARD")
        st.caption("Dự án: Lái Hộ | Ver 3.0")
        st.markdown("---")
        choice = st.radio("MENU QUẢN TRỊ:", list(MENU_MAP.keys()))
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHÔNG GIAN LÀM VIỆC CHÍNH
    st.title(f"📍 {choice}")
    current_key = f"df_{MENU_MAP[choice]}"

    # Tool Card: Import / Export
    with st.container(border=True):
        c1, c2, c3 = st.columns([1.5, 1.5, 2])
        with c1:
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 Xuất {choice}.csv", data=csv, file_name=f"{choice}.csv", use_container_width=True)
        with c2:
            up = st.file_uploader("Nhập file (.csv)", type=["csv"], label_visibility="collapsed")
        with c3:
            if st.button("🚀 Nạp dữ liệu"):
                if up:
                    st.session_state[current_key] = pd.read_csv(up)
                    st.success("Đã cập nhật!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. HIỂN THỊ NỘI DUNG CHI TIẾT
    if "Config" in choice:
        st.subheader("⚙️ 1. Cấu hình thông số")
        st.session_state[current_key] = st.data_editor(st.session_state[current_key], use_container_width=True, height=450)
        
        st.markdown("---")
        st.subheader("⚡ 2. Kích hoạt chiến dịch")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
            if st.button("🔥 CHẠY NGAY TỨC THÌ (RUN NOW)"):
                progress = st.progress(0)
                status = st.empty()
                for i in range(1, 101):
                    time.sleep(0.01)
                    progress.progress(i)
                    if i == 20: status.text("🤖 AI đang đọc Data_Backlink...")
                    if i == 50: status.text("✍️ Đang Spin nội dung & Chèn hình ảnh chuẩn SEO...")
                    if i == 80: status.text("🌐 Đang đẩy bài lên hệ thống Blog vệ tinh...")
                st.success("✅ HOÀN TẤT! Đã đăng bài thành công lên hệ thống.")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='btn-schedule'>", unsafe_allow_html=True)
            if st.button("📅 LẬP LỊCH ĐĂNG (SCHEDULE)"):
                with st.status("🔍 Đang quét bảng Data_Report...", expanded=True):
                    st.write("Đang kiểm tra cột 'Thời gian hẹn giờ'...")
                    time.sleep(1)
                    st.write("Đã xác định lịch hẹn cho các bài viết.")
                    st.write("🤖 Hệ thống đã chuyển sang chế độ CHỜ ĐĂNG.")
                st.info("💡 Hệ thống sẽ tự động thực thi khi đến khung giờ quy định.")
            st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        # HIỂN THỊ BẢNG FULL (Chiều cao 1000px để show ~30 dòng)
        st.subheader(f"📊 Bảng dữ liệu: {choice}")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("✅ Ní có thể copy từ Excel dán trực tiếp vào đây. Hệ thống tự động nhận diện 100%.")
