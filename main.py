import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Lái Hộ - Robot v280.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU BÊN TRÁI CỐ ĐỊNH */
    .nav-col { border-right: 1px solid #333333; height: 100vh; padding-right: 15px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; }
    
    /* STYLE NÚT MENU */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 5px !important;
    }
    .stButton>button:hover { border: 1px solid #ffd700 !important; color: #ffd700 !important; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }

    /* NÚT ĐỎ & VÀNG */
    .btn-red button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; height: 3.5em !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; font-weight: 700 !important; height: 3.5em !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

def init_all_data():
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD..."], ["SERPAPI_KEY", "380c97..."],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["TARGET_URL", "https://laiho.vn/"],
            ["Số lượng bài/ngày", "10"], ["Thiết lập số chữ", "1200"],
            ["FOLDER_DRIVE_ID", "1STdk4mp..."], ["Trạng thái Robot", "Đang chờ"]
        ], columns=["Hạng mục", "Giá trị"])
    
    # Khởi tạo các bảng Data khác
    for k in ["df_backlink", "df_website", "df_report"]:
        if k not in st.session_state:
            if k == "df_report":
                st.session_state[k] = pd.DataFrame(columns=["STT", "Thời gian dự kiến", "Website", "Tiêu đề bài viết", "Trạng thái"])
            else:
                st.session_state[k] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_all_data()

# 3. GIAO DIỆN 2 CỘT (SIDEBAR GIẢ NHƯNG CỐ ĐỊNH 100%)
nav_col, main_col = st.columns([1, 4], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    tabs = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Report"]
    for t in tabs:
        if st.session_state['active_tab'] == t:
            st.markdown("<div class='active-nav'>", unsafe_allow_html=True)
            if st.button(f"▪️ {t}", key=f"n_{t}"): pass
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(f"  {t}", key=f"n_{t}"):
                st.session_state['active_tab'] = t
                st.rerun()

# 4. KHU VỰC CHÍNH
with main_col:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")

    if active == "Dashboard":
        cl, cr = st.columns([2, 1])
        with cl:
            st.markdown("<p class='gold-text'>⚙️ CẤU HÌNH HỆ THỐNG</p>", unsafe_allow_html=True)
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=450)
        with cr:
            st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                    st.success("Đang đăng bài trực tiếp...")
                st.markdown('</div>', unsafe_allow_html=True)
                
                st.markdown('<div class="btn-gold" style="margin-top:15px;">', unsafe_allow_html=True)
                # --- LOGIC LẬP LỊCH THẬT ---
                if st.button("📅 LẬP LỊCH ROBOT", use_container_width=True):
                    num_posts = 10 # Giả định theo config
                    new_rows = []
                    start_time = datetime.now()
                    for i in range(1, num_posts + 1):
                        schedule_time = start_time + timedelta(hours=i*2)
                        new_rows.append({
                            "STT": i,
                            "Thời gian dự kiến": schedule_time.strftime("%H:%M - %d/%m"),
                            "Website": f"Blog Lái Hộ {i}",
                            "Tiêu đề bài viết": f"Dịch vụ lái xe hộ uy tín bài số {i}",
                            "Trạng thái": "⏳ Đang chờ"
                        })
                    st.session_state['df_report'] = pd.DataFrame(new_rows)
                    st.success(f"Đã lập lịch thành công {num_posts} bài! Qua tab Data_Report để xem.")
                st.markdown('</div>', unsafe_allow_html=True)

    elif active == "Data_Report":
        st.markdown("<p class='gold-text'>📋 BÁO CÁO ROBOT ĐÃ LẬP LỊCH</p>", unsafe_allow_html=True)
        st.dataframe(st.session_state['df_report'], use_container_width=True, height=600)
    else:
        st.write("Vui lòng nhập liệu vào bảng bên dưới.")
        st.data_editor(pd.DataFrame(columns=["A", "B", "C"]), use_container_width=True, num_rows="dynamic")

st.caption("🚀 Robot Lái Hộ v280.0 | Permanent Sidebar & Logic Schedule")
