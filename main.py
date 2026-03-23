import streamlit as st
import pandas as pd
import time
from datetime import datetime

# =================================================================
# 1. CẤU HÌNH TRANG & CSS (UI/UX CHUẨN XẾ HỘ)
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v330.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* TÔNG NỀN ĐEN SÂU */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* ẨN SIDEBAR GỐC ĐỂ DÙNG MENU TỰ CHẾ (CHỐNG ẨN HIỆN) */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* CHỮ TRẮNG & VÀNG GOLD */
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; }
    
    /* MENU BÊN TRÁI CỐ ĐỊNH (100% HIỆN DIỆN) */
    .nav-col {
        border-right: 1px solid #333333;
        height: 100vh;
        padding: 15px;
        position: fixed;
    }

    /* NÚT MENU SideBar */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 4px !important;
    }
    .stButton>button:hover {
        border: 1px solid #ffd700 !important; color: #ffd700 !important;
        background-color: #111111 !important;
    }
    
    /* NÚT ĐANG CHỌN */
    .active-nav button {
        background-color: #1a1a1a !important;
        border-left: 5px solid #ffd700 !important;
        color: #ffd700 !important;
    }

    /* NÚT START (MÀU ĐỎ) & EXCEL (MÀU TỐI) */
    .btn-start button {
        background-color: #ff0000 !important; color: white !important;
        border: none !important; font-weight: 700 !important; height: 3.5em !important;
        text-transform: uppercase; border-radius: 8px !important;
    }
    .btn-excel button {
        background-color: #222222 !important; color: #ffd700 !important;
        border: 1px solid #ffd700 !important; height: 2.8em !important;
        font-size: 13px !important; font-weight: 700 !important;
    }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    [data-testid="stDataFrame"] * { color: #eeeeee !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU THẬT (MASTER DATA)
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

def init_data():
    # NẠP 13 DÒNG CẤU HÌNH THẬT TỪ GOOGLE SHEET
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Từ khóa (Keywords)", "thuê tài xế lái hộ, đưa người say..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu nội dung", "Bài viết tư vấn, chốt sale dịch vụ"],
            ["Số lượng bài/ngày", "10"],
            ["Thiết lập số chữ", "1000 - 1200"],
            ["Mật độ Backlink", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ], columns=["Hạng mục cấu hình", "Giá trị thực tế"])

    # Khởi tạo các bảng Data_...
    sheets = ["Backlink", "Website", "Image", "Spin", "Local", "Report"]
    for s in sheets:
        key = f"df_{s.lower()}"
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3", "Cột 4"])

init_data()

# =================================================================
# 3. SIDEBAR CỐ ĐỊNH (2 CỘT: 1 NAV | 4 CONTENT)
# =================================================================
col_nav, col_main = st.columns([1, 4], gap="large")

with col_nav:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Menu danh sách phẳng (Không rườm rà)
    menu_list = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    
    for item in menu_list:
        is_active = st.session_state['active_tab'] == item
        style = "active-nav" if is_active else ""
        
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {item}", key=f"btn_{item}"):
            st.session_state['active_tab'] = item
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
                
    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# =================================================================
# 4. KHU VỰC CHÍNH (DYNAMIC CONTENT)
# =================================================================
with col_main:
    active = st.session_state['active_tab']
    st.markdown(f"#### 📍 {active}")

    if active == "Dashboard":
        # TOOLBAR Dashboard
        c_start, c_ex, c_im, _ = st.columns([1.2, 1, 1, 1.8])
        with c_start:
            st.markdown('<div class="btn-start">', unsafe_allow_html=True)
            if st.button("🔥 START (CHẠY NGAY)", use_container_width=True):
                st.success("Robot v55.0 đang khởi động...")
            st.markdown('</div>', unsafe_allow_html=True)
        with c_ex:
            st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
            st.button("📤 XUẤT EXCEL", key="ex_dash", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with c_im:
            st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
            st.button("📥 NHẬP EXCEL", key="im_dash", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        cl, cr = st.columns([2, 1.2])
        with cl:
            st.markdown("<p class='gold-text'>⚙️ THÔNG SỐ CẤU HÌNH (13 DÒNG CHUẨN)</p>", unsafe_allow_html=True)
            # HIỂN THỊ ĐỦ 13 DÒNG SÁT NÓC
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
        with cr:
            st.markdown("<p class='gold-text'>🚀 TRẠNG THÁI ROBOT</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Phiên bản: v55.0 Stable")
                st.write(f"Thời gian: {datetime.now().strftime('%H:%M:%S')}")
                st.info("Robot đang ở chế độ chờ (Idle).")
                st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

    else:
        # THANH CÔNG CỤ EXCEL CHO CÁC TRANG DATA
        xc1, xc2, _ = st.columns([1, 1, 3])
        with xc1:
            st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
            st.button("📤 XUẤT EXCEL", key=f"ex_{active}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        with xc2:
            st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
            st.button("📥 NHẬP EXCEL", key=f"im_{active}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # LẤY KEY DATA AN TOÀN
        key = f"df_{active.lower().replace('data_', '')}"
        st.markdown(f"<p class='gold-text'>📥 DỮ LIỆU: {active.upper()}</p>", unsafe_allow_html=True)
        
        if active == "Data_Report":
            st.dataframe(st.session_state[key], use_container_width=True, height=750)
        else:
            st.session_state[key] = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", height=750)

st.caption("🚀 SEO Automation Lái Hộ v330.0 | Enterprise Web Control")
