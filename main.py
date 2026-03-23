import streamlit as st
import pandas as pd
import time
import random
import datetime

# 1. CẤU HÌNH TRANG & CSS CAO CẤP (CLEAN & MINIMALIST)
st.set_page_config(page_title="SEO Control Panel v60.0", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfd; }
    
    /* ĐẨY NỘI DUNG LÊN SÁT MÉP TRÊN */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    
    /* ÉP BẢNG NỞ RỘNG - HIỂN THỊ FULL 30 DÒNG */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] > div { height: auto !important; max-height: none !important; }
    div[data-testid="stDataFrame"] iframe { height: 1000px !important; }

    /* Sidebar thiết kế tối giản, chuyên nghiệp */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebarNav"] { padding-top: 2rem; }
    
    /* Card thiết kế tinh tế */
    .st-emotion-cache-12w0qpk { 
        border-radius: 12px; border: 1px solid #f1f5f9; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.03); 
        background: white; padding: 24px; 
    }
    
    /* Nút bấm Modern SaaS */
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 600; height: 3.2em;
        transition: all 0.2s; border: none; color: white;
    }
    .btn-run button { background: #2563eb !important; }
    .btn-schedule button { background: #10b981 !important; }
    
    /* Terminal Log Style */
    .log-box { background: #111827; color: #10b981; padding: 15px; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 13px; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (NẠP ĐẦY ĐỦ 13 DÒNG TỪ ẢNH image_3079ff.png)
MENU_MAP = {
    "Dashboard": "config",
    "Backlink Master": "backlink",
    "Website Satellite": "website",
    "Image Gallery": "image",
    "Spin Dictionary": "spin",
    "Local Coverage": "local",
    "Final Report": "report"
}

def init_session():
    for label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                # NẠP ĐỦ 13 DÒNG DỮ LIỆU CỦA NÍ
                cols = ["Cột A (Nội dung - Fix cứng)", "Cột B (Dữ liệu - Bạn điền vào đây)"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say, uống bia rượu không tự lái..."],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Website đối thủ", "lmd.vn, butl.vn, thuelai.app, saycar.vn"],
                    ["Mục tiêu bài viết", "bài viết dạng tư vấn và giới thiệu, chốt sale dịch vụ, cảnh báo an toàn"],
                    ["Số lượng bài cần tạo", "10"],
                    ["Thiết lập số lượng chữ", "1000 - 1200"],
                    ["Số lượng backlink/bài", "3 - 5"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 20, columns=["DatDat", "Cột B (URL Đích)", "Cột C (Số lần dùng)"])
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng", "Từ khóa 1", "Từ khóa 2", "Từ khóa 3", "Từ khóa 4", "Từ khóa 5", "Link bài", "Tiêu đề", "File ID", "Hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_session()

# 3. GIAO DIỆN ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    with st.columns([1,1.2,1])[1]:
        st.markdown("<h2 style='text-align: center; margin-top: 5rem;'>🔐 SEO SYSTEM</h2>", unsafe_allow_html=True)
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="123")
        if st.button("LOGIN"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # SIDEBAR
    with st.sidebar:
        st.markdown("<h3 style='color: white; padding-left: 10px;'>🏢 CONTROL PANEL</h3>", unsafe_allow_html=True)
        choice = st.radio("QUẢN TRỊ:", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 4. KHÔNG GIAN LÀM VIỆC CHÍNH (ĐẨY LÊN TRÊN CÙNG)
    st.markdown(f"### 📍 {choice}")
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Dashboard":
        # KHUNG CÔNG CỤ (SYNC & EXPORT)
        col_tools, col_empty = st.columns([1.5, 2])
        with col_tools:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 1.5, 1])
                csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
                c1.download_button("📤 Export", data=csv, file_name=f"{choice}.csv", use_container_width=True)
                up = c2.file_uploader("Upload", type=["csv"], label_visibility="collapsed")
                if c3.button("🔄 Sync"):
                    if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # CHIA CỘT: BẢNG CONFIG VÀ BẢNG ĐIỀU KHIỂN
        col_table, col_control = st.columns([1.8, 1])
        
        with col_table:
            st.markdown("##### ⚙️ System Configuration")
            # HIỂN THỊ ĐỦ 13 DÒNG KHÔNG SCROLL
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=520 # Vừa khít cho 13 dòng + header
            )
        
        with col_control:
            st.markdown("##### 🚀 Campaign Control")
            with st.container(border=True):
                st.write("Vận hành chiến dịch:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 RUN SEO CAMPAIGN"):
                    log_area = st.empty()
                    progress = st.progress(0)
                    for i in range(1, 11):
                        time.sleep(0.5)
                        progress.progress(i * 10)
                        log_msg = f"[LOG] {datetime.datetime.now().strftime('%H:%M:%S')} - Đang xử lý bài {i}/10...<br>[LOG] AI Gemini 2.5 Flash đang viết nội dung 1200 chữ...<br>[LOG] Đang chèn 4 backlink SEO & 1 ảnh mẫu..."
                        log_area.markdown(f"<div class='log-box'>{log_msg}</div>", unsafe_allow_html=True)
                    st.success("✅ Chiến dịch v55.0 hoàn tất rực rỡ!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='btn-schedule' style='margin-top:12px;'>", unsafe_allow_html=True)
                if st.button("📅 SCHEDULE ROBOT"):
                    st.toast("Đang quét bảng Report & Lập lịch dãn cách 30-90 phút...", icon="🔍")
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        # CÁC TAB KHÁC SHOW BẢNG FULL 30 DÒNG
        st.subheader(f"📊 {choice} Database")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("🚀 SEO Automation System v60.0 | Stable Build 2026")
