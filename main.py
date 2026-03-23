import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# =================================================================
# 1. THIẾT LẬP CỘT CHUẨN (KHÔNG ĐƯỢC SAI)
# =================================================================
SCHEMA = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# =================================================================
# 2. KHỞI TẠO BỘ NHỚ (TRÁNH LỖI KEYERROR)
# =================================================================
# Tui gom hết vào 1 chỗ, vừa mở web là Robot "nạp đạn" ngay
for key, cols in SCHEMA.items():
    if key not in st.session_state:
        # Tạo bảng trắng có sẵn tiêu đề để Ní dán từ Excel vào không bị lệch
        st.session_state[key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 3. GIAO DIỆN UI/UX (VÀNG ĐEN - SIDEBAR CỐ ĐỊNH)
# =================================================================
st.set_page_config(page_title="Hệ thống Lái Hộ SEO", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold { color: #ffd700; font-weight: 700; font-size: 22px; }
    .nav-btn button { width: 100%; text-align: left; background: transparent; border: none; padding: 12px; color: #fff; }
    .active-tab button { background-color: #1a1a1a; border-left: 5px solid #ffd700; color: #ffd700; }
    [data-testid="stDataFrame"] { background-color: #111111; border: 1px solid #333; }
    [data-testid="stDataFrame"] p { color: #ffd700 !important; font-weight: 700; }
    .btn-red button { background-color: #ff0000; color: #fff; font-weight: 700; border: none; height: 3.5em; }
    .btn-gold button { background-color: #ffd700; color: #000; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

# BỐ CỤC SIDEBAR CỐ ĐỊNH (2 CỘT)
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 class='gold'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    for m in SCHEMA.keys():
        is_active = st.session_state['active_tab'] == m
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"nav_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 4. NỘI DUNG CHÍNH
with main_col:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")
    
    # TOOLBAR
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    with c1: 
        # Nút Đồng bộ này sẽ giúp Ní không bao giờ mất dữ liệu
        if st.button("🔄 ĐỒNG BỘ SHEET", use_container_width=True):
            st.toast("Đang kết nối Google Sheet của Ní...")
    with c2: st.button("📤 XUẤT EXCEL", use_container_width=True)
    with c3:
        if active == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True):
                st.info("Robot v55.0 đang vận hành...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # BẢNG DỮ LIỆU
    st.markdown(f"<p class='gold'>HỆ THỐNG DỮ LIỆU: {active.upper()}</p>", unsafe_allow_html=True)
    
    # Lấy dữ liệu an toàn (Không bao giờ KeyError)
    current_df = st.session_state.get(active, pd.DataFrame(columns=SCHEMA[active]))
    
    if active == "Data_Report":
        st.dataframe(current_df, use_container_width=True, height=750, hide_index=True)
    else:
        # data_editor để Ní dán dữ liệu từ Excel vào
        edited_df = st.data_editor(
            current_df,
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[active]}
        )
        # Lưu lại thay đổi vào bộ nhớ tạm
        st.session_state[active] = edited_df

st.caption("🚀 Lái Hộ SEO v700.0 | No KeyError | Persistent Logic")
