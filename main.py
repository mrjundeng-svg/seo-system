import streamlit as st
import pandas as pd

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (DỮ LIỆU CHỐT HẠ)
# =================================================================
if 'df_Dashboard' not in st.session_state:
    st.session_state['df_Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
        ["📧 EMAIL ROBOT (Cấp quyền Editor trong Sheet)", "Dán_Email_Robot_Vào_Đây"],
        ["📄 GOOGLE SHEET ID", "Dán_ID_File_Sheet_Vào_Đây"],
        ["🚀 TARGET_URL", "https://laiho.vn/"],
        ["📁 FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

# Các bảng khác giữ nguyên logic cũ của Ní
OTHERS = {
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}
for k, cols in OTHERS.items():
    if f'df_{k}' not in st.session_state:
        st.session_state[f'df_{k}'] = pd.DataFrame([[""] * len(cols)], columns=cols)

# =================================================================
# 2. UI/UX: NÚT KHÍT NHAU, BẰNG NHAU, ICON MÀU
# =================================================================
st.set_page_config(page_title="Lái Hộ SEO v1800", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT BẰNG NHAU & KHÍT RẠT NHAU */
    .nav-btn button {
        width: 100% !important; height: 50px !important;
        text-align: left !important; background-color: #111111 !important;
        border: 1px solid #222 !important; border-radius: 0px !important;
        margin: 0px !important; color: #ffffff !important;
        font-weight: 600 !important; font-size: 15px !important;
    }
    .active-tab button { background-color: #1a1a1a !important; border-left: 6px solid #ffd700 !important; color: #ffd700 !important; }

    /* TOOLBAR 3 NÚT: CHIA ĐỀU 1/3, THẲNG HÀNG */
    .stButton>button { width: 100% !important; height: 48px !important; border-radius: 4px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; color: #fff !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; }
    .btn-blue button { background-color: #0055ff !important; color: #fff !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 3. BỐ CỤC SIDEBAR CỐ ĐỊNH
nav_col, main_col = st.columns([1, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    menu = [
        ("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"),
        ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"),
        ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"),
        ("📊 Data_Report", "Data_Report")
    ]
    for label, key in menu:
        is_active = st.session_state['active_tab'] == key
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"n_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 4. NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR 3 NÚT THẲNG HÀNG, SÁT NHAU
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            st.button("🔥 START ROBOT", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            st.button("🔄 UPDATE DB", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # BẢNG DỮ LIỆU
    state_key = f"df_{tab}"
    st.session_state[state_key] = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        num_rows="dynamic",
        height=720,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[state_key].columns}
    )

st.caption("🚀 Lái Hộ SEO v1800.0 | Robot Identity Ready")
