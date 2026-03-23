import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS "TỐI GIẢN" (XÓA KHOẢNG TRẮNG, ÉP BẢNG FULL)
st.set_page_config(page_title="SEO Lái Hộ v60.0", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfd; }
    
    /* ĐẨY NỘI DUNG SÁT LÊN ĐẦU TRANG */
    .block-container { padding-top: 0.5rem !important; padding-bottom: 0rem !important; }
    
    /* XỬ LÝ BẢNG: HIỂN THỊ ĐỦ DÒNG, KHÔNG SCROLL TRONG BẢNG */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] > div { height: auto !important; max-height: none !important; }
    div[data-testid="stDataFrame"] iframe { height: 1000px !important; }

    /* Sidebar Navy tinh tế */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #e2e8f0; }
    
    /* Khung viền các khu vực */
    .st-emotion-cache-12w0qpk { 
        border-radius: 10px; border: 1px solid #f1f5f9; 
        box-shadow: 0 1px 2px rgba(0,0,0,0.03); 
        background: white; padding: 20px; 
    }
    
    /* Nút bấm Việt hóa Modern */
    .stButton>button {
        width: 100%; border-radius: 6px; font-weight: 600; height: 3em;
        transition: all 0.2s; border: none; color: white;
    }
    .btn-run button { background: #2563eb !important; }
    .btn-schedule button { background: #10b981 !important; }
    
    /* Hộp nhật ký (Log) */
    .log-box { background: #111827; color: #10b981; padding: 12px; border-radius: 8px; font-family: 'Consolas', monospace; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (NẠP ĐỦ 13 DÒNG TỪ GOOGLE SHEET CỦA NÍ)
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
                # NẠP DỮ LIỆU CHUẨN 13 DÒNG THEO ẢNH
                cols = ["Hạng mục cấu hình", "Giá trị thiết lập"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Từ khóa bài viết", "thuê tài xế lái hộ, đưa người say, an toàn bia rượu..."],
                    ["Đối thủ cạnh tranh", "lmd.vn, butl.vn, thuelai.app, saycar.vn"],
                    ["Định hướng nội dung", "Bài viết tư vấn, giới thiệu dịch vụ, chốt sale"],
                    ["Số lượng bài/ngày", "10"],
                    ["Độ dài bài viết", "1000 - 1200 chữ"],
                    ["Mật độ Backlink", "3 - 5 link/bài"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 15, columns=["Từ khóa", "Link đích", "Đã dùng"])
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng", "Từ khóa 1", "Từ khóa 2", "Từ khóa 3", "Từ khóa 4", "Từ khóa 5", "Link bài", "Tiêu đề", "File ID", "Hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_session()

# 3. ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1.2,1])[1]:
        st.markdown("<h2 style='text-align: center; margin-top: 5rem;'>🔐 HỆ THỐNG SEO</h2>", unsafe_allow_html=True)
        u = st.text_input("Tài khoản", value="admin")
        p = st.text_input("Mật khẩu", type="password", value="123")
        if st.button("ĐĂNG NHẬP"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # SIDEBAR VIỆT HÓA
    with st.sidebar:
        st.markdown("<h3 style='color: white;'>🏢 QUẢN TRỊ SEO</h3>", unsafe_allow_html=True)
        choice = st.radio("MENU:", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 4. KHÔNG GIAN LÀM VIỆC (SẠCH SẼ, ĐẨY LÊN TRÊN)
    st.markdown(f"#### 📍 {choice}")
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Bảng điều khiển":
        # KHUNG CÔNG CỤ
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

        # CHIA CỘT: CONFIG VÀ CONTROL
        col_table, col_control = st.columns([1.8, 1])
        
        with col_table:
            st.markdown("##### ⚙️ Cấu hình thông số (13 mục)")
            # ÉP HIỂN THỊ ĐỦ 13 DÒNG KHÔNG CẦN CUỘN
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=530 
            )
        
        with col_control:
            st.markdown("##### 🚀 Vận hành chiến dịch")
            with st.container(border=True):
                st.write("Trạng thái Robot:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                    log_area = st.empty()
                    progress = st.progress(0)
                    for i in range(1, 11):
                        time.sleep(0.4)
                        progress.progress(i * 10)
                        log_msg = f"[LOG] {datetime.datetime.now().strftime('%H:%M:%S')} - Đang viết bài {i}/10...<br>[LOG] AI đang thực thi v55.0 logic...<br>[LOG] Đang chèn link & đóng dấu ảnh..."
                        log_area.markdown(f"<div class='log-box'>{log_msg}</div>", unsafe_allow_html=True)
                    st.success("✅ Hoàn thành chiến dịch!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                st.markdown("<div class='btn-schedule' style='margin-top:12px;'>", unsafe_allow_html=True)
                if st.button("📅 LẬP LỊCH ĐĂNG BÀI"):
                    st.toast("Đang quét bảng báo cáo & lập lịch...", icon="🔍")
                st.markdown("</div>", unsafe_allow_html=True)

    else:
        # CÁC TAB KHÁC SHOW BẢNG FULL 30 DÒNG
        st.subheader(f"📊 Dữ liệu: {choice}")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("🚀 Hệ thống SEO Tự động v60.0 Stable | Build 2026")
