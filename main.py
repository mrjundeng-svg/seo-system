import streamlit as st
import pandas as pd
import time
import datetime

# =================================================================
# 1. CẤU HÌNH TRANG & GIAO DIỆN (UI/UX)
# =================================================================
st.set_page_config(
    page_title="SEO Lái Hộ - v220.0 Pro", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* TÔNG NỀN ĐEN CHUẨN APP XẾ HỘ */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR ĐEN - VIỀN VÀNG SANG TRỌNG */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
        min-width: 300px !important;
    }
    
    /* ÉP CHỮ HIỂN THỊ MÀU VÀNG GOLD & TRẮNG */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    .stMarkdown, label, p, span { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }

    /* SUB-MENU (EXPANDER) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #1a1a1a !important;
    }
    div[data-testid="stExpander"] p { color: #ffd700 !important; font-weight: 600 !important; }

    /* NÚT BẤM TRONG SIDEBAR */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #aaaaaa !important;
        border: none !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-size: 14px !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #111111 !important;
    }

    /* BẢNG DỮ LIỆU ĐẦU VÀO & ĐẦU RA */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }

    /* NÚT HÀNH ĐỘNG CHÍNH (ĐỎ QUYỀN LỰC) */
    .btn-red button {
        background-color: #ff0000 !important; 
        color: #ffffff !important; 
        font-weight: 700 !important; 
        border: 2px solid #000000 !important;
        border-radius: 5px !important;
        height: 3.5em !important;
        text-transform: uppercase;
    }
    .btn-red button:hover { background-color: #cc0000 !important; box-shadow: 0 0 10px #ff0000; }

    /* NÚT VÀNG CHO CÁC TÍNH NĂNG KHÁC */
    .btn-gold button {
        background-color: #ffd700 !important;
        color: #000000 !important;
        font-weight: 700 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU (SESSION STATE)
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "🚀 Dashboard"

def init_data():
    # 1. Cấu hình hệ thống (13 dòng chuẩn)
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Danh sách Keyword", "thuê tài xế lái hộ, lái xe hộ tphcm..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu bài viết", "Bài viết tư vấn, chốt sale dịch vụ"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200 chữ"],
            ["Mật độ Backlink", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ], columns=["Hạng mục", "Giá trị"])

    # 2. Dữ liệu đầu vào (Ní nhập)
    tables = ["df_backlink", "df_website", "df_image", "df_spin", "df_local"]
    for t in tables:
        if t not in st.session_state:
            st.session_state[t] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

    # 3. Dữ liệu đầu ra (Hệ thống in)
    if 'df_report' not in st.session_state:
        st.session_state['df_report'] = pd.DataFrame(columns=["Website", "Ngày đăng", "Tiêu đề", "Link bài", "Trạng thái Index"])

init_data()

# =================================================================
# 3. SIDEBAR: MENU ĐA CẤP (SUB-MENU)
# =================================================================
with st.sidebar:
    st.markdown("<div class='gold-title'>🏢 ĐIỀU HÀNH LÁI HỘ</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Dashboard chính
    if st.button("🚀 Dashboard & Robot"): st.session_state['active_tab'] = "🚀 Dashboard"

    # Nhóm nhập liệu
    with st.expander("📥 DỮ LIỆU ĐẦU VÀO (Input)"):
        if st.button("🔗 Data_Backlink"): st.session_state['active_tab'] = "Data_Backlink"
        if st.button("🌐 Data_Website"): st.session_state['active_tab'] = "Data_Website"
        if st.button("🖼️ Data_Image"): st.session_state['active_tab'] = "Data_Image"
        if st.button("✍️ Data_Spin"): st.session_state['active_tab'] = "Data_Spin"
        if st.button("📍 Data_Local"): st.session_state['active_tab'] = "Data_Local"

    # Nhóm báo cáo
    with st.expander("📊 KẾT QUẢ ĐẦU RA (Output)"):
        if st.button("📋 Data_Report"): st.session_state['active_tab'] = "Data_Report"

    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# =================================================================
# 4. KHU VỰC CHÍNH (CONTENT)
# =================================================================
active = st.session_state['active_tab']
st.markdown(f"### 📍 {active}")

if active == "🚀 Dashboard":
    # Cấu hình Toolbar
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE CSV", type=["csv"], label_visibility="collapsed")
    with c3: 
        if st.button("🔄 ĐỒNG BỘ"): st.toast("Đã đồng bộ dữ liệu thành công!")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH HỆ THỐNG (13 DÒNG)</p>", unsafe_allow_html=True)
        # ÉP HIỂN THỊ ĐỦ 13 DÒNG
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
    
    with col_r:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN CHIẾN DỊCH</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành Robot v55.0 Stable:")
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                prog = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.2)
                    prog.progress(i * 10)
                st.success("✅ ĐÃ XONG 10 BÀI VIẾT!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

elif "Data_" in active and active != "Data_Report":
    # Giao diện cho các Tab nhập liệu
    st.markdown(f"##### Nhập dữ liệu cho: {active}")
    key = f"df_{active.split('_')[1].lower()}"
    st.session_state[key] = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", height=750)

elif active == "Data_Report":
    # Giao diện cho báo cáo (Chỉ xem)
    st.markdown("<p style='color:#ffd700; font-weight:700;'>📋 BÁO CÁO KẾT QUẢ ĐĂNG BÀI</p>", unsafe_allow_html=True)
    st.dataframe(st.session_state['df_report'], use_container_width=True, height=800)

st.caption("🚀 SEO Automation Lái Hộ v220.0 | Enterprise Edition")
