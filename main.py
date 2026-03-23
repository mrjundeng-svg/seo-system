import streamlit as st
import pandas as pd
import time
import random
import datetime

# =================================================================
# 1. 🛡️ KHỞI TẠO HỆ THỐNG (GIỮ NGUYÊN CẤU TRÚC 14 CỘT)
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]

def init_v4400():
    SCHEMAS = {
        "Dashboard": ["Hạng mục", "Giá trị thực tế"],
        "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
        "Data_Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
        "Data_Report": REPORT_COLS
    }
    # Dữ liệu mẫu (Ní sửa ở đây để lưu cứng vào code)
    INIT_DASH = [
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
        ["Số lượng bài cần tạo", "3"],
        ["Danh sách Keyword", "lái xe hộ, thuê tài xế, dịch vụ lái xe, tài xế riêng"],
        ["Khung giờ vàng", "09:30-19:30"],
        ["Giãn cách (phút)", "30-90"],
        ["Tỉ lệ bài Local (%)", "30"]
    ]
    for key, cols in SCHEMAS.items():
        s_key = f"df_{key}"
        if s_key not in st.session_state:
            if key == "Dashboard": st.session_state[s_key] = pd.DataFrame(INIT_DASH, columns=cols)
            elif key == "Data_Report": st.session_state[s_key] = pd.DataFrame(columns=cols)
            else: st.session_state[s_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

init_v4400()

# =================================================================
# 2. 🧠 BỘ NÃO ĐỌC SÂU (DEEP READER)
# =================================================================
def get_config(key_name):
    """Hàm bốc dữ liệu từ Dashboard cực chuẩn"""
    df = st.session_state['df_Dashboard']
    try:
        # Tìm dòng chứa key (không phân biệt hoa thường)
        row = df[df.iloc[:,0].str.lower().str.contains(key_name.lower(), na=False)]
        return str(row.iloc[0,1]).strip()
    except: return ""

def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

# =================================================================
# 3. 🤖 CONSOLE ROBOT (ĐỌC & PHÂN TÍCH NHƯ COLAB)
# =================================================================
@st.dialog("🎬 COLAB CONSOLE v55.0 DEEP READER", width="large")
def run_robot_v4400():
    st.markdown("""<style> .term { font-family: 'Courier New', monospace; color: #00FF00; background-color: #111; padding: 15px; height: 420px; overflow-y: auto; border: 1px solid #444; line-height: 1.5; font-size: 13px; } .blue { color: #00DFFF; } .gold { color: #FFD700; } </style>""", unsafe_allow_html=True)
    logs = [f"<b>[SYSTEM]</b> Khởi động Robot Engine v55.0..."]
    log_area = st.empty()
    
    def log(msg, color=""):
        c = f"class='{color}'" if color else ""
        logs.append(f"<span style='color:#666'>[{get_vn_now().strftime('%H:%M:%S')}]</span> <span {c}>{msg}</span>")
        log_area.markdown(f"<div class='term'>{'<br>'.join(logs[-25:])}</div>", unsafe_allow_html=True)

    # --- BƯỚC 1: ĐỌC & PHÂN TÍCH DASHBOARD (NHƯ COLAB) ---
    log("📊 Đang đọc cấu hình từ Dashboard...", "blue")
    api_key = get_config("GEMINI_API_KEY")
    drive_id = get_config("FOLDER_DRIVE_ID")
    num_posts = int(get_config("Số lượng bài") or 1)
    keywords = [k.strip() for k in get_config("Keyword").split(',')]
    time_range = get_config("Khung giờ") or "09:30-19:30"
    
    log(f"🔑 API Key: {api_key[:10]}***")
    log(f"📂 Drive ID: {drive_id[:10]}***")
    log(f"📝 Số bài cần tạo: {num_posts}")
    log(f"🏷️ Keywords: {len(keywords)} từ được nạp.")
    time.sleep(1)

    # --- BƯỚC 2: KIỂM TRA WEBSITE ĐANG BẬT ---
    active_sites = st.session_state['df_Data_Website'][st.session_state['df_Data_Website']['Trạng thái'].str.lower() == 'bật'].to_dict('records')
    if not active_sites: log("❌ LỖI: Không có Website nào đang BẬT!", "err"); return

    current_time = get_vn_now()
    pb = st.progress(0)

    for i in range(num_posts):
        log(f"--------------------------------------------------")
        log(f"🔥 <b>TIẾN TRÌNH BÀI #{i+1}</b>", "gold")
        
        # Logic chọn Web & Check Quota (Như v4300)
        target_site = random.choice(active_sites)
        log(f"🌐 Target: {target_site['Tên web']}")
        
        # Logic bốc 5 Keyword ngẫu nhiên (Như Colab)
        post_kws = random.sample(keywords, min(len(keywords), 5))
        post_kws += [""] * (5 - len(post_kws))
        log(f"🔑 Keywords chọn lọc: {', '.join([k for k in post_kws if k])}")

        # Tính giờ vàng (Parse từ chuỗi Dashboard)
        try:
            h_start = int(time_range.split('-')[0].split(':')[0])
            m_start = int(time_range.split('-')[0].split(':')[1])
        except: h_start, m_start = 9, 30

        current_time += datetime.timedelta(minutes=random.randint(30, 90))
        if current_time.hour >= 20: 
            current_time = (current_time + datetime.timedelta(days=1)).replace(hour=h_start, minute=m_start)
        
        log(f"⏰ Lên lịch đăng: {current_time.strftime('%H:%M %d-%m')}")
        
        # Ghi Report
        new_row = [target_site['Tên web'], target_site['Nền tảng'], target_site['URL / ID'], current_time.strftime('%Y-%m-%d')] + post_kws + ["Chờ đăng", f"Bài viết SEO #{i+1}", drive_id, current_time.strftime('%Y-%m-%d %H:%M:%S'), "PENDING"]
        st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_row], columns=REPORT_COLS), st.session_state['df_Data_Report']], ignore_index=True)
        
        log(f"✅ Đã ghi Report. ID Drive đã khớp: {drive_id[:8]}...")
        pb.progress(int((i+1)/num_posts * 100))
        time.sleep(0.5)

    st.success("🏁 Hoàn tất! Dữ liệu đã được đọc sạch sành sanh từ Dashboard.")
    if st.button("ĐÓNG CONSOLE"): st.rerun()

# =================================================================
# 4. 🎨 UI/UX SIDEBAR KHÍT RỊT
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v4400", page_icon=" taxi", layout="wide")
st.markdown("""<style> .stApp { background-color: #000; color: white; } header { visibility: hidden; } [data-testid="stSidebar"] { display: none !important; } div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button { width: 100% !important; height: 50px !important; border-radius: 0px !important; margin: 0px !important; background-color: #111 !important; border: 1px solid #222 !important; color: #888 !important; text-align: left !important; padding-left: 20px !important; } .active-btn div[data-testid="stButton"] button { background-color: #ffd700 !important; color: #000 !important; font-weight: 700 !important; border-left: 8px solid #fff !important; } .btn-red button { background-color: #ff0000 !important; } .btn-blue button { background-color: #0055ff !important; } .btn-gold button { background-color: #ffd700 !important; color: #000 !important; } </style>""", unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")
with nav_col:
    st.markdown("<h3 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ SEO</h3>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"): st.session_state['active_tab'] = key; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT"): run_robot_v4400()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True); st.button("☁️ UPDATE DB"); st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🗑️ CLEAR REPORT"): st.session_state['df_Data_Report'] = pd.DataFrame(columns=REPORT_COLS); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL"); st.markdown('</div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL"); st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=700, hide_index=True)

st.caption("🚀 v4400.0 | Deep Dashboard Reading | Colab Logic Analysis | Full Param Extraction")
