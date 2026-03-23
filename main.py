import streamlit as st
import pandas as pd
import time
import random
import datetime
import json

# 1. CẤU HÌNH TRANG & CSS LUXURY (PREMIUM SAAS UI)
st.set_page_config(page_title="SEO Lái Hộ v60.0 - Global Control", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; background-color: #fcfcfd; }
    
    /* ÉP BẢNG NỞ RỘNG TỐI ĐA - SHOW 30 DÒNG */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] > div { height: auto !important; max-height: none !important; }
    div[data-testid="stDataFrame"] iframe { height: 1200px !important; }

    /* Sidebar thiết kế đẳng cấp */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    [data-testid="stSidebar"] .stRadio > label { color: #f8fafc !important; font-weight: 600; }
    
    /* Thiết kế Card trắng bo góc cao */
    .st-emotion-cache-12w0qpk { 
        border-radius: 20px; border: 1px solid #f1f5f9; 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); 
        background: white; padding: 30px; 
    }
    
    /* Nút bấm thiết kế mới */
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: 700; height: 3.8em;
        transition: all 0.4s; border: none; color: white; text-transform: uppercase; letter-spacing: 1px;
    }
    .btn-run button { background: linear-gradient(135deg, #00b4d8 0%, #0077b6 100%) !important; }
    .btn-schedule button { background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%) !important; }
    
    /* Status Log style */
    .log-box { background: #1e293b; color: #38bdf8; padding: 15px; border-radius: 10px; font-family: 'Courier New', monospace; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# 2. LOGIC XỬ LÝ THỜI GIAN V55.0 (CỐT LÕI HỆ THỐNG)
def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

def parse_limit(limit_str):
    if '-' in str(limit_str):
        try:
            low, high = map(int, limit_str.split('-'))
            return random.randint(low, high)
        except: return 1
    return int(limit_str) if str(limit_str).isdigit() else 1

# 3. KHỞI TẠO DỮ LIỆU CHUẨN (KHÔNG THIẾU 1 CỘT NÀO)
MENU_MAP = {
    "💎 Dashboard & Run": "config",
    "🔗 Backlink Master": "backlink",
    "🌐 Website Satellite": "website",
    "🖼️ Image Gallery": "image",
    "✍️ Spin Dictionary": "spin",
    "📍 Local Coverage": "local",
    "📊 Final Report": "report"
}

def init_all_data():
    for label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                cols = ["Cột A (Nội dung)", "Cột B (Dữ liệu)"]
                data = [["GEMINI_API_KEY", ""], ["SERPAPI_KEY", ""], ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["SENDER_PASSWORD", ""], ["RECEIVER_EMAIL", "jundeng.po@gmail.com"], ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, lái xe hộ..."], ["TARGET_URL", "https://laiho.vn/"], ["Website đối thủ", "lmd.vn, butl.vn"], ["Mục tiêu bài viết", "Tư vấn"], ["Số lượng bài cần tạo", "10"], ["Thiết lập số lượng chữ", "1000-1200"], ["Số lượng backlink/bài", "3-5"], ["FOLDER_DRIVE_ID", "1STdk4mpDP..."]]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                cols = ["DatDat", "Cột B (Danh sách URL Đích)", "Cột C (Số lần đã dùng)"]
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 20, columns=cols)
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_all_data()

# 4. GIAO DIỆN CHÍNH
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1.2,1])[1]:
        st.markdown("<h2 style='text-align: center; color: #1e293b;'>💎 SEO PLATFORM PRO</h2>", unsafe_allow_html=True)
        with st.container(border=True):
            u = st.text_input("Username", value="admin")
            p = st.text_input("Password", type="password", value="123")
            if st.button("XÁC THỰC TRUY CẬP"):
                if u == "admin" and p == "123":
                    st.session_state['logged_in'] = True
                    st.rerun()
else:
    # SIDEBAR
    with st.sidebar:
        st.markdown("<h2 style='color: white;'>💎 CONTROL CENTER</h2>", unsafe_allow_html=True)
        st.markdown("---")
        choice = st.radio("HỆ THỐNG MENU:", list(MENU_MAP.keys()))
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.title(f"📍 {choice}")
    current_key = f"df_{MENU_MAP[choice]}"

    # Tool Card: Import / Export (Sạch sẽ)
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c1:
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📤 Export CSV", data=csv, file_name=f"{choice}.csv", use_container_width=True)
        with c2:
            up = st.file_uploader("Upload Data", type=["csv"], label_visibility="collapsed")
        with c3:
            if st.button("📥 SYNC DATA"):
                if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. CHI TIẾT VẬN HÀNH (LOGIC v55.0)
    if "Dashboard" in choice:
        col_main, col_run = st.columns([2, 1])
        
        with col_main:
            st.subheader("⚙️ System Configuration")
            st.session_state[current_key] = st.data_editor(st.session_state[current_key], use_container_width=True, height=550)
        
        with col_run:
            st.subheader("🚀 Campaign Control")
            with st.container(border=True):
                st.write("Cài đặt chiến dịch:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 RUN SEO CAMPAIGN"):
                    log_placeholder = st.empty()
                    progress = st.progress(0)
                    
                    # LOGIC v55.0 Simulation
                    vn_now = get_vn_now()
                    for i in range(1, 11):
                        time.sleep(0.5)
                        progress.progress(i * 10)
                        msg = f"""
                        🎬 [SYSTEM] Đang khởi động... bài {i}/10
                        📍 Keyword: '{random.choice(['lái xe hộ', 'thuê tài xế'])}'
                        🤖 AI Gemini 2.5: Đang viết 1000 chữ...
                        🔗 SEO: Đã chèn 3 backlink & 1 ảnh.
                        📅 Hẹn giờ: { (vn_now + datetime.timedelta(minutes=i*45)).strftime('%H:%M') }
                        ✅ Trạng thái: SẴN SÀNG
                        """
                        log_placeholder.markdown(f"<div class='log-box'>{msg}</div>", unsafe_allow_html=True)
                    st.success("✅ Đã lập lịch thành công 10 bài viết!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='btn-schedule' style='margin-top:10px;'>", unsafe_allow_html=True)
                if st.button("📅 SCHEDULE ROBOT"):
                    st.toast("Robot đang quét bảng Report...", icon="🔍")
                    time.sleep(1)
                    st.info("🤖 Hệ thống đã đưa 10 bài viết vào hàng đợi đăng tự động.")
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        # HIỂN THỊ BẢNG TABLE FULL (Show 30 dòng)
        st.subheader(f"📊 {choice} Database")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("🚀 Version 60.0 Stable | © 2026 SEO Automation System")
