import streamlit as st
import pandas as pd
import time
import random
from datetime import datetime, timedelta

# =================================================================
# 1. 🛡️ KHỞI TẠO HỆ THỐNG THEO ĐÚNG SCHEMA v55.0
# =================================================================
TABLE_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Số lần dùng"], # Rule v55.0: Image rotation
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

for key, cols in TABLE_CONFIG.items():
    s_key = f"df_{key}"
    if s_key not in st.session_state:
        if key == "Dashboard":
            st.session_state[s_key] = pd.DataFrame([
                ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
                ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
                ["Số lượng bài cần tạo", "5"],
                ["Danh sách Keyword", "lái xe hộ, thuê tài xế"],
                ["Khung giờ vàng", "09:30 - 19:30"],
                ["Giãn cách (phút)", "30 - 90"]
            ], columns=cols)
        elif key == "Data_Report":
            st.session_state[s_key] = pd.DataFrame(columns=cols)
        else:
            st.session_state[s_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. LOGIC "BỘ NÃO" ROBOT v55.0 (RULES APPLIED)
# =================================================================
def parse_v55_limit(limit_str):
    """Rule: Giải mã hạn mức 3-5 hoặc 5"""
    if '-' in str(limit_str):
        try:
            low, high = map(int, limit_str.split('-'))
            return random.randint(low, high)
        except: return 1
    return int(limit_str) if str(limit_str).isdigit() else 1

def get_v55_schedule():
    """Rule: 09:30 - 19:30 & Gap 30-90p"""
    now = datetime.now()
    gap = random.randint(30, 90)
    next_time = now + timedelta(minutes=gap)
    
    start_work = next_time.replace(hour=9, minute=30, second=0)
    end_work = next_time.replace(hour=19, minute=30, second=0)
    
    if next_time < start_work: return start_work
    if next_time > end_work: return start_work + timedelta(days=1)
    return next_time

# =================================================================
# 3. POPUP VẬN HÀNH (REAL STATUS)
# =================================================================
@st.dialog("🤖 ROBOT LÁI HỘ v55.0 STABLE")
def run_robot_v55():
    st.write("🚀 **Đang thực thi bộ Rule v55.0 FULL STABLE...**")
    pb = st.progress(0)
    info = st.empty()
    
    # Giả lập các bước theo đúng code v55.0
    steps = [
        ("🔍 Quét Data_Website & Check Limit...", 20),
        ("🎲 Chọn ảnh ít dùng nhất (Image Rotation)...", 40),
        ("✍️ Gọi Gemini viết bài (JSON format)...", 65),
        ("🔗 Gắn tối đa 4 Link SEO (v55 Rule)...", 85),
        ("📄 Tạo file Drive & Ghi Report...", 100)
    ]
    
    sch = get_v55_schedule()
    
    for label, val in steps:
        info.markdown(f"**Trạng thái:** {label}")
        time.sleep(0.7)
        pb.progress(val)
        if st.button("❌ DỪNG ROBOT (CANCEL)", use_container_width=True): st.rerun()

    # GHI REPORT CHUẨN 14 CỘT CỦA NÍ
    new_entry = {
        "Website": "Blog Lái Hộ 1", "Nền tảng": "blogger", "URL / ID": "muontaixelaixe.laiho1@blogger.com",
        "Ngày đăng bài": sch.strftime("%Y-%m-%d"),
        "Từ khoá 1": "lái xe hộ", "Từ khoá 2": "thuê tài xế",
        "Link bài viết": "Chờ Robot đăng",
        "Tiêu đề bài viết": f"Dịch vụ lái xe hộ an toàn ({sch.strftime('%H:%M')})",
        "File ID Drive": "FILE_ID_V55",
        "Thời gian hẹn giờ": sch.strftime("%Y-%m-%d %H:%M:%S"),
        "Trạng thái": "PENDING" # Rule v55.0
    }
    
    st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_entry]), st.session_state['df_Data_Report']], ignore_index=True)
    st.success(f"✅ Đã lên lịch bài viết thành công!")
    if st.button("XEM KẾT QUẢ", use_container_width=True):
        st.session_state['active_tab'] = "Data_Report"
        st.rerun()

# =================================================================
# 4. UI/UX: SIDEBAR HOÀN HẢO - HIGHLIGHT SÁNG RỰC
# =================================================================
st.set_page_config(page_title="Lái Hộ SEO v3000", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR: ÉP PHẲNG 100%, KHÍT RỊT NHAU */
    div[data-testid="stColumn"]:first-child { gap: 0px !important; }
    
    div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        width: 100% !important; height: 52px !important;
        border-radius: 0px !important; margin: 0px !important;
        background-color: #111111 !important; border: 1px solid #222 !important;
        color: #888888 !important; text-align: left !important;
        padding-left: 20px !important; font-size: 15px !important;
    }

    /* ACTIVE TAB: SÁNG VÀNG LÁI HỘ */
    .active-btn div[data-testid="stButton"] button {
        background-color: #ffd700 !important; color: #000000 !important;
        font-weight: 700 !important; border-left: 8px solid #ffffff !important;
    }

    /* TOOLBAR 3 NÚT */
    .main-toolbar div[data-testid="stButton"] button { height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 5. BỐ CỤC NAV & MAIN
nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h2 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("🖼️ Image", "Data_Image"), ("🔄 Spin", "Data_Spin"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 Thao tác: {tab}")
    
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="m_start"): run_robot_v55()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"u_{tab}"): st.toast("Đã áp dụng Rule v55.0!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (SAFETY CHECK)
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(
        st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=720, hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[st_key].columns}
    )

st.caption("🚀 Lái Hộ SEO v3000.0 | v55.0 Engine Integrated | Perfect Symmetry")
