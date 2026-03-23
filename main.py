import streamlit as st
import pandas as pd

# 1. THIẾT LẬP TRANG (PHẢI ĐỂ ĐẦU TIÊN)
st.set_page_config(page_title="LAI HO SYSTEM", layout="wide")

# 2. KHỞI TẠO TEMPLATE
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
TABS = ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]

# Khởi tạo Session State (Dùng try-except để đảm bảo an toàn)
for t in TABS:
    key = f"df_{t}"
    if key not in st.session_state:
        if t == "Dashboard":
            st.session_state[key] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["SERVICE_ACCOUNT_JSON", ""],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"]
            ], columns=["Hạng mục", "Giá trị thực tế"])
        elif t == "Report":
            st.session_state[key] = pd.DataFrame(columns=REPORT_COLS)
        else:
            st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

# 3. SIDEBAR GIAO DIỆN (DÙNG SELECTBOX CHO ỔN ĐỊNH)
st.sidebar.title("🚕 LÁI HỘ SEO")
st.sidebar.markdown("---")
choice = st.sidebar.selectbox("CHỌN MỤC QUẢN LÝ:", TABS)

# 4. KHU VỰC HIỂN THỊ CHÍNH
st.title(f"📍 {choice}")

# Toolbar tối giản
c1, c2, _ = st.columns([1, 1, 3])
with c1:
    st.button("☁️ CẬP NHẬT", use_container_width=True)
with c2:
    st.button("🔄 TẢI VỀ", use_container_width=True)

st.markdown("---")

# HIỂN THỊ BẢNG
data_key = f"df_{choice}"
st.data_editor(
    st.session_state[data_key],
    use_container_width=True,
    num_rows="dynamic",
    height=550,
    hide_index=True
)

st.caption("🚀 Version 6100.0 | Emergency Stable Build")
