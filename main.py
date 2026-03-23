import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Lái Hộ - v310.0 Pro", page_icon="🚕", layout="wide")

# --- CSS SIÊU CẤP: GIAO DIỆN PHẲNG, SIDEBAR CỐ ĐỊNH, TÔNG VÀNG - ĐEN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    
    /* ẨN SIDEBAR MẶC ĐỊNH */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU BÊN TRÁI CỐ ĐỊNH */
    .nav-col { border-right: 1px solid #333333; height: 100vh; padding-right: 15px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    
    /* STYLE NÚT MENU */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 10px !important; margin-bottom: 2px !important;
    }
    .stButton>button:hover { border: 1px solid #ffd700 !important; color: #ffd700 !important; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }

    /* NÚT START ĐỎ & NÚT EXCEL */
    .btn-start button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; height: 3.5em !important; text-transform: uppercase; }
    .btn-excel button { background-color: #222222 !important; color: #ffd700 !important; border: 1px solid #ffd700 !important; height: 2.5em !important; font-size: 13px !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU THẬT (THEO SHEET CỦA NÍ)
if 'tab' not in st.session_state: st.session_state['tab'] = "Dashboard"

def init_all_data():
    # NẠP 13 DÒNG CẤU HÌNH THẬT
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Từ khóa bài viết", "thuê tài xế lái hộ, lái xe hộ tphcm, đưa người say, an toàn bia rượu..."],
            ["Website đối thủ", "lmd.vn, butl.vn, thuelai.app, saycar.vn"],
            ["Mục tiêu nội dung", "Bài viết tư vấn chuyên sâu, chốt sale dịch vụ, giới thiệu tiện ích"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200 chữ"],
            ["Mật độ Backlink", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ], columns=["Hạng mục", "Giá trị hiện tại"])

    # Khởi tạo các bảng dữ liệu nhập liệu
    map_sheets = {
        "df_backlink": ["Từ khóa", "Link đích", "Ghi chú"],
        "df_website": ["Tên Blog", "Nền tảng", "URL/ID"],
        "df_image": ["Tên ảnh", "Link Google Drive", "Mô tả"],
        "df_spin": ["Từ gốc", "{Cấu trúc|Spin}", "Ghi chú"],
        "df_local": ["Tỉnh/Thành", "Quận/Huyện", "Tuyến đường"],
        "df_report": ["STT", "Thời gian", "Tiêu đề", "Link bài", "Index"]
    }
    for key, cols in map_sheets.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=cols)

init_all_data()

# 3. GIAO DIỆN 2 CỘT CỐ ĐỊNH (SIDEBAR KHÔNG THỂ ẨN)
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Menu Nhập liệu
    st.markdown("<p style='color:#777; font-size:12px; font-weight:700;'>ĐẦU VÀO (NÍ NHẬP)</p>", unsafe_allow_html=True)
    menu_in = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local"]
    for m in menu_in:
        style = "active-nav" if st.session_state['tab'] == m else ""
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"nav_{m}"):
            st.session_state['tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br><p style='color:#777; font-size:12px; font-weight:700;'>ĐẦU RA (ROBOT IN)</p>", unsafe_allow_html=True)
    if st.button("📊 Data_Report", key="nav_report"):
        st.session_state['tab'] = "Data_Report"
        st.rerun()
        
    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# 4. KHU VỰC CHÍNH
with main_col:
    tab = st.session_state['tab']
    st.markdown(f"### 📍 {tab}")

    # Thanh công cụ Excel (Hiện ở mọi trang nhập liệu)
    if tab != "Dashboard" and tab != "Data_Report":
        xc1, xc2, _ = st.columns([1, 1, 3])
        with xc1: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL", key=f"ex_{tab}"); st.markdown('</div>', unsafe_allow_html=True)
        with xc2: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL", key=f"im_{tab}"); st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    if tab == "Dashboard":
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.markdown("<p class='gold-text'>⚙️ CẤU HÌNH HỆ THỐNG (DỮ LIỆU THẬT)</p>", unsafe_allow_html=True)
            # HIỂN THỊ 13 DÒNG THẬT SÁT NÓC
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
        with col_r:
            st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Trạng thái v55.0 Stable:")
                st.markdown('<div class="btn-start">', unsafe_allow_html=True)
                if st.button("🔥 START (CHẠY NGAY)", use_container_width=True):
                    st.success("Robot đã kích hoạt chiến dịch Lái Hộ!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

    elif tab == "Data_Report":
        st.markdown("<p class='gold-text'>📋 NHẬT KÝ HỆ THỐNG TỰ ĐỘNG IN RA</p>", unsafe_allow_html=True)
        st.dataframe(st.session_state['df_report'], use_container_width=True, height=750)

    else:
        # Tự động lấy bảng dữ liệu tương ứng
        key = f"df_{tab.split('_')[1].lower()}"
        st.markdown(f"<p class='gold-text'>📥 NHẬP DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)
        st.session_state[key] = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", height=750)

st.caption("🚀 SEO Automation Lái Hộ v310.0 | Full Master Data Ready")
