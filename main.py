import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# =================================================================
# 1. 🏗️ TEMPLATE CẤU TRÚC BẢNG (DỮ LIỆU GỐC)
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
    "P1": {"name": "🚕 DỰ ÁN 1: LÁI HỘ", "id": "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw", "tabs": ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]},
    "P2": {"name": "🏠 DỰ ÁN 2: GIÚP VIỆC NHANH", "id": "ID_SHEET_GIUP_VIEC", "tabs": ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]},
    "ADM": {"name": "⚙️ QUẢN TRỊ HỆ THỐNG", "id": "ADMIN_SYSTEM", "tabs": ["Danh sách tài khoản", "Phân quyền tính năng"]}
}

# =================================================================
# 2. 🧠 KHỞI TẠO BỘ NHỚ (SESSION STATE)
# =================================================================
def init_system():
    if 'current_proj_id' not in st.session_state: st.session_state['current_proj_id'] = "P1"
    if 'current_tab_name' not in st.session_state: st.session_state['current_tab_name'] = "Dashboard"
    
    # Khởi tạo dữ liệu cho từng tab của từng dự án
    for p_id, info in PROJECTS.items():
        for t_name in info['tabs']:
            data_key = f"df_{p_id}_{t_name}"
            if data_key not in st.session_state:
                cols = TEMPLATES.get(t_name, ["Cột 1", "Cột 2"])
                # Nạp sẵn Dashboard cho chuyên nghiệp
                if t_name == "Dashboard":
                    st.session_state[data_key] = pd.DataFrame([
                        ["GOOGLE_SHEET_ID", info['id']],
                        ["SERVICE_ACCOUNT_JSON", ""],
                        ["GEMINI_API_KEY", ""],
                        ["FOLDER_DRIVE_ID", ""],
                        ["Số lượng bài cần tạo", "3"]
                    ], columns=cols)
                else:
                    st.session_state[data_key] = pd.DataFrame(columns=cols)

init_system()

# =================================================================
# 3. 🎨 GIAO DIỆN SIDEBAR CHA-CON (ANTI-LOOP)
# =================================================================
st.set_page_config(page_title="SEO Hub v5500", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    .nav-header { 
        color: #ffd700; font-weight: 800; font-size: 13px; 
        padding: 15px 10px 5px 10px; border-bottom: 1px solid #333; 
        margin-top: 10px; text-transform: uppercase; letter-spacing: 1px;
    }
    .btn-blue button { background-color: #0055ff !important; width: 100%; font-weight: 700; border: none; height: 42px; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1.3, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>SEO HUB</h2>", unsafe_allow_html=True)
    
    for p_id, p_info in PROJECTS.items():
        # Hiển thị tên Dự án (Cha)
        st.markdown(f"<div class='nav-header'>{p_info['name']}</div>", unsafe_allow_html=True)
        
        # Xác định vị trí tab hiện tại để tô màu đúng
        active_idx = p_info['tabs'].index(st.session_state['current_tab_name']) if st.session_state['current_proj_id'] == p_id else -1
        
        # Hiển thị Menu tính năng (Con)
        sel_tab = option_menu(
            menu_title=None,
            options=p_info['tabs'],
            icons=["speedometer2", "link-45deg", "globe2", "image", "arrow-repeat", "geo-alt", "bar-chart"] if "P" in p_id else ["people", "shield-lock"],
            key=f"menu_{p_id}", # Key duy nhất cho từng dự án
            default_index=active_idx,
            styles={
                "container": {"background-color": "transparent", "padding": "0px"},
                "nav-link": {"font-size": "13px", "color": "#888", "text-align": "left", "height": "38px", "padding-left": "20px"},
                "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700"},
            }
        )
        
        # Chỉ kích hoạt chuyển đổi khi Ní bấm vào tab khác dự án hiện tại
        if sel_tab and (st.session_state['current_tab_name'] != sel_tab or st.session_state['current_proj_id'] != p_id):
            st.session_state['current_proj_id'] = p_id
            st.session_state['current_tab_name'] = sel_tab
            st.rerun()

# =================================================================
# 4. 🖼️ KHU VỰC HIỂN THỊ DỮ LIỆU CHÍNH
# =================================================================
with main_col:
    p_id = st.session_state['current_proj_id']
    t_name = st.session_state['current_tab_name']
    data_key = f"df_{p_id}_{t_name}"
    
    # Tiêu đề Header
    st.markdown(f"### {PROJECTS[p_id]['name']} <span style='color:#888; font-size:18px;'>/ {t_name}</span>", unsafe_allow_html=True)
    
    # Toolbar chức năng
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns([1, 1, 2.5])
    with t1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.toast(f"Đã lưu {t_name}!")
    with t2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.toast(f"Đã kéo dữ liệu {t_name} về!")
    
    st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

    # Hiển thị bảng Editor chuẩn Template
    if data_key in st.session_state:
        st.session_state[data_key] = st.data_editor(
            st.session_state[data_key],
            use_container_width=True,
            num_rows="dynamic",
            height=650,
            hide_index=True,
            column_config={
                "Giá trị thực tế": st.column_config.TextColumn(width="large"),
                "Bộ Spin": st.column_config.TextColumn(width="large")
            }
        )
    else:
        st.warning("Đang tải dữ liệu...")

st.caption(f"🚀 v5500.0 | Multi-Project Architecture | Nested UI Fixed | Full Templates Restored")
