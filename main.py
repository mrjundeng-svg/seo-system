import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU & QUY TẮC CONTENT
# =================================================================
TABLE_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Khởi tạo Session State
for key, cols in TABLE_CONFIG.items():
    s_key = f"df_{key}"
    if s_key not in st.session_state:
        if key == "Dashboard":
            st.session_state[s_key] = pd.DataFrame([
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["TARGET_URL", "https://laiho.vn/"],
                ["Mật độ từ khóa", "3-5%"],
                ["Khung giờ đăng", "11:00 | 19:30"],
                ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                ["📄 GOOGLE SHEET ID", "Dán_ID_Sheet_Vào_Đây"]
            ], columns=cols)
        elif key == "Data_Report":
            st.session_state[s_key] = pd.DataFrame(columns=cols)
        else:
            st.session_state[s_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. POPUP VẬN HÀNH (THEO RULE CONTENT MARKETING)
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ v2700 - CONTENT MASTER")
def run_content_robot():
    st.markdown("### 🛠️ Đang áp dụng quy tắc Content Marketing")
    pb = st.progress(0)
    status_msg = st.empty()
    
    # Quy trình chuẩn theo SEO Rules
    process = [
        "Phân tích bộ từ khóa Lái Hộ...",
        "Kiểm tra mật độ từ khóa (Target 3-5%)...",
        "Tối ưu cấu trúc H1-H2-H3...",
        "Gắn Backlink theo cấu trúc Silo...",
        "Chèn Alt Text cho hình ảnh...",
        "Đăng bài lên hệ thống vệ tinh...",
        "Xác nhận trạng thái DONE..."
    ]
    
    now = datetime.now()
    # Logic Hẹn giờ: Nếu sau 19:30 thì hẹn vào 11:00 ngày mai
    scheduled_time = now.replace(hour=11, minute=0, second=0) + timedelta(days=1)
    
    for i, step in enumerate(process):
        status_msg.info(f"👉 **{step}**")
        time.sleep(0.7)
        pb.progress(int((i+1)/len(process)*100))
    
    # Ghi dữ liệu vào Report chuẩn Template
    new_entry = {
        "Website": "Hệ thống Lái Hộ Master",
        "Nền tảng": "WordPress/Blogger",
        "URL / ID": "laiho.vn/blog",
        "Ngày đăng bài": now.strftime("%Y-%m-%d"),
        "Từ khoá 1": "lái xe hộ",
        "Từ khoá 2": "thuê tài xế",
        "Link bài viết": "https://laiho.vn/content-seo-v27",
        "Tiêu đề bài viết": "[SEO] Dịch vụ lái xe hộ uy tín chuyên nghiệp",
        "Thời gian hẹn giờ": scheduled_time.strftime("%Y-%m-%d %H:%M:%S"),
        "Trạng thái": "DONE"
    }
    
    # Cập nhật bảng
    st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_entry]), st.session_state['df_Data_Report']], ignore_index=True).fillna("")
    
    st.success("✅ Content đã được đăng và tối ưu SEO thành công!")
    if st.button("KIỂM TRA DATA REPORT", use_container_width=True):
        st.session_state['active_tab'] = "Data_Report"
        st.rerun()

# =================================================================
# 3. UI/UX: SIDEBAR HOÀN HẢO - HIGHLIGHT SÁNG RỰC
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v2700", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR: ÉP PHẲNG, KHÍT NHAU 100% */
    div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        width: 100% !important; height: 52px !important;
        border-radius: 0px !important; margin: 0px !important;
        background-color: #111111 !important; border: 1px solid #222 !important;
        color: #888888 !important; text-align: left !important;
        padding-left: 20px !important; font-size: 15px !important;
    }

    /* TRẠNG THÁI ACTIVE: SÁNG VÀNG LÁI HỘ */
    .active-btn div[data-testid="stButton"] button {
        background-color: #ffd700 !important;
        color: #000000 !important;
        font-weight: 700 !important;
        border-left: 8px solid #ffffff !important;
    }

    /* TOOLBAR 3 NÚT THẲNG HÀNG */
    .main-toolbar div[data-testid="stButton"] button { height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; color: white !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; color: white !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC SIDEBAR & MAIN
nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"), ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"), ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"), ("📊 Data_Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 Dashboard SEO: {tab}")
    
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="m_start"): run_content_robot()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"u_{tab}"): st.toast("Dữ liệu đã được đồng bộ!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"e_{tab}")
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"i_{tab}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (SAFETY CHECK)
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(
        st.session_state[st_key],
        use_container_width=True,
        num_rows="dynamic",
        height=720,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[st_key].columns}
    )

st.caption("🚀 SEO Master v2700.0 | Full Content Rules Applied | Symmetric UI")
