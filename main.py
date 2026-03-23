import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS "SIÊU ĐEN - SIÊU VÀNG"
st.set_page_config(page_title="Hệ thống Điều hành SEO v170.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* NỀN ĐEN SÂU SANG TRỌNG */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR ĐEN MỜ VỚI VIỀN VÀNG MẢNH */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important; 
    }
    
    /* TEXT VÀNG GOLD */
    h1, h2, h3, h4, p, span, label { 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
    }
    .gold-text { color: #ffd700 !important; font-weight: 700; }

    /* STYLE CHO MENU ĐA CẤP (SUB-MENU) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #1a1a1a !important;
    }
    div[data-testid="stExpander"] p { font-weight: 600 !important; color: #ffd700 !important; }

    /* NÚT BẤM TRONG SIDEBAR (DẠNG LIST) */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #cccccc !important;
        border: none !important;
        text-align: left !important;
        font-size: 14px !important;
        height: 2.5em !important;
        padding-left: 20px !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #111111 !important;
    }

    /* BẢNG DỮ LIỆU & EDITOR */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="gridcell"] { color: #ffffff !important; }

    /* NÚT HÀNH ĐỘNG CHÍNH (VÀNG/ĐỎ) */
    .btn-run button {
        background-color: #ffd700 !important; color: #000000 !important; font-weight: 700 !important;
    }
    .btn-stop button {
        background-color: #ff4b4b !important; color: #ffffff !important; font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. QUẢN LÝ TRẠNG THÁI MENU
if 'active_tab' not in st.session_state: 
    st.session_state['active_tab'] = "Bảng điều khiển"

# ĐỊNH NGHĨA CẤU TRÚC SUB-MENU (PROJECT-BASED)
STRUCTURE = {
    "🏠 Tổng quan": ["Bảng điều khiển", "Thống kê Index"],
    "🚕 Dịch vụ Lái Hộ": ["Phủ sóng vùng", "Tính cước Lái Hộ", "Quản lý Tài xế"],
    "🏠 Giúp Việc Nhanh": ["Đối tác B2B", "Quản lý Nhân sự"],
    "⚙️ Hệ thống SEO": ["Data Config", "Hệ thống Website", "Backlink Master"],
    "🖼️ Kho dữ liệu": ["Kho hình ảnh", "Từ điển Spin"],
    "📊 Báo cáo": ["Báo cáo cuối", "Lịch sử Robot"]
}

# 3. SIDEBAR ĐA CẤP (PHỤC HỒI SUB-MENU)
with st.sidebar:
    st.markdown("<h2 class='gold-text'>🏢 ĐIỀU HÀNH</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    for main_menu, sub_menus in STRUCTURE.items():
        if sub_menus:
            with st.expander(main_menu, expanded=(main_menu == "⚙️ Hệ thống SEO")):
                for sub in sub_menus:
                    if st.button(f"▪️ {sub}", key=f"menu_{sub}", use_container_width=True):
                        st.session_state['active_tab'] = sub
                        st.rerun()
        else:
            if st.button(main_menu, key=f"menu_{main_menu}", use_container_width=True):
                st.session_state['active_tab'] = main_menu
                st.rerun()
    
    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Đăng xuất"): st.stop()

# 4. KHU VỰC CHÍNH (DYNAMIC CONTENT)
tab = st.session_state['active_tab']
st.markdown(f"#### 📍 {tab}")

# --- LOGIC HIỂN THỊ THEO TAB ---
if tab in ["Bảng điều khiển", "Data Config"]:
    # THANH CÔNG CỤ
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data="...", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    with c3: st.button("🔄 ĐỒNG BỘ")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p class='gold-text'>⚙️ THÔNG SỐ CẤU HÌNH (13 DÒNG)</p>", unsafe_allow_html=True)
        # Nạp dữ liệu 13 dòng từ summary
        df_cfg = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Số lượng bài/ngày", "10"],
            ["Thiết lập số chữ", "1000 - 1200"],
            ["Số backlink/bài", "3 - 5"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ], columns=["Hạng mục", "Giá trị"])
        st.data_editor(df_cfg, use_container_width=True, height=520)
    
    with col_r:
        st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown('<div class="btn-run">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                st.info("Robot v55.0 đang thực thi...")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('<div class="btn-stop" style="margin-top:10px;">', unsafe_allow_html=True)
            st.button("🛑 DỪNG KHẨN CẤP")
            st.markdown('</div>', unsafe_allow_html=True)

elif tab == "Phủ sóng vùng":
    st.write("Dữ liệu các tuyến đường và khu vực phục vụ của dự án Lái Hộ.")
    st.data_editor(pd.DataFrame([["Quận 1", "Bật"], ["Quận 7", "Bật"]], columns=["Khu vực", "Trạng thái"]), use_container_width=True)

else:
    st.info(f"Đang kết nối dữ liệu cho tính năng: {tab}")

st.caption("🚕 Hệ thống quản trị tập trung | Ver 170.0 Stable")
