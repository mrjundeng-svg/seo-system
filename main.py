import streamlit as st
import pandas as pd
import time
import datetime

# 1. CẤU HÌNH TRANG & SIÊU CSS (ÉP BẢNG SÁNG TOÀN DIỆN)
st.set_page_config(page_title="Hệ thống SEO Lái Hộ", page_icon="🌿", layout="wide")

st.markdown("""
    <style>
    /* 1. ÉP TÔNG MÀU TRẮNG XÁM NHẸ TOÀN BỘ (GIỐNG MẪU 100%) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    .stApp { background-color: #f8fafc !important; }
    [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #e5e7eb !important; }
    
    /* 2. ĐẨY NỘI DUNG LÊN TRÊN & XÓA KHOẢNG TRẮNG */
    .block-container { padding-top: 2rem !important; }
    header { visibility: hidden; }

    /* 3. "DIỆT TẬN GỐC" MÀU ĐEN TRONG BẢNG (CRITICAL) */
    /* Ép tất cả thành phần của bảng về màu sáng */
    [data-testid="stDataFrame"] { background-color: white !important; border: 1px solid #e5e7eb !important; border-radius: 8px !important; }
    div[data-testid="stTable"] { background-color: white !important; }
    
    /* Ép màu chữ trong bảng */
    [data-testid="stDataFrame"] div[role="gridcell"] { color: #374151 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] { background-color: #f9fafb !important; color: #6b7280 !important; font-weight: 600 !important; }

    /* 4. TIÊU ĐỀ XANH LÁ MẠ (SOFT EMERALD) */
    .main-title { color: #10b981; font-size: 20px; font-weight: 600; margin-bottom: 20px; }
    .sub-title { color: #6b7280; font-size: 14px; font-weight: 500; margin-bottom: 10px; }

    /* 5. NÚT BẤM STYLE ĐẠI LÝ (MẢNH & SẠCH) */
    .stButton>button {
        width: 100%; border-radius: 6px; font-weight: 500; height: 2.6em;
        transition: all 0.2s; border: 1px solid #e5e7eb; background-color: white; color: #374151;
        font-size: 14px;
    }
    .stButton>button:hover { border-color: #10b981; color: #10b981; background-color: #f0fdf4; }
    
    /* Nút chạy chính */
    .btn-run button { background-color: #10b981 !important; color: white !important; border: none !important; }
    .btn-run button:hover { background-color: #059669 !important; }

    /* 6. KHUNG LOG & FORM (TRẮNG TINH) */
    div[data-testid="stExpander"], .st-emotion-cache-12w0qpk {
        background-color: white !important; border: 1px solid #e5e7eb !important; border-radius: 10px !important;
    }
    
    /* 7. CUSTOM FONT CHO TOÀN TRANG */
    * { font-family: 'Inter', sans-serif !important; }
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
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_session()

# 3. SIDEBAR (STYLE ĐẠI LÝ TRẮNG)
with st.sidebar:
    st.markdown("<div style='padding: 10px 0;'><h2 style='color: #10b981; font-size: 18px;'>🏢 ĐIỀU HÀNH SEO</h2></div>", unsafe_allow_html=True)
    choice = st.radio("Menu", list(MENU_MAP.keys()), label_visibility="collapsed")
    st.markdown("<div style='height:400px'></div>", unsafe_allow_html=True)
    if st.button("🚪 Thoát hệ thống"):
        st.session_state['logged_in'] = False
        st.rerun()

# 4. KHU VỰC CHÍNH (ÉP TÔNG TRẮNG PHẲNG)
st.markdown(f"<div class='main-title'>Danh sách {choice}</div>", unsafe_allow_html=True)
current_key = f"df_{MENU_MAP[choice]}"

if choice == "Bảng điều khiển":
    # THANH CÔNG CỤ MẢNH
    c1, c2, c3, c4 = st.columns([0.8, 1, 0.8, 2])
    csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
    c1.download_button("📤 Xuất file", data=csv, file_name=f"{choice}.csv", use_container_width=True)
    up = c2.file_uploader("Upload", type=["csv"], label_visibility="collapsed")
    if c3.button("🔄 Đồng bộ"):
        if up: st.session_state[current_key] = pd.read_csv(up); st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # CHIA CỘT: CONFIG VÀ CONTROL
    col_table, col_run = st.columns([1.8, 1])
    
    with col_table:
        st.markdown("<div class='sub-title'>⚙️ Thông số cấu hình (13 dòng)</div>", unsafe_allow_html=True)
        # BẢNG TRẮNG, VIỀN XÁM NHẠT
        st.session_state[current_key] = st.data_editor(
            st.session_state[current_key], 
            use_container_width=True, 
            num_rows="fixed",
            height=520 
        )
    
    with col_run:
        st.markdown("<div class='sub-title'>🚀 Điều khiển chiến dịch</div>", unsafe_allow_html=True)
        with st.container():
            st.write("Vận hành v55.0:")
            st.markdown("<div class='btn-run'>", unsafe_allow_html=True)
            if st.button("🔥 CHẠY CHIẾN DỊCH NGAY"):
                with st.spinner('Đang chạy...'): time.sleep(1)
                st.success("✅ Đã hoàn thành!")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("📅 LẬP LỊCH ĐĂNG"):
                st.toast("Đang quét lịch...")

else:
    # TAB DATA KHÁC
    st.session_state[current_key] = st.data_editor(
        st.session_state[current_key],
        use_container_width=True,
        num_rows="dynamic",
        height=1000 
    )

st.caption("🚀 SEO Automation | Clean Enterprise Interface")
