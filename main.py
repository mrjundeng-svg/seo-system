import streamlit as st
import pandas as pd

# 1. THIẾT LẬP TRANG (BẮT BUỘC ĐẦU DÒNG)
st.set_page_config(page_title="LAI HO SYSTEM", layout="wide")

# 2. KHỞI TẠO DỮ LIỆU (DÙNG CACHE ĐỂ KHÔNG BỊ LOAD LẠI)
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
TABS_LIST = ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]

# Khởi tạo Session State
for t in TABS_LIST:
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

# 3. GIAO DIỆN CHÍNH (BỎ SIDEBAR - DÙNG TAB NGANG CHO MƯỢT)
st.title("🚕 LÁI HỘ SEO SYSTEM")

# Tạo các Tab ngang - Cách này KHÔNG BAO GIỜ gây loop xoay vòng
tabs = st.tabs(TABS_LIST)

for i, tab_name in enumerate(TABS_LIST):
    with tabs[i]:
        st.subheader(f"📍 Quản lý {tab_name}")
        
        # Toolbar đơn giản
        c1, c2, _ = st.columns([1, 1, 3])
        with c1: st.button(f"☁️ Cập nhật {tab_name}", key=f"up_{tab_name}")
        with c2: st.button(f"🔄 Tải về {tab_name}", key=f"dl_{tab_name}")
        
        st.write("---")
        
        # Hiển thị bảng Editor
        data_key = f"df_{tab_name}"
        st.data_editor(
            st.session_state[data_key],
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            hide_index=True,
            key=f"editor_{tab_name}"
        )

st.caption("🚀 Version 7000.0 | No-Sidebar Mode | Ultra Stable")
