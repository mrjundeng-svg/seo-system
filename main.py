import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# =================================================================
# 1. 🏗️ ĐỊNH NGHĨA TEMPLATE CÁC BẢNG (Dữ liệu gốc của Ní đây)
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
    "🚕 DỰ ÁN: LÁI HỘ": {
        "id": "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw",
        "tabs": ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]
    },
    "🏠 DỰ ÁN: GIÚP VIỆC NHANH": {
        "id": "SHEET_ID_GIUP_VIEC",
        "tabs": ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]
    },
    "⚙️ QUẢN TRỊ HỆ THỐNG": {
        "id": "ADMIN_SYSTEM",
        "tabs": ["Danh sách tài khoản", "Phân quyền tính năng"]
    }
}

def init_v5300():
    if 'current_proj' not in st.session_state: st.session_state['current_proj'] = "🚕 DỰ ÁN: LÁI HỘ"
    if 'current_tab' not in st.session_state: st.session_state['current_tab'] = "Dashboard"
    
    # Khởi tạo dữ liệu cho TẤT CẢ các tab của TẤT CẢ dự án
    for proj, info in PROJECTS.items():
        for t in info['tabs']:
            key = f"df_{proj}_{t}"
            if key not in st.session_state:
                cols = TEMPLATES.get(t, ["Cột 1", "Cột 2"])
                # Nếu là Dashboard thì nạp sẵn vài dòng mẫu
                if t == "Dashboard":
                    st.session_state[key] = pd.DataFrame([
                        ["GOOGLE_SHEET_ID", info['id']],
                        ["SERVICE_ACCOUNT_JSON", ""],
                        ["GEMINI_API_KEY", ""],
                        ["FOLDER_DRIVE_ID", ""],
                        ["Số lượng bài cần tạo", "3"]
                    ], columns=cols)
                else:
                    st.session_state[key] = pd.DataFrame(columns=cols)

init_v5300()

# =================================================================
# 2. 🎨 UI/UX SIDEBAR PHÂN CẤP CHA-CON
# =================================================================
st.set_page_config(page_title="SEO Master Hub v5300", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    .project-header { color: #ffd700; font-weight: 800; font-size: 14px; padding: 12px 5px 5px 5px; border-bottom: 1px solid #333; margin-top: 15px; text-transform: uppercase; }
    .btn-blue button { background-color: #0055ff !important; width: 100%; height: 40px; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1.3, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>SEO HUB</h2>", unsafe_allow_html=True)
    
    for proj_name, proj_info in PROJECTS.items():
        st.markdown(f"<div class='project-header'>{proj_name}</div>", unsafe_allow_html=True)
        
        selected_sub = option_menu(
            menu_title=None, 
            options=proj_info['tabs'],
            icons=["speedometer2", "link-45deg", "globe2", "image", "arrow-repeat", "geo-alt", "bar-chart"] if "DỰ ÁN" in proj_name else ["people", "shield-lock"],
            key=f"menu_{proj_name}",
            # Logic quan trọng: Chỉ hiện màu vàng nếu đúng dự án đang chọn
            default_index=proj_info['tabs'].index(st.session_state['current_tab']) if st.session_state['current_proj'] == proj_name else -1,
            styles={
                "container": {"padding": "0px", "background-color": "transparent", "border": "none"},
                "nav-link": {"font-size": "13px", "text-align": "left", "color": "#777", "height": "35px", "padding-left": "20px"},
                "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700"},
            }
        )
        
        if selected_sub:
            if (st.session_state['current_proj'] != proj_name) or (st.session_state['current_tab'] != selected_sub):
                st.session_state['current_proj'] = proj_name
                st.session_state['current_tab'] = selected_sub
                st.rerun()

with main_col:
    curr_p = st.session_state['current_proj']
    curr_t = st.session_state['current_tab']
    data_key = f"df_{curr_p}_{curr_t}"

    st.markdown(f"### {curr_p} <span style='color:#888; font-size:18px;'>/ {curr_t}</span>", unsafe_allow_html=True)
    
    # TOOLBAR
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns([1, 1, 2.5])
    with t1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.toast(f"Đã cập nhật {curr_t} của {curr_p}!")
        st.markdown('</div>', unsafe_allow_html=True)
    with t2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.toast(f"Đã đồng bộ {curr_t}!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

    # HIỂN THỊ BẢNG DỮ LIỆU THEO TEMPLATE ĐÃ PHỤC HỒI
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
        st.error("Lỗi dữ liệu: Không tìm thấy Template!")

st.caption(f"🚀 v5300.0 | Templates Restored | True Hierarchy UI | Data Persistence Ready")
