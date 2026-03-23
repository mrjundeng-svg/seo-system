import streamlit as st
import pandas as pd

# =================================================================
# 1. 📋 ĐỊNH NGHĨA TEMPLATE (GIỮ NGUYÊN BỘ KHUNG XỊN)
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]

TABS_CONFIG = {
    "🏠 Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "🔗 Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "🌐 Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "🖼️ Image": ["Link ảnh", "Số lần dùng"],
    "🔄 Spin": ["Từ Spin", "Bộ Spin"],
    "📍 Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "📊 Report": REPORT_COLS
}

def init_v5900():
    # Khởi tạo dữ liệu vào Session State
    for tab_label, cols in TABS_CONFIG.items():
        s_key = f"df_{tab_label}"
        if s_key not in st.session_state:
            if "Dashboard" in tab_label:
                st.session_state[s_key] = pd.DataFrame([
                    ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                    ["SERVICE_ACCOUNT_JSON", ""],
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
                    ["Số lượng bài cần tạo", "3"]
                ], columns=cols)
            else:
                st.session_state[s_key] = pd.DataFrame(columns=cols)

init_v5900()

# =================================================================
# 2. 🎨 GIAO DIỆN SIDEBAR GỐC (CHỐNG XOAY TUYỆT ĐỐI)
# =================================================================
st.set_page_config(page_title="LÁI HỘ SEO Master", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000; color: white; }
    /* Sidebar Dark Mode */
    [data-testid="stSidebar"] { background-color: #111 !important; border-right: 1px solid #222; }
    /* Chỉnh màu Radio button cho sang */
    div[data-testid="stSidebarUserContent"] .st-emotion-cache-6qob1r { color: #ffd700 !important; font-weight: bold; }
    /* Button Styles */
    .btn-blue button { background-color: #0055ff !important; width: 100%; font-weight: 700; height: 45px; border: none; }
    .btn-red button { background-color: #ff4b4b !important; width: 100%; font-weight: 700; height: 45px; border: none; }
    </style>
    """, unsafe_allow_html=True)

# Dùng Sidebar gốc - Đây là cách ổn định nhất trong Streamlit
with st.sidebar:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    st.markdown("---")
    selected_tab = st.radio(
        "DANH MỤC HỆ THỐNG",
        options=list(TABS_CONFIG.keys()),
        index=0,
        key="main_navigation"
    )
    st.markdown("---")
    st.caption("🚀 Version 5900.0 - Stable")

# =================================================================
# 3. 🖼️ KHU VỰC HIỂN THỊ DỮ LIỆU
# =================================================================
tab = selected_tab
st.markdown(f"### Dự án: Lái Hộ <span style='color:#888; font-size:18px;'>/ {tab}</span>", unsafe_allow_html=True)

# Toolbar
st.markdown("<br>", unsafe_allow_html=True)
t1, t2, t3 = st.columns([1, 1, 2.5])
with t1:
    if "Dashboard" in tab:
        st.markdown('<div class="btn-red">', unsafe_allow_html=True)
        if st.button("🔥 START ROBOT"): st.toast("Robot đang khởi động...")
    else:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE CLOUD"): st.toast("Đã lưu lên Cloud!")
with t2:
    st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
    if st.button("🔄 RESTORE CLOUD"): st.toast("Đã đồng bộ từ Cloud!")

st.markdown("<hr style='border-color:#222'>", unsafe_allow_html=True)

# Hiển thị bảng Editor chuẩn Template
s_key = f"df_{tab}"
if s_key in st.session_state:
    st.session_state[s_key] = st.data_editor(
        st.session_state[s_key],
        use_container_width=True,
        num_rows="dynamic",
        height=700,
        hide_index=True,
        column_config={
            "Giá trị thực tế": st.column_config.TextColumn(width="large"),
            "Bộ Spin": st.column_config.TextColumn(width="large"),
            "Website": st.column_config.TextColumn(width="medium"),
            "Link bài viết": st.column_config.TextColumn(width="medium")
        }
    )
