import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & SIÊU CSS (DARK & GOLD APP STYLE)
st.set_page_config(page_title="Hệ thống SEO Lái Hộ", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    /* ÉP TÔNG MÀU ĐEN SÂU (DARK MODE) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp { background-color: #000000 !important; }
    
    /* Chữ Vàng / Trắng cho nội dung */
    .stMarkdown, label, p, span, h1, h2, h3, h4 { 
        color: #ffffff !important; 
        font-family: 'Inter', sans-serif !important; 
    }
    
    /* Đẩy nội dung lên sát nóc */
    .block-container { padding-top: 1rem !important; }
    header { visibility: hidden; }

    /* SIDEBAR ĐEN SANG TRỌNG */
    [data-testid="stSidebar"] { 
        background-color: #0a0a0a !important; 
        border-right: 1px solid #333333 !important; 
    }
    
    /* BẢNG DỮ LIỆU (DARK STYLE) */
    [data-testid="stDataFrame"] { 
        background-color: #1a1a1a !important; 
        border: 1px solid #ffd700 !important; 
    }
    
    /* NÚT BẤM MÀU VÀNG ĐỒNG (GOLD BUTTONS) */
    .stButton>button {
        width: 100%; border-radius: 12px; font-weight: 700; height: 3.5em;
        background-color: #ffd700 !important; /* MÀU VÀNG GOLD */
        color: #000000 !important;
        border: none !important;
        text-transform: uppercase;
        transition: 0.3s;
    }
    .stButton>button:hover { 
        background-color: #ffcc00 !important; 
        box-shadow: 0 4px 15px rgba(255, 215, 0, 0.4);
        transform: translateY(-2px);
    }
    
    /* NÚT XUẤT FILE / ĐỒNG BỘ (MÀU XÁM ĐẬM) */
    .stDownloadButton>button {
        background-color: #333333 !important;
        color: #ffffff !important;
        border-radius: 12px;
        border: 1px solid #ffd700 !important;
    }

    /* KHUNG THÔNG BÁO / LOG */
    .log-card { 
        background-color: #111111; border-radius: 12px; padding: 15px; 
        border: 1px solid #333333; color: #ffd700 !important;
    }
    
    /* TÙY CHỈNH TABLE EDITOR */
    [data-testid="stDataFrame"] div[role="gridcell"] { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (13 DÒNG CONFIG)
MENU_MAP = {
    "Bảng điều khiển": "config",
    "Quản lý Backlink": "backlink",
    "Hệ thống Website": "website",
    "Kho hình ảnh": "image",
    "Từ điển Spin": "spin",
    "Phủ sóng vùng": "local",
    "Báo cáo cuối": "report"
}

def init_session():
    for label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                cols = ["DANH MỤC CẤU HÌNH", "GIÁ TRỊ THIẾT LẬP"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Danh sách Keyword", "thuê tài xế lái hộ, đưa người say..."],
                    ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
                    ["Mục tiêu bài viết", "Tư vấn dịch vụ, chốt sale, an toàn"],
                    ["Số lượng bài/ngày", "10"],
                    ["Độ dài bài viết", "1000 - 1200 chữ"],
                    ["Mật độ Link", "3 - 5 link/bài"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 15, columns=["Từ khóa", "Link đích", "Đã dùng"])
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_session()

# 3. SIDEBAR (BLACK & GOLD)
with st.sidebar:
    st.markdown("<h2 style='color: #ffd700 !important;'>🚕 SEO LÁI HỘ</h2>", unsafe_allow_html=True)
    st.markdown("---")
    choice = st.radio("MENU", list(MENU_MAP.keys()), label_visibility="collapsed")
    st.markdown("---")
    if st.button("🚪 THOÁT"):
        st.session_state['logged_in'] = False
        st.rerun()

# 4. KHU VỰC CHÍNH
st.markdown(f"<h3 style='color: #ffd700 !important;'>📍 {choice}</h3>", unsafe_allow_html=True)
current_key = f"df_{MENU_MAP[choice]}"

if choice == "Bảng điều khiển":
    # THANH CÔNG CỤ (STYLE HIỆN ĐẠI)
    c1, c2, c3, c4 = st.columns([1, 1.2, 0.8, 2])
    csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
    
    with c1:
        st.download_button("📤 XUẤT CSV", data=csv, file_name=f"{choice}.csv", use_container_width=True)
    with c2:
        up = st.file_uploader("NHẬP FILE CSV", type=["csv"], label_visibility="collapsed")
    with c3:
        if st.button("🔄 SYNC"):
            if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # CHIA CỘT: CONFIG VÀ ĐIỀU KHIỂN
    col_table, col_run = st.columns([1.8, 1])
    
    with col_table:
        st.markdown("<p style='color: #ffd700;'>⚙️ CẤU HÌNH HỆ THỐNG (13 DÒNG)</p>", unsafe_allow_html=True)
        # SHOW FULL 13 DÒNG
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key], 
            use_container_width=True, 
            num_rows="fixed",
            height=520 
        )
    
    with col_run:
        st.markdown("<p style='color: #ffd700;'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
        with st.container():
            st.write("Vận hành v55.0 Stable:")
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                log_placeholder = st.empty()
                progress = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.3)
                    progress.progress(i * 10)
                    log_placeholder.markdown(f"<div class='log-card'>[LOG] {datetime.datetime.now().strftime('%H:%M:%S')} - Đang viết bài {i}/10...</div>", unsafe_allow_html=True)
                st.success("✅ HOÀN THÀNH!")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("📅 LẬP LỊCH ĐĂNG"):
                st.toast("Đang quét hàng đợi...")

else:
    # TAB DATA KHÁC (SHOW BẢNG 30 DÒNG)
    st.session_state[current_key] = st.data_editor(
        st.session_state[current_key],
        use_container_width=True,
        num_rows="dynamic",
        height=1000 
    )

st.caption("🚕 Hệ thống Quản trị SEO v140.0 | Gold Edition")
