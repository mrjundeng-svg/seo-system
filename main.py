import streamlit as st
import pandas as pd
import time

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (NÍ DÁN DỮ LIỆU THẬT VÀO ĐÂY)
# =================================================================
if 'df_Dashboard' not in st.session_state:
    st.session_state['df_Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
        ["📧 EMAIL ROBOT (Service Account)", "Dán_Email_Vào_Đây"],
        ["📄 GOOGLE SHEET ID", "Dán_ID_Sheet_Vào_Đây"],
        ["🚀 TARGET_URL", "https://laiho.vn/"],
        ["📁 FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

# Khởi tạo các bảng khác trắng tinh (Ní dán dữ liệu thật vào đây nếu cần)
TABLE_KEYS = ["Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
SCHEMA = {
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}
for k in TABLE_KEYS:
    if f'df_{k}' not in st.session_state:
        st.session_state[f'df_{k}'] = pd.DataFrame([[""] * len(SCHEMA[k])], columns=SCHEMA[k])

# =================================================================
# 2. UI/UX: CHỈNH SIDEBAR BẰNG NHAU & HIGHLIGHT SÁNG RỰC
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v2200", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* ÉP NÚT SIDEBAR FULL CHIỀU NGANG & KHÍT NHAU */
    .nav-btn div[data-testid="stButton"] button {
        width: 100% !important;
        height: 50px !important;
        border-radius: 0px !important;
        margin: 0px !important;
        background-color: #111111 !important;
        border: 1px solid #222 !important;
        color: #ffffff !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-weight: 500 !important;
    }

    /* TRẠNG THÁI NÚT ĐANG CHỌN - SÁNG LÊN */
    .active-tab div[data-testid="stButton"] button {
        background-color: #ffd700 !important; /* Màu Vàng Lái Hộ */
        color: #000000 !important; /* Chữ đen cho nổi */
        font-weight: 700 !important;
        border-left: 8px solid #ffffff !important; /* Thêm vạch trắng bên trái cho chất */
    }

    /* TOOLBAR 3 NÚT Ở MAIN CONTENT */
    .main-toolbar div[data-testid="stButton"] button {
        width: 100% !important;
        height: 48px !important;
        font-weight: 700 !important;
    }
    .btn-red button { background-color: #ff0000 !important; color: white !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; color: white !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 3. POPUP ĐANG CHẠY
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ ĐANG CHẠY")
def run_robot_popup():
    st.write("🚀 Robot v55.0 đang xử lý SEO cho Ní...")
    bar = st.progress(0)
    for i in range(100):
        time.sleep(0.03)
        bar.progress(i + 1)
    st.success("✅ HOÀN THÀNH!")
    if st.button("ĐÓNG", use_container_width=True): st.rerun()

# =================================================================
# 4. BỐ CỤC 2 CỘT
# =================================================================
nav_col, main_col = st.columns([1, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center; margin-bottom:20px;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    
    menu = [
        ("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"),
        ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"),
        ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"),
        ("📊 Data_Report", "Data_Report")
    ]
    
    # RENDER MENU VỚI LOGIC HIGHLIGHT
    for label, key in menu:
        is_active = st.session_state['active_tab'] == key
        # Dùng container để áp class CSS
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"btn_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR 3 NÚT THẲNG HÀNG
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="start_main"): run_robot_popup()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"up_{tab}"): st.toast("Đã cập nhật!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{tab}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

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

st.caption("🚀 SEO Master v2200.0 | Full-Width Sidebar | Active Highlight")
