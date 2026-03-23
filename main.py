import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hệ thống SEO Lái Hộ v350.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU BÊN TRÁI CỐ ĐỊNH */
    .nav-col { border-right: 1px solid #333333; height: 100vh; padding: 15px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    
    /* NÚT MENU */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 2px !important;
    }
    .stButton>button:hover { border: 1px solid #ffd700 !important; color: #ffd700 !important; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }

    /* NÚT CHỨC NĂNG */
    .btn-red button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; height: 3.5em !important; text-transform: uppercase; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; font-weight: 700 !important; height: 2.8em !important; font-size: 13px !important; }

    /* NHUỘM VÀNG TIÊU ĐỀ CỘT CHO RÕ */
    [data-testid="stDataFrame"] div[role="columnheader"] p {
        color: #ffd700 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU VỚI TIÊU ĐỀ CỘT CHUẨN (CÓ SẴN 1 DÒNG TRỐNG)
if 'tab' not in st.session_state: st.session_state['tab'] = "Dashboard"

def init_tables():
    # 13 Dòng cấu hình Dashboard
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["FOLDER_DRIVE_ID", "1STdk4mp..."],
            ["Số lượng bài/ngày", "10"],
            ["Thiết lập số chữ", "1200"],
            ["Trạng thái Robot", "Sẵn sàng"]
        ] + [["...", ""]] * 6, columns=["Hạng mục", "Giá trị thực tế"])

    # Định nghĩa chính xác các cột Ní yêu cầu
    sheets_config = {
        "df_backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "df_website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
        "df_image": ["Link ảnh", "Đã dùng"],
        "df_spin": ["Từ Spin", "Bộ Spin"],
        "df_local": ["Tỉnh thành", "Quận", "Cung đường"],
        "df_report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
    }
    
    for key, cols in sheets_config.items():
        if key not in st.session_state:
            # Tạo sẵn 1 dòng trống để tiêu đề luôn hiện rõ
            empty_row = {c: "" for c in cols}
            st.session_state[key] = pd.DataFrame([empty_row], columns=cols)

init_tables()

# 3. GIAO DIỆN 2 CỘT (SIDEBAR KHÔNG THỂ ẨN)
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    for m in menu:
        style = "active-nav" if st.session_state['tab'] == m else ""
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"nav_{m}"):
            st.session_state['tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 4. KHU VỰC CHÍNH
with main_col:
    tab = st.session_state['tab']
    st.markdown(f"### 📍 {tab}")

    # Thanh công cụ Export/Import
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    if tab == "Dashboard":
        with c1: st.markdown('<div class="btn-red">', unsafe_allow_html=True); st.button("🔥 START", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    else:
        with c1: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    
    with c2: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("🔄 ĐỒNG BỘ", key=f"sy_{tab}", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # LẤY BẢNG THEO TAB (Fix lỗi gọi tên bảng)
    df_key = "df_config" if tab == "Dashboard" else f"df_{tab.split('_')[1].lower()}"
    
    st.markdown(f"<p style='color:#ffd700; font-weight:700;'>BẢNG DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)
    
    if tab == "Data_Report":
        # Report chỉ xem nên dùng dataframe
        st.dataframe(st.session_state[df_key], use_container_width=True, height=750)
    else:
        # Các bảng khác cho phép nhập liệu (dán từ excel)
        st.session_state[df_key] = st.data_editor(
            st.session_state[df_key], 
            use_container_width=True, 
            num_rows="dynamic", 
            height=700
        )

st.caption("🚀 SEO Automation Lái Hộ v350.0 | Visible Headers & Gold Style")
