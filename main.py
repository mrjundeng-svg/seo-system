import streamlit as st
import pandas as pd
import time
import datetime
import random

# =================================================================
# 1. 🛡️ KHỞI TẠO HỆ THỐNG (FIX LỖI VALUEERROR 100%)
# =================================================================
def init_system_v3500():
    # Định nghĩa cấu trúc cột chuẩn cho từng bảng
    SCHEMAS = {
        "Dashboard": ["Hạng mục", "Giá trị thực tế"],
        "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
        "Data_Image": ["Link ảnh", "Số lần dùng"],
        "Data_Spin": ["Từ Spin", "Bộ Spin"],
        "Data_Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
        "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
    }
    
    # Dữ liệu mẫu ban đầu (Ní dán dữ liệu thật của Ní vào đây)
    INITIAL_DATA = {
        "Dashboard": [["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"], ["Số lượng bài tạo", "5"], ["Khung giờ", "09:30-19:30"]],
        "Data_Backlink": [["lái xe hộ", "https://laiho.vn", "0"]],
        "Data_Website": [["Blog Lái Hộ 1", "blogger", "admin@blogger.com", "Bật", "3-5"]],
        "Data_Image": [["https://anh.com/1.jpg", "0"]],
        "Data_Spin": [["lái xe", "{tài xế|bác tài}"]],
        "Data_Local": [["Hà Nội", "Hoàn Kiếm", "Phố Tạ Hiện"], ["TP.HCM", "Quận 1", "Bùi Viện"]],
        "Data_Report": []
    }

    for key, cols in SCHEMAS.items():
        s_key = f"df_{key}"
        if s_key not in st.session_state:
            data = INITIAL_DATA.get(key, [])
            # Nếu bảng Report trống thì tạo DataFrame chỉ có cột
            if not data:
                st.session_state[s_key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[s_key] = pd.DataFrame(data, columns=cols)

init_system_v3500()
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. 🧠 LOGIC ROBOT & CONSOLE (MÔ PHỎNG LỖI 429)
# =================================================================
def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

@st.dialog("🎬 COLAB CONSOLE - LOGGING v55.0", width="large")
def show_colab_console():
    st.markdown("""<style> .terminal { font-family: 'Courier New', monospace; color: #00FF00; background-color: #111; padding: 15px; border-radius: 5px; height: 350px; overflow-y: auto; border: 1px solid #333; line-height: 1.5; } .err { color: #FF4B4B; } </style>""", unsafe_allow_html=True)
    
    log_area = st.empty()
    logs = [f"<b>[HỆ THỐNG]</b> Khởi động Robot SEO v55.0..."]
    
    def log(msg, is_error=False):
        timestamp = get_vn_now().strftime('%H:%M:%S')
        prefix = f"<span style='color:#aaa'>[{timestamp}]</span> "
        content = f"<span class='{'err' if is_error else ''}'>{msg}</span>"
        logs.append(prefix + content)
        log_area.markdown(f"<div class='terminal'>{'<br>'.join(logs[-20:])}</div>", unsafe_allow_html=True)

    pb = st.progress(0)
    
    # Đọc số bài từ Dashboard
    dash_df = st.session_state['df_Dashboard']
    try: num_posts = int(dash_df[dash_df.iloc[:,0] == "Số lượng bài tạo"].iloc[0,1])
    except: num_posts = 1

    for i in range(num_posts):
        log(f"🚀 <b>Bắt đầu bài {i+1}/{num_posts}...</b>")
        time.sleep(0.6)
        
        # Giả lập logic v55.0
        log("🎲 Tung xí ngầu địa điểm Local...")
        time.sleep(0.4)
        
        # MÔ PHỎNG LỖI 429 NHƯ HÌNH image_57fe47
        if i == 2: # Giả sử đến bài thứ 3 thì hết quota
            log("❌ <b>Lỗi bài: 429 RESOURCE_EXHAUSTED.</b>", is_error=True)
            log("⚠️ You exceeded your current quota, please check your plan and billing details.", is_error=True)
            st.error("Robot tạm dừng do lỗi API Quota (429).")
            break
            
        log(f"✅ Đã soạn bài. Đang lưu Drive ID: {random.randint(1000,9999)}...")
        
        # Ghi vào Report trạng thái PENDING
        new_row = {"Website": "Blog Lái Hộ 1", "Nền tảng": "blogger", "Trạng thái": "PENDING", "Tiêu đề bài viết": f"Dịch vụ Lái Hộ #{i+1}", "Ngày đăng bài": get_vn_now().strftime('%Y-%m-%d')}
        st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_row]), st.session_state['df_Data_Report']], ignore_index=True).fillna("...")
        
        pb.progress(int((i+1)/num_posts * 100))
        time.sleep(0.5)

    if st.button("ĐÓNG CONSOLE & XEM REPORT", use_container_width=True):
        st.session_state['active_tab'] = "Data_Report"; st.rerun()

# =================================================================
# 3. 🎨 GIAO DIỆN SIDEBAR KHÍT RỊT (UI MASTER)
# =================================================================
st.set_page_config(page_title="Lái Hộ SEO v3500", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR ÉP PHẲNG 100% */
    div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        width: 100% !important; height: 52px !important;
        border-radius: 0px !important; margin: 0px !important;
        background-color: #111111 !important; border: 1px solid #222 !important;
        color: #888888 !important; text-align: left !important;
        padding-left: 20px !important; font-size: 15px !important;
    }
    .active-btn div[data-testid="stButton"] button {
        background-color: #ffd700 !important; color: #000 !important;
        font-weight: 700 !important; border-left: 8px solid #ffffff !important;
    }

    /* TOOLBAR NÚT CHỨC NĂNG */
    .main-toolbar div[data-testid="stButton"] button { height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h3 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ SEO</h3>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("🖼️ Image", "Data_Image"), ("🔄 Spin", "Data_Spin"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"#### 📍 Tab đang mở: {tab}")
    
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="btn_run"): show_colab_console()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"u_{tab}"): st.toast("Đã nạp lại dữ liệu chuẩn!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
    with c3:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(
        st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=720, hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[st_key].columns}
    )

st.caption("🚀 v3500.0 | Fix ValueError | Colab Console | 429 Error Simulation | Perfect UI")
