import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG (LUÔN ĐỂ ĐẦU TIÊN)
st.set_page_config(page_title="LÁI HỘ SEO SYSTEM", layout="wide", page_icon="🚕")

# 2. ĐỊNH NGHĨA TEMPLATE CHUẨN
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
TABS_LIST = ["Dashboard", "Backlink", "Website", "Image", "Spin", "Local", "Report"]

# Khởi tạo Session State (Dùng cơ chế tránh loop)
if 'initialized' not in st.session_state:
    for t in TABS_LIST:
        key = f"df_{t}"
        if t == "Dashboard":
            st.session_state[key] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["SERVICE_ACCOUNT_JSON", ""],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["FOLDER_DRIVE_ID", ""],
                ["Số lượng bài cần tạo", "3"]
            ], columns=["Hạng mục", "Giá trị thực tế"])
        elif t == "Report":
            st.session_state[key] = pd.DataFrame(columns=REPORT_COLS)
        else:
            cols = ["Từ khoá", "Website đích", "Đã dùng"] if t == "Backlink" else ["Cột 1", "Cột 2", "Cột 3"]
            st.session_state[key] = pd.DataFrame(columns=cols)
    st.session_state['initialized'] = True

# 3. GIAO DIỆN CHÍNH (DÙNG TAB NGANG - SIÊU ỔN ĐỊNH)
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO SYSTEM v8500</h2>", unsafe_allow_html=True)

# Tạo các Tab ngang (Native Tabs của Streamlit cực kỳ nhẹ)
tabs = st.tabs([f" {t}" for t in TABS_LIST])

for i, tab_name in enumerate(TABS_LIST):
    with tabs[i]:
        # Toolbar chức năng
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if tab_name == "Dashboard":
                if st.button("🔥 START ROBOT", key="btn_start"): st.toast("Robot đang khởi động...")
            else:
                if st.button(f"☁️ UPDATE {tab_name.upper()}", key=f"up_{tab_name}"): st.toast("Đã lưu!")
        with c2:
            if st.button(f"🔄 RESTORE {tab_name.upper()}", key=f"dl_{tab_name}"): st.toast("Đã tải về!")
        
        st.write("---")
        
        # Hiển thị bảng Editor
        data_key = f"df_{tab_name}"
        st.data_editor(
            st.session_state[data_key],
            use_container_width=True,
            num_rows="dynamic",
            height=600,
            hide_index=True,
            key=f"editor_{tab_name}"
        )

st.caption("🚀 Version 8500.0 | Multi-Tab Stable Mode | Light Architecture")
