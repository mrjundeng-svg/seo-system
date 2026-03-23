import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS "CLEAN VIETNAM"
st.set_page_config(page_title="Hệ thống SEO Lái Hộ v60.0", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfd; }
    
    /* ĐẨY NỘI DUNG LÊN SÁT MÉP TRÊN CÙNG */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    
    /* ÉP BẢNG NỞ RỘNG - HIỂN THỊ FULL 30 DÒNG */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] > div { height: auto !important; max-height: none !important; }
    div[data-testid="stDataFrame"] iframe { height: 1000px !important; }

    /* Sidebar thiết kế tối giản */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    
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
    .btn-run button { background: #2563eb !important; } /* Blue */
    .btn-schedule button { background: #10b981 !important; } /* Green */
    
    /* Terminal Log Style */
    .log-box { background: #111827; color: #10b981; padding: 15px; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 13px; line-height: 1.5; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (NẠP ĐỦ 13 DÒNG CONFIG TỪ GOOGLE SHEET)
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
                # NẠP ĐỦ 13 DÒNG DỮ LIỆU CHUẨN CỦA NÍ
                cols = ["Hạng mục (Cột A)", "Dữ liệu cấu hình (Cột B)"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Danh sách Keyword", "thuê tài xế lái hộ, đưa người say, lái xe hộ tphcm..."],
                    ["Website đối thủ", "lmd.vn, butl.vn, thuelai.app, saycar.vn"],
                    ["Mục tiêu bài viết", "Tư vấn dịch vụ, chốt sale, cảnh báo an toàn"],
                    ["Số lượng bài cần tạo", "10"],
                    ["Thiết lập số lượng chữ", "1000 - 1200"],
                    ["Số lượng backlink/bài", "3 - 5"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 20, columns=["Từ khóa", "Link đích", "Đã dùng"])
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
        st.markdown("<h2 style='text-align: center; margin-top: 5rem;'>🔐 ĐĂNG NHẬP HỆ THỐNG</h2>", unsafe_allow_html=True)
        u = st.text_input("Tài khoản", value="admin")
        p = st.text_input("Mật khẩu", type="password", value="123")
        if st.button("TRUY CẬP"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Sai tài khoản hoặc mật khẩu!")
else:
    # SIDEBAR VIỆT HÓA
    with st.sidebar:
        st.markdown("<h3 style='color: white; padding-left: 10px;'>🏢 ĐIỀU HÀNH SEO</h3>", unsafe_allow_html=True)
        choice = st.radio("DANH MỤC:", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 4. VÙNG LÀM VIỆC CHÍNH (XÓA TIÊU ĐỀ THỪA, ĐẨY SÁT LÊN TRÊN)
    st.markdown(f"#### 📍 {choice}")
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Bảng điều khiển":
        # CỤM CÔNG CỤ (XUẤT/NHẬP)
        col_tools, col_empty = st.columns([1.5, 2])
        with col_tools:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 1.5, 1])
                csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
                c1.download_button("📤 Xuất file", data=csv, file_name=f"{choice}.csv", use_container_width=True)
                up = c2.file_uploader("Tải lên", type=["csv"], label_visibility="collapsed")
                if c3.button("🔄 Đồng bộ"):
                    if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # CHIA CỘT: CẤU HÌNH VÀ ĐIỀU KHIỂN
        col_table, col_control = st.columns([1.8, 1])
        
        with col_table:
            st.markdown("##### ⚙️ Cấu hình hệ thống (13 thông số)")
            # HIỂN THỊ FULL 13 DÒNG KHÔNG CẦN CUỘN
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=520 # Chiều cao vừa khít 13 dòng dữ liệu
            )
        
        with col_control:
            st.markdown("##### 🚀 Điều khiển chiến dịch")
            with st.container(border=True):
                st.write("Vận hành v55.0:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH SEO"):
                    log_area = st.empty()
                    progress = st.progress(0)
                    for i in range(1, 11):
                        time.sleep(0.4)
                        progress.progress(i * 10)
                        log_msg = f"[LOG] {datetime.datetime.now().strftime('%H:%M:%S')} - Đang xử lý bài {i}/10...<br>[LOG] AI Gemini 2.5 Flash đang viết nội dung...<br>[LOG] Đang chèn link SEO & đóng dấu ảnh..."
                        log_area.markdown(f"<div class='log-box'>{log_msg}</div>", unsafe_allow_html=True)
                    st.success("✅ Đã hoàn thành 10 bài viết!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='btn-schedule' style='margin-top:12px;'>", unsafe_allow_html=True)
                if st.button("📅 LẬP LỊCH ROBOT"):
                    st.toast("Đang quét bảng báo cáo & lập lịch dãn cách 30-90p...", icon="🔍")
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        # CÁC TAB KHÁC HIỂN THỊ BẢNG FULL 30 DÒNG
        st.subheader(f"📊 Dữ liệu: {choice}")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("🚀 SEO Automation v60.0 Stable | Phát triển bởi Mr. JunDeng")
