import streamlit as st
import pandas as pd
import os

# 1. SCHEMA DỮ LIỆU CHUẨN
SCHEMA = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# 2. HỆ THỐNG LƯU TRỮ TỰ ĐỘNG (BẤT TỬ)
def get_path(key): return f"db_v13_{key}.csv"

def load_db(key):
    path = get_path(key)
    if os.path.exists(path):
        try: return pd.read_csv(path).fillna("")
        except: pass
    cols = SCHEMA[key]
    if key == "Dashboard":
        return pd.DataFrame([["GEMINI_API_KEY", ""], ["SENDER_EMAIL", ""], ["TARGET_URL", ""], ["FOLDER_DRIVE_ID", ""]]+[["...", ""]]*9, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def auto_save(key, df):
    df.to_csv(get_path(key), index=False)

# KHỞI TẠO SESSION STATE
for k in SCHEMA.keys():
    if f"df_{k}" not in st.session_state:
        st.session_state[f"df_{k}"] = load_db(k)
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 3. GIAO DIỆN & STYLE (NÚT BẰNG NHAU, SÁT NHAU, ICON RỰC RỠ)
st.set_page_config(page_title="SEO Lái Hộ Master", page_icon="🚕", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT BẰNG NHAU & SÁT NHAU TUYỆT ĐỐI */
    .nav-btn button {
        width: 100% !important;
        height: 48px !important;
        text-align: left !important;
        background-color: #111111 !important;
        border: 1px solid #222 !important;
        border-radius: 0px !important; /* Để vuông vức khi xếp chồng */
        margin-bottom: -1px !important; /* Xóa khoảng cách giữa các nút */
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }
    .active-tab button {
        background-color: #1a1a1a !important;
        border-left: 6px solid #ffd700 !important;
        color: #ffd700 !important;
    }
    .nav-btn button:hover { background-color: #1a1a1a !important; border-color: #ffd700 !important; }

    /* TOOLBAR NÚT TÍNH NĂNG (BẰNG NHAU, SÁT NHAU) */
    .stButton>button {
        width: 100% !important;
        height: 45px !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
    }
    .btn-red button { background-color: #ff0000 !important; color: #fff !important; border: none !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; border: none !important; }
    .btn-blue button { background-color: #0055ff !important; color: #fff !important; border: none !important; }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    
    /* STATUS AUTO-SAVE */
    .save-status { font-size: 12px; color: #00ff00; font-style: italic; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC 2 CỘT
nav_col, main_col = st.columns([1, 4.2], gap="small")

with nav_col:
    st.markdown("<h1 style='color:#ffd700; margin-bottom:10px; font-size:28px;'>🚕 LÁI HỘ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#777; font-size:12px;'>AUTOMATION SYSTEM</p>", unsafe_allow_html=True)
    
    menu_icons = {
        "Dashboard": "🏠", "Data_Backlink": "🔗", "Data_Website": "🌐", 
        "Data_Image": "🖼️", "Data_Spin": "🔄", "Data_Local": "📍", "Data_Report": "📊"
    }
    
    for m in SCHEMA.keys():
        is_active = st.session_state['active_tab'] == m
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(f"{menu_icons.get(m, '▪️')} {m}", key=f"n_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR: 4 NÚT CHIỀU NGANG BẰNG NHAU, SÁT NHAU
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if "Dashboard" in tab:
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 đang vận hành...")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
            st.button("🔄 ĐỒNG BỘ", key=f"sy_{tab}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        st.button("📧 GỬI REPORT", key=f"mail_{tab}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div class='save-status'>● Auto-saving enabled</div>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG & AUTO-SAVE KHI CÓ THAY ĐỔI
    state_key = f"df_{tab}"
    
    # Dùng data_editor để Ní sửa hoặc dán dữ liệu vào
    edited_df = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        num_rows="dynamic",
        height=720,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[tab]}
    )
    
    # KIỂM TRA THAY ĐỔI ĐỂ TỰ ĐỘNG LƯU
    if not edited_df.equals(st.session_state[state_key]):
        st.session_state[state_key] = edited_df
        auto_save(tab, edited_df)
        st.toast(f"Đã tự động lưu {tab}!", icon="💾")

st.caption("🚀 Lái Hộ SEO v1300.0 | Perfect Symmetry | Real-time Auto-Save")
