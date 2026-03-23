import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# =================================================================
# 1. 📋 ĐỊNH NGHĨA TEMPLATE CHUẨN (LÁI HỘ)
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]

TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": REPORT_COLS
}

def init_v5700():
    if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"
    
    for tab, cols in TABS_CONFIG.items():
        s_key = f"df_{tab}"
        if s_key not in st.session_state:
            if tab == "Dashboard":
                st.session_state[s_key] = pd.DataFrame([
                    ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                    ["SERVICE_ACCOUNT_JSON", ""],
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
                    ["Số lượng bài cần tạo", "3"]
                ], columns=cols)
            else:
                st.session_state[s_key] = pd.DataFrame(columns=cols)

init_v5700()

# =================================================================
# 2. 🎨 GIAO DIỆN SIDEBAR (CHỈ 1 DỰ ÁN - SIÊU GỌN)
# =================================================================
st.set_page_config(page_title="LÁI HỘ SEO Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    .btn-blue button { background-color: #0055ff !important; width: 100%; font-weight: 700; height: 45px; border: none; }
    .btn-red button { background-color: #ff4b4b !important; width: 100%; font-weight: 700; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; text-align:center; font-size:12px;'>Hệ thống SEO Automation</p>", unsafe_allow_html=True)
    
    # Menu duy nhất cho dự án Lái Hộ
    selected = option_menu(
        menu_title=None,
        options=list(TABS_CONFIG.keys()),
        icons=["speedometer2", "link-45deg", "globe2", "image", "arrow-repeat", "geo-alt", "bar-chart"],
        default_index=list(TABS_CONFIG.keys()).index(st.session_state['active_tab']),
        styles={
            "container": {"padding": "0px", "background-color": "#111", "border": "1px solid #222", "border-radius": "0px"},
            "nav-link": {"font-size": "14px", "text-align": "left", "color": "#888", "height": "50px", "border-radius": "0px"},
            "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700", "border-left": "8px solid #fff"},
        }
    )
    st.session_state['active_tab'] = selected

# =================================================================
# 3. 🖼️ KHU VỰC HIỂN THỊ DỮ LIỆU
# =================================================================
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### Dự án: Lái Hộ <span style='color:#888; font-size:18px;'>/ {tab}</span>", unsafe_allow_html=True)
    
    # Toolbar chỉ 2 nút chính cho gọn
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns([1, 1, 2.5])
    with t1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT"): st.toast("Robot đang khởi động...")
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("☁️ UPDATE CLOUD"): st.toast("Đã đẩy lên Google Sheets!")
    with t2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.toast("Đã kéo từ Google Sheets về!")
    
    st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

    # Hiển thị bảng Editor
    s_key = f"df_{tab}"
    st.session_state[s_key] = st.data_editor(
        st.session_state[s_key],
        use_container_width=True,
        num_rows="dynamic",
        height=700,
        hide_index=True,
        column_config={
            "Giá trị thực tế": st.column_config.TextColumn(width="large"),
            "Bộ Spin": st.column_config.TextColumn(width="large"),
            "URL / ID": st.column_config.TextColumn(width="medium"),
            "Link bài viết": st.column_config.TextColumn(width="medium")
        }
    )

st.caption("🚀 v5700.0 | Single Project Focus | Stable UI | All Templates Restored")
