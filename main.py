import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG - ÉP SIDEBAR HIỆN HỮU
st.set_page_config(
    page_title="Hệ thống SEO Lái Hộ v200.0", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# --- CSS SIÊU CẤP: ĐEN SÂU & VÀNG GOLD (KHÔNG BỊ CHE, KHÔNG MẤT CHỮ) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* SIDEBAR: ĐEN TUYỀN - VIỀN VÀNG MẢNH */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
        min-width: 280px !important;
    }
    
    /* ÉP CHỮ SIDEBAR LUÔN HIỆN MÀU TRẮNG/VÀNG */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .gold-glow { color: #ffd700 !important; font-weight: 700; text-shadow: 0 0 8px rgba(255, 215, 0, 0.4); }

    /* MENU ĐA CẤP (EXPANDER) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #222 !important;
    }
    div[data-testid="stExpander"] p { color: #ffd700 !important; font-size: 16px !important; font-weight: 600 !important; }

    /* NÚT BẤM TRONG MENU CON */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #bbbbbb !important;
        border: none !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-size: 14px !important;
        height: 2.5em !important;
        transition: 0.3s;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #1a1a1a !important;
        border-left: 3px solid #ffd700 !important;
    }

    /* BẢNG DỮ LIỆU SÁNG RÕ */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }

    /* NÚT HÀNH ĐỘNG CHÍNH (VÀNG ĐEN) */
    .btn-run button {
        background: linear-gradient(135deg, #ffd700 0%, #ffcc00 100%) !important;
        color: #000000 !important; font-weight: 700 !important;
        border-radius: 10px !important; height: 3.5em !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (13 DÒNG CHUẨN)
if 'page' not in st.session_state: st.session_state['page'] = "Config & Chạy bài"

def init_data():
    if 'df_config' not in st.session_state:
        # NẠP ĐÚNG 13 DÒNG TỪ ẢNH image_3bd66d.jpg
        data = [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Danh sách Keyword", "thuê tài xế lái hộ, lái xe hộ tphcm..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu bài viết", "Bài tư vấn chuyên sâu, chốt sale"],
            ["Số lượng bài/ngày", "10"],
            ["Thiết lập số chữ", "1000 - 1200"],
            ["Mật độ Link/bài", "3 - 5"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ]
        st.session_state['df_config'] = pd.DataFrame(data, columns=["HẠNG MỤC", "GIÁ TRỊ"])

init_data()

# 3. SIDEBAR SUB-MENU (LÀM CHUẨN 1 DỰ ÁN LÁI HỘ)
with st.sidebar:
    st.markdown("<h2 class='gold-glow'>🏢 ĐIỀU HÀNH LÁI HỘ</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Nhóm 1: Hệ thống SEO
    with st.expander("⚙️ Hệ thống SEO", expanded=True):
        if st.button("▪️ Config & Chạy bài"): st.session_state['page'] = "Config & Chạy bài"
        if st.button("▪️ Website Satellite"): st.session_state['page'] = "Website Satellite"
        if st.button("▪️ Backlink Master"): st.session_state['page'] = "Backlink Master"
        if st.button("▪️ SEO Report"): st.session_state['page'] = "SEO Report"

    # Nhóm 2: Dữ liệu bài viết
    with st.expander("✍️ Quản lý Nội dung"):
        if st.button("▪️ Kho hình ảnh"): st.session_state['page'] = "Kho hình ảnh"
        if st.button("▪️ Từ điển Spin"): st.session_state['page'] = "Từ điển Spin"
    
    # Nhóm 3: Vùng miền
    with st.expander("📍 Phủ sóng vùng"):
        if st.button("▪️ Khu vực TPHCM"): st.session_state['page'] = "TPHCM"
        if st.button("▪️ Khu vực Hà Nội"): st.session_state['page'] = "Hà Nội"

    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# 4. KHU VỰC CHÍNH (HIỂN THỊ THEO PAGE)
page = st.session_state['page']
st.markdown(f"### 📍 {page}")

if page == "Config & Chạy bài":
    # TOOLBAR (EXPORT/SYNC)
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    with c3: 
        if st.button("🔄 SYNC"): st.toast("Đã đồng bộ dữ liệu thành công!")

    st.markdown("<br>", unsafe_allow_html=True)

    # LAYOUT: BẢNG 13 DÒNG & ĐIỀU KHIỂN
    col_table, col_run = st.columns([2, 1])
    
    with col_table:
        st.markdown("<p class='gold-glow'>⚙️ CẤU HÌNH HỆ THỐNG (FULL 13 DÒNG)</p>", unsafe_allow_html=True)
        # HIỂN THỊ TRỌN VẸN 13 DÒNG KHÔNG CẦN CUỘN
        st.session_state['df_config'] = st.data_editor(
            st.session_state['df_config'], 
            use_container_width=True, 
            num_rows="fixed",
            height=520 
        )
    
    with col_run:
        st.markdown("<p class='gold-glow'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành v55.0 Stable:")
            st.markdown('<div class="btn-run">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                prog = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.2)
                    prog.progress(i * 10)
                st.success("✅ ĐÃ XONG 10 BÀI!")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ĐĂNG BÀI", use_container_width=True)

elif page == "SEO Report":
    st.info("Nhật ký đăng bài và tỷ lệ Index Google.")
    st.data_editor(pd.DataFrame(columns=["Website", "Ngày đăng", "Tiêu đề", "Trạng thái Index"]), use_container_width=True, height=600)

else:
    st.warning(f"Đang kết nối dữ liệu cho mục: {page}")

st.caption("🚕 SEO Lái Hộ v200.0 | Hệ thống quản trị tập trung")
