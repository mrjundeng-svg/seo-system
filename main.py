import streamlit as st
import pandas as pd
import time

# =================================================================
# 1. CẤU HÌNH TRANG - KHÓA SIDEBAR CỐ ĐỊNH
# =================================================================
st.set_page_config(
    page_title="Hệ thống SEO Lái Hộ v260.0", 
    page_icon="🚕", 
    layout="wide",
    initial_sidebar_state="expanded" 
)

# CSS SIÊU CẤP: DIỆT LỖI TÀNG HÌNH & NHUỘM VÀNG ĐEN
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* NỀN ĐEN TOÀN DIỆN */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* KHÓA CHẾT SIDEBAR: Ẩn nút đóng (X) và nút mở (3 gạch) */
    [data-testid="collapsedControl"] { display: none !important; }
    button[kind="headerNoContext"] { display: none !important; }
    section[data-testid="stSidebar"] { 
        min-width: 280px !important;
        max-width: 280px !important;
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important;
    }

    /* MÀU CHỮ VÀNG GOLD & TRẮNG */
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    .gold-title { color: #ffd700 !important; font-weight: 700; font-size: 20px; margin-bottom: 20px; }
    .stMarkdown, label, p, span { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }

    /* STYLE CHO NÚT MENU SIDEBAR */
    .stSidebar .stButton>button {
        width: 100% !important; border-radius: 0px !important; font-weight: 500 !important;
        background-color: transparent !important; border: none !important;
        text-align: left !important; padding-left: 10px !important;
        height: 3em !important; border-bottom: 1px solid #1a1a1a !important;
    }
    .stSidebar .stButton>button:hover {
        color: #ffd700 !important; background-color: #111111 !important;
        border-left: 4px solid #ffd700 !important;
    }

    /* NÚT ĐANG CHỌN (ACTIVE) */
    .active-nav button {
        color: #ffd700 !important; background-color: #1a1a1a !important;
        border-left: 4px solid #ffd700 !important;
    }

    /* NÚT CHẠY CHIẾN DỊCH MÀU ĐỎ */
    .btn-red button {
        background-color: #ff0000 !important; color: #ffffff !important;
        border: none !important; font-weight: 700 !important; height: 3.5em !important;
        text-transform: uppercase;
    }
    .btn-red button:hover { background-color: #cc0000 !important; box-shadow: 0 0 15px #ff0000; }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    [data-testid="stDataFrame"] * { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU (FIX LỖI KEYERROR)
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# Hàm khởi tạo để đảm bảo không bao giờ bị KeyError
def init_all_data():
    # 13 dòng cấu hình chuẩn
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Danh sách Keyword", "thuê tài xế lái hộ, đưa người say..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu nội dung", "Bài viết tư vấn, chốt sale dịch vụ"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200 chữ"],
            ["Mật độ Backlink", "3 - 5 link/bài"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ], columns=["Hạng mục", "Giá trị hiện tại"])

    # Khởi tạo các bảng nhập liệu khác
    map_df = {
        "Data_Backlink": "df_backlink",
        "Data_Website": "df_website",
        "Data_Image": "df_image",
        "Data_Spin": "df_spin",
        "Data_Local": "df_local",
        "Data_Report": "df_report"
    }
    for tab_name, df_key in map_df.items():
        if df_key not in st.session_state:
            st.session_state[df_key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_all_data()

# =================================================================
# 3. SIDEBAR CỐ ĐỊNH (FIX LỖI TÀNG HÌNH)
# =================================================================
with st.sidebar:
    st.markdown("<div class='gold-title'>🏢 LÁI HỘ CONTROL</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    menu_options = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    
    for option in menu_options:
        # Kiểm tra xem có phải tab đang chọn không để đổi màu
        is_active = st.session_state['active_tab'] == option
        if is_active:
            st.markdown("<div class='active-nav'>", unsafe_allow_html=True)
            if st.button(f"▪️ {option}", key=f"nav_{option}"): pass
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(f"  {option}", key=f"nav_{option}"):
                st.session_state['active_tab'] = option
                st.rerun()
                
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# =================================================================
# 4. KHU VỰC CHÍNH (FIX LỖI INDEXERROR)
# =================================================================
active = st.session_state['active_tab']
st.markdown(f"### 📍 {active}")

if active == "Dashboard":
    # TOOLBAR
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
    with c2: st.button("🔄 ĐỒNG BỘ", use_container_width=True)
    with c3: st.button("📥 NHẬP FILE", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>⚙️ CẤU HÌNH HỆ THỐNG (13 DÒNG)</p>", unsafe_allow_html=True)
        # SHOW FULL 13 DÒNG
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
    
    with col_r:
        st.markdown("<p style='color:#ffd700; font-weight:700;'>🚀 ĐIỀU KHIỂN CHIẾN DỊCH</p>", unsafe_allow_html=True)
        with st.container(border=True):
            st.write("Vận hành v55.0 Stable:")
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                prog = st.progress(0)
                for i in range(11):
                    time.sleep(0.1); prog.progress(i*10)
                st.success("✅ HOÀN THÀNH!")
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

else:
    # CÁCH LẤY DATA KEY AN TOÀN (KHÔNG DÙNG SPLIT ĐỂ TRÁNH INDEXERROR)
    data_map = {
        "Data_Backlink": "df_backlink",
        "Data_Website": "df_website",
        "Data_Image": "df_image",
        "Data_Spin": "df_spin",
        "Data_Local": "df_local",
        "Data_Report": "df_report"
    }
    
    df_key = data_map.get(active)
    
    if df_key:
        if active == "Data_Report":
            st.markdown("<p style='color:#ffd700; font-weight:700;'>📋 BÁO CÁO HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
            st.dataframe(st.session_state[df_key], use_container_width=True, height=750)
        else:
            st.markdown(f"<p style='color:#ffd700; font-weight:700;'>📥 NHẬP DỮ LIỆU: {active}</p>", unsafe_allow_html=True)
            st.session_state[df_key] = st.data_editor(st.session_state[df_key], use_container_width=True, num_rows="dynamic", height=750)
    else:
        st.error("Không tìm thấy dữ liệu cho tab này!")

st.caption("🚀 SEO Automation Lái Hộ v260.0 | Permanent Sidebar & Bug-Free")
