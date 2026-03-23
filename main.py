import streamlit as st
import pandas as pd
import time

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (NÍ DÁN DỮ LIỆU THẬT VÀO ĐÂY LÀ KHÔNG BAO GIỜ MẤT)
# =================================================================
# [GỢI Ý]: Ní dán 1 lần vào đây, sau này update code UI thoải mái dữ liệu vẫn còn.

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

if 'df_Data_Backlink' not in st.session_state:
    st.session_state['df_Data_Backlink'] = pd.DataFrame([
        ["lái xe hộ", "https://laiho.vn", "0"],
        ["thuê tài xế", "https://laiho.vn/thue-xe", "0"]
        # Ní có thể dán thêm các dòng dữ liệu thật của Ní ở đây...
    ], columns=["Từ khoá", "Website đích", "Đã dùng"])

if 'df_Data_Website' not in st.session_state:
    st.session_state['df_Data_Website'] = pd.DataFrame([
        ["Blog Lái Hộ", "Blogger", "123456789", "", "", "Bật", "5"]
    ], columns=["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"])

# Khởi tạo các bảng khác trắng tinh
SCHEMA = {
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}
for k, cols in SCHEMA.items():
    if f'df_{k}' not in st.session_state:
        st.session_state[f'df_{k}'] = pd.DataFrame([[""] * len(cols)], columns=cols)

# =================================================================
# 2. POPUP ĐANG CHẠY (MODAL DIALOG)
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ ĐANG VẬN HÀNH")
def run_robot_popup():
    st.write("⚠️ **Đừng đóng trình duyệt nhé, Robot đang cày SEO cho Ní...**")
    progress_text = st.empty()
    bar = st.progress(0)
    steps = ["Nạp cấu hình...", "Gọi Gemini AI...", "Viết nội dung...", "Chèn link...", "Đăng bài...", "Gửi Mail..."]
    for i, s in enumerate(steps):
        progress_text.markdown(f"**Đang làm:** {s}")
        for p in range(i*16, (i+1)*16):
            time.sleep(0.04)
            bar.progress(min(p, 100))
        if st.button(f"❌ CANCEL (Dừng ở bước {i+1})", use_container_width=True):
            st.warning("Đã dừng Robot!")
            time.sleep(1)
            st.rerun()
    bar.progress(100)
    st.success("✅ XONG RỒI NÍ ƠI!")
    if st.button("ĐÓNG", use_container_width=True): st.rerun()

# =================================================================
# 3. UI/UX: NÚT KHÍT NHAU, BẰNG NHAU, ICON MÀU
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v2100", page_icon=" taxi", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT KHÍT NHAU & BẰNG NHAU */
    .nav-btn button {
        width: 100% !important; height: 50px !important;
        text-align: left !important; background-color: #111111 !important;
        border: 1px solid #222 !important; border-radius: 0px !important;
        margin-bottom: -1px !important; color: #ffffff !important;
        font-weight: 600 !important; font-size: 15px !important;
    }
    .active-tab button { background-color: #1a1a1a !important; border-left: 6px solid #ffd700 !important; color: #ffd700 !important; }

    /* TOOLBAR 3 NÚT: CHIA ĐỀU 1/3, THẲNG HÀNG, SÁT NHAU */
    .stButton>button { width: 100% !important; height: 48px !important; border-radius: 4px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; }
    .btn-blue button { background-color: #0055ff !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 4. BỐ CỤC SIDEBAR CỐ ĐỊNH
nav_col, main_col = st.columns([1, 4.2], gap="small")
with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"), ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"), ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"), ("📊 Data_Report", "Data_Report")]
    for label, key in menu:
        style = "active-tab" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='nav-btn {style}'>", unsafe_allow_html=True)
        if st.button(label, key=f"n_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 5. NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR 3 NÚT THẲNG HÀNG, BẰNG NHAU
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): run_robot_popup()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", use_container_width=True): st.toast("Đã nạp dữ liệu từ Code!")
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
    
    # BẢNG DỮ LIỆU (KHÔNG HIỆN INDEX)
    state_key = f"df_{tab}"
    st.session_state[state_key] = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        num_rows="dynamic",
        height=720,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[state_key].columns}
    )

st.caption("🚀 Lái Hộ SEO v2100.0 | Permanent Data Vault | Popup UI")
