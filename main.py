import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Lái Hộ v360.0", page_icon="🚕", layout="wide")

# --- CSS CAO CẤP: BLACK & GOLD - SIDEBAR KHÔNG THỂ ĐÓNG ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    
    /* VÔ HIỆU HÓA SIDEBAR MẶC ĐỊNH */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU BÊN TRÁI CỐ ĐỊNH (CỘT 1) */
    .nav-col { border-right: 1px solid #333333; height: 100vh; padding-right: 15px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    
    /* STYLE NÚT MENU */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 2px !important;
    }
    .stButton>button:hover { border: 1px solid #ffd700 !important; color: #ffd700 !important; background-color: #111111 !important; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }

    /* NÚT CHỨC NĂNG START (ĐỎ) & EXCEL (VÀNG TỐI) */
    .btn-red button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; height: 3.5em !important; text-transform: uppercase; border: none !important; }
    .btn-excel button { background-color: #222222 !important; color: #ffd700 !important; border: 1px solid #ffd700 !important; height: 2.8em !important; font-size: 13px !important; font-weight: 700 !important; }

    /* LÀM RÕ TIÊU ĐỀ CỘT */
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU ĐÚNG 100% CỘT CỦA NÍ
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

def init_all_data():
    # 13 Dòng cấu hình Dashboard
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200"],
            ["Mật độ Backlink", "3 - 5"],
            ["Trạng thái Robot", "Sẵn sàng"],
            ["... ", ""], ["... ", ""], ["... ", ""]
        ], columns=["Hạng mục", "Giá trị hiện tại"])

    # Định nghĩa chính xác các cột Ní yêu cầu cho 6 bảng
    sheets_def = {
        "df_backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "df_website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
        "df_image": ["Link ảnh", "Đã dùng"],
        "df_spin": ["Từ Spin", "Bộ Spin"],
        "df_local": ["Tỉnh thành", "Quận", "Cung đường"],
        "df_report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
    }
    
    for key, cols in sheets_def.items():
        if key not in st.session_state:
            # Tạo sẵn 1 dòng trống để giữ form
            st.session_state[key] = pd.DataFrame([{c: "" for c in cols}], columns=cols)

init_all_data()

# 3. GIAO DIỆN 2 CỘT (SIDEBAR GIẢ NHƯNG CỐ ĐỊNH 100%)
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    for m in menu:
        style = "active-nav" if st.session_state['active_tab'] == m else ""
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"nav_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# 4. KHU VỰC CHÍNH (CỘT PHẢI)
with main_col:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")

    # Toolbar Export/Import
    c1, c2, c3, _ = st.columns([1.2, 1, 1, 2.5])
    if active == "Dashboard":
        with c1: st.markdown('<div class="btn-red">', unsafe_allow_html=True); st.button("🔥 START", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    else:
        with c1: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL", key=f"ex_{active}", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    
    with c2: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL", key=f"im_{active}", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("🔄 ĐỒNG BỘ", key=f"sy_{active}", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Lấy bảng dữ liệu
    df_key = "df_config" if active == "Dashboard" else f"df_{active.split('_')[1].lower()}"
    
    st.markdown(f"<p style='color:#ffd700; font-weight:700;'>HỆ THỐNG DỮ LIỆU: {active.upper()}</p>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG - ẨN CỘT INDEX (hide_index=True)
    if active == "Data_Report":
        st.dataframe(st.session_state[df_key], use_container_width=True, height=750, hide_index=True)
    else:
        st.session_state[df_key] = st.data_editor(
            st.session_state[df_key], 
            use_container_width=True, 
            num_rows="dynamic", 
            height=700,
            hide_index=True # DẸP BỎ CỘT SỐ 0
        )

st.caption("🚀 SEO Automation Lái Hộ v360.0 | Clean Interface - No Index Column")
