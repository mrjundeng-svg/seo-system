import streamlit as st
import pandas as pd
import os

# 1. CẤU TRÚC DỮ LIỆU CHUẨN
TABLES = {
    "config": ["Hạng mục", "Giá trị thực tế"],
    "backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "image": ["Link ảnh", "Đã dùng"],
    "spin": ["Từ Spin", "Bộ Spin"],
    "local": ["Tỉnh thành", "Quận", "Cung đường"],
    "report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# 2. HỆ THỐNG LƯU TRỮ TỰ ĐỘNG
def load_data(key):
    path = f"laiho_{key}.csv"
    if os.path.exists(path):
        try: return pd.read_csv(path).fillna("")
        except: pass
    cols = TABLES[key]
    if key == "config":
        return pd.DataFrame([["GEMINI_API_KEY", ""], ["SENDER_EMAIL", ""], ["TARGET_URL", ""], ["FOLDER_DRIVE_ID", ""], ["Số lượng bài/ngày", "10"], ["Mật độ Link", "3-5"]]+[["...", ""]]*7, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def save_data(key, df):
    df.to_csv(f"laiho_{key}.csv", index=False)

# KHỞI TẠO STATE (PHẢI CHẠY TRƯỚC UI)
for k in TABLES.keys():
    state_key = f"df_{k}"
    if state_key not in st.session_state:
        st.session_state[state_key] = load_data(k)

if 'tab' not in st.session_state: st.session_state['tab'] = "Dashboard"

# 3. GIAO DIỆN & STYLE
st.set_page_config(page_title="Hệ thống SEO Lái Hộ", page_icon="🚕", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #ffffff; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold { color: #ffd700; font-weight: 700; }
    .nav-btn button { width: 100%; text-align: left; background: transparent; border: none; padding: 12px; color: #fff; }
    .active-tab button { background-color: #1a1a1a; border-left: 5px solid #ffd700; color: #ffd700; }
    [data-testid="stDataFrame"] { background-color: #111111; border: 1px solid #333; }
    [data-testid="stDataFrame"] p { color: #ffd700 !important; font-weight: 700; }
    .btn-red button { background-color: #ff0000; color: #fff; font-weight: 700; border: none; }
    .btn-gold button { background-color: #ffd700; color: #000; font-weight: 700; border: none; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC SIDEBAR CỐ ĐỊNH
nav_col, main_col = st.columns([1, 4], gap="large")

with nav_col:
    st.markdown("<h2 class='gold'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    for m in menu:
        is_active = st.session_state['tab'] == m
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"n_{m}"):
            st.session_state['tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 5. NỘI DUNG CHÍNH
with main_col:
    active = st.session_state['tab']
    st.markdown(f"### 📍 {active}")
    
    # TOOLBAR
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])
    with c1: 
        if st.button("💾 LƯU CỨNG", use_container_width=True):
            for k in TABLES.keys(): save_data(k, st.session_state[f"df_{k}"])
            st.toast("Dữ liệu đã được ghi vào ổ cứng!")
    with c2: st.button("📤 XUẤT EXCEL", key=f"ex_{active}", use_container_width=True)
    with c3: st.button("📥 NHẬP EXCEL", key=f"im_{active}", use_container_width=True)
    with c4:
        if active == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 khởi động...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (AUTO-SAVE KHI EDIT)
    db_key = active.lower().replace('data_', '')
    state_key = f"df_{db_key}"
    
    st.markdown(f"<p class='gold'>BẢNG: {active.upper()}</p>", unsafe_allow_html=True)
    
    if active == "Data_Report":
        st.dataframe(st.session_state[state_key], use_container_width=True, height=750, hide_index=True)
    else:
        edited_df = st.data_editor(
            st.session_state[state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in TABLES[db_key]}
        )
        # Cập nhật và tự động lưu
        if not edited_df.equals(st.session_state[state_key]):
            st.session_state[state_key] = edited_df
            save_data(db_key, edited_df)

st.caption("🚀 Lái Hộ SEO v500.0 | Clean & Persistent")
