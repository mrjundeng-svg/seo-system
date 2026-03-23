import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS PHONG CÁCH "ENTERPRISE WHITE"
st.set_page_config(page_title="SEO Lái Hộ - Quản trị viên", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* Font chữ Inter chuẩn App quốc tế */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #f9fafb; color: #111827; }
    
    /* XÓA KHOẢNG TRẮNG ĐẦU TRANG & TIÊU ĐỀ THỪA */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; }
    footer { visibility: hidden; }

    /* SIDEBAR TRẮNG GỌN GÀNG (Giống ảnh mẫu Ní gửi) */
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e5e7eb; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { color: #374151; font-weight: 500; }
    
    /* Cấu hình bảng dữ liệu (Table) */
    [data-testid="stDataFrame"] { background-color: white; border-radius: 8px; border: 1px solid #e5e7eb; }
    
    /* Nút bấm phong cách Modern (Xanh Lá của Lái Hộ) */
    .stButton>button {
        width: 100%; border-radius: 6px; font-weight: 600; height: 2.8em;
        transition: all 0.2s; border: 1px solid #d1d5db; background-color: white; color: #374151;
    }
    .stButton>button:hover { border-color: #10b981; color: #10b981; background-color: #f0fdf4; }
    
    /* Nút chạy chính (Màu xanh lá đậm) */
    .btn-run button { background-color: #10b981 !important; color: white !important; border: none !important; }
    .btn-run button:hover { background-color: #059669 !important; }

    /* Hộp thông tin / Log */
    .log-card { background-color: #f3f4f6; border-radius: 8px; padding: 15px; font-family: monospace; font-size: 13px; color: #1f2937; border: 1px solid #e5e7eb; }
    
    /* Header bảng */
    .table-header { font-size: 18px; font-weight: 700; color: #111827; margin-bottom: 10px; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU CHUẨN (NẠP ĐỦ 13 DÒNG TỪ EXCEL)
MENU_MAP = {
    "Bảng điều khiển": "config",
    "Quản lý Backlink": "backlink",
    "Hệ thống Website": "website",
    "Kho hình ảnh": "image",
    "Từ điển Spin": "spin",
    "Phủ sóng vùng": "local",
    "Báo cáo cuối": "report"
}

def init_all_data():
    for label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                # NẠP ĐỦ 13 DÒNG NHƯ TRONG ẢNH image_3079ff.png
                cols = ["Cấu hình (Cột A)", "Giá trị hiện tại (Cột B)"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Danh sách Keyword", "thuê tài xế lái hộ, đưa người say, lái xe hộ tphcm..."],
                    ["Website đối thủ", "lmd.vn, butl.vn, thuelai.app, saycar.vn"],
                    ["Mục tiêu nội dung", "Bài viết tư vấn, giới thiệu dịch vụ, chốt sale"],
                    ["Số lượng bài/ngày", "10"],
                    ["Độ dài bài viết", "1000 - 1200 chữ"],
                    ["Mật độ Backlink", "3 - 5 link/bài"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 15, columns=["Từ khóa", "Link đích", "Đã dùng"])
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL/ID", "Ngày đăng", "Từ khóa 1", "Từ khóa 2", "Từ khóa 3", "Từ khóa 4", "Từ khóa 5", "Link bài", "Tiêu đề", "File ID", "Hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["STT", "Nội dung", "Trạng thái"])

init_all_data()

# 3. GIAO DIỆN ĐĂNG NHẬP (STYLE TRẮNG)
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1,1])[1]:
        st.markdown("<h3 style='text-align: center; margin-top: 10rem;'>Đăng nhập SEO Lái Hộ</h3>", unsafe_allow_html=True)
        u = st.text_input("Tài khoản", value="admin")
        p = st.text_input("Mật khẩu", type="password", value="123")
        if st.button("Truy cập"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # 4. SIDEBAR (THANH ĐIỀU HƯỚNG BÊN TRÁI)
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=50) # Icon demo
        st.markdown("#### ĐIỀU HÀNH SEO")
        st.markdown("---")
        choice = st.radio("Menu chính", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHU VỰC CHÍNH (XÓA KHOẢNG TRẮNG, SHOW DỮ LIỆU SÁT NÓC)
    st.markdown(f"<div class='table-header'>📍 {choice}</div>", unsafe_allow_html=True)
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Bảng điều khiển":
        # THANH CÔNG CỤ (Giống thanh lọc ở ảnh mẫu)
        col_btn, col_info = st.columns([1.5, 2])
        with col_btn:
            with st.container():
                c1, c2, c3 = st.columns([1, 1, 1])
                csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
                c1.download_button("📤 Xuất file", data=csv, file_name=f"{choice}.csv", use_container_width=True)
                up = c2.file_uploader("Nạp file", type=["csv"], label_visibility="collapsed")
                if c3.button("🔄 Đồng bộ"):
                    if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # CHIA CỘT: BẢNG CONFIG VÀ ĐIỀU KHIỂN
        col_table, col_run = st.columns([1.8, 1])
        
        with col_table:
            st.markdown("##### ⚙️ Thông số cấu hình (13 dòng)")
            # SHOW FULL 13 DÒNG - KHÔNG SCROLL
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=525 # Chiều cao chuẩn để hiện trọn 13 dòng dữ liệu
            )
        
        with col_run:
            st.markdown("##### 🚀 Vận hành robot")
            with st.container(border=True):
                st.write("Chiến dịch v55.0:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH"):
                    log_p = st.empty()
                    prog = st.progress(0)
                    for i in range(1, 11):
                        time.sleep(0.3)
                        prog.progress(i * 10)
                        log_p.markdown(f"<div class='log-card'>[LOG] {datetime.datetime.now().strftime('%H:%M:%S')} - Đang xử lý bài {i}/10...<br>🤖 AI Gemini đang viết bài theo logic v55.0...</div>", unsafe_allow_html=True)
                    st.success("Đã hoàn thành!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("📅 LẬP LỊCH ĐĂNG"):
                    st.toast("Đang quét bảng báo cáo để dãn cách giờ...")

    else:
        # CÁC TAB DATA KHÁC (SHOW BẢNG DÀI 30 DÒNG)
        st.markdown(f"##### 📊 Danh sách dữ liệu: {choice}")
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("Phiên bản v70.0 Enterprise | Phục vụ bởi Mr. JunDeng AI")
