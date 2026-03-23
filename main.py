import streamlit as st
import pandas as pd
import time
import datetime
import random
import traceback

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU (DÁN DATA THẬT VÀO ĐÂY - F5 KHÔNG MẤT)
# =================================================================
def init_system_data():
    TABLES = {
        "Dashboard": [["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"], ["Số lượng bài tạo", "3"], ["Khung giờ", "09:30-19:30"]],
        "Data_Local": [["Hà Nội", "Hoàn Kiếm", "Phố Tạ Hiện"], ["TP.HCM", "Quận 1", "Bùi Viện"]],
        "Data_Backlink": [["lái xe hộ", "https://laiho.vn", "0"]],
        "Data_Website": [["Blog Lái Hộ 1", "blogger", "admin@blogger.com", "Bật", "3-5"]],
        "Data_Report": []
    }
    for key, val in TABLES.items():
        s_key = f"df_{key}"
        if s_key not in st.session_state:
            cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"] if key == "Data_Report" else ["Cột 1", "Cột 2", "Cột 3"]
            if key == "Dashboard": cols = ["Hạng mục", "Giá trị thực tế"]
            st.session_state[s_key] = pd.DataFrame(val, columns=cols if val else ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"])

init_system_data()
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. 🧠 LOGIC ROBOT MÔ PHỎNG COLAB
# =================================================================
def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

@st.dialog("🤖 COLAB CONSOLE - LÁI HỘ SEO v55.0", width="large")
def show_colab_console():
    st.markdown("""<style> .console-text { font-family: 'Courier New', monospace; color: #00FF00; background-color: #1e1e1e; padding: 10px; border-radius: 5px; height: 300px; overflow-y: scroll; border: 1px solid #333; } </style>""", unsafe_allow_html=True)
    
    log_container = st.empty()
    logs = [f"🎬 [{get_vn_now().strftime('%H:%M:%S')}] KHỞI ĐỘNG HỆ THỐNG SEO V55.0..."]
    
    def update_log(msg, type="info"):
        color = "#00FF00" if type == "info" else "#FF0000"
        logs.append(f"[{get_vn_now().strftime('%H:%M:%S')}] {msg}")
        # Hiển thị 10 dòng cuối cùng như Colab
        log_html = f"<div class='console-text'>{'<br>'.join(logs[-15:])}</div>"
        log_container.markdown(log_html, unsafe_allow_html=True)

    pb = st.progress(0)
    
    # Lấy số bài cần tạo từ Dashboard
    try:
        dash_df = st.session_state['df_Dashboard']
        num_posts = int(dash_df[dash_df.iloc[:,0] == "Số lượng bài tạo"].iloc[0,1])
    except: num_posts = 1

    update_log(f"📍 Mốc thời gian bắt đầu: {get_vn_now().strftime('%Y-%m-%d %H:%M:%S')}")

    for i in range(num_posts):
        try:
            update_log(f"🚀 Đang xử lý bài {i+1}/{num_posts}...")
            time.sleep(0.5)
            
            # Rule 1: Tung xí ngầu
            update_log("🎲 Đang tung xí ngầu chọn Local...")
            time.sleep(0.5)
            
            # GIẢ LẬP LỖI 429 ĐỂ NÍ XEM (Ní có thể xóa đoạn này sau)
            if i == 2: # Giả sử bài thứ 3 bị lỗi
                raise Exception("429 RESOURCE_EXHAUSTED: You exceeded your current quota!")

            # Rule 2: Ghi Report
            update_log(f"✅ Đã tạo file Drive. Đang ghi vào Data_Report...")
            new_entry = {"Website": "Blog Lái Hộ", "Trạng thái": "PENDING", "Tiêu đề bài viết": f"Post SEO #{i+1}", "Ngày đăng bài": get_vn_now().strftime('%Y-%m-%d')}
            st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_entry]), st.session_state['df_Data_Report']], ignore_index=True).fillna("...")
            
            pb.progress(int((i+1)/num_posts * 100))
            update_log(f"✨ Xong bài {i+1}!")
            time.sleep(0.5)

        except Exception as e:
            update_log(f"⚠️ LỖI BÀI {i+1}: {str(e)}", type="error")
            st.error(f"Robot dừng lại do lỗi: {str(e)}")
            break # Dừng robot nếu lỗi

    if st.button("ĐÓNG CONSOLE & XEM REPORT", use_container_width=True):
        st.session_state['active_tab'] = "Data_Report"
        st.rerun()

# =================================================================
# 3. 🎨 GIAO DIỆN CHUẨN (SIDEBAR KHÍT RỊT)
# =================================================================
st.set_page_config(page_title="Lái Hộ SEO v3400", page_icon="🚕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR KHÍT RỊT 100% */
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
    .main-toolbar div[data-testid="stButton"] button { height: 48px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-blue button { background-color: #0055ff !important; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h3 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ SEO</h3>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("🔄 Spin", "Data_Spin"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"#### 📍 {tab}")
    
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", key="btn_run"): show_colab_console()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("🔄 UPDATE DB", key=f"u_{tab}"): st.toast("Đã nạp lại dữ liệu!")
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

st.caption("🚀 v3400.0 | Colab Style Console | Real-time Logging | Error Detection")
