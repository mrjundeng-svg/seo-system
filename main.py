import streamlit as st
import pandas as pd
import time

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (KHÔNG ĐỔI)
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
        st.session_state[f'df_{k}'] = pd.DataFrame([[""] * len(SCHEMA[k])], columns=SCHEMA[k])

# =================================================================
# 2. POPUP ĐANG CHẠY (MODAL DIALOG)
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ V55.0 ĐANG VẬN HÀNH")
def run_robot_logic():
    st.write("⚠️ **Vui lòng không tắt trình duyệt khi Robot đang chạy.**")
    st.write("---")
    
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Giả lập quy trình SEO
    steps = ["Đang đọc cấu hình Dashboard...", "Kết nối Gemini AI...", "Quét danh sách Website...", "Đang soạn thảo nội dung...", "Chèn Backlink...", "Đang đăng bài...", "Cập nhật báo cáo Report..."]
    
    for i, step in enumerate(steps):
        status_text.markdown(f"**Bước {i+1}/{len(steps)}:** {step}")
        # Chạy thanh tiến trình
        for percent in range(i * 14, (i + 1) * 14):
            time.sleep(0.05)
            progress_bar.progress(min(percent, 100))
        
        # Kiểm tra nút Cancel (Dừng)
        # Lưu ý: Trong Streamlit, bấm nút sẽ trigger rerun, dialog tự đóng
        if st.button(f"❌ DỪNG ROBOT (CANCEL) - Bước {i+1}", use_container_width=True):
            st.error("Đã nhận lệnh dừng! Đang thoát...")
            time.sleep(1)
            st.rerun()

    progress_bar.progress(100)
    st.success("🎉 ROBOT ĐÃ HOÀN THÀNH NHIỆM VỤ!")
    if st.button("ĐÓNG CỬA SỔ", use_container_width=True):
        st.rerun()

# =================================================================
# 3. UI/UX: NÚT KHÍT NHAU, BẰNG NHAU
# =================================================================
st.set_page_config(page_title="Lái Hộ SEO v2000", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT KHÍT NHAU */
    .nav-btn button {
        width: 100% !important; height: 50px !important;
        text-align: left !important; background-color: #111111 !important;
        border: 1px solid #222 !important; border-radius: 0px !important;
        margin: 0px !important; color: #ffffff !important;
        font-weight: 600 !important; font-size: 15px !important;
    }
    .active-tab button { background-color: #1a1a1a !important; border-left: 6px solid #ffd700 !important; color: #ffd700 !important; }

    /* TOOLBAR 3 NÚT BẰNG NHAU */
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

# 4. BỐ CỤC SIDEBAR CỐ ĐỊNH
nav_col, main_col = st.columns([1, 4.2], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Data_Backlink", "Data_Backlink"), ("🌐 Data_Website", "Data_Website"), ("🖼️ Data_Image", "Data_Image"), ("🔄 Data_Spin", "Data_Spin"), ("📍 Data_Local", "Data_Local"), ("📊 Data_Report", "Data_Report")]
    for label, key in menu:
        is_active = st.session_state['active_tab'] == key
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"n_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 5. NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR 3 NÚT THẲNG HÀNG
    c1, c2, c3 = st.columns(3, gap="small")
    
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True):
                # GỌI POPUP KHI BẤM NÚT
                run_robot_logic()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", use_container_width=True):
                st.toast("Đã cập nhật Database!")
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

st.caption("🚀 Lái Hộ SEO v2000.0 | Modal Popup & Cancel Action")
