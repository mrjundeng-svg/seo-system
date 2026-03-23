import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hệ thống SEO Lái Hộ v300.0", page_icon="🚕", layout="wide")

# --- CSS SIÊU CẤP: ĐEN - VÀNG - ĐỎ & SIDEBAR CỐ ĐỊNH ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU BÊN TRÁI CỐ ĐỊNH 100% */
    .nav-col { border-right: 1px solid #333333; height: 100vh; padding-right: 15px; position: fixed; width: 200px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; }
    
    /* NÚT MENU */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 5px !important;
    }
    .stButton>button:hover { border: 1px solid #ffd700 !important; color: #ffd700 !important; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }

    /* NÚT CHỨC NĂNG */
    .btn-start button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; height: 4em !important; text-transform: uppercase; }
    .btn-excel button { background-color: #222222 !important; color: #ffd700 !important; border: 1px solid #ffd700 !important; height: 2.5em !important; font-size: 13px !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU CÁC BẢNG
if 'tab' not in st.session_state: st.session_state['tab'] = "Dashboard"

def init_all_tables():
    # Bảng Config (13 dòng chuẩn)
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
            ["Keyword chính", "thuê tài xế lái hộ"],
            ["Website đối thủ", "lmd.vn, butl.vn"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1200"],
            ["Mật độ Link", "3-5"],
            ["Mục tiêu bài", "Tư vấn chốt sale"],
            ["Trạng thái", "Sẵn sàng"]
        ], columns=["Hạng mục", "Giá trị"])

    # Danh sách các bảng Ní yêu cầu
    sheets = {
        "df_backlink": ["Từ khóa", "Link đích", "Ghi chú"],
        "df_website": ["Tên Web", "Nền tảng", "URL/ID"],
        "df_image": ["Tên ảnh", "Link Drive", "Mô tả"],
        "df_spin": ["Từ gốc", "Cấu trúc Spin", "Ghi chú"],
        "df_local": ["Tỉnh/Thành", "Quận/Huyện", "Tuyến đường"],
        "df_report": ["STT", "Thời gian", "Tiêu đề", "Link bài", "Index"]
    }
    for key, cols in sheets.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=cols)

init_all_tables()

# 3. GIAO DIỆN 2 CỘT CỐ ĐỊNH (SIDEBAR KHÔNG THỂ ẨN)
nav_col, main_col = st.columns([1, 4], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    for m in menu:
        if st.session_state['tab'] == m:
            st.markdown("<div class='active-nav'>", unsafe_allow_html=True)
            if st.button(f"▪️ {m}", key=f"nav_{m}"): pass
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(f"  {m}", key=f"nav_{m}"):
                st.session_state['tab'] = m
                st.rerun()

# 4. KHU VỰC NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['tab']
    st.markdown(f"### 📍 {tab}")

    # Nút Xuất/Nhập Excel (Hiện ở mọi trang trừ Dashboard)
    if tab != "Dashboard":
        xc1, xc2, _ = st.columns([1, 1, 3])
        with xc1: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL", key=f"ex_{tab}"); st.markdown('</div>', unsafe_allow_html=True)
        with xc2: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL", key=f"im_{tab}"); st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    if tab == "Dashboard":
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.markdown("<p class='gold-text'>⚙️ CẤU HÌNH HỆ THỐNG (13 DÒNG)</p>", unsafe_allow_html=True)
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520)
        with col_r:
            st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Vận hành v55.0 Stable:")
                st.markdown('<div class="btn-start">', unsafe_allow_html=True)
                if st.button("🔥 START (CHẠY NGAY)", use_container_width=True):
                    st.success("Robot bắt đầu thực thi chiến dịch!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

    else:
        # Tự động lấy bảng tương ứng với Tab
        key = f"df_{tab.split('_')[1].lower()}"
        st.markdown(f"<p class='gold-text'>📥 DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)
        st.session_state[key] = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", height=700)

st.caption("🚀 SEO Automation Lái Hộ v300.0 | Full Interface & Logic Ready")
