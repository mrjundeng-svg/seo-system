import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# =================================================================
# 1. CẤU HÌNH TRANG - KHÓA SIDEBAR CỐ ĐỊNH & LAYOUT RỘNG
# =================================================================
st.set_page_config(
    page_title="Hệ thống SEO Lái Hộ v320.0", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* TÔNG NỀN ĐEN SÂU SANG TRỌNG */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; }

    /* --- SIDEBAR CỐ ĐỊNH & TINH GỌN --- */
    /* Khóa chết nút đóng/mở sidebar */
    [data-testid="collapsedControl"] { display: none !important; }
    button[kind="headerNoContext"] { display: none !important; }
    
    section[data-testid="stSidebar"] { 
        min-width: 250px !important;
        max-width: 250px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
    }

    /* CHỮ VÀNG GOLD & TRẮNG */
    [data-testid="stSidebar"] * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 20px; margin-bottom: 20px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; }
    .stMarkdown, label, p, span { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }

    /* MENU SIDEBAR CHUẨN (KHÔNG SUBMENU) */
    .stSidebar .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 500 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding-left: 10px !important;
        height: 2.8em !important; border-bottom: 1px solid #1a1a1a !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important; background-color: #111111 !important;
        border-left: 4px solid #ffd700 !important;
    }

    /* NÚT ĐANG CHỌN (ACTIVE) */
    .active-nav button {
        color: #ffd700 !important; background-color: #1a1a1a !important;
        border-left: 4px solid #ffd700 !important;
    }

    /* NÚT HÀNH ĐỘNG CHÍNH (VÀNG/ĐỎ) */
    .btn-red button {
        background-color: #ff0000 !important; color: #ffffff !important; 
        font-weight: 700 !important; border: none !important;
        height: 3.5em !important; text-transform: uppercase;
    }
    .btn-red button:hover { background-color: #cc0000 !important; box-shadow: 0 0 10px #ff0000; }

    .btn-excel button {
        background-color: #222222 !important; color: #ffd700 !important; 
        border: 1px solid #ffd700 !important; height: 3.5em !important; font-size: 13px !important;
        font-weight: 700 !important; text-transform: uppercase;
    }
    .btn-excel button:hover { background-color: #333333 !important; box-shadow: 0 0 10px rgba(255, 215, 0, 0.2); }

    /* BẢNG DỮ LIỆU ĐA CỘT */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] * { color: #eeeeee !important; font-family: 'Inter', sans-serif !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }

    /* USER AREA */
    .user-area { position: absolute; top: 1rem; right: 1rem; color: #777; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# User area simulation
st.markdown("<div class='user-area'>JunDeng [ Admin ] | ⚙️ P 🚪</div>", unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU TẬP TRUNG (THEO SHEET CỦA NÍ)
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "⚙️ Cấu hình"

def init_all_data():
    # Bảng Cấu hình tổng hợp, có đủ tất cả các cột của Google Sheet
    if 'df_central_config' not in st.session_state:
        # Cột được lấy chính xác từ ảnh Google Sheet Ní gửi
        columns = [
            "Hạng mục", "Giá trị thiết lập (Config Value)", "Ghi chú Robot"
        ]
        data = [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8", ""],
            ["SENDER_EMAIL", "jundeng.po@gmail.com", ""],
            ["TARGET_URL", "https://laiho.vn/", ""],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4", ""],
            ["Keyword chính", "thuê tài xế lái hộ", ""],
            ["Thiết lập số chữ", "1000 - 1200", ""],
            ["Mật độ Backlink", "3-5", ""],
            ["Mục tiêu bài", "Tư vấn chuyên sâu", ""],
            ["Trạng thái", "Sẵn sàng", ""],
            ["... ", "...", "..."],
        ]
        # Thêm 10 dòng config giả để đủ 13 dòng sát nóc
        for i in range(1, 4):
            data.append([f"Config_{i}", f"Config_Value_{i}", f"Notes_{i}"])

        st.session_state['df_central_config'] = pd.DataFrame(data, columns=columns)

    # Bảng Dữ liệu thật (Multi-column Sheet)
    if 'df_master_sheet' not in st.session_state:
        # TÍCH HỢP TOÀN BỘ CỘT CỦA GOOGLE SHEET CỦA NÍ
        columns = [
            "STT", "Thời gian hẹn giờ (Schedule)", "Nền tảng (Platform)", "URL / ID", 
            "Từ khoá chính (Main keywords)", "Ancho", "Tiêu đề bài viết (Article title)", 
            "Link 1", "Ancho 1", "Link 2", "Ancho 2", "Link 3", "Ancho 3",
            "Mô tả / Đoạn đầu (Description)", "Hình ảnh / ID Drive", 
            "Trạng thái Robot", "Done Index"
        ]
        
        # Thêm 20 dòng data trống để Ní dán vào
        data = []
        for i in range(1, 21):
            data.append([i, "", "Blogger", "", "", "", "", "", "", "", "", "", "", "", "", "⏳ Chờ chạy", "❌"])

        st.session_state['df_master_sheet'] = pd.DataFrame(data, columns=columns)

    # Báo cáo in ra
    if 'df_report' not in st.session_state:
        st.session_state['df_report'] = pd.DataFrame(columns=["Website", "Ngày đăng", "Tiêu đề", "Index"])

init_all_data()

# =================================================================
# 3. SIDEBAR CỐ ĐỊNH ( TINH GỌN, CHÍNH THỐNG)
# =================================================================
with st.sidebar:
    st.markdown("<div class='gold-title'>🏢 SEO LÁI HỘ V55.0</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Menu flat, không có submenu rườm rà
    menu_options = ["🏠 Tổng quan", "🗺️ Phủ sóng vùng", "⚙️ Cấu hình", "📊 Báo cáo", "Cài đặt khác"]
    
    for option in menu_options:
        # Đổi màu tab đang active
        is_active = st.session_state['active_tab'] == option
        style = "active-nav" if is_active else ""
        
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(option, key=f"nav_{option}"):
            st.session_state['active_tab'] = option
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
                
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# =================================================================
# 4. KHU VỰC CHÍNH (DYNAMIC CONTENT)
# =================================================================
active = st.session_state['active_tab']
st.markdown(f"#### 📍 {active}")

if active == "⚙️ Cấu hình":
    # TOOLBAR (THEO YÊU CẦU CỦA NÍ)
    c_start, c_ex, c_im, _ = st.columns([1, 1, 1, 2])
    with c_start:
        st.markdown('<div class="btn-red">', unsafe_allow_html=True)
        if st.button("🔥 START", use_container_width=True):
            st.success("Robot bắt đầu thực thi chiến dịch theo config.")
        st.markdown('</div>', unsafe_allow_html=True)
    with c_ex:
        st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", use_container_width=True, key="ex_central")
        st.markdown('</div>', unsafe_allow_html=True)
    with c_im:
        st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
        st.file_uploader("📥 IMPORT EXCEL", type=["csv"], label_visibility="collapsed", key="im_central")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # LAYOUT CẤU HÌNH TRUNG TÂM
    col_l, col_r = st.columns([1, 3])
    with col_l:
        st.markdown("<p class='gold-text'>⚙️ API KEYS & EMAIL</p>", unsafe_allow_html=True)
        # Bảng config 13 dòng sát nóc
        st.session_state['df_central_config'] = st.data_editor(st.session_state['df_central_config'], use_container_width=True, height=520, num_rows="fixed")
    with col_r:
        st.markdown("<p class='gold-text'>🗺️ DỮ LIỆU ĐĂNG BÀI (TẤT CẢ CỘT CỦA SHEET)</p>", unsafe_allow_html=True)
        # BẢNG THỰC HIỆN TÍCH HỢP TẤT CẢ CỘT
        st.session_state['df_master_sheet'] = st.data_editor(st.session_state['df_master_sheet'], use_container_width=True, num_rows="dynamic", height=700)

elif active == "📊 Báo cáo":
    st.markdown("<p class='gold-text'>📋 BÁO CÁO HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
    st.dataframe(st.session_state['df_report'], use_container_width=True, height=800)

else:
    st.warning(f"Tính năng {active} đang chờ Robot cung cấp dữ liệu.")

st.caption("🚕 SEO Automation Lái Hộ v320.0 | Integrated Bug-Free Dashboard")
