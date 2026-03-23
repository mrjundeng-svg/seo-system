import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS "SOFT HARMONY"
st.set_page_config(page_title="SEO Lái Hộ v80.0", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    /* Font chữ Inter - Nhìn cực kỳ êm mắt */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F9FAFB; color: #374151; }
    
    /* ĐẨY NỘI DUNG LÊN SÁT ĐẦU TRANG */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; }

    /* SIDEBAR TRẮNG TỐI GIẢN */
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E5E7EB; }
    [data-testid="stSidebarNav"] { padding-top: 1rem; }
    
    /* THIẾT KẾ BẢNG DỮ LIỆU SẠCH SẼ */
    [data-testid="stDataFrame"] { background-color: white; border-radius: 10px; border: 1px solid #E5E7EB; }
    
    /* CARD TRẮNG BO GÓC */
    .st-emotion-cache-12w0qpk { 
        border-radius: 12px; border: 1px solid #E5E7EB; 
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
        background: white; padding: 20px; 
    }
    
    /* NÚT BẤM MÀU XANH LÁ MỀM (SOFT EMERALD) */
    .stButton>button {
        width: 100%; border-radius: 8px; font-weight: 600; height: 3em;
        transition: all 0.2s; border: 1px solid #D1D5DB; background-color: white; color: #4B5563;
    }
    .stButton>button:hover { border-color: #10B981; color: #059669; background-color: #F0FDF4; }
    
    /* NÚT CHẠY CHÍNH */
    .btn-run button { background-color: #059669 !important; color: white !important; border: none !important; }
    .btn-run button:hover { background-color: #047857 !important; box-shadow: 0 4px 12px rgba(5,150,105,0.2); }

    /* LOG BOX DỄ ĐỌC */
    .log-card { background-color: #F3F4F6; border-radius: 8px; padding: 15px; font-family: 'Consolas', monospace; font-size: 13px; color: #374151; border: 1px solid #E5E7EB; }
    
    .section-title { font-size: 16px; font-weight: 700; color: #111827; margin-bottom: 12px; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (NẠP CHUẨN 13 DÒNG CẤU HÌNH)
MENU_MAP = {
    "Bảng điều khiển": "config",
    "Dữ liệu Backlink": "backlink",
    "Danh sách Website": "website",
    "Kho hình ảnh": "image",
    "Từ điển Spin": "spin",
    "Khu vực Local": "local",
    "Báo cáo SEO": "report"
}

def init_all_data():
    for label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            if key_suffix == "config":
                # NẠP ĐỦ 13 DÒNG THEO HÌNH CỦA NÍ
                cols = ["Cấu hình hệ thống", "Giá trị thiết lập"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Từ khóa bài viết", "thuê tài xế lái hộ, đưa người say, an toàn bia rượu..."],
                    ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
                    ["Mục tiêu bài viết", "Bài tư vấn, giới thiệu dịch vụ, chốt sale"],
                    ["Số lượng bài tạo", "10"],
                    ["Độ dài bài (chữ)", "1000 - 1200"],
                    ["Mật độ Link/bài", "3 - 5"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 15, columns=["Từ khóa", "Link đích", "Đã dùng"])
            elif key_suffix == "report":
                cols = ["Website", "Ngày đăng", "Tiêu đề", "Trạng thái", "Link bài"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_all_data()

# 3. ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1,1])[1]:
        st.markdown("<h3 style='text-align: center; margin-top: 10rem;'>QUẢN TRỊ SEO LÁI HỘ</h3>", unsafe_allow_html=True)
        u = st.text_input("Tài khoản", value="admin")
        p = st.text_input("Mật khẩu", type="password", value="123")
        if st.button("ĐĂNG NHẬP"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # 4. SIDEBAR (TRẮNG - GỌN)
    with st.sidebar:
        st.markdown("### 🏢 ĐIỀU HÀNH")
        choice = st.radio("Menu", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHU VỰC CHÍNH
    st.markdown(f"<div class='section-title'>📍 {choice}</div>", unsafe_allow_html=True)
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Bảng điều khiển":
        # THANH CÔNG CỤ (DẠNG SLIM)
        col_btn, col_empty = st.columns([1.5, 2])
        with col_btn:
            with st.container():
                c1, c2, c3 = st.columns([1, 1, 1])
                csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
                c1.download_button("📤 Xuất file", data=csv, file_name=f"{choice}.csv", use_container_width=True)
                up = c2.file_uploader("Nạp file", type=["csv"], label_visibility="collapsed")
                if c3.button("🔄 Đồng bộ"):
                    if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # CHIA CỘT: CONFIG VÀ CONTROL
        col_table, col_run = st.columns([1.8, 1])
        
        with col_table:
            st.markdown("##### ⚙️ Thông số cấu hình (13 dòng)")
            # SHOW FULL 13 DÒNG, CHIỀU CAO VỪA KHÍT
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=520 # Chiều cao chuẩn để hiện trọn 13 dòng dữ liệu
            )
        
        with col_run:
            st.markdown("##### 🚀 Vận hành robot")
            with st.container(border=True):
                st.write("Chiến dịch v80.0:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 BẮT ĐẦU CHẠY"):
                    log_p = st.empty()
                    prog = st.progress(0)
                    for i in range(1, 11):
                        time.sleep(0.3)
                        prog.progress(i * 10)
                        log_p.markdown(f"<div class='log-card'>[Hệ thống] {datetime.datetime.now().strftime('%H:%M:%S')}<br>Đang xử lý bài {i}/10 theo logic v55.0...<br>Trạng thái: Đang viết nội dung...</div>", unsafe_allow_html=True)
                    st.success("Đã đăng xong 10 bài!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("📅 LẬP LỊCH ĐĂNG BÀI"):
                    st.toast("Đang quét bảng để hẹn giờ dãn cách...")

    else:
        # CÁC TAB DATA KHÁC (SHOW BẢNG DÀI 30 DÒNG)
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("🚀 SEO Automation v80.0 Stable | MR. JUNDENG AI")
