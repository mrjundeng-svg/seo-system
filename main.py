import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & CSS "PURE WHITE ENTERPRISE"
st.set_page_config(page_title="Hệ thống SEO Lái Hộ", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    /* 1. ÉP NỀN TRẮNG TOÀN BỘ HỆ THỐNG */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    /* Nền chính trắng xám nhẹ giống mẫu */
    .stApp { background-color: #f9fafb !important; }
    
    /* Sidebar trắng tinh */
    [data-testid="stSidebar"] { 
        background-color: #ffffff !important; 
        border-right: 1px solid #eeeeee !important; 
    }
    
    /* Đẩy nội dung lên sát nóc */
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; }
    header { visibility: hidden; }

    /* 2. CHỮ & TIÊU ĐỀ (MÀU XANH LÁ GIỐNG MẪU) */
    h1, h2, h3, .section-header { 
        color: #10b981 !important; 
        font-family: 'Inter', sans-serif;
        font-weight: 600;
    }
    .stMarkdown p { color: #374151; }

    /* 3. BẢNG DỮ LIỆU (TRẮNG, VIỀN MẢNH) */
    [data-testid="stDataFrame"] { 
        background-color: white !important; 
        border-radius: 8px !important; 
        border: 1px solid #e5e7eb !important; 
    }
    
    /* 4. NÚT BẤM (VIỀN XANH LÁ, NỀN TRẮNG) */
    .stButton>button {
        width: 100%; border-radius: 6px; font-weight: 500; height: 2.8em;
        transition: all 0.2s; border: 1px solid #10b981; background-color: white; color: #10b981;
    }
    .stButton>button:hover { background-color: #f0fdf4; border-color: #059669; color: #059669; }
    
    /* Nút chạy bài (Nền xanh lá chữ trắng) */
    .btn-run button { 
        background-color: #10b981 !important; 
        color: white !important; 
        border: none !important;
    }

    /* 5. KHUNG NHẬP LIỆU (CARD TRẮNG) */
    div[data-testid="stExpander"], .st-emotion-cache-12w0qpk {
        background-color: white !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 10px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    
    /* Log Box chuyển sang xám trắng cho hài hòa */
    .log-card { 
        background-color: #f8fafc; border-radius: 8px; padding: 12px; 
        font-family: 'Inter', sans-serif; font-size: 13px; color: #4b5563; 
        border: 1px solid #e2e8f0; 
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (NẠP ĐỦ 13 DÒNG)
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
                cols = ["Cấu hình hệ thống", "Giá trị thiết lập"]
                data = [
                    ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                    ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
                    ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
                    ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["TARGET_URL", "https://laiho.vn/"],
                    ["Từ khóa bài viết", "thuê tài xế lái hộ, đưa người say..."],
                    ["Đối thủ cạnh tranh", "lmd.vn, butl.vn, saycar.vn"],
                    ["Mục tiêu nội dung", "Bài viết tư vấn, chốt sale dịch vụ"],
                    ["Số lượng bài tạo", "10"],
                    ["Độ dài bài viết", "1000 - 1200 chữ"],
                    ["Số Link mỗi bài", "3 - 5"],
                    ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 15, columns=["Từ khóa", "Link đích", "Đã dùng"])
            elif key_suffix == "report":
                st.session_state[key] = pd.DataFrame(columns=["Website", "Ngày đăng", "Tiêu đề", "Trạng thái", "Link bài"])
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_session()

# 3. ĐĂNG NHẬP (STYLE TRẮNG SẠCH)
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
if not st.session_state['logged_in']:
    with st.columns([1,1,1])[1]:
        st.markdown("<div style='height:150px'></div>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>Hệ thống Quản trị Lái Hộ</h3>", unsafe_allow_html=True)
        u = st.text_input("Username", value="admin")
        p = st.text_input("Password", type="password", value="123")
        if st.button("Đăng nhập"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # 4. SIDEBAR TRẮNG TINH (GIỐNG MẪU)
    with st.sidebar:
        st.markdown("<h2 style='color: #10b981; font-size: 20px;'>🏢 ĐIỀU HÀNH SEO</h2>", unsafe_allow_html=True)
        choice = st.radio("Menu", list(MENU_MAP.keys()), label_visibility="collapsed")
        st.markdown("<div style='height:350px'></div>", unsafe_allow_html=True)
        if st.button("🚪 Thoát hệ thống"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. KHU VỰC CHÍNH (TRẮNG & XANH LÁ)
    st.markdown(f"<h3 style='font-size: 22px;'>Danh sách {choice}</h3>", unsafe_allow_html=True)
    current_key = f"df_{MENU_MAP[choice]}"

    if choice == "Bảng điều khiển":
        # THANH CÔNG CỤ SLIM
        with st.container():
            c1, c2, c3, c4 = st.columns([1, 1.2, 1, 2])
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            c1.download_button("📤 Xuất file", data=csv, file_name=f"{choice}.csv", use_container_width=True)
            up = c2.file_uploader("Upload", type=["csv"], label_visibility="collapsed")
            if c3.button("🔄 Đồng bộ"):
                if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # CHIA CỘT: CONFIG VÀ CONTROL
        col_table, col_run = st.columns([1.8, 1])
        
        with col_table:
            st.markdown("<p style='font-weight:600;'>⚙️ Thông số cấu hình (13 dòng)</p>", unsafe_allow_html=True)
            # SHOW FULL 13 DÒNG TRÊN NỀN TRẮNG
            st.session_state[current_key] = st.data_editor(
                st.session_state[current_key], 
                use_container_width=True, 
                num_rows="fixed",
                height=520 
            )
        
        with col_run:
            st.markdown("<p style='font-weight:600;'>🚀 Điều khiển chiến dịch</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Vận hành robot v55.0:")
                st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                    with st.spinner('Đang thực thi...'):
                        time.sleep(2)
                    st.success("✅ Thành công!")
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.button("📅 LẬP LỊCH ĐĂNG"):
                    st.toast("Đang quét lịch hẹn bài...")

    else:
        # CÁC TAB KHÁC SHOW BẢNG FULL TRÊN NỀN TRẮNG
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key],
            use_container_width=True,
            num_rows="dynamic",
            height=1000 
        )

    st.caption("🚀 Phiên bản Doanh nghiệp | Phát triển bởi Mr. JunDeng AI")
