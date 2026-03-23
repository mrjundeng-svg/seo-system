import streamlit as st
import pandas as pd

# 1. KHỞI TẠO BỘ KHUNG (PHẢI NẰM ĐẦU TIÊN ĐỂ CHỐNG KEYERROR)
TABLES = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Nạp dữ liệu mặc định (Tránh trắng trơn khi mới mở)
for key, cols in TABLES.items():
    if key not in st.session_state:
        st.session_state[key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

# 2. GIAO DIỆN (UI/UX TINH GỌN)
st.set_page_config(page_title="SEO Lái Hộ Master", page_icon="🚕", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold { color: #ffd700; font-weight: 700; font-size: 20px; }
    .nav-btn button { width: 100%; text-align: left; background: transparent; border: none; padding: 12px; color: #fff; }
    .active-tab button { background-color: #1a1a1a; border-left: 5px solid #ffd700; color: #ffd700; }
    [data-testid="stDataFrame"] { background-color: #111111; border: 1px solid #333; }
    [data-testid="stDataFrame"] p { color: #ffd700 !important; font-weight: 700; }
    .btn-red button { background-color: #ff0000; color: #fff; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR CỐ ĐỊNH
nav_col, main_col = st.columns([1, 4.2], gap="large")
with nav_col:
    st.markdown("<h2 class='gold'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    for m in TABLES.keys():
        is_active = st.session_state['active_tab'] == m
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"n_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 4. NỘI DUNG
with main_col:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")
    
    c1, c2, _ = st.columns([1, 1, 3])
    with c1: st.button("📤 XUẤT EXCEL", use_container_width=True)
    with c2:
        if active == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot đang nạp dữ liệu...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p class='gold'>BẢNG DỮ LIỆU: {active.upper()}</p>", unsafe_allow_html=True)
    
    # Hiển thị bảng và cho phép sửa
    st.session_state[active] = st.data_editor(
        st.session_state[active],
        use_container_width=True,
        num_rows="dynamic",
        height=700,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in TABLES[active]}
    )

st.caption("🚀 Lái Hộ SEO v900.0 | Clean & Stable")
