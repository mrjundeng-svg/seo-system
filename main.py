import streamlit as st
import pandas as pd
import json
from streamlit_option_menu import option_menu

# =================================================================
# 1. 🏗️ DANH SÁCH "HỘ KHẨU" CÁC DỰ ÁN (Sửa ở đây để thêm dự án)
# =================================================================
PROJECTS = {
    "🚕 Lái Hộ": "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw",
    "🏠 Giúp Việc": "ID_SHEET_GIUP_VIEC_CUA_NI",
    "🤖 CTech AI": "ID_SHEET_CTECH_CUA_NI"
}

def init_v4900():
    if 'current_project' not in st.session_state:
        st.session_state['current_project'] = list(PROJECTS.keys())[0]
    if 'selected_menu' not in st.session_state:
        st.session_state['selected_menu'] = "Dashboard"

init_v4900()

# =================================================================
# 2. 🎨 UI/UX SIDEBAR ĐA DỰ ÁN
# =================================================================
st.set_page_config(page_title="Multi-Project SEO Master", layout="wide")

# CSS để làm Sidebar đẹp hơn
st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    /* Style cho bộ chọn dự án */
    .project-box {
        background-color: #1a1a1a; padding: 10px; border: 1px solid #333;
        border-radius: 5px; margin-bottom: 20px; text-align: center;
    }
    .btn-blue button { background-color: #0055ff !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>SEO HUB</h2>", unsafe_allow_html=True)
    
    # --- BỘ CHỌN DỰ ÁN ---
    st.markdown("<p style='color:#888; font-size:12px; margin-bottom:5px;'>CHỌN DỰ ÁN:</p>", unsafe_allow_html=True)
    new_project = st.selectbox("Select Project", options=list(PROJECTS.keys()), label_visibility="collapsed")
    
    if new_project != st.session_state['current_project']:
        st.session_state['current_project'] = new_project
        st.toast(f"Đã chuyển sang dự án: {new_project}")
        # Chỗ này sau này mình sẽ thêm hàm tự động RESTORE FROM CLOUD khi đổi dự án
        st.rerun()

    st.markdown("<hr style='border-color:#333'>", unsafe_allow_html=True)

    # --- MENU ĐIỀU HƯỚNG (GIỐNG NHAU 100%) ---
    st.session_state['selected_menu'] = option_menu(
        menu_title=None,
        options=["Dashboard", "Backlink", "Website", "Image Data", "Content Spin", "Local Data", "Report"],
        icons=["home", "link-45deg", "globe2", "image", "arrow-repeat", "geo-alt", "bar-chart-line"],
        styles={
            "container": {"background-color": "#000", "padding": "0px"},
            "nav-link": {"color": "#888", "font-size": "14px", "text-align": "left", "height": "45px"},
            "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700"}
        }
    )

with main_col:
    curr_proj = st.session_state['current_project']
    curr_tab = st.session_state['selected_menu']
    
    # Hiển thị tiêu đề Dự án + Tab
    st.markdown(f"### {curr_proj} <span style='color:#888; font-size:18px;'>/ {curr_tab}</span>", unsafe_allow_html=True)
    st.info(f"Đang kết nối Sheet ID: `{PROJECTS[curr_proj]}`")

    # TOOLBAR
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.success(f"Đã đẩy data {curr_proj} lên Cloud!")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.success(f"Đã kéo data {curr_proj} về Web!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Dữ liệu bảng (Giả lập)
    st.data_editor(pd.DataFrame({"Hạng mục": ["ID Dự án", "Folder Drive", "Trạng thái"], "Giá trị": [PROJECTS[curr_proj], "Folder_ABC_123", "Active"]}), use_container_width=True, hide_index=True)

st.caption(f"🚀 v4900.0 | Multi-Project Hub | Project: {st.session_state['current_project']}")
