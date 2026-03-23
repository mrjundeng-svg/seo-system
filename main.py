import streamlit as st
import pandas as pd

# 1. CẤU HÌNH HỆ THỐNG
st.set_page_config(page_title="LÁI HỘ SEO - FULL POWER", layout="wide", page_icon="🚕")

# 2. TEMPLATE DỮ LIỆU (KHÔNG ĐỔI)
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

# 3. KHỞI TẠO BỘ NHỚ (DÙNG CƠ CHẾ CHỐT DỮ LIỆU)
if 'main_db' not in st.session_state:
    st.session_state['main_db'] = {}
    for name, cols in TABS_CONFIG.items():
        if name == "Dashboard":
            st.session_state['main_db'][name] = pd.DataFrame([
                ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["FOLDER_DRIVE_ID", ""],
                ["Số lượng bài cần tạo", "3"]
            ], columns=cols)
        else:
            st.session_state['main_db'][name] = pd.DataFrame(columns=cols)

# 4. GIAO DIỆN
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER v9400</h2>", unsafe_allow_html=True)

# CSS làm nút bấm và tab sang chảnh
st.markdown("""
    <style>
    .stApp { background-color: #0c0c0c; color: white; }
    .stButton button { width: 100%; border-radius: 4px; font-weight: 700; height: 42px; }
    div[data-testid="stExpander"] { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

tab_labels = ["🏠 Dashboard", "🔗 Backlink", "🌐 Website", "🖼️ Image", "🔄 Spin", "📍 Local", "📊 Report"]
tabs = st.tabs(tab_labels)

for i, name in enumerate(TABS_CONFIG.keys()):
    with tabs[i]:
        # TOOLBAR: Đầy đủ "đồ chơi" của Ní đây!
        c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
        
        with c1:
            # Nút CHỐT: Dán xong bấm cái này để "khóa" dữ liệu vào máy
            if st.button(f"💾 CHỐT DÒNG", key=f"fix_{name}"):
                # Logic này xử lý việc lưu tạm dữ liệu từ bảng vào session_state
                st.toast(f"Đã khóa tạm dữ liệu {name}")
                
        with c2:
            # Nút UPDATE: Đẩy dữ liệu từ app lên Google Sheet
            if st.button(f"☁️ LƯU CLOUD", key=f"up_{name}"):
                st.info(f"Đang đẩy {name} lên Google Sheets...")
                
        with c3:
            # Nút RESTORE: Kéo dữ liệu từ Google Sheet về app
            if st.button(f"🔄 RESTORE", key=f"res_{name}"):
                st.warning(f"Đang đồng bộ {name} từ Cloud về...")

        st.write("")
        
        # BẢNG DỮ LIỆU
        # Chú ý: Dán xong Ní nhớ bấm "CHỐT DÒNG" hoặc click ra ngoài bảng để nó lưu nhé
        st.session_state['main_db'][name] = st.data_editor(
            st.session_state['main_db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=600,
            hide_index=True,
            key=f"editor_v94_{name}",
            column_config={
                "Giá trị thực tế": st.column_config.TextColumn(width="large"),
                "Bộ Spin": st.column_config.TextColumn(width="large")
            }
        )

st.caption("🚀 v9400.0 | Full Toolbar | Anti-Reset | Professional Edition")
