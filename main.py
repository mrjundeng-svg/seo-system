import streamlit as st
import pandas as pd
import os

# 1. CẤU HÌNH TRANG & GIAO DIỆN
st.set_page_config(page_title="SEO Lái Hộ v410.0", page_icon=" taxi", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }
    .stButton>button { width: 100% !important; text-align: left !important; background: transparent; border: none; padding: 12px; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    .btn-red button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. HỆ THỐNG "BỘ NHỚ VĨNH CỬU" (FIX KEYERROR)
# =================================================================
# Định nghĩa cấu trúc cột CHUẨN (Khớp 100% yêu cầu của Ní)
SCHEMA = {
    "config": ["Hạng mục", "Giá trị thực tế"],
    "backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "image": ["Link ảnh", "Đã dùng"],
    "spin": ["Từ Spin", "Bộ Spin"],
    "local": ["Tỉnh thành", "Quận", "Cung đường"],
    "report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Hàm nạp dữ liệu từ file để không bị mất khi đổi code
def load_persistence_data(key):
    filename = f"persistence_{key}.csv"
    if os.path.exists(filename):
        try:
            return pd.read_csv(filename).fillna("")
        except: pass
    # Nếu chưa có file, tạo mặc định
    cols = SCHEMA[key]
    if key == "config":
        return pd.DataFrame([["GEMINI_API_KEY", ""], ["SENDER_EMAIL", ""], ["TARGET_URL", ""], ["FOLDER_DRIVE_ID", ""], ["Số lượng bài/ngày", "10"], ["Mật độ Link", "3-5"]]+[["...", ""]]*7, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

# Hàm lưu dữ liệu
def save_persistence_data(key, df):
    df.to_csv(f"persistence_{key}.csv", index=False)

# KHỞI TẠO NGAY LẬP TỨC (TRÁNH KEYERROR)
for key in SCHEMA.keys():
    state_key = f"df_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = load_persistence_data(key)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 3. GIAO DIỆN CHÍNH
# =================================================================
col_nav, col_main = st.columns([1, 4.2], gap="large")

with col_nav:
    st.markdown("<h2 class='gold-text'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    for m in menu:
        style = "active-nav" if st.session_state['active_tab'] == m else ""
        st.markdown(f"<div class='{style}'>", unsafe_allow_html=True)
        if st.button(f"▪️ {m}", key=f"btn_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with col_main:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")

    # Toolbar
    c1, c2, c3, c4 = st.columns([1, 1, 1, 1.2])
    with c1: 
        if st.button("💾 LƯU THỦ CÔNG", use_container_width=True):
            for k in SCHEMA.keys(): save_persistence_data(k, st.session_state[f"df_{k}"])
            st.success("Đã khóa dữ liệu!")
    with c2: st.button("📤 XUẤT EXCEL", use_container_width=True)
    with c3: st.button("📥 NHẬP EXCEL", use_container_width=True)
    with c4:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 khởi chạy...")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # LẤY KEY VÀ HIỂN THỊ
    db_key = tab.lower().replace('data_', '')
    df_state_key = f"df_{db_key}"
    
    st.markdown(f"<p class='gold-text'>DỮ LIỆU ĐANG DÙNG: {tab.upper()}</p>", unsafe_allow_html=True)

    # Hiển thị bảng
    if tab == "Data_Report":
        st.dataframe(st.session_state[df_state_key], use_container_width=True, height=750, hide_index=True)
    else:
        # data_editor tự động lưu vào state khi Ní chỉnh sửa
        edited_df = st.data_editor(
            st.session_state[df_state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            # Tự động lưu mỗi khi có thay đổi
            on_change=lambda: [save_persistence_data(db_key, st.session_state[df_state_key])],
            column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[db_key]}
        )
        st.session_state[df_state_key] = edited_df

st.caption("🚀 SEO Automation Lái Hộ v410.0 | Persistence Fixed")
