import streamlit as st
import pandas as pd

# 1. TEMPLATE CHUẨN LÁI HỘ (PHỤC HỒI 100%)
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": REPORT_COLS
}

# 2. KHỞI TẠO HỆ THỐNG
st.set_page_config(page_title="LÁI HỘ SEO SYSTEM", layout="wide")

# Khởi tạo data một lần duy nhất
for tab, cols in TABS_CONFIG.items():
    if f"df_{tab}" not in st.session_state:
        if tab == "Dashboard":
            st.session_state[f"df_{tab}"] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["SERVICE_ACCOUNT_JSON", ""],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
                ["Số lượng bài cần tạo", "3"]
            ], columns=cols)
        else:
            st.session_state[f"df_{tab}"] = pd.DataFrame(columns=cols)

# 3. GIAO DIỆN SIDEBAR (DÙNG SELECTBOX GỐC - CHỐNG LOOP)
with st.sidebar:
    st.header("🚕 LÁI HỘ MASTER")
    # Dùng selectbox cho cực kỳ ổn định, không bao giờ gây xoay vòng
    tab_selection = st.selectbox("DANH MỤC QUẢN LÝ", list(TABS_CONFIG.keys()))
    st.divider()
    st.info("Version: 6000.0 (Stable Mode)")

# 4. KHU VỰC HIỂN THỊ
st.subheader(f"📍 Phân mục: {tab_selection}")

col1, col2, _ = st.columns([1, 1, 3])
with col1:
    if st.button("☁️ CẬP NHẬT CLOUD", use_container_width=True):
        st.toast("Đang đồng bộ dữ liệu...")
with col2:
    if st.button("🔄 TẢI TỪ CLOUD", use_container_width=True):
        st.toast("Đang tải dữ liệu mới...")

st.divider()

# RENDER BẢNG EDITOR
data_key = f"df_{tab_selection}"
st.session_state[data_key] = st.data_editor(
    st.session_state[data_key],
    use_container_width=True,
    num_rows="dynamic",
    height=600,
    hide_index=True,
    column_config={
        "Giá trị thực tế": st.column_config.TextColumn(width="large"),
        "Bộ Spin": st.column_config.TextColumn(width="large")
    }
)
