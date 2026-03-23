import streamlit as st
import pandas as pd
import os

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Lái Hộ v390.0", page_icon="🚕", layout="wide")

# --- CSS: BLACK & GOLD - SIDEBAR CỐ ĐỊNH ---
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 22px; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }
    .stButton>button { width: 100% !important; text-align: left !important; background: transparent; border: none; padding: 10px; }
    .stButton>button:hover { color: #ffd700 !important; border: 1px solid #ffd700 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. LOGIC BỘ NHỚ "BẤT TỬ" (SAVE & LOAD)
# =================================================================
TABLE_COLS = {
    "config": ["Hạng mục", "Giá trị thực tế"],
    "backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "image": ["Link ảnh", "Đã dùng"],
    "spin": ["Từ Spin", "Bộ Spin"],
    "local": ["Tỉnh thành", "Quận", "Cung đường"],
    "report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

def load_data(key):
    filename = f"db_{key}.csv"
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame(columns=TABLE_COLS[key])

def save_data(key, df):
    filename = f"db_{key}.csv"
    df.to_csv(filename, index=False)

# KHỞI TẠO DỮ LIỆU TỪ FILE (NẾU CÓ)
if 'tab' not in st.session_state: st.session_state['tab'] = "Dashboard"

for k in TABLE_COLS.keys():
    state_key = f"df_{k}"
    if state_key not in st.session_state:
        st.session_state[state_key] = load_data(k)

# =================================================================
# 3. GIAO DIỆN CHÍNH
# =================================================================
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

with main_col:
    tab = st.session_state['tab']
    st.markdown(f"### 📍 {tab}")
    
    # Nút bấm trung tâm
    c1, c2, c3, _ = st.columns([1, 1, 1, 2])
    with c1: 
        if st.button("💾 LƯU TOÀN BỘ", use_container_width=True):
            for k in TABLE_COLS.keys():
                save_data(k, st.session_state[f"df_{k}"])
            st.toast("Đã lưu dữ liệu vào hệ thống!")
    with c2: st.button("📤 XUẤT EXCEL", use_container_width=True)
    with c3: st.button("📥 NHẬP EXCEL", use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # LẤY BẢNG THEO TAB
    db_key = tab.lower().replace('data_', '')
    state_key = f"df_{db_key}"
    
    st.markdown(f"<p style='color:#ffd700; font-weight:700;'>BẢNG DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)

    # HIỂN THỊ BẢNG VỚI TỰ ĐỘNG XUỐNG DÒNG (WRAP TEXT)
    if tab == "Data_Report":
        st.dataframe(st.session_state[state_key], use_container_width=True, height=750, hide_index=True)
    else:
        # data_editor tự động lưu vào session_state khi Ní chỉnh sửa
        edited_df = st.data_editor(
            st.session_state[state_key], 
            use_container_width=True, 
            num_rows="dynamic", 
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in TABLE_COLS[db_key]}
        )
        # Cập nhật session_state ngay lập tức
        st.session_state[state_key] = edited_df

st.caption("🚀 SEO Automation Lái Hộ v390.0 | Data Persistence Edition")
