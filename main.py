import streamlit as st
import pandas as pd

# 1. CẤU HÌNH HỆ THỐNG
st.set_page_config(page_title="LÁI HỘ SEO - EXCEL STYLE", layout="wide", page_icon="📊")

# Định nghĩa các cột chuẩn (Sạch tên để không lỗi Key)
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

# 2. KHỞI TẠO DỮ LIỆU (SESSION STATE)
if 'initialized' not in st.session_state:
    for name, cols in TABS_CONFIG.items():
        key = f"df_{name}"
        if name == "Dashboard":
            st.session_state[key] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["SERVICE_ACCOUNT_JSON", ""],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["FOLDER_DRIVE_ID", ""],
                ["Số lượng bài cần tạo", "3"]
            ], columns=cols)
        else:
            st.session_state[key] = pd.DataFrame(columns=cols)
    st.session_state['initialized'] = True

# 3. GIAO DIỆN STYLE EXCEL
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)

# CSS làm Tab đẹp và giống Excel
st.markdown("""
    <style>
    .stApp { background-color: #0c0c0c; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e1e; border-radius: 4px 4px 0 0;
        padding: 8px 16px; color: #888; border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] { background-color: #ffd700 !important; color: #000 !important; font-weight: bold; border: 1px solid #ffd700 !important; }
    </style>
    """, unsafe_allow_html=True)

# Hiển thị Tab ngang với Emoji chỉ ở phần nhãn (Label)
tab_labels = [
    "🏠 Dashboard", "🔗 Backlink", "🌐 Website", 
    "🖼️ Image", "🔄 Spin", "📍 Local", "📊 Report"
]
tabs = st.tabs(tab_labels)

# Duyệt qua từng Tab để hiển thị nội dung
for i, (name, cols) in enumerate(TABS_CONFIG.items()):
    with tabs[i]:
        # Toolbar
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            if name == "Dashboard":
                st.button("🔥 START ROBOT", key=f"run_{name}", use_container_width=True)
            else:
                st.button(f"☁️ UPDATE {name.upper()}", key=f"up_{name}", use_container_width=True)
        with c2:
            st.button(f"🔄 RESTORE DATA", key=f"dl_{name}", use_container_width=True)
        
        st.write("") 
        
        # Bảng Editor
        data_key = f"df_{name}"
        if data_key in st.session_state:
            st.session_state[data_key] = st.data_editor(
                st.session_state[data_key],
                use_container_width=True,
                num_rows="dynamic",
                height=600,
                hide_index=True,
                key=f"editor_{name}",
                column_config={
                    "Giá trị thực tế": st.column_config.TextColumn(width="large"),
                    "Bộ Spin": st.column_config.TextColumn(width="large")
                }
            )

st.caption("🚀 v8900.0 | Fixed KeyError | Excel Style | Stable Architecture")
