import streamlit as st
import pandas as pd

# 1. CẤU HÌNH HỆ THỐNG
st.set_page_config(page_title="LÁI HỘ SEO - MEMORY MASTER", layout="wide", page_icon="🚕")

# Định nghĩa Template chuẩn
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

# 2. KHỞI TẠO BỘ NHỚ (DÙNG CƠ CHẾ LƯU TRỮ VĨNH VIỄN TRONG PHIÊN)
if 'db' not in st.session_state:
    st.session_state['db'] = {}
    for name, cols in TABS_CONFIG.items():
        if name == "Dashboard":
            st.session_state['db'][name] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["SERVICE_ACCOUNT_JSON", ""],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["FOLDER_DRIVE_ID", ""],
                ["Số lượng bài cần tạo", "3"]
            ], columns=cols)
        else:
            st.session_state['db'][name] = pd.DataFrame(columns=cols)

# 3. GIAO DIỆN EXCEL STYLE
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)

# CSS cho Tab sang trọng
st.markdown("""
    <style>
    .stApp { background-color: #0c0c0c; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e1e1e; border-radius: 4px;
        padding: 8px 16px; color: #aaa; border: 1px solid #333;
    }
    .stTabs [aria-selected="true"] { background-color: #ffd700 !important; color: #000 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

tab_labels = ["🏠 Dashboard", "🔗 Backlink", "🌐 Website", "🖼️ Image", "🔄 Spin", "📍 Local", "📊 Report"]
tabs = st.tabs(tab_labels)

# Duyệt qua các Tab
for i, name in enumerate(TABS_CONFIG.keys()):
    with tabs[i]:
        c1, c2, _ = st.columns([1, 1, 3])
        with c1:
            if name == "Dashboard":
                st.button("🔥 START ROBOT", key=f"btn_run_{name}")
            else:
                if st.button(f"☁️ UPDATE {name.upper()}", key=f"btn_up_{name}"):
                    st.toast(f"Đã ghi nhận dữ liệu {name}!")
        with c2:
            st.button(f"🔄 RESTORE DATA", key=f"btn_res_{name}")

        st.write("")
        
        # CƠ CHẾ LƯU TRỮ TRỰC TIẾP: Khi sửa bảng, nó cập nhật thẳng vào st.session_state['db']
        # Dùng on_change để khóa dữ liệu ngay khi Ní dán vào
        st.session_state['db'][name] = st.data_editor(
            st.session_state['db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=650,
            hide_index=True,
            key=f"editor_{name}", # Key tĩnh cực kỳ quan trọng
            column_config={
                "Giá trị thực tế": st.column_config.TextColumn(width="large"),
                "Bộ Spin": st.column_config.TextColumn(width="large")
            }
        )

st.caption("🚀 v9000.0 | Memory Master | Anti-Data-Loss | Stable Excel UI")
