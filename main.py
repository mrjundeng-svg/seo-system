import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG - ƯU TIÊN HIỆN SIDEBAR
st.set_page_config(
    page_title="SEO Lái Hộ - Quản trị tập trung", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- CSS DARK & GOLD: TỐI GIẢN, CHỮ RÕ, NỀN ĐEN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR CHUYÊN NGHIỆP */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
        min-width: 280px !important;
    }
    
    /* ÉP CHỮ SIDEBAR MÀU TRẮNG VÀ VÀNG */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 20px; text-shadow: 0 0 5px rgba(255, 215, 0, 0.2); }

    /* SUB-MENU (EXPANDER) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #1a1a1a !important;
    }
    div[data-testid="stExpander"] p { color: #ffd700 !important; font-weight: 600 !important; }

    /* NÚT TRONG MENU CON */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #cccccc !important;
        border: none !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-size: 14px !important;
        transition: 0.2s;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #111111 !important;
    }

    /* BẢNG DATA EDITOR */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }

    /* NÚT CHẠY CHIẾN DỊCH */
    .btn-run button {
        background: #ffd700 !important; color: #000000 !important; 
        font-weight: 700 !important; border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO TẤT CẢ CÁC NGĂN CHỨA DỮ LIỆU
if 'current_tab' not in st.session_state: st.session_state['current_tab'] = "⚙️ Cấu hình hệ thống"

def init_all_sheets():
    # 13 Dòng Cấu hình
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD..."], ["SERPAPI_KEY", "380c97..."], 
            ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["SENDER_PASSWORD", "vddy misk..."],
            ["TARGET_URL", "https://laiho.vn/"], ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000-1200"], ["Mật độ Link", "3-5"],
            ["FOLDER_DRIVE_ID", "1STdk4mp..."], ["Keyword chính", "lái hộ..."]
        ], columns=["Hạng mục", "Giá trị"])
    
    # Các bảng nhập liệu (Ní nhập)
    if 'df_backlink' not in st.session_state:
        st.session_state['df_backlink'] = pd.DataFrame(columns=["Từ khóa", "Link đích", "Đã dùng"])
    if 'df_website' not in st.session_state:
        st.session_state['df_website'] = pd.DataFrame(columns=["Tên Blog", "Nền tảng", "URL/ID", "Trạng thái"])
    if 'df_image' not in st.session_state:
        st.session_state['df_image'] = pd.DataFrame(columns=["URL Ảnh", "Số lần dùng"])
    if 'df_spin' not in st.session_state:
        st.session_state['df_spin'] = pd.DataFrame(columns=["Từ gốc", "Từ đồng nghĩa"])
    if 'df_local' not in st.session_state:
        st.session_state['df_local'] = pd.DataFrame(columns=["Tỉnh/Thành", "Quận/Huyện", "Tuyến đường"])
    
    # Bảng kết quả (Hệ thống in ra)
    if 'df_report' not in st.session_state:
        st.session_state['df_report'] = pd.DataFrame(columns=["Website", "Ngày đăng", "Tiêu đề", "Link bài", "Trạng thái Index"])

init_all_sheets()

# 3. SIDEBAR: CHIA NHÓM NHẬP LIỆU & BÁO CÁO
with st.sidebar:
    st.markdown("<div class='gold-title'>🚕 LÁI HỘ CONTROL</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("🚀 Dashboard & Chạy bài"): st.session_state['current_tab'] = "🚀 Dashboard"

    with st.expander("📥 DỮ LIỆU ĐẦU VÀO (Ní nhập)"):
        if st.button("🔗 Data_Backlink"): st.session_state['current_tab'] = "Data_Backlink"
        if st.button("🌐 Data_Website"): st.session_state['current_tab'] = "Data_Website"
        if st.button("🖼️ Data_Image"): st.session_state['current_tab'] = "Data_Image"
        if st.button("✍️ Data_Spin"): st.session_state['current_tab'] = "Data_Spin"
        if st.button("📍 Data_Local"): st.session_state['current_tab'] = "Data_Local"

    with st.expander("📊 KẾT QUẢ ĐẦU RA (Hệ thống)"):
        if st.button("📋 Data_Report"): st.session_state['current_tab'] = "Data_Report"

    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Đăng xuất"): st.stop()

# 4. KHU VỰC CHÍNH (CONTENT)
tab = st.session_state['current_tab']
st.markdown(f"#### 📍 {tab}")

# --- LOGIC XỬ LÝ TỪNG TAB ---
if tab == "🚀 Dashboard":
    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH HỆ THỐNG</p>", unsafe_allow_html=True)
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=450)
    with col_r:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="btn-run">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                st.success("Robot v55.0 đang thực thi theo Quota...")
            st.markdown('</div>', unsafe_allow_html=True)

elif tab == "Data_Backlink":
    st.session_state['df_backlink'] = st.data_editor(st.session_state['df_backlink'], use_container_width=True, num_rows="dynamic", height=700)
elif tab == "Data_Website":
    st.session_state['df_website'] = st.data_editor(st.session_state['df_website'], use_container_width=True, num_rows="dynamic", height=700)
elif tab == "Data_Image":
    st.session_state['df_image'] = st.data_editor(st.session_state['df_image'], use_container_width=True, num_rows="dynamic", height=700)
elif tab == "Data_Spin":
    st.session_state['df_spin'] = st.data_editor(st.session_state['df_spin'], use_container_width=True, num_rows="dynamic", height=700)
elif tab == "Data_Local":
    st.session_state['df_local'] = st.data_editor(st.session_state['df_local'], use_container_width=True, num_rows="dynamic", height=700)

elif tab == "Data_Report":
    st.markdown("<p style='color:#ffd700; font-weight:700;'>📋 NHẬT KÝ HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
    # Tab này dùng .dataframe thay vì .data_editor để chỉ xem (Hệ thống in ra)
    st.dataframe(st.session_state['df_report'], use_container_width=True, height=800)

st.caption("🚕 SEO Lái Hộ v210.0 | Hoàn thiện luồng dữ liệu")
