import streamlit as st
import pandas as pd
import os

# 1. KHỞI TẠO SCHEMA CHUẨN (PHẢI CHẠY ĐẦU TIÊN)
SCHEMA = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# 2. HỆ THỐNG LƯU TRỮ (PERSISTENCE)
def load_db(key):
    path = f"db_v11_{key}.csv"
    if os.path.exists(path):
        try: return pd.read_csv(path).fillna("")
        except: pass
    cols = SCHEMA[key]
    if key == "Dashboard":
        return pd.DataFrame([["GEMINI_API_KEY", ""], ["SENDER_EMAIL", ""], ["TARGET_URL", ""], ["FOLDER_DRIVE_ID", ""], ["Số lượng bài/ngày", "10"], ["Mật độ Link", "3-5"]]+[["...", ""]]*7, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def save_db(key, df):
    df.to_csv(f"db_v11_{key}.csv", index=False)

# KHỞI TẠO SESSION STATE
for k in SCHEMA.keys():
    if f"df_{k}" not in st.session_state:
        st.session_state[f"df_{k}"] = load_db(k)
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# 3. GIAO DIỆN & STYLE (NÚT BẰNG NHAU, SÁT NHAU, ICON CÓ MÀU)
st.set_page_config(page_title="SEO Lái Hộ Master", page_icon="🚕", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT BẰNG NHAU & SÁT NHAU */
    .nav-btn button {
        width: 100% !important;
        height: 45px !important;
        text-align: left !important;
        background-color: #111111 !important;
        border: 1px solid #333 !important;
        border-radius: 6px !important;
        margin-bottom: -5px !important; /* Cho các nút sát vào nhau */
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .active-tab button {
        background-color: #222222 !important;
        border-left: 5px solid #ffd700 !important;
        color: #ffd700 !important;
    }
    .nav-btn button:hover { border-color: #ffd700 !important; }

    /* NÚT TÍNH NĂNG Ở BẢNG (BẰNG NHAU, 1 HÀNG) */
    .stButton>button {
        width: 100% !important;
        height: 42px !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
    }
    .btn-red button { background-color: #ff0000 !important; color: #fff !important; border: none !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; border: none !important; }
    .btn-save button { background-color: #1e3a8a !important; color: #fff !important; border: none !important; }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC 2 CỘT (SIDEBAR CỐ ĐỊNH)
nav_col, main_col = st.columns([1, 4.5], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; margin-bottom:0px;'>🚕 LÁI HỘ SEO</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
    
    # DANH SÁCH MENU VỚI ICON CÓ MÀU
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

# 5. NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR: 4 NÚT BẰNG NHAU, SÁT NHAU TRÊN 1 HÀNG
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        st.markdown('<div class="btn-save">', unsafe_allow_html=True)
        if st.button("💾 LƯU CỨNG", use_container_width=True):
            for k in SCHEMA.keys(): save_db(k, st.session_state[f"df_{k}"])
            st.toast("Đã khóa dữ liệu vào hệ thống!")
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
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 khởi động...")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
            st.button("🔄 ĐỒNG BỘ", key=f"sy_{tab}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#ffd700; font-weight:700;'>HỆ THỐNG DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (TỰ ĐỘNG LƯU KHI EDIT)
    state_key = f"df_{tab}"
    if tab == "Data_Report":
        st.dataframe(st.session_state[state_key], use_container_width=True, height=750, hide_index=True)
    else:
        st.session_state[state_key] = st.data_editor(
            st.session_state[state_key],
            use_container_width=True,
            num_rows="dynamic",
            height=700,
            hide_index=True,
            column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[tab]}
        )

st.caption("🚀 SEO Automation Lái Hộ v1100.0 | Perfect UI | Persistence")
