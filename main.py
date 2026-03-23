import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS PHONG CÁCH "ĐẠI LÝ CẤP 2" (TRẮNG & XANH LÁ)
st.set_page_config(page_title="Hệ thống Quản trị SEO", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    /* Font chữ Inter chuẩn quốc tế */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #fcfcfd; color: #374151; }
    
    /* XÓA KHOẢNG TRẮNG ĐẦU TRANG - ĐẨY WEB LÊN SÁT NÓC */
    .block-container { padding-top: 0rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; }
    footer { visibility: hidden; }

    /* SIDEBAR TRẮNG TINH KHÔI (GIỐNG ẢNH MẪU) */
    [data-testid="stSidebar"] { 
        background-color: #ffffff !important; 
        border-right: 1px solid #f0f0f0; 
        box-shadow: 2px 0 5px rgba(0,0,0,0.02);
    }
    [data-testid="stSidebarNav"] { padding-top: 0rem; }

    /* ĐỊNH DẠNG BẢNG DỮ LIỆU SẠCH SẼ */
    [data-testid="stDataFrame"] { border: 1px solid #eef2f6; border-radius: 8px; }
    
    /* NÚT BẤM PHONG CÁCH ĐẠI LÝ (VIỀN XANH LÁ, CHỮ XANH LÁ) */
    .stButton>button {
        width: 100%; border-radius: 6px; font-weight: 500; height: 2.8em;
        transition: all 0.2s; border: 1px solid #10b981; background-color: white; color: #10b981;
    }
    .stButton>button:hover { background-color: #f0fdf4; border-color: #059669; color: #059669; }
    
    /* NÚT CHẠY CHIẾN DỊCH (XANH LÁ ĐẬM - NỔI BẬT) */
    .btn-run button { 
        background-color: #10b981 !important; 
        color: white !important; 
        border: none !important;
        font-weight: 600 !important;
    }
    .btn-run button:hover { background-color: #059669 !important; box-shadow: 0 4px 10px rgba(16,185,129,0.3); }

    /* HỘP NHẬT KÝ (SOFT LOG) */
    .log-card { 
        background-color: #f9fafb; border-radius: 8px; padding: 12px; 
        font-family: 'Segoe UI', sans-serif; font-size: 13px; color: #4b5563; 
        border: 1px solid #f3f4f6; 
    }
    
    /* TIÊU ĐỀ MỤC */
    .section-header { font-size: 18px; font-weight: 600; color: #065f46; margin: 15px 0 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (NẠP CHUẨN 13 DÒNG CONFIG TỪ ẢNH CỦA NÍ)
MENU_MAP = {
    "Bảng điều khiển": "config",
    "Dữ liệu Backlink": "backlink",
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
                # NẠP ĐẦY ĐỦ 13 DÒNG NHƯ FILE EXCEL CỦA NÍ
                cols = ["Cấu hình (Cột A)", "Giá trị hiện tại (Cột B)"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Từ khóa bài viết", "thuê tài xế lái hộ, lái xe hộ tphcm, say rượu gọi tài xế..."],
                    ["Đối thủ cạnh tranh", "lmd.vn, butl.vn, saycar.vn"],
                    ["Mục tiêu nội dung", "Bài viết tư vấn chuyên sâu, chốt sale dịch vụ"],
                    ["Số lượng bài tạo", "10"],
                    ["Độ dài bài viết", "1000 - 1200 chữ"],
                    ["Số Link mỗi bài", "3 - 5"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 20, columns=["Từ khóa", "Link đích", "Đã dùng"])
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "Ngày đăng", "Tiêu đề", "Trạng thái", "Link bài"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_session()

# 3. ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1,1])[1]:
        st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>ĐIỀU HÀNH SEO LÁI HỘ</h3>", unsafe_allow_html=True)
        u = st.text_input("Tên đăng nhập", value="admin")
        p = st.text_input("Mật khẩu", type="password", value="123")
        if st.button("VÀO HỆ THỐNG"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # 4. SIDEBAR (TRẮNG TINH, CHỮ XÁM - GIỐNG ẢNH MẪU)
    with st.sidebar:
        st.markdown("<div style='padding: 10px 0;'><h4 style='color: #10b981;'>🏢 SEO DASHBOARD</h4></div>", unsafe_allow_html=True)
        choice = st.radio("Menu", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("<div style='height:300px'></div>", unsafe_allow_html=True)
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHU VỰC CHÍNH (XÓA TIÊU ĐỀ THỪA, ĐẨY SÁT NÓC)
    st.markdown(f"<div class='section-header'>Danh sách {choice}</div>", unsafe_allow_html=True)
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Bảng điều khiển":
        # THANH CÔNG CỤ (STYLE GIỐNG ẢNH MẪU)
        col_btn, col_empty = st.columns([1.8, 2])
        with col_btn:
            c1, c2, c3 = st.columns([1, 1.2, 1])
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            c1.download_button("📥 Xuất file", data=csv, file_name=f"{choice}.csv", use_container_width=True)
            up = c2.file_uploader("Nạp file CSV", type=["csv"], label_visibility="collapsed")
            if c3.button("🔄 Đồng bộ"):
                if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # CHIA CỘT: CONFIG VÀ ĐIỀU KHIỂN
        col_table, col_run = st.columns([2, 1])
        
        with col_table:
            st.markdown("<div style='font-weight:600; margin-bottom:10px;'>⚙️ Thông số cấu hình (13 dòng)</div>", unsafe_allow_html=True)
            # SHOW FULL 13 DÒNG, CHIỀU CAO VỪA KHÍT
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=520 
            )
        
        with col_run:
            st.markdown("<div style='font-weight:600; margin-bottom:10px;'>🚀 Vận hành robot</div>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Cài đặt chiến dịch:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH SEO"):
                    log_p = st.empty()
                    prog = st.progress(0)
                    for i in range(1, 11):
                        time.sleep(0.3)
                        prog.progress(i * 10)
                        log_msg = f"<b>[LOG] bài {i}/10</b>: Đang xử lý nội dung AI chuẩn v55.0..."
                        log_p.markdown(f"<div class='log-card'>{log_msg}</div>", unsafe_allow_html=True)
                    st.success("✅ Đã đăng thành công 10 bài viết!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("📅 LẬP LỊCH ĐĂNG"):
                    st.toast("Đang quét dữ liệu để dãn cách giờ...")

    else:
        # CÁC TAB DATA KHÁC (SHOW BẢNG DÀI 30 DÒNG)
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("Phiên bản v90.0 Enterprise | Thiết kế bởi Mr. JunDeng AI")
