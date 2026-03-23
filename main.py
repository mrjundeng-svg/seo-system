import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Lái Hộ v340.0", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU BÊN TRÁI CỐ ĐỊNH 100% */
    .nav-col { border-right: 1px solid #333333; height: 100vh; padding: 15px; }
    .gold-text { color: #ffd700 !important; font-weight: 700; font-size: 20px; }
    
    /* NÚT MENU */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 2px !important;
    }
    .stButton>button:hover { border: 1px solid #ffd700 !important; color: #ffd700 !important; background-color: #111111 !important; }
    .active-nav button { background-color: #1a1a1a !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }

    /* NÚT CHỨC NĂNG START & EXCEL */
    .btn-start button { background-color: #ff0000 !important; color: white !important; font-weight: 700 !important; height: 3.5em !important; text-transform: uppercase; border-radius: 8px !important; }
    .btn-excel button { background-color: #222222 !important; color: #ffd700 !important; border: 1px solid #ffd700 !important; height: 2.8em !important; font-size: 13px !important; font-weight: 700 !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU ĐÚNG CHUẨN CỘT CỦA NÍ
if 'tab' not in st.session_state: st.session_state['tab'] = "Dashboard"

def init_tables():
    # 13 Dòng cấu hình
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97..."], ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"], ["FOLDER_DRIVE_ID", "1STdk4mp..."],
            ["Số lượng bài/ngày", "10"], ["Mật độ Link", "3-5"], ["Trạng thái", "Sẵn sàng"]
        ] + [["...", ""]] * 5, columns=["Hạng mục", "Giá trị"])

    # Cấu trúc các bảng theo đúng yêu cầu
    sheets = {
        "df_backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "df_website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
        "df_image": ["Link ảnh", "Đã dùng"],
        "df_spin": ["Từ Spin", "Bộ Spin"],
        "df_local": ["Tỉnh thành", "Quận", "Cung đường"],
        "df_report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
    }
    for key, cols in sheets.items():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=cols)

init_tables()

# 3. SIDEBAR CỐ ĐỊNH (2 CỘT)
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

# 4. KHU VỰC NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['tab']
    st.markdown(f"### 📍 {tab}")

    # Nút START cho Dashboard
    if tab == "Dashboard":
        c1, c2, c3, _ = st.columns([1.2, 1, 1, 2])
        with c1: st.markdown('<div class="btn-start">', unsafe_allow_html=True); st.button("🔥 START", use_container_width=True); st.markdown('</div>', unsafe_allow_html=True)
        with c2: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL", key="ex_d"); st.markdown('</div>', unsafe_allow_html=True)
        with c3: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL", key="im_d"); st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.markdown("<p class='gold-text'>⚙️ CẤU HÌNH (13 DÒNG)</p>", unsafe_allow_html=True)
        st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520)

    else:
        # Nút Export/Import Excel cho các trang khác
        xc1, xc2, _ = st.columns([1, 1, 3.5])
        with xc1: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL", key=f"ex_{tab}"); st.markdown('</div>', unsafe_allow_html=True)
        with xc2: st.markdown('<div class="btn-excel">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL", key=f"im_{tab}"); st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        # Lấy bảng dữ liệu tương ứng
        df_key = f"df_{tab.split('_')[1].lower()}"
        st.markdown(f"<p class='gold-text'>📥 DỮ LIỆU: {tab.upper()}</p>", unsafe_allow_html=True)
        
        if tab == "Data_Report":
            st.dataframe(st.session_state[df_key], use_container_width=True, height=750)
        else:
            st.session_state[df_key] = st.data_editor(st.session_state[df_key], use_container_width=True, num_rows="dynamic", height=750)

st.caption("🚀 SEO Automation Lái Hộ v340.0 | Full Final Columns")
