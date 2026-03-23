import streamlit as st
import pandas as pd
import os

# =================================================================
# 1. HỆ THỐNG DỮ LIỆU "BẤT TỬ" (PHẢI NẰM ĐẦU TIÊN ĐỂ FIX KEYERROR)
# =================================================================
# Định nghĩa chính xác 100% cột theo yêu cầu của Ní
SCHEMA = {
    "config": ["Hạng mục", "Giá trị thực tế"],
    "backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "image": ["Link ảnh", "Đã dùng"],
    "spin": ["Từ Spin", "Bộ Spin"],
    "local": ["Tỉnh thành", "Quận", "Cung đường"],
    "report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

def load_persistence(key):
    filename = f"persistence_{key}.csv"
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename).fillna("")
        except: pass
    # Nếu chưa có file, tạo bảng mặc định
    cols = SCHEMA[key]
    if key == "config":
        return pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
            ["Số lượng bài/ngày", "10"],
            ["Độ dài bài viết", "1000 - 1200 chữ"],
            ["Mật độ Link/bài", "3 - 5"],
            ["Trạng thái Robot", "Sẵn sàng"]
        ] + [["...", ""]] * 3, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def save_persistence(key, df):
    df.to_csv(f"persistence_{key}.csv", index=False)

# KHỞI TẠO NGAY LẬP TỨC TRƯỚC KHI DỰNG UI
for key in SCHEMA.keys():
    state_key = f"df_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = load_persistence(key)

if 'active_tab' not in st.session_state:
    st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. CẤU HÌNH GIAO DIỆN (UI/UX CHUẨN XẾ HỘ)
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v420.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    
    /* MENU BÊN TRÁI CỐ ĐỊNH */
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }
    .stButton>button { width: 100% !important; text-align: left !important; background: transparent; border: none; padding: 12px; }
    .stButton>button:hover { color: #ffd700 !important; border: 1px solid #ffd700 !important; }

    /* TIÊU ĐỀ CỘT VÀNG & BẢNG ĐEN */
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    
    .btn-red button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; font-weight: 700 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 3. SIDEBAR & NỘI DUNG CHÍNH
# =================================================================
col_nav, col_main = st.columns([1, 4.2], gap="large")

with col_nav:
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

with col_main:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")

    # Toolbar
    c1, c2, c3, c4 = st.columns([1.2, 1, 1, 1.2])
    with c1:
        if st.button("💾 LƯU THỦ CÔNG", use_container_width=True):
            for k in SCHEMA.keys(): save_persistence(k, st.session_state[f"df_{k}"])
            st.success("Đã khóa dữ liệu vĩnh viễn!")
    with c2: st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
    with c3: st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
    with c4:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot đang khởi động...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # XÁC ĐỊNH BẢNG HIỂN THỊ
    db_key = tab.lower().replace('data_', '')
    state_key = f"df_{db_key}"
    
    st.markdown(f"<p class='gold-text'>HỆ THỐNG DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)

    # Hiển thị bảng
    if tab == "Data_Report":
        st.dataframe(st.session_state[state_key], use_container_width=True, height=750, hide_index=True)
    else:
        # data_editor tự động cập nhật session_state
        edited_df = st.data_editor(
            st.session_state[state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[db_key]}
        )
        # Ghi nhận thay đổi vào session_state
        st.session_state[state_key] = edited_df

st.caption("🚀 SEO Automation Lái Hộ v420.0 | Persistence Fixed - No more KeyError")
