import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS DARK-GOLD SIÊU CẤP
st.set_page_config(page_title="Hệ thống SEO Lái Hộ", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Roboto+Mono&display=swap');
    
    /* NỀN ĐEN SÂU TOÀN HỆ THỐNG */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR ĐEN MỜ (GIỐNG APP XẾ HỘ) */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #222222 !important; 
    }
    
    /* CHỮ TRẮNG & VÀNG GOLD */
    h1, h2, h3, h4, p, span, label { 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
    }
    .gold-glow { color: #ffd700 !important; font-weight: 700; text-shadow: 0 0 10px rgba(255, 215, 0, 0.3); }

    /* STYLE CHO SUB-MENU (EXPANDER) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #1a1a1a !important;
    }
    div[data-testid="stExpander"] p { font-weight: 600 !important; color: #ffd700 !important; }

    /* BẢNG DỮ LIỆU (DARK MODE) */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="gridcell"] { color: #eeeeee !important; }

    /* NÚT BẤM VÀNG GOLD CHỦ ĐẠO */
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 700; height: 3em;
        background-color: #ffd700 !important; 
        color: #000000 !important;
        border: none !important;
        text-transform: uppercase;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #ffcc00 !important; 
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        transform: translateY(-2px);
    }

    /* NÚT PHỤ (MÀU TỐI VIỀN VÀNG) */
    .stDownloadButton>button {
        background-color: #000000 !important;
        color: #ffd700 !important;
        border: 1px solid #ffd700 !important;
        border-radius: 8px;
    }
    
    /* HỘP NHẬT KÝ */
    .log-box { 
        background-color: #0a0a0a; border-radius: 10px; padding: 15px; 
        border: 1px solid #222; color: #ffd700; font-family: 'Roboto Mono', monospace; font-size: 13px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU & QUẢN LÝ MENU
if 'active_tab' not in st.session_state: 
    st.session_state['active_tab'] = "Bảng điều khiển"

# Định nghĩa cấu trúc Menu (Main -> Sub)
STRUCTURE = {
    "🏠 Tổng quan": ["Bảng điều khiển", "Thống kê nhanh"],
    "🗺️ Phủ sóng vùng": ["Dịch vụ lái hộ TPHCM", "Khu vực Hà Nội", "Liên tỉnh"],
    "⚙️ Cấu hình": ["Data Config", "API Keys"],
    "🖼️ Hình ảnh": ["Kho hình ảnh (Data Image)"],
    "💬 Nội dung": ["Từ điển Spin", "Mẫu bài viết"],
    "👥 SEO Offpage": ["Backlink Master"],
    "📊 Báo cáo": ["SEO Report", "Lịch sử đăng bài"]
}

def init_data():
    if 'df_config' not in st.session_state:
        data = [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Từ khóa chính", "thuê tài xế lái hộ, đưa người say..."],
            ["Đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu", "Bài viết tư vấn chuyên sâu"],
            ["Số lượng bài", "10"],
            ["Độ dài bài", "1000 - 1200 chữ"],
            ["Mật độ Link", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ]
        st.session_state['df_config'] = pd.DataFrame(data, columns=["DANH MỤC", "GIÁ TRỊ"])

init_data()

# 3. SIDEBAR ĐA CẤP (SUB-MENU)
with st.sidebar:
    st.markdown("<h2 class='gold-glow'>🚕 ĐIỀU HÀNH SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    for main, subs in STRUCTURE.items():
        with st.expander(main):
            for sub in subs:
                # Tạo nút cho mỗi sub-menu
                if st.button(f"▪️ {sub}", key=f"btn_{sub}", use_container_width=True):
                    st.session_state['active_tab'] = sub
                    st.rerun()
    
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT"): st.stop()

# 4. KHU VỰC CHÍNH (DYNAMIC CONTENT)
tab = st.session_state['active_tab']
st.markdown(f"### 📍 {tab}")

if tab in ["Bảng điều khiển", "Data Config"]:
    # THANH CÔNG CỤ
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    with c3: 
        if st.button("🔄 SYNC"): st.toast("Đã đồng bộ dữ liệu!")

    st.markdown("<br>", unsafe_allow_html=True)

    # LAYOUT CHÍNH: BẢNG & ĐIỀU KHIỂN
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        st.markdown("<p class='gold-glow'>⚙️ THÔNG SỐ CẤU HÌNH (FULL 13 DÒNG)</p>", unsafe_allow_html=True)
        st.session_state['df_config'] = st.data_editor(
            st.session_state['df_config'], 
            use_container_width=True, 
            num_rows="fixed",
            height=520 
        )
    
    with col_r:
        st.markdown("<p class='gold-glow'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container():
            st.write("Trạng thái v55.0 Stable:")
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                log_p = st.empty()
                prog = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.3)
                    prog.progress(i * 10)
                    log_p.markdown(f"<div class='log-box'>[LOG] {datetime.datetime.now().strftime('%H:%M:%S')}<br>Đang gen bài {i}/10...<br>AI Gemini đang viết nội dung chuẩn SEO.</div>", unsafe_allow_html=True)
                st.success("✅ HOÀN THÀNH!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📅 LẬP LỊCH ĐĂNG"):
                st.toast("Robot đã vào hàng đợi dãn cách 30-90p...")

else:
    # HIỂN THỊ CHO CÁC TAB KHÁC
    st.info(f"Hệ thống đang tải dữ liệu cho mục: {tab}")
    st.data_editor(pd.DataFrame(columns=["Cột 1", "Cột 2", "Trạng thái"]), use_container_width=True, num_rows="dynamic", height=600)

st.caption("🚕 SEO Lái Hộ v160.0 | High-End Dashboard System")
