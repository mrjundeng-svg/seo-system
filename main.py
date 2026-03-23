import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# =================================================================
# 1. 🏗️ TEMPLATE & DỮ LIỆU (KHÔNG THAY ĐỔI)
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
TEMPLATES = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": REPORT_COLS,
    "Danh sách tài khoản": ["Username", "Email", "Quyền hạn", "Trạng thái"],
    "Phân quyền tính năng": ["Tính năng", "Nhóm quyền", "Mức độ truy cập"]
}

PROJECTS = {
    "PROJ1": {"name": "🚕 DỰ ÁN: LÁI HỘ", "id": "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw", "tabs": ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]},
    "PROJ2": {"name": "🏠 DỰ ÁN: GIÚP VIỆC NHANH", "id": "ID_SHEET_GIUP_VIEC", "tabs": ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]},
    "ADMIN": {"name": "⚙️ QUẢN TRỊ HỆ THỐNG", "id": "ADMIN", "tabs": ["Danh sách tài khoản", "Phân quyền tính năng"]}
}

def init_v5400():
    if 'current_proj' not in st.session_state: st.session_state['current_proj'] = "PROJ1"
    if 'current_tab' not in st.session_state: st.session_state['current_tab'] = "Dashboard"
    
    for p_id, info in PROJECTS.items():
        for t in info['tabs']:
            key = f"df_{p_id}_{t}"
            if key not in st.session_state:
                cols = TEMPLATES.get(t, ["Cột 1", "Cột 2"])
                st.session_state[key] = pd.DataFrame(columns=cols)

init_v5400()

# =================================================================
# 2. 🎨 GIAO DIỆN SIDEBAR (FIX LỖI XOAY VÒNG)
# =================================================================
st.set_page_config(page_title="SEO Master Hub", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    .nav-header { color: #ffd700; font-weight: 800; font-size: 13px; padding: 15px 5px 5px 5px; border-bottom: 1px solid #222; text-transform: uppercase; }
    .btn-blue button { background-color: #0055ff !important; width: 100%; height: 40px; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1.3, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>SEO HUB</h2>", unsafe_allow_html=True)
    
    # Render từng khối dự án riêng biệt
    for p_id, info in PROJECTS.items():
        st.markdown(f"<div class='nav-header'>{info['name']}</div>", unsafe_allow_html=True)
        
        # Xác định index mặc định để không bị loạn màu
        default_idx = info['tabs'].index(st.session_state['current_tab']) if st.session_state['current_proj'] == p_id else -1
        
        sel = option_menu(
            menu_title=None, 
            options=info['tabs'],
            icons=["speedometer2", "link-45deg", "globe2", "image", "arrow-repeat", "geo-alt", "bar-chart"] if "PROJ" in p_id else ["people", "shield-lock"],
            key=f"menu_{p_id}",
            default_index=default_idx,
            styles={
                "container": {"background-color": "transparent", "padding": "0px"},
                "nav-link": {"font-size": "13px", "color": "#777", "text-align": "left", "height": "35px"},
                "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700"}
            }
        )
        
        # Chỉ rerun khi thực sự đổi tab/dự án
        if sel and (st.session_state['current_tab'] != sel or st.session_state['current_proj'] != p_id):
            st.session_state['current_proj'] = p_id
            st.session_state['current_tab'] = sel
            st.rerun()

with main_col:
    p_id = st.session_state['current_proj']
    c_tab = st.session_state['current_tab']
    data_key = f"df_{p_id}_{c_tab}"
    
    st.markdown(f"### {PROJECTS[p_id]['name']} <span style='color:#888; font-size:18px;'>/ {c_tab}</span>", unsafe_allow_html=True)
    
    # Toolbar
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns([1, 1, 2.5])
    with t1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.toast("Đang đồng bộ...")
    with t2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.toast("Đang tải dữ liệu...")
    
    st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

    # Hiển thị bảng dữ liệu (Check tồn tại key trước khi render)
    if data_key in st.session_state:
        st.session_state[data_key] = st.data_editor(
            st.session_state[data_key], 
            use_container_width=True, num_rows="dynamic", height=650, hide_index=True
        )

st.caption("🚀 v5400.0 | Anti-Loop Sidebar | Full Templates | Multi-Project Hub")
