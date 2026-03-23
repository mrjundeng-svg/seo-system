import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# =================================================================
# 1. 🏗️ CẤU HÌNH HỆ THỐNG (Ní thêm dự án hoặc quyền tại đây)
# =================================================================
PROJECT_CONFIG = {
    "DỰ ÁN 1: LÁI HỘ": ["Lái Hộ: Dashboard", "Lái Hộ: Backlink", "Lái Hộ: Website", "Lái Hộ: Image", "Lái Hộ: Spin", "Lái Hộ: Local", "Lái Hộ: Report"],
    "DỰ ÁN 2: GIÚP VIỆC": ["Giúp Việc: Dashboard", "Giúp Việc: Backlink", "Giúp Việc: Website", "Giúp Việc: Image", "Giúp Việc: Spin", "Giúp Việc: Local", "Giúp Việc: Report"],
    "⚙️ QUẢN TRỊ": ["Admin: Tài khoản", "Admin: Phân quyền"]
}

def init_v5100():
    if 'selected_task' not in st.session_state: 
        st.session_state['selected_task'] = "Lái Hộ: Dashboard"

init_v5100()

# =================================================================
# 2. 🎨 UI/UX LEFT MENU (ĐẸP - ĐỒNG BỘ - CHUYÊN NGHIỆP)
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ Master Hub", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    /* Nút bấm đồng bộ */
    .btn-blue button { background-color: #0055ff !important; width: 100%; border-radius: 4px; height: 40px; font-weight: 700; border: none; }
    .btn-red button { background-color: #ff4b4b !important; width: 100%; border-radius: 4px; height: 40px; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1.3, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center; letter-spacing: 2px;'>SEO HUB</h2>", unsafe_allow_html=True)
    
    # Gom tất cả các lựa chọn vào một danh sách phẳng để Option Menu xử lý
    all_options = []
    for section in PROJECT_CONFIG.values():
        all_options.extend(section)
    
    # Định nghĩa Icon cho từng loại tab (Đồng bộ cho mọi dự án)
    icon_map = {
        "Dashboard": "speedometer2", "Backlink": "link-45deg", "Website": "globe2", 
        "Image": "image", "Spin": "arrow-repeat", "Local": "geo-alt", "Report": "bar-chart",
        "Tài khoản": "people", "Phân quyền": "shield-lock"
    }
    
    icons = []
    for opt in all_options:
        key = opt.split(": ")[1] if ": " in opt else opt
        icons.append(icon_map.get(key, "circle"))

    # --- RENDER LEFT MENU ---
    selected = option_menu(
        menu_title="HỆ THỐNG SEO", 
        options=all_options,
        icons=icons,
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0px", "background-color": "#111", "border": "1px solid #222", "border-radius": "0px"},
            "menu-title": {"color": "#ffd700", "font-size": "13px", "font-weight": "800", "padding": "15px", "text-transform": "uppercase"},
            "nav-link": {"font-size": "13px", "text-align": "left", "margin": "0px", "color": "#aaa", "height": "38px", "border-radius": "0px"},
            "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700", "border-left": "6px solid #fff"},
        }
    )
    st.session_state['selected_task'] = selected

with main_col:
    # Logic tách tên Dự án và tên Tab
    if ": " in selected:
        project_part, tab_name = selected.split(": ")
    else:
        project_part, tab_name = "System", selected

    st.markdown(f"### {project_part} <span style='color:#888; font-size:18px;'>/ {tab_name}</span>", unsafe_allow_html=True)
    
    # TOOLBAR (Đẹp & Giống nhau)
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns([1, 1, 2.5])
    
    with t1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.toast(f"Đã cập nhật {selected}")
        st.markdown('</div>', unsafe_allow_html=True)
    with t2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.toast(f"Đã đồng bộ {selected}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

    # NỘI DUNG TỪNG TAB (MẪU)
    if tab_name == "Dashboard":
        st.info(f"Chào mừng Ní đến với Dashboard của {project_part}")
        # Chèn bảng Dashboard cấu hình Sheet ID, JSON tại đây
    elif "Admin" in project_part:
        st.warning("⚠️ Khu vực quản trị hệ thống")
    else:
        st.write(f"Đang hiển thị dữ liệu cho mục: **{tab_name}**")
        st.data_editor(pd.DataFrame(columns=["Cột 1", "Cột 2", "Ghi chú"]), use_container_width=True, num_rows="dynamic")

st.caption(f"🚀 v5100.0 | Multi-Project Architecture | Nested Menu UI | Clean & Professional")
