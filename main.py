import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG (PHẢI LÀ DÒNG ĐẦU TIÊN)
st.set_page_config(page_title="SEO Lái Hộ v250.0", page_icon="🚕", layout="wide")

# --- CSS TÙY CHỈNH: TÔNG VÀNG - ĐEN & CỐ ĐỊNH MENU ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* Nền đen toàn diện */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* ẨN SIDEBAR MẶC ĐỊNH ĐỂ DÙNG MENU TỰ CHẾ (CHỐNG ẨN HIỆN) */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* CHỮ TRẮNG & VÀNG */
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; }
    
    /* MENU BÊN TRÁI CỐ ĐỊNH */
    .nav-column {
        border-right: 1px solid #333333;
        height: 100vh;
        padding: 10px;
    }

    /* STYLE NÚT MENU */
    .stButton>button {
        width: 100%; border-radius: 4px; font-weight: 500; text-align: left;
        background-color: transparent !important; border: 1px solid transparent !important;
        margin-bottom: 2px; padding: 10px !important;
    }
    .stButton>button:hover {
        border: 1px solid #ffd700 !important; color: #ffd700 !important;
    }
    
    /* NÚT ĐANG ACTIVE */
    .active-btn button {
        background-color: #1a1a1a !important;
        border-left: 4px solid #ffd700 !important;
        color: #ffd700 !important;
    }

    /* NÚT CHẠY CHIẾN DỊCH (MÀU ĐỎ) */
    .btn-run button {
        background-color: #ff0000 !important; color: white !important;
        border: none !important; font-weight: 700 !important; height: 3.5em;
        text-transform: uppercase;
    }

    /* ĐỊNH DẠNG BẢNG */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU (SESSION STATE)
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

def init_data():
    # Nạp 13 dòng cấu hình chuẩn
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
    
    # Khởi tạo các bảng nhập liệu
    tabs = ["backlink", "website", "image", "spin", "local", "report"]
    for t in tabs:
        key = f"df_{t}"
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_data()

# =================================================================
# 3. BỐ CỤC CHÍNH (CHIA 2 CỘT CỐ ĐỊNH)
# =================================================================
col_nav, col_main = st.columns([1, 4], gap="large")

with col_nav:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Danh sách Menu
    menu_list = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    
    for m in menu_list:
        if st.session_state['active_tab'] == m:
            st.markdown("<div class='active-btn'>", unsafe_allow_html=True)
            if st.button(f"▪️ {m}", key=f"nav_{m}"): pass
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(f" {m}", key=f"nav_{m}"):
                st.session_state['active_tab'] = m
                st.rerun()
                
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT"): st.stop()

# =================================================================
# 4. HIỂN THỊ NỘI DUNG (CỘT PHẢI)
# =================================================================
with col_main:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")

    if active == "Dashboard":
        # Toolbar
        c1, c2, c3, _ = st.columns([1, 1, 1, 2])
        with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv")
        with c2: st.button("🔄 ĐỒNG BỘ")
        with c3: st.button("📥 NHẬP DỮ LIỆU")

        st.markdown("<br>", unsafe_allow_html=True)

        cl, cr = st.columns([2, 1])
        with cl:
            st.markdown("<p class='gold-text'>⚙️ CẤU HÌNH (13 DÒNG CHUẨN)</p>", unsafe_allow_html=True)
            # Hiển thị bảng 13 dòng cố định chiều cao
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520)
        with cr:
            st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Vận hành v55.0 Stable:")
                st.markdown('<div class="btn-run">', unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                    b = st.progress(0)
                    for i in range(11):
                        time.sleep(0.1); b.progress(i*10)
                    st.success("✅ HOÀN THÀNH!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

    else:
        # Xử lý các Tab dữ liệu khác (Fix lỗi IndexError)
        if "_" in active:
            data_key = f"df_{active.split('_')[1].lower()}"
        else:
            data_key = f"df_{active.lower()}"
        
        if active == "Data_Report":
            st.markdown("<p class='gold-text'>📋 BÁO CÁO HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
            st.dataframe(st.session_state[data_key], use_container_width=True, height=750)
        else:
            st.markdown(f"<p class='gold-text'>📥 NHẬP DỮ LIỆU: {active}</p>", unsafe_allow_html=True)
            st.session_state[data_key] = st.data_editor(st.session_state[data_key], use_container_width=True, num_rows="dynamic", height=750)

st.caption("🚀 SEO Automation Lái Hộ v250.0 | Clean & Fixed UI")
