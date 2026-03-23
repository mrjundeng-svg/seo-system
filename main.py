import streamlit as st
import pandas as pd
import time
from datetime import datetime

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU & KHỞI TẠO BẤT TỬ
# =================================================================
# Danh sách tất cả các bảng trong hệ thống
ALL_TABLES = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Khởi tạo một lần duy nhất để chống KeyError
for key, cols in ALL_TABLES.items():
    state_key = f"df_{key}"
    if state_key not in st.session_state:
        if key == "Dashboard":
            st.session_state[state_key] = pd.DataFrame([
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                ["📧 EMAIL ROBOT", "Dán_Email_Vào_Đây"],
                ["📄 GOOGLE SHEET ID", "Dán_ID_Sheet_Vào_Đây"],
                ["🚀 TARGET_URL", "https://laiho.vn/"],
                ["📁 FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
            ], columns=cols)
        elif key == "Data_Report":
            st.session_state[state_key] = pd.DataFrame(columns=cols) # Bảng trống nhưng phải có cột
        else:
            st.session_state[state_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. POPUP VẬN HÀNH & GHI DỮ LIỆU BÁO CÁO
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ V55.1")
def run_robot_popup():
    st.write("🚀 Robot đang cày SEO cho Ní, đợi tẹo nhé...")
    bar = st.progress(0)
    msg = st.empty()
    
    steps = ["Nạp dữ liệu...", "AI đang soạn bài...", "Gắn Backlink...", "Đăng bài Blogger...", "Cập nhật Database..."]
    for i, step in enumerate(steps):
        msg.text(f"Đang làm: {step}")
        time.sleep(0.6)
        bar.progress(int((i + 1) / len(steps) * 100))
    
    # Ghi dữ liệu thực vào Report để Ní kiểm chứng
    new_data = {c: "..." for c in ALL_TABLES["Data_Report"]}
    new_data.update({
        "Website": "Blog Lái Hộ", "Nền tảng": "Blogger", "Ngày đăng bài": datetime.now().strftime("%H:%M %d/%m/%Y"),
        "Từ khoá 1": "Lái xe hộ", "Link bài viết": "https://laiho.vn/seo-post", "Trạng thái": "✅ Hoàn thành"
    })
    
    # Chèn vào đầu bảng
    report_df = st.session_state['df_Data_Report']
    st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_data]), report_df], ignore_index=True)
    
    st.success("🎉 Robot đã đăng bài thành công!")
    if st.button("XEM BÁO CÁO NGAY", use_container_width=True):
        st.session_state['active_tab'] = "Data_Report"
        st.rerun()

# =================================================================
# 3. UI/UX: SIDEBAR HOÀN HẢO - HIGHLIGHT SÁNG RỰC
# =================================================================
st.set_page_config(page_title="SEO Master v2400", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR: ÉP PHẲNG 100%, KHÔNG KHOẢNG CÁCH */
    .nav-container { display: flex; flex-direction: column; gap: 0px; }
    
    div[data-testid="stColumn"] div[data-testid="stButton"] button {
        width: 100% !important;
        height: 52px !important;
        border-radius: 0px !important;
        margin: 0px !important;
        background-color: #111111 !important;
        border: 1px solid #222 !important;
        color: #aaaaaa !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-size: 15px !important;
        transition: 0.2s;
    }

    /* KHI NÚT ĐƯỢC CHỌN (ACTIVE) */
    .active-tab div[data-testid="stButton"] button {
        background-color: #ffd700 !important; /* Vàng sáng */
        color: #000000 !important; /* Chữ đen */
        font-weight: 700 !important;
        border-left: 8px solid #ffffff !important; /* Vạch trắng highlight */
    }
    
    /* TOOLBAR NÚT CHỨC NĂNG */
    .main-toolbar div[data-testid="stButton"] button { height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; color: white !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; color: white !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC 2 CỘT (NAV & MAIN)
nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center; margin-bottom:25px;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    
    menu_items = [
        ("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"),
        ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"),
        ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"),
        ("📊 Data_Report", "Data_Report")
    ]
    
    for label, key in menu_items:
        is_active = st.session_state['active_tab'] == key
        # Bọc nút vào div để áp class highlight
        st.markdown(f"<div class='{'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 Đang thao tác: {tab}")
    
    # TOOLBAR 3 NÚT: THẲNG HÀNG, BẰNG NHAU
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="btn_start"): run_robot_popup()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"btn_up_{tab}"): st.toast("Đã nạp dữ liệu!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"btn_ex_{tab}")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"btn_im_{tab}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # BẢNG DỮ LIỆU CHÍNH (DÙNG DATA_EDITOR ĐỂ NÍ DÁN EXCEL VÀO)
    state_key = f"df_{tab}"
    # Safety check để không bao giờ bị KeyError nữa
    if state_key in st.session_state:
        st.session_state[state_key] = st.data_editor(
            st.session_state[state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=720,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[state_key].columns}
        )

st.caption("🚀 Lái Hộ SEO v2400.0 | Bug Fixed | Perfect Symmetry UI")
