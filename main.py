import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Lái Hộ - v240.0", page_icon="🚕", layout="wide")

# --- CSS "BLACK & GOLD" - ÉP GIAO DIỆN PHẲNG ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* ẨN SIDEBAR MẶC ĐỊNH CỦA STREAMLIT ĐỂ DÙNG SIDEBAR TỰ CHẾ */
    [data-testid="stSidebar"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }

    /* CHỮ TRẮNG & VÀNG */
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 22px; margin-bottom: 20px; }
    
    /* MENU BÊN TRÁI (SIDEBAR TỰ CHẾ) */
    .nav-box {
        border-right: 1px solid #333333;
        height: 100vh;
        padding-right: 15px;
    }

    /* STYLE NÚT MENU */
    .stButton>button {
        width: 100%; border-radius: 5px; font-weight: 600; text-align: left;
        background-color: transparent !important; border: 1px solid transparent !important;
        margin-bottom: 5px;
    }
    .stButton>button:hover {
        border: 1px solid #ffd700 !important; color: #ffd700 !important;
    }
    
    /* NÚT ĐANG CHỌN (ACTIVE) */
    .active-btn button {
        background-color: #1a1a1a !important;
        border-left: 4px solid #ffd700 !important;
        color: #ffd700 !important;
    }

    /* NÚT CHẠY MÀU ĐỎ */
    .btn-red button {
        background-color: #ff0000 !important; color: white !important;
        border: none !important; font-weight: 700 !important; height: 3.5em;
    }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

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
    
    for t in ["df_backlink", "df_website", "df_image", "df_spin", "df_local", "df_report"]:
        if t not in st.session_state: st.session_state[t] = pd.DataFrame(columns=["STT", "Nội dung", "Ghi chú"])

init_data()

# =================================================================
# 3. BỐ CỤC CHÍNH (SIDEBAR CỐ ĐỊNH BẰNG COLUMNS)
# =================================================================
# Chia trang web làm 2 phần: Cột Menu (Sidebar) và Cột Nội dung
col_nav, col_main = st.columns([1, 4], gap="large")

with col_nav:
    st.markdown("<div class='nav-box'>", unsafe_allow_html=True)
    st.markdown("<h2 class='gold-title'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    
    # Danh sách menu
    menus = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    
    for m in menus:
        # Nếu tab đang active thì đổi style nút
        if st.session_state['active_tab'] == m:
            st.markdown("<div class='active-btn'>", unsafe_allow_html=True)
            if st.button(f"▪️ {m}", key=f"btn_{m}"): pass
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(f" {m}", key=f"btn_{m}"):
                st.session_state['active_tab'] = m
                st.rerun()
                
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT"): st.stop()
    st.markdown("</div>", unsafe_allow_html=True)

# =================================================================
# 4. HIỂN THỊ NỘI DUNG (CỘT PHẢI)
# =================================================================
with col_main:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")

    if active == "Dashboard":
        # Thanh công cụ
        c1, c2, c3, _ = st.columns([1, 1, 1, 2])
        with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv")
        with c2: st.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
        with c3: st.button("🔄 SYNC")

        st.markdown("<br>", unsafe_allow_html=True)

        cl, cr = st.columns([2, 1])
        with cl:
            st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH (13 DÒNG CHUẨN)</p>", unsafe_allow_html=True)
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520)
        with cr:
            st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Trạng thái v55.0 Stable:")
                st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                    bar = st.progress(0)
                    for i in range(11):
                        time.sleep(0.1); bar.progress(i*10)
                    st.success("✅ ĐÃ XONG!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

    elif active == "Data_Report":
        st.markdown("<p style='color:#ffd700; font-weight:700;'>📋 BÁO CÁO HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
        st.dataframe(st.session_state['df_report'], use_container_width=True, height=700)

    else:
        # Các Tab nhập liệu
        key = f"df_{active.split('_')[1].lower()}"
        st.markdown(f"##### Nhập dữ liệu cho {active}:")
        st.session_state[key] = st.data_editor(st.session_state[key], use_container_width=True, num_rows="dynamic", height=700)

st.caption("🚀 SEO Automation Lái Hộ v240.0 | Fixed Navigation Edition")
