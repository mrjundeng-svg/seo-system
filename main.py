import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="LÁI HỘ SEO MASTER", layout="wide", page_icon="🚕")

# 2. KHỞI TẠO BỘ NHỚ CỨNG (SESSION STATE)
# Tui khởi tạo thủ công từng cái để không bị lỗi Key
if 'df_Dashboard' not in st.session_state:
    st.session_state['df_Dashboard'] = pd.DataFrame([
        ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
        ["SERVICE_ACCOUNT_JSON", ""],
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["FOLDER_DRIVE_ID", ""],
        ["Số lượng bài cần tạo", "3"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

if 'df_Backlink' not in st.session_state:
    st.session_state['df_Backlink'] = pd.DataFrame(columns=["Từ khoá", "Website đích", "Đã dùng"])

if 'df_Website' not in st.session_state:
    st.session_state['df_Website'] = pd.DataFrame(columns=["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"])

if 'df_Image' not in st.session_state:
    st.session_state['df_Image'] = pd.DataFrame(columns=["Link ảnh", "Số lần dùng"])

if 'df_Spin' not in st.session_state:
    st.session_state['df_Spin'] = pd.DataFrame(columns=["Từ Spin", "Bộ Spin"])

if 'df_Local' not in st.session_state:
    st.session_state['df_Local'] = pd.DataFrame(columns=["Tỉnh thành", "Quận", "Điểm nóng"])

if 'df_Report' not in st.session_state:
    st.session_state['df_Report'] = pd.DataFrame(columns=["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"])

# 3. GIAO DIỆN
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)

# Tabs ngang (Tui viết code riêng cho từng Tab để chống reset)
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(["🏠 Dashboard", "🔗 Backlink", "🌐 Website", "🖼️ Image", "🔄 Spin", "📍 Local", "📊 Report"])

with tab1:
    st.button("🔥 START ROBOT", key="run_p1")
    st.session_state['df_Dashboard'] = st.data_editor(st.session_state['df_Dashboard'], use_container_width=True, hide_index=True, key="edit_p1")

with tab2:
    col_a, col_b = st.columns([1, 4])
    with col_a: st.button("☁️ UPDATE BACKLINK", key="up_p2")
    st.session_state['df_Backlink'] = st.data_editor(st.session_state['df_Backlink'], use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_p2")

with tab3:
    col_a, col_b = st.columns([1, 4])
    with col_a: st.button("☁️ UPDATE WEBSITE", key="up_p3")
    st.session_state['df_Website'] = st.data_editor(st.session_state['df_Website'], use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_p3")

with tab4:
    col_a, col_b = st.columns([1, 4])
    with col_a: st.button("☁️ UPDATE IMAGE", key="up_p4")
    st.session_state['df_Image'] = st.data_editor(st.session_state['df_Image'], use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_p4")

with tab5:
    col_a, col_b = st.columns([1, 4])
    with col_a: st.button("☁️ UPDATE SPIN", key="up_p5")
    st.session_state['df_Spin'] = st.data_editor(st.session_state['df_Spin'], use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_p5", column_config={"Bộ Spin": st.column_config.TextColumn(width="large")})

with tab6:
    col_a, col_b = st.columns([1, 4])
    with col_a: st.button("☁️ UPDATE LOCAL", key="up_p6")
    st.session_state['df_Local'] = st.data_editor(st.session_state['df_Local'], use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_p6")

with tab7:
    col_a, col_b = st.columns([1, 4])
    with col_a: st.button("🔄 RESTORE REPORT", key="up_p7")
    st.session_state['df_Report'] = st.data_editor(st.session_state['df_Report'], use_container_width=True, num_rows="dynamic", hide_index=True, key="edit_p7")

st.caption("🚀 v9100.0 | Concrete Memory | Anti-Reset Data | Stable Architecture")
