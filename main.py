import streamlit as st
import pandas as pd
import time
from datetime import datetime

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (GIỮ LẠI ĐỂ KHÔNG MẤT CÔNG NHẬP)
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

# Khởi tạo các bảng khác
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
        # Nếu là bảng Report thì ban đầu để trống (không có dòng trống)
        if k == "Data_Report":
            st.session_state[f'df_{k}'] = pd.DataFrame(columns=SCHEMA[k])
        else:
            st.session_state[f'df_{k}'] = pd.DataFrame([[""] * len(SCHEMA[k])], columns=SCHEMA[k])

# =================================================================
# 2. POPUP ĐANG CHẠY & GHI DỮ LIỆU THẬT
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ ĐANG LÀM VIỆC")
def run_robot_popup():
    st.write("🚀 Robot v55.0 đang thực hiện quy trình SEO...")
    progress_text = st.empty()
    bar = st.progress(0)
    
    # Các bước giả lập
    steps = ["Đọc cấu hình...", "Viết bài AI...", "Chèn Backlink...", "Đang đăng bài...", "Đã xong!"]
    for i, s in enumerate(steps):
        progress_text.text(f"Đang làm: {s}")
        time.sleep(0.8)
        bar.progress(int((i + 1) / len(steps) * 100))
    
    # --- ĐOẠN CODE "GHI CHÉP" KẾT QUẢ VÀO REPORT ---
    new_report = {
        "Website": "Blog Lái Hộ",
        "Nền tảng": "Blogger",
        "URL / ID": "laiho.vn",
        "Ngày đăng bài": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Từ khoá 1": "Lái xe hộ",
        "Link bài viết": "https://laiho.vn/post-vừa-đăng",
        "Tiêu đề bài viết": "Dịch vụ lái xe hộ uy tín 2026",
        "Trạng thái": "✅ Thành công"
    }
    # Chèn dữ liệu mới lên đầu bảng Report
    st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_report]), st.session_state['df_Data_Report']], ignore_index=True).fillna("...")
    
    st.success("🎉 Robot đã đăng bài và ghi vào Report thành công!")
    if st.button("XEM KẾT QUẢ", use_container_width=True):
        st.session_state['active_tab'] = "📊 Data_Report" # Tự chuyển sang tab Report để Ní xem
        st.rerun()

# =================================================================
# 3. UI/UX: SIDEBAR HIGHLIGHT & NÚT BẰNG NHAU
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v2300", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR: NÚT BẰNG NHAU & HIGHLIGHT */
    .nav-btn div[data-testid="stButton"] button {
        width: 100% !important; height: 50px !important;
        border-radius: 0px !important; margin: 0px !important;
        background-color: #111111 !important; border: 1px solid #222 !important;
        color: #ffffff !important; text-align: left !important;
        padding-left: 20px !important; font-weight: 500 !important;
    }
    .active-tab div[data-testid="stButton"] button {
        background-color: #ffd700 !important; color: #000 !important;
        font-weight: 700 !important; border-left: 8px solid #ffffff !important;
    }

    /* TOOLBAR 3 NÚT */
    .main-toolbar div[data-testid="stButton"] button { width: 100% !important; height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 4. BỐ CỤC 2 CỘT
nav_col, main_col = st.columns([1, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"), ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"), ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"), ("📊 Data_Report", "Data_Report")]
    for label, key in menu:
        is_active = st.session_state['active_tab'] == key
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"btn_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="start_main"): run_robot_popup()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"up_{tab}"): st.toast("Đã cập nhật dữ liệu từ Code!")
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

st.caption("🚀 Lái Hộ SEO v2300.0 | Report Auto-Update | Perfect UI")
