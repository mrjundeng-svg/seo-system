import streamlit as st
import pandas as pd
import time

# =================================================================
# 1. CẤU HÌNH TRANG - KHÓA SIDEBAR (TRẠNG THÁI MỞ)
# =================================================================
st.set_page_config(
    page_title="Hệ thống SEO Lái Hộ v230.0", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* NỀN ĐEN CHUẨN */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* --- CHIÊU THỨC: KHÓA CHẾT SIDEBAR --- */
    /* 1. Ẩn nút 3 gạch (Mở sidebar) */
    [data-testid="collapsedControl"] { display: none !important; }
    
    /* 2. Ẩn nút 'X' (Đóng sidebar) */
    button[kind="headerNoContext"] { display: none !important; }
    
    /* 3. Ép Sidebar luôn rộng và không thể co giãn */
    [data-testid="stSidebar"] { 
        min-width: 300px !important;
        max-width: 300px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
    }

    /* --- GIAO DIỆN CHỮ & MÀU SẮC --- */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 20px; margin-bottom: 20px; }
    .stMarkdown, label, p, span { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }

    /* MENU ĐA CẤP (EXPANDER) */
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
        padding-left: 15px !important;
        font-size: 14px !important;
        height: 2.5em !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #111111 !important;
        border-left: 3px solid #ffd700 !important;
    }

    /* NÚT CHẠY CHIẾN DỊCH (MÀU ĐỎ) */
    .btn-red button {
        background-color: #ff0000 !important; 
        color: #ffffff !important; 
        font-weight: 700 !important; 
        border-radius: 8px !important;
        height: 3.5em !important;
        text-transform: uppercase;
        border: none !important;
    }
    .btn-red button:hover { background-color: #cc0000 !important; box-shadow: 0 0 15px #ff0000; }
    
    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU & MENU
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "🚀 Dashboard"

def init_data():
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200"],
            ["Mật độ Backlink", "3 - 5"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
            ["Keyword chính", "thuê tài xế lái hộ"],
            ["Website đối thủ", "lmd.vn, butl.vn"],
            ["Mục tiêu bài", "Tư vấn dịch vụ"],
            ["Trạng thái Robot", "Sẵn sàng"]
        ], columns=["Hạng mục", "Giá trị"])

    # Khởi tạo các bảng khác nếu chưa có
    for t in ["df_backlink", "df_website", "df_image", "df_spin", "df_local", "df_report"]:
        if t not in st.session_state:
            st.session_state[t] = pd.DataFrame(columns=["Cột A", "Cột B", "Cột C"])

init_data()

# =================================================================
# 3. SIDEBAR CỐ ĐỊNH (FIXED SIDEBAR)
# =================================================================
with st.sidebar:
    st.markdown("<div class='gold-title'>🏢 SEO LÁI HỘ CONTROL</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.button("🚀 Dashboard & Robot"): 
        st.session_state['active_tab'] = "🚀 Dashboard"
        st.rerun()

    with st.expander("📥 DỮ LIỆU ĐẦU VÀO", expanded=True):
        if st.button("▪️ Data_Backlink"): st.session_state['active_tab'] = "Data_Backlink"; st.rerun()
        if st.button("▪️ Data_Website"): st.session_state['active_tab'] = "Data_Website"; st.rerun()
        if st.button("▪️ Data_Image"): st.session_state['active_tab'] = "Data_Image"; st.rerun()
        if st.button("▪️ Data_Spin"): st.session_state['active_tab'] = "Data_Spin"; st.rerun()
        if st.button("▪️ Data_Local"): st.session_state['active_tab'] = "Data_Local"; st.rerun()

    with st.expander("📊 BÁO CÁO KẾT QUẢ"):
        if st.button("▪️ Data_Report"): st.session_state['active_tab'] = "Data_Report"; st.rerun()

    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Đăng xuất", use_container_width=True): st.stop()

# =================================================================
# 4. KHU VỰC CHÍNH (DYNAMIC CONTENT)
# =================================================================
active = st.session_state['active_tab']
st.markdown(f"#### 📍 {active}")

if active == "🚀 Dashboard":
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE CSV", type=["csv"], label_visibility="collapsed")
    with c3: 
        if st.button("🔄 ĐỒNG BỘ"): st.toast("Đã đồng bộ!")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH HỆ THỐNG (13 DÒNG)</p>", unsafe_allow_html=True)
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
    
    with col_r:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành v55.0 Stable:")
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                p = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.1)
                    p.progress(i * 10)
                st.success("✅ ĐÃ XONG 10 BÀI!")
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

elif "Data_" in active and active != "Data_Report":
    key = f"df_{active.split('_')[1].lower()}"
    st.session_state[key] = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", height=750)

elif active == "Data_Report":
    st.markdown("<p style='color:#ffd700; font-weight:700;'>📋 NHẬT KÝ HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
    st.dataframe(st.session_state['df_report'], use_container_width=True, height=800)

st.caption("🚀 SEO Automation Lái Hộ v230.0 | Permanent Sidebar Edition")
