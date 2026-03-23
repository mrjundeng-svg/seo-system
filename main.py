import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG & CSS (UI/UX CHUẨN XẾ HỘ)
st.set_page_config(page_title="SEO Lái Hộ Master", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    /* NỀN ĐEN & CHỮ TRẮNG */
    .stApp { background-color: #000000; color: #ffffff; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT BẰNG NHAU, ICON MÀU */
    .nav-btn button {
        width: 100% !important;
        height: 50px !important;
        text-align: left !important;
        background-color: #111111 !important;
        border: 1px solid #333 !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
        display: flex !important;
        align-items: center !important;
        font-weight: 600 !important;
    }
    .nav-btn button:hover { border-color: #ffd700 !important; color: #ffd700 !important; }
    
    /* TRẠNG THÁI NÚT ĐANG CHỌN */
    .active-tab button {
        background-color: #222222 !important;
        border-left: 5px solid #ffd700 !important;
        color: #ffd700 !important;
    }

    /* ICON MÀU SẮC NỔI BẬT */
    .icon-gold { color: #ffd700; margin-right: 10px; font-size: 1.2rem; }
    .icon-blue { color: #00ccff; margin-right: 10px; font-size: 1.2rem; }
    .icon-green { color: #00ff00; margin-right: 10px; font-size: 1.2rem; }
    .icon-red { color: #ff3300; margin-right: 10px; font-size: 1.2rem; }

    /* NÚT TÍNH NĂNG Ở BẢNG (MỘT HÀNG, BẰNG NHAU) */
    .feature-row { display: flex; gap: 10px; margin-bottom: 20px; }
    .stButton>button {
        width: 100% !important;
        height: 45px !important;
        border-radius: 6px !important;
        font-weight: 700 !important;
    }
    
    /* MÀU RIÊNG CHO CÁC NÚT START/EXCEL */
    .btn-start button { background-color: #ff0000 !important; color: white !important; border: none !important; }
    .btn-excel button { background-color: #222222 !important; color: #ffd700 !important; border: 1px solid #ffd700 !important; }
    .btn-sync button { background-color: #1e3a8a !important; color: white !important; border: none !important; }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (TRÁNH LỖI KEYERROR)
# Định nghĩa các bảng và tiêu đề cột chính xác như Ní yêu cầu
TABLES_SCHEMA = {
    "🏠 Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "🔗 Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "🌐 Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "🖼️ Data_Image": ["Link ảnh", "Đã dùng"],
    "🔄 Data_Spin": ["Từ Spin", "Bộ Spin"],
    "📍 Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "📊 Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Nạp dữ liệu vào Session State (Nếu chưa có thì tạo bảng trống)
for key, cols in TABLES_SCHEMA.items():
    if key not in st.session_state:
        # Tạo sẵn 1 dòng để giữ form
        st.session_state[key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "🏠 Dashboard"

# 3. BỐ CỤC SIDEBAR CỐ ĐỊNH (CỘT TRÁI)
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Render Menu với icon màu và kích thước bằng nhau
    for m in TABLES_SCHEMA.keys():
        is_active = st.session_state['active_tab'] == m
        style_class = "active-tab" if is_active else ""
        
        st.markdown(f"<div class='nav-btn {style_class}'>", unsafe_allow_html=True)
        if st.button(m, key=f"btn_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div style='height:100px'></div>", unsafe_allow_html=True)
    st.button("🚪 Đăng xuất", key="logout")

# 4. NỘI DUNG CHÍNH (CỘT PHẢI)
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")

    # CÁC NÚT TÍNH NĂNG: XẾP HÀNG NGANG, KÍCH THƯỚC BẰNG NHAU
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col2:
        st.markdown('<div class="btn-excel">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{tab}")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col3:
        st.markdown('<div class="btn-sync">', unsafe_allow_html=True)
        if st.button("🔄 ĐỒNG BỘ SHEET", key=f"sync_{tab}"):
            st.toast("Đang đồng bộ dữ liệu vĩnh viễn từ Google Sheet...")
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col4:
        if "Dashboard" in tab:
            st.markdown('<div class="btn-start">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="start"):
                st.info("Robot v55.0 đang vận hành...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#ffd700; font-weight:700;'>BẢNG DỮ LIỆU ĐANG DÙNG:</p>", unsafe_allow_html=True)

    # HIỂN THỊ BẢNG (HIDE INDEX ĐỂ SẠCH GIAO DIỆN)
    # data_editor giúp Ní dán dữ liệu từ Excel vào cực nhanh
    st.session_state[tab] = st.data_editor(
        st.session_state[tab],
        use_container_width=True,
        num_rows="dynamic",
        height=700,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in TABLES_SCHEMA[tab]}
    )

st.caption("🚀 Lái Hộ SEO v1000.0 | Enterprise Persistent Interface")
