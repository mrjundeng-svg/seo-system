import streamlit as st
import pandas as pd
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hệ thống SEO Lái Hộ v400.0", page_icon="🚕", layout="wide")

# --- CSS: BLACK & GOLD - SIDEBAR CỐ ĐỊNH & XUỐNG DÒNG ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 22px; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }
    .stButton>button { width: 100% !important; text-align: left !important; background: transparent; border: none; padding: 12px; }
    .stButton>button:hover { color: #ffd700 !important; border: 1px solid #ffd700 !important; }
    
    /* TIÊU ĐỀ CỘT VÀNG & XUỐNG DÒNG */
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    
    .btn-save button { background-color: #00ff00 !important; color: black !important; font-weight: 800 !important; height: 3.5em !important; }
    .btn-red button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. HỆ THỐNG LƯU TRỮ "BẤT TỬ" (KHÔNG MẤT DỮ LIỆU)
# =================================================================
# Định nghĩa đúng các cột Ní yêu cầu
TABLE_MAP = {
    "config": ["Hạng mục", "Giá trị thực tế"],
    "backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "image": ["Link ảnh", "Đã dùng"],
    "spin": ["Từ Spin", "Bộ Spin"],
    "local": ["Tỉnh thành", "Quận", "Cung đường"],
    "report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

def load_db(name):
    path = f"data_{name}.csv"
    if os.path.exists(path):
        return pd.read_csv(path).fillna("")
    # Nếu chưa có file thì tạo bảng 13 dòng cho config, 1 dòng trống cho các bảng khác
    cols = TABLE_MAP[name]
    if name == "config":
        return pd.DataFrame([["GEMINI_API_KEY", ""], ["SENDER_EMAIL", ""], ["TARGET_URL", ""], ["FOLDER_DRIVE_ID", ""], ["Số lượng bài/ngày", ""], ["Thiết lập số chữ", ""], ["Mật độ Link", ""]] + [["...", ""]]*6, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def save_db(name, df):
    df.to_csv(f"data_{name}.csv", index=False)

# KHỞI TẠO BỘ NHỚ KHI MỞ WEB
if 'current_tab' not in st.session_state: st.session_state['current_tab'] = "Dashboard"

for key in TABLE_MAP.keys():
    state_key = f"df_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = load_db(key)

# =================================================================
# 3. GIAO DIỆN
# =================================================================
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    for m in menu:
        is_active = st.session_state['current_tab'] == m
        style = "active-nav" if is_active else ""
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"nav_{m}"):
            st.session_state['current_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['current_tab']
    st.markdown(f"### 📍 {tab}")

    # TOOLBAR QUYỀN LỰC
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
    with c1:
        st.markdown('<div class="btn-save">', unsafe_allow_html=True)
        if st.button("💾 LƯU DỮ LIỆU", use_container_width=True):
            for k in TABLE_MAP.keys():
                save_db(k, st.session_state[f"df_{k}"])
            st.success("Đã khóa dữ liệu vĩnh viễn!")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2: st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
    with c3: st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
    with c4:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            st.button("🔥 START ROBOT", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # LẤY DỮ LIỆU HIỆN TẠI
    key_db = tab.lower().replace('data_', '')
    state_key = f"df_{key_db}"
    
    st.markdown(f"<p class='gold-text'>HỆ THỐNG DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)

    # HIỂN THỊ BẢNG - HỖ TRỢ XUỐNG DÒNG & ẨN INDEX
    if tab == "Data_Report":
        st.dataframe(st.session_state[state_key], use_container_width=True, height=750, hide_index=True)
    else:
        # Tự cập nhật dữ liệu khi dán từ Excel vào
        edited_df = st.data_editor(
            st.session_state[state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in TABLE_MAP[key_db]}
        )
        st.session_state[state_key] = edited_df

st.caption("🚀 SEO Automation Lái Hộ v400.0 | Permanent Storage Edition")
