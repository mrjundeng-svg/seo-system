import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="LÁI HỘ SEO - IRON WALL", layout="wide", page_icon="🚕")

# 2. KHỞI TẠO TEMPLATE CHUẨN
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

# 3. HÀM KHỞI TẠO DỮ LIỆU (CHỐNG RESET)
if 'main_db' not in st.session_state:
    st.session_state['main_db'] = {}
    for name, cols in TABS_CONFIG.items():
        if name == "Dashboard":
            st.session_state['main_db'][name] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["Số lượng bài cần tạo", "3"]
            ], columns=cols)
        else:
            st.session_state['main_db'][name] = pd.DataFrame(columns=cols)

# 4. GIAO DIỆN
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER v9300</h2>", unsafe_allow_html=True)

# Dùng Tabs ngang
tab_list = list(TABS_CONFIG.keys())
tabs = st.tabs([f" {t}" for t in tab_list])

for i, name in enumerate(tab_list):
    with tabs[i]:
        st.subheader(f"📍 Phân mục: {name}")
        
        # Toolbar
        col_save, col_clear, _ = st.columns([1, 1, 3])
        
        # HIỂN THỊ BẢNG (Dùng key tĩnh để Streamlit không bị lú)
        # Ní dán dữ liệu vào đây thoải mái
        edited_df = st.data_editor(
            st.session_state['main_db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=600,
            hide_index=True,
            key=f"editor_v93_{name}"
        )
        
        with col_save:
            # NÚT CHỐT: Chỉ khi Ní bấm nút này, dữ liệu mới thực sự được khóa vào Session
            if st.button(f"💾 CHỐT DỮ LIỆU {name.upper()}", key=f"save_{name}"):
                st.session_state['main_db'][name] = edited_df
                st.success(f"Đã khóa {len(edited_df)} dòng vào bộ nhớ!")
                st.balloons() # Ăn mừng dán thành công

        with col_clear:
            if st.button(f"🗑️ XÓA BẢNG", key=f"clear_{name}"):
                st.session_state['main_db'][name] = pd.DataFrame(columns=TABS_CONFIG[name])
                st.rerun()

st.caption("🚀 v9300.0 | Manual Save Mode | Anti-Reset | Heavy Data Support")
