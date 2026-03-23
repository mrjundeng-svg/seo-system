import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS DARK-GOLD PREMIUM
st.set_page_config(page_title="SEO Lái Hộ v150.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* NỀN ĐEN SÂU SANG TRỌNG */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR TRẮNG NGÀ / ĐEN (TÙY CHỈNH THEO STYLE XẾ HỘ) */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important; 
    }
    
    /* CHỮ VÀNG GOLD CHO TIÊU ĐỀ */
    h1, h2, h3, h4, p, span, label { 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
    }
    .gold-text { color: #ffd700 !important; font-weight: 700; }

    /* STYLE CHO MENU ĐA CẤP (SUB-MENU) */
    .st-emotion-cache-164776p { color: #ffd700 !important; } /* Màu icon expander */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #222 !important;
    }

    /* BẢNG DỮ LIỆU SÁNG RÕ */
    [data-testid="stDataFrame"] { 
        background-color: #1a1a1a !important; 
        border: 1px solid #444 !important; 
    }

    /* NÚT BẤM VÀNG GOLD - CHỮ ĐEN (DỄ NHÌN) */
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 700; height: 3em;
        background-color: #ffd700 !important; 
        color: #000000 !important;
        border: none !important;
        text-transform: uppercase;
    }
    .stButton>button:hover { 
        background-color: #ffcc00 !important; 
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.4);
    }

    /* CÁC NÚT NHỎ HƠN */
    .stDownloadButton>button {
        background-color: #222 !important;
        color: #ffd700 !important;
        border: 1px solid #ffd700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU
if 'menu_active' not in st.session_state: st.session_state['menu_active'] = "Bảng điều khiển"

MENU_STRUCTURE = {
    "🏠 Tổng quan": [],
    "🗺️ Phủ sóng vùng": ["Khu vực TPHCM", "Khu vực Hà Nội", "Dịch vụ lái hộ liên tỉnh"],
    "⚙️ Data Config": [],
    "🖼️ Data Image": [],
    "💬 Từ điển Spin": [],
    "👥 Backlink Master": [],
    "📊 SEO Report": [],
    "📍 Local Map": []
}

def init_session_data():
    if 'df_config' not in st.session_state:
        cols = ["DANH MỤC", "GIÁ TRỊ THIẾT LẬP"]
        data = [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Keyword chính", "thuê tài xế lái hộ, đưa người say..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu bài", "Tư vấn, giới thiệu dịch vụ"],
            ["Số lượng bài", "10"],
            ["Độ dài bài", "1000 - 1200 chữ"],
            ["Mật độ Link", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ]
        st.session_state['df_config'] = pd.DataFrame(data, columns=cols)
    if 'df_report' not in st.session_state:
        st.session_state['df_report'] = pd.DataFrame(columns=["Website", "Ngày đăng", "Trạng thái", "Tiêu đề"])

init_session_data()

# 3. SIDEBAR VỚI SUB-MENU ĐA CẤP
with st.sidebar:
    st.markdown("<h2 class='gold-text'>🚕 ĐIỀU HÀNH SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    for main_menu, sub_menus in MENU_STRUCTURE.items():
        if sub_menus:
            with st.expander(main_menu):
                for sub in sub_menus:
                    if st.button(f"▪️ {sub}", key=sub, use_container_width=True):
                        st.session_state['menu_active'] = sub
        else:
            if st.button(main_menu, key=main_menu, use_container_width=True):
                st.session_state['menu_active'] = main_menu
    
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT"): st.rerun()

# 4. KHU VỰC CHÍNH (DYNAMIC CONTENT)
active = st.session_state['menu_active']
st.markdown(f"### 📍 {active}")

if "Config" in active or "Tổng quan" in active or "Bảng điều khiển" in active:
    # THANH CÔNG CỤ
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    with c3: st.button("🔄 SYNC")

    st.markdown("<br>", unsafe_allow_html=True)

    # CHIA CỘT: BẢNG VÀ ĐIỀU KHIỂN
    col_t, col_r = st.columns([2, 1])
    
    with col_t:
        st.markdown("<p class='gold-text'>⚙️ CẤU HÌNH HỆ THỐNG (SHOW FULL 13 DÒNG)</p>", unsafe_allow_html=True)
        st.session_state['df_config'] = st.data_editor(
            st.session_state['df_config'], 
            use_container_width=True, 
            num_rows="fixed",
            height=520 
        )
    
    with col_r:
        st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành v55.0 Stable:")
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                p = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.2)
                    p.progress(i * 10)
                st.success("✅ ĐÃ XONG 10 BÀI!")
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ĐĂNG")

elif "Phủ sóng" in active:
    st.info(f"Đang hiển thị dữ liệu cho: {active}")
    st.data_editor(pd.DataFrame([["Tuyến 1", "Bật"], ["Tuyến 2", "Tắt"]], columns=["Tên vùng", "Trạng thái"]), use_container_width=True)

else:
    st.write(f"Tính năng {active} đang được kết nối dữ liệu...")

st.caption("🚕 SEO Lái Hộ v150.0 | Enterprise Sub-menu System")
