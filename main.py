import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS "BLACK - WHITE - RED"
st.set_page_config(page_title="SEO Lái Hộ - Admin", page_icon="⚙️", layout="wide")

st.markdown("""
    <style>
    /* 1. TỔNG THỂ TRẮNG TINH KHÔI */
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;500;700&display=swap');
    
    .stApp { background-color: #FFFFFF !important; }
    
    /* Chữ đen toàn hệ thống */
    * { color: #000000 !important; font-family: 'Roboto Mono', monospace !important; }
    
    /* Đẩy nội dung lên sát nóc */
    .block-container { padding-top: 1rem !important; }
    header { visibility: hidden; }

    /* 2. KHUNG MÀU ĐEN (BORDERS) */
    [data-testid="stSidebar"] { 
        background-color: #FFFFFF !important; 
        border-right: 2px solid #000000 !important; 
    }
    
    /* Khung bảng và các ô dữ liệu */
    [data-testid="stDataFrame"], div[data-testid="stTable"] { 
        border: 2px solid #000000 !important; 
        border-radius: 0px !important; 
    }
    
    /* Các khung bao quanh (Card) */
    div[data-testid="stExpander"], .st-emotion-cache-12w0qpk {
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
        border-radius: 0px !important;
    }

    /* 3. NÚT BẤM MÀU ĐỎ (RED BUTTONS) */
    .stButton>button {
        width: 100%; border-radius: 0px; font-weight: 700; height: 3em;
        transition: all 0.2s; 
        border: 2px solid #000000 !important; 
        background-color: #FF0000 !important; 
        color: #FFFFFF !important;
        text-transform: uppercase;
    }
    .stButton>button:hover { 
        background-color: #CC0000 !important; 
        box-shadow: 4px 4px 0px #000000;
    }
    
    /* Nút xuất file/đồng bộ (Nếu muốn khác biệt có thể để nền trắng viền đen) */
    .stDownloadButton>button {
        background-color: #000000 !important;
        color: #FFFFFF !important;
    }

    /* 4. TÙY CHỈNH INPUT */
    input { border: 2px solid #000000 !important; border-radius: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU CHUẨN (13 DÒNG CONFIG)
MENU_MAP = {
    "BẢNG ĐIỀU KHIỂN": "config",
    "DATA BACKLINK": "backlink",
    "DATA WEBSITE": "website",
    "KHO HÌNH ẢNH": "image",
    "TỪ ĐIỂN SPIN": "spin",
    "KHU VỰC LOCAL": "local",
    "BÁO CÁO CUỐI": "report"
}

def init_session():
    for label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                cols = ["DANH MỤC", "GIÁ TRỊ"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["KEYWORD", "thuê tài xế lái hộ, đưa người say..."],
                    ["ĐỐI THỦ", "lmd.vn, butl.vn, saycar.vn"],
                    ["MỤC TIÊU", "Bài viết tư vấn, chốt sale dịch vụ"],
                    ["SỐ LƯỢNG BÀI", "10"],
                    ["ĐỘ DÀI BÀI", "1000 - 1200 chữ"],
                    ["MẬT ĐỘ LINK", "3 - 5"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 15, columns=["Từ khóa", "Link đích", "Đã dùng"])
            else:
                st.session_state[key] = pd.DataFrame(columns=["CỘT 1", "CỘT 2", "CỘT 3"])

init_session()

# 3. SIDEBAR
with st.sidebar:
    st.markdown("## ⚙️ HỆ THỐNG SEO")
    st.markdown("---")
    choice = st.radio("MENU", list(MENU_MAP.keys()), label_visibility="collapsed")
    st.markdown("---")
    if st.button("🚪 THOÁT"):
        st.session_state['logged_in'] = False
        st.rerun()

# 4. KHU VỰC CHÍNH
st.markdown(f"### 📍 {choice}")
current_key = f"df_{MENU_MAP[choice]}"

if choice == "BẢNG ĐIỀU KHIỂN":
    # THANH CÔNG CỤ
    c1, c2, c3, c4 = st.columns([1, 1.2, 1, 2])
    csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
    c1.download_button("📤 XUẤT CSV", data=csv, file_name=f"{choice}.csv", use_container_width=True)
    up = c2.file_uploader("NHẬP FILE", type=["csv"], label_visibility="collapsed")
    if c3.button("🔄 ĐỒNG BỘ"):
        if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # CHIA CỘT: CONFIG VÀ CONTROL
    col_table, col_run = st.columns([1.8, 1])
    
    with col_table:
        st.markdown("**⚙️ CẤU HÌNH HỆ THỐNG (13 DÒNG)**")
        # SHOW FULL 13 DÒNG KHÔNG CẦN CUỘN
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key], 
            use_container_width=True, 
            num_rows="fixed",
            height=520 
        )
    
    with col_run:
        st.markdown("**🚀 ĐIỀU KHIỂN**")
        with st.container():
            st.write("Vận hành v55.0:")
            if st.button("🔥 CHẠY CHIẾN DỊCH"):
                with st.spinner('ĐANG THỰC THI...'):
                    time.sleep(2)
                st.success("✅ HOÀN THÀNH!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📅 LẬP LỊCH ĐĂNG"):
                st.toast("ĐANG QUÉT LỊCH HẸN...")

else:
    # TAB DATA KHÁC
    st.session_state[current_key] = st.data_editor(
        st.session_state[current_key],
        use_container_width=True,
        num_rows="dynamic",
        height=1000 
    )

st.caption("🚀 SEO AUTOMATION v120.0 | BLACK & RED EDITION")
