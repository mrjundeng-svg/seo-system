import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG - PHẢI LÀ DÒNG ĐẦU TIÊN
st.set_page_config(
    page_title="Hệ thống SEO Lái Hộ v190.0", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" # ÉP SIDEBAR PHẢI HIỆN RA KHI MỞ WEB
)

# --- CSS CUSTOM: ÉP SIDEBAR HIỆN HỮU & MÀU GOLD DARK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* NỀN ĐEN SÂU */
    .stApp { background-color: #000000 !important; }
    
    /* HIỆN SIDEBAR VÀ ĐỊNH DẠNG MÀU */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
        min-width: 280px !important;
    }

    /* FIX LỖI MẤT CHỮ TRÊN SIDEBAR */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* TIÊU ĐỀ VÀNG GOLD */
    .gold-title { 
        color: #ffd700 !important; 
        font-weight: 800; 
        font-size: 22px; 
        margin-bottom: 20px;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.3);
    }

    /* STYLE CHO EXPANDER (SUB-MENU) */
    div[data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 1px solid #222 !important;
    }
    div[data-testid="stExpander"] p { color: #ffd700 !important; font-weight: 600; }

    /* NÚT BẤM TRONG SIDEBAR (SUB-MENU ITEMS) */
    .stSidebar .stButton>button {
        background-color: transparent !important;
        color: #bbbbbb !important;
        border: none !important;
        text-align: left !important;
        padding-left: 10px !important;
        font-size: 14px !important;
        height: 2.5em !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important;
        background-color: #1a1a1a !important;
    }

    /* BẢNG DỮ LIỆU & EDITOR */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }

    /* NÚT HÀNH ĐỘNG CHÍNH */
    .btn-run button {
        background: linear-gradient(135deg, #ffd700 0%, #ffcc00 100%) !important;
        color: #000000 !important; font-weight: 700 !important;
        border-radius: 10px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU & MENU
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Data Config"

# Cấu trúc Menu đa cấp
STRUCTURE = {
    "🏠 Tổng quan": ["Bảng điều khiển", "Thống kê Index"],
    "🚕 Dịch vụ Lái Hộ": ["Phủ sóng vùng", "Tính cước Lái Hộ", "Quản lý Tài xế"],
    "🏠 Giúp Việc Nhanh": ["Đối tác B2B", "Quản lý Nhân sự"],
    "⚙️ Hệ thống SEO": ["Data Config", "Hệ thống Website", "Backlink Master"],
    "🖼️ Kho dữ liệu": ["Kho hình ảnh", "Từ điển Spin"],
    "📊 Báo cáo": ["Báo cáo cuối", "Lịch sử Robot"]
}

def init_data():
    if 'df_config' not in st.session_state:
        # NẠP CHUẨN 13 DÒNG TỪ ẢNH image_3bd66d.jpg
        data = [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Keyword chính", "thuê tài xế lái hộ, đưa người say..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu bài viết", "Bài tư vấn chuyên sâu, chốt sale"],
            ["Số lượng bài/ngày", "10"],
            ["Thiết lập số chữ", "1000 - 1200"],
            ["Mật độ Link/bài", "3 - 5"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ]
        st.session_state['df_config'] = pd.DataFrame(data, columns=["HẠNG MỤC", "GIÁ TRỊ"])

init_data()

# 3. RENDER SIDEBAR (BẮT BUỘC PHẢI HIỆN)
with st.sidebar:
    st.markdown("<div class='gold-title'>🏢 ĐIỀU HÀNH SEO</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Render từng nhóm Menu
    for main, subs in STRUCTURE.items():
        # Tự động mở Expander nếu tab hiện tại thuộc nhóm đó
        is_expanded = st.session_state['active_tab'] in subs
        with st.expander(main, expanded=is_expanded):
            for sub in subs:
                # Nút cho Sub-menu
                if st.button(f"▪️ {sub}", key=f"menu_{sub}", use_container_width=True):
                    st.session_state['active_tab'] = sub
                    st.rerun()
    
    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# 4. KHU VỰC CHÍNH (CONTENT)
tab = st.session_state['active_tab']
st.markdown(f"### 📍 {tab}")

if tab == "Data Config" or tab == "Bảng điều khiển":
    # TOOLBAR
    c1, c2, c3, _ = st.columns([1, 1.2, 0.8, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: up = st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    with c3: st.button("🔄 ĐỒNG BỘ")

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH CHI TIẾT (13 DÒNG)</p>", unsafe_allow_html=True)
        # SHOW FULL 13 DÒNG CẤU HÌNH
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
    
    with col_r:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành v55.0 Stable:")
            st.markdown('<div class="btn-run">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                p = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.1)
                    p.progress(i * 10)
                st.success("✅ ĐÃ XONG 10 BÀI!")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ĐĂNG BÀI", use_container_width=True)

elif tab == "Phủ sóng vùng":
    st.info(f"Quản lý địa điểm cho dự án Lái Hộ.")
    st.data_editor(pd.DataFrame([["Quận 1", "Bật"], ["Quận 7", "Bật"], ["Quận 2", "Bật"]], columns=["Khu vực", "Trạng thái"]), use_container_width=True)

else:
    st.warning(f"Tính năng {tab} đang chờ nạp dữ liệu từ hệ thống.")

st.caption("🚕 SEO Lái Hộ v190.0 | High-End Control System")
