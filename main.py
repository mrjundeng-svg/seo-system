import streamlit as st
import pandas as pd

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (DÁN DỮ LIỆU THẬT CỦA NÍ VÀO ĐÂY)
# =================================================================
# Ní hãy điền thông tin của Ní vào các phần ngoặc vuông [] bên dưới.
# Một khi dán vào đây, Ní đổi UI thoải mái mà không bao giờ mất dữ liệu.

if 'df_Dashboard' not in st.session_state:
    st.session_state['df_Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
        ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
        ["TARGET_URL", "https://laiho.vn/"],
        ["Số lượng bài/ngày", "10"],
        ["Mật độ Link", "3-5"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

if 'df_Data_Backlink' not in st.session_state:
    # Ní có thể dán list backlink của Ní vào đây
    st.session_state['df_Data_Backlink'] = pd.DataFrame([
        ["lái xe hộ", "https://laiho.vn", "0"],
        ["thuê tài xế", "https://laiho.vn/thue-xe", "0"]
    ], columns=["Từ khoá", "Website đích", "Đã dùng"])

if 'df_Data_Website' not in st.session_state:
    st.session_state['df_Data_Website'] = pd.DataFrame([
        ["Blog Lái Hộ", "Blogger", "123456789", "", "", "Bật", "5"]
    ], columns=["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"])

# Các bảng khác khởi tạo mặc định (Ní có thể thêm tương tự như trên)
OTHERS = {
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}
for k, cols in OTHERS.items():
    if f'df_{k}' not in st.session_state:
        st.session_state[f'df_{k}'] = pd.DataFrame([[""] * len(cols)], columns=cols)

# =================================================================
# 2. UI/UX: NÚT BẰNG NHAU, SÁT NHAU, ICON MÀU
# =================================================================
st.set_page_config(page_title="SEO Master v1400", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT BẰNG NHAU & SÁT RẠT NHAU */
    .nav-btn button {
        width: 100% !important;
        height: 50px !important;
        text-align: left !important;
        background-color: #111111 !important;
        border: 1px solid #222 !important;
        border-radius: 0px !important; /* Vuông vức để khít nhau */
        margin: 0px !important; /* Triệt tiêu khoảng cách */
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        display: flex !important;
        align-items: center !important;
    }
    .active-tab button {
        background-color: #1a1a1a !important;
        border-left: 6px solid #ffd700 !important;
        color: #ffd700 !important;
    }
    .nav-btn button:hover { border-color: #ffd700 !important; }

    /* TOOLBAR NÚT TÍNH NĂNG (BẰNG NHAU TRÊN 1 HÀNG) */
    .stButton>button {
        width: 100% !important;
        height: 45px !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
    }
    .btn-red button { background-color: #ff0000 !important; color: #fff !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; }
    .btn-blue button { background-color: #0055ff !important; color: #fff !important; }

    /* ICON MÀU SẮC */
    .i-h { color: #ff4b4b; } .i-b { color: #00d2ff; } .i-w { color: #00ff8d; }
    .i-i { color: #ffcc00; } .i-s { color: #ff00ff; } .i-l { color: #ff8c00; } .i-r { color: #ffffff; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 3. BỐ CỤC 2 CỘT
nav_col, main_col = st.columns([1, 4.5], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; margin-bottom:15px;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    
    # RENDER MENU SÁT NHAU
    menu = [
        ("🏠 Dashboard", "Dashboard"),
        ("🔗 Data_Backlink", "Data_Backlink"),
        ("🌐 Data_Website", "Data_Website"),
        ("🖼️ Data_Image", "Data_Image"),
        ("🔄 Data_Spin", "Data_Spin"),
        ("📍 Data_Local", "Data_Local"),
        ("📊 Data_Report", "Data_Report")
    ]
    
    for label, key in menu:
        is_active = st.session_state['active_tab'] == key
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(label, key=f"n_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR: 4 NÚT CHIỀU NGANG BẰNG NHAU, SÁT NHAU
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 khởi động...")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
            st.button("🔄 ĐỒNG BỘ", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        st.button("📧 GỬI REPORT", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (DỮ LIỆU LUÔN CỐ ĐỊNH)
    state_key = f"df_{tab}"
    st.session_state[state_key] = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        num_rows="dynamic",
        height=720,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[state_key].columns}
    )

st.caption("🚀 Lái Hộ SEO v1400.0 | Hard-coded Persistence | Perfect Symmetry")
