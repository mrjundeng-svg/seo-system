import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG - ÉP SIDEBAR LUÔN MỞ
st.set_page_config(
    page_title="Hệ thống SEO Lái Hộ v180.0", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" # ÉP SIDEBAR HIỆN RA NGAY
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR ĐEN SÂU - VIỀN VÀNG */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
        min-width: 300px !important;
    }
    
    /* CHỮ TRẮNG & VÀNG GOLD */
    h1, h2, h3, h4, p, span, label, .stMarkdown { 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
    }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 20px; }

    /* STYLE SUB-MENU (EXPANDER) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #222 !important;
        margin-bottom: 0px !important;
    }
    div[data-testid="stExpander"] p { color: #ffd700 !important; font-weight: 600 !important; }

    /* NÚT TRONG SIDEBAR */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #aaaaaa !important;
        border: none !important;
        text-align: left !important;
        padding-left: 15px !important;
        font-size: 14px !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #111111 !important;
    }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }

    /* NÚT CHẠY CHIẾN DỊCH */
    .btn-run button {
        background-color: #ffd700 !important; color: #000000 !important; font-weight: 700 !important;
        border-radius: 10px !important; height: 3.5em !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. QUẢN LÝ MENU & DATA
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Data Config"

# Cấu trúc Menu y chang ảnh Xế Hộ
STRUCTURE = {
    "🏠 Tổng quan": ["Bảng điều khiển", "Thống kê Index"],
    "🚕 Dịch vụ Lái Hộ": ["Phủ sóng vùng", "Tính cước Lái Hộ", "Quản lý Tài xế"],
    "🏠 Giúp Việc Nhanh": ["Đối tác B2B", "Quản lý Nhân sự"],
    "⚙️ Hệ thống SEO": ["Data Config", "Hệ thống Website", "Backlink Master"],
    "🖼️ Kho dữ liệu": ["Kho hình ảnh", "Từ điển Spin"],
    "📊 Báo cáo": ["Báo cáo cuối", "Lịch sử Robot"]
}

def init_data():
    if 'df_config' not in st.session_state:
        # NẠP ĐẦY ĐỦ 13 DÒNG TỪ ẢNH image_3bd66d.jpg
        data = [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Danh sách Keyword", "thuê tài xế lái hộ, đưa người say..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu nội dung", "Bài viết tư vấn chuyên sâu, chốt sale"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200 chữ"],
            ["Mật độ Backlink", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ]
        st.session_state['df_config'] = pd.DataFrame(data, columns=["DANH MỤC", "GIÁ TRỊ"])

init_data()

# 3. SIDEBAR ĐA CẤP (PHỤC HỒI)
with st.sidebar:
    st.markdown("<h2 class='gold-title'>🏢 ĐIỀU HÀNH SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    for main, subs in STRUCTURE.items():
        with st.sidebar.expander(main, expanded=(st.session_state['active_tab'] in subs)):
            for sub in subs:
                if st.button(f"▪️ {sub}", key=f"sub_{sub}", use_container_width=True):
                    st.session_state['active_tab'] = sub
                    st.rerun()
    
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT"): st.stop()

# 4. KHU VỰC CHÍNH
tab = st.session_state['active_tab']
st.markdown(f"#### 📍 {tab}")

if tab == "Data Config" or tab == "Bảng điều khiển":
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    with c3: st.button("🔄 ĐỒNG BỘ")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH CHI TIẾT (13 DÒNG)</p>", unsafe_allow_html=True)
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
    
    with col_r:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành v55.0 Stable:")
            st.markdown('<div class="btn-run">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                p = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.2)
                    p.progress(i * 10)
                st.success("✅ ĐÃ XONG 10 BÀI!")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ĐĂNG")

elif tab == "Phủ sóng vùng":
    st.info("Quản lý các khu vực hoạt động của dự án Lái Hộ.")
    st.data_editor(pd.DataFrame([["Quận 1", "Bật"], ["Quận 7", "Bật"]], columns=["Khu vực", "Trạng thái"]), use_container_width=True)

else:
    st.warning(f"Tính năng {tab} đang chờ kết nối dữ liệu từ Robot.")

st.caption("🚕 SEO Lái Hộ v180.0 | High-End Project Management")
