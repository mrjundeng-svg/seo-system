import streamlit as st
import pandas as pd
import os

# 1. SCHEMA DỮ LIỆU CHUẨN (100% THEO YÊU CẦU)
SCHEMA = {
    "config": ["Hạng mục", "Giá trị thực tế"],
    "backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "image": ["Link ảnh", "Đã dùng"],
    "spin": ["Từ Spin", "Bộ Spin"],
    "local": ["Tỉnh thành", "Quận", "Cung đường"],
    "report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# 2. HỆ THỐNG LƯU TRỮ CỐ ĐỊNH
def load_db(key):
    path = f"db_laiho_{key}.csv"
    if os.path.exists(path):
        try: return pd.read_csv(path).fillna("")
        except: pass
    cols = SCHEMA[key]
    if key == "config":
        return pd.DataFrame([["GEMINI_API_KEY", ""], ["SENDER_EMAIL", ""], ["TARGET_URL", ""], ["FOLDER_DRIVE_ID", ""], ["Số lượng bài/ngày", "10"], ["Mật độ Link", "3-5"]]+[["...", ""]]*7, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def save_db(key, df):
    df.to_csv(f"db_laiho_{key}.csv", index=False)

# KHỞI TẠO STATE
for k in SCHEMA.keys():
    if f"df_{k}" not in st.session_state:
        st.session_state[f"df_{k}"] = load_db(k)
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 3. GIAO DIỆN & STYLE
st.set_page_config(page_title="SEO Lái Hộ Master", page_icon="🚕", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold { color: #ffd700 !important; font-weight: 700; }
    .nav-btn button { width: 100% !important; text-align: left !important; background: transparent; border: none; padding: 12px; color: #fff; }
    .active-tab button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; color: #fff !important; font-weight: 700; border: none; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; font-weight: 700; border: none; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC 2 CỘT (SIDEBAR CỐ ĐỊNH)
nav_col, main_col = st.columns([1, 4.2], gap="large")

with nav_col:
    st.markdown("<h2 class='gold'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    for m in ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]:
        is_active = st.session_state['active_tab'] == m
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"n_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])
    with c1: 
        if st.button("💾 LƯU DỮ LIỆU", use_container_width=True):
            for k in SCHEMA.keys(): save_db(k, st.session_state[f"df_{k}"])
            st.toast("Đã sao lưu thành công!")
    with c2: st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
    with c3: st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
    with c4:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 đang xử lý...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG DỮ LIỆU
    db_key = tab.lower().replace('data_', '')
    state_key = f"df_{db_key}"
    
    st.markdown(f"<p class='gold'>BẢNG DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)
    
    if tab == "Data_Report":
        st.dataframe(st.session_state[state_key], use_container_width=True, height=750, hide_index=True)
    else:
        # Tự động cập nhật session_state khi edit
        st.session_state[state_key] = st.data_editor(
            st.session_state[state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[db_key]}
        )

st.caption("🚀 Lái Hộ SEO v450.0 | Clean Code | Persistent Storage")
