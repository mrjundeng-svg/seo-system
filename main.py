import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu

# =================================================================
# 1. 🏗️ CẤU TRÚC DỮ LIỆU ĐA DỰ ÁN
# =================================================================
# Định nghĩa các dự án và các tính năng con bên trong
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

def init_v5200():
    if 'current_proj' not in st.session_state: st.session_state['current_proj'] = "🚕 DỰ ÁN: LÁI HỘ"
    if 'current_tab' not in st.session_state: st.session_state['current_tab'] = "Dashboard"

init_v5200()

# =================================================================
# 2. 🎨 GIAO DIỆN SIDEBAR TÁCH BIỆT CHA - CON
# =================================================================
st.set_page_config(page_title="SEO Multi-Project Hub", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    [data-testid="stSidebar"] { display: none !important; }
    /* Style cho tiêu đề Cha */
    .project-header {
        color: #ffd700; font-weight: 800; font-size: 14px;
        padding: 10px 5px; border-bottom: 1px solid #222; margin-top: 10px;
    }
    .btn-blue button { background-color: #0055ff !important; width: 100%; height: 40px; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1.3, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>SEO HUB</h2>", unsafe_allow_html=True)
    
    # Duyệt qua từng dự án (Cha)
    for proj_name, proj_info in PROJECTS.items():
        # Tạo tiêu đề Cha
        st.markdown(f"<div class='project-header'>{proj_name}</div>", unsafe_allow_html=True)
        
        # Tạo Menu Con cho từng Cha
        # Dùng key duy nhất cho mỗi menu để không bị đụng hàng
        selected_sub = option_menu(
            menu_title=None, 
            options=proj_info['tabs'],
            icons=["speedometer2", "link-45deg", "globe2", "image", "arrow-repeat", "geo-alt", "bar-chart"] if "DỰ ÁN" in proj_name else ["people", "shield-lock"],
            default_index=0 if st.session_state['current_proj'] == proj_name else -1, # Tự động bỏ chọn nếu không phải dự án đang dùng
            key=f"menu_{proj_name}",
            styles={
                "container": {"padding": "0px", "background-color": "transparent", "border": "none"},
                "nav-link": {"font-size": "12px", "text-align": "left", "color": "#888", "height": "35px", "padding-left": "20px"},
                "nav-link-selected": {"background-color": "#ffd700", "color": "#000", "font-weight": "700"},
            }
        )
        
        # Cập nhật trạng thái khi Ní bấm vào con của bất kỳ cha nào
        if selected_sub:
            # Kiểm tra xem có phải vừa bấm vào menu mới không
            # (Phải dùng logic này vì streamlit render lại toàn bộ khi có tương tác)
            if (st.session_state['current_proj'] != proj_name) or (st.session_state['current_tab'] != selected_sub):
                st.session_state['current_proj'] = proj_name
                st.session_state['current_tab'] = selected_sub
                # Lưu ý: do giới hạn của thư viện menu, việc reset index menu khác cần xử lý rerun
                # st.rerun() 

with main_col:
    curr_p = st.session_state['current_proj']
    curr_t = st.session_state['current_tab']
    sheet_id = PROJECTS[curr_p]['id']

    st.markdown(f"### {curr_p} <span style='color:#888; font-size:18px;'>/ {curr_t}</span>", unsafe_allow_html=True)
    st.caption(f"🔑 Kết nối Sheet ID: `{sheet_id}`")

    # TOOLBAR (ĐỒNG BỘ)
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns([1, 1, 2.5])
    with t1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.toast("Đã cập nhật!")
        st.markdown('</div>', unsafe_allow_html=True)
    with t2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE CLOUD"): st.toast("Đã đồng bộ!")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

    # KHU VỰC HIỂN THỊ DỮ LIỆU
    st.write(f"Đang hiển thị dữ liệu cho dự án: **{curr_p}** - Tab: **{curr_t}**")
    st.data_editor(pd.DataFrame(columns=["Thông tin", "Giá trị"]), use_container_width=True, num_rows="dynamic")

st.caption(f"🚀 v5200.0 | True Hierarchy | Parent-Child Relationship | Multi-Project Hub")
