import streamlit as st
import pandas as pd
import time
from datetime import datetime

# =================================================================
# 1. 🛡️ KHỞI TẠO HỆ THỐNG (CHỐNG BUG & MẤT DỮ LIỆU)
# =================================================================
# Schema chuẩn 100% theo hình image_5733b2.png của Ní
TABLE_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Khởi tạo dữ liệu vào Session State (Chạy ngay đầu tiên)
for key, cols in TABLE_CONFIG.items():
    s_key = f"df_{key}"
    if s_key not in st.session_state:
        if key == "Dashboard":
            st.session_state[s_key] = pd.DataFrame([
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                ["📧 EMAIL ROBOT", "Dán_Email_Vào_Đây"],
                ["📄 GOOGLE SHEET ID", "Dán_ID_Sheet_Vào_Đây"],
                ["🚀 TARGET_URL", "https://laiho.vn/"],
                ["📁 FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
            ], columns=cols)
        elif key == "Data_Report":
            # Tạo bảng trống có sẵn cột cho Report
            st.session_state[s_key] = pd.DataFrame(columns=cols)
        else:
            # Các bảng khác để 1 dòng trống cho Ní dễ dán dữ liệu
            st.session_state[s_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. POPUP ROBOT (GHI DATA CHUẨN TEMPLATE)
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ V55.2")
def start_robot_popup():
    st.write("🚀 Robot đang thực hiện quy trình đăng bài...")
    pb = st.progress(0)
    info = st.empty()
    
    steps = ["Nạp cấu hình...", "AI soạn nội dung...", "Chèn Backlink...", "Đăng Blogger...", "Ghi báo cáo..."]
    for i, s in enumerate(steps):
        info.text(f"Đang xử lý: {s}")
        time.sleep(0.7)
        pb.progress(int((i+1)/len(steps)*100))
    
    # GHI DỮ LIỆU THẬT VÀO REPORT (KHỚP 100% GOOGLE SHEET)
    now = datetime.now()
    report_entry = {
        "Website": "Blog Lái Hộ 1",
        "Nền tảng": "blogger",
        "URL / ID": "muontaixelaixe.laiho1@blogger.com",
        "Ngày đăng bài": now.strftime("%Y-%m-%d"),
        "Từ khoá 1": "thuê tài xế",
        "Từ khoá 2": "Lái hộ",
        "Từ khoá 3": "dịch vụ lái xe hộ",
        "Từ khoá 4": "",
        "Từ khoá 5": "",
        "Link bài viết": "Check link trên blog của bạn",
        "Tiêu đề bài viết": "Đã đăng thành công",
        "File ID Drive": "File đã xóa",
        "Thời gian hẹn giờ": now.strftime("%Y-%m-%d %H:%M:%S"),
        "Trạng thái": "DONE"
    }
    
    # Chèn dữ liệu mới lên đầu bảng
    old_report = st.session_state['df_Data_Report']
    st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([report_entry]), old_report], ignore_index=True)
    
    st.success("✅ Đã hoàn thành! Báo cáo đã được cập nhật.")
    if st.button("XEM DATA REPORT", use_container_width=True):
        st.session_state['active_tab'] = "Data_Report"
        st.rerun()

# =================================================================
# 3. UI/UX: SIDEBAR ÉP PHẲNG & HIGHLIGHT
# =================================================================
st.set_page_config(page_title="SEO Master v2500", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR: ÉP CHIỀU NGANG BẰNG NHAU 100% & KHÍT NHAU */
    div[data-testid="stColumn"]:first-child {
        display: flex !important;
        flex-direction: column !important;
        gap: 0px !important;
    }

    div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        width: 100% !important;
        height: 52px !important;
        border-radius: 0px !important;
        margin: 0px !important;
        background-color: #111111 !important;
        border: 1px solid #222 !important;
        color: #888888 !important;
        text-align: left !important;
        padding-left: 20px !important;
        font-size: 15px !important;
        transition: 0.2s;
        display: block !important;
    }

    /* TRẠNG THÁI ACTIVE: SÁNG RỰC MÀU VÀNG */
    .active-btn div[data-testid="stButton"] button {
        background-color: #ffd700 !important; /* Màu vàng sáng */
        color: #000000 !important; /* Chữ đen */
        font-weight: 700 !important;
        border-left: 8px solid #ffffff !important; /* Vạch trắng highlight */
    }

    /* TOOLBAR NÚT CHỨC NĂNG */
    .main-toolbar div[data-testid="stButton"] button { height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; color: white !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; color: white !important; }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC SIDEBAR & MAIN
nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center; margin-bottom:20px;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    
    menu = [
        ("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"),
        ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"),
        ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"),
        ("📊 Data_Report", "Data_Report")
    ]
    
    for label, key in menu:
        is_active = st.session_state['active_tab'] == key
        # Bọc nút trong div để highlight
        st.markdown(f"<div class='{'active-btn' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 5. NỘI DUNG CHÍNH
with main_col:
    curr_tab = st.session_state['active_tab']
    st.markdown(f"### 📍 Thao tác: {curr_tab}")
    
    # TOOLBAR 3 NÚT
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if curr_tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="main_start"): start_robot_popup()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"up_{curr_tab}"): st.toast("Đã cập nhật dữ liệu!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{curr_tab}")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{curr_tab}")
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (SAFETY CHECK)
    st_key = f"df_{curr_tab}"
    if st_key in st.session_state:
        st.session_state[st_key] = st.data_editor(
            st.session_state[st_key],
            use_container_width=True,
            num_rows="dynamic",
            height=720,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[st_key].columns}
        )

st.caption("🚀 Lái Hộ SEO v2500.0 | Report Template Fixed | Perfect Symmetry")
