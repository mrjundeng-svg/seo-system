import streamlit as st
import pandas as pd
import time
import random
import datetime
import json
import gspread
from google.oauth2.service_account import Credentials

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU & CẤU HÌNH DASHBOARD
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
TABS = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]

def init_v4600():
    if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"
    
    # Khởi tạo Dashboard mẫu nếu chưa có gì
    if 'df_Dashboard' not in st.session_state:
        st.session_state['df_Dashboard'] = pd.DataFrame([
            ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
            ["SERVICE_ACCOUNT_JSON", "Dán_Nội_Dung_JSON_Vào_Đây"],
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
            ["Số lượng bài cần tạo", "3"],
            ["Tỉ lệ bài Local (%)", "30"]
        ], columns=["Hạng mục", "Giá trị thực tế"])

    for tab in TABS[1:]: # Khởi tạo các tab còn lại
        s_key = f"df_{tab}"
        if s_key not in st.session_state:
            cols = REPORT_COLS if tab == "Data_Report" else ["Cột 1", "Cột 2", "Cột 3"] # Tạm thời
            st.session_state[s_key] = pd.DataFrame(columns=cols)

init_v4600()

# =================================================================
# 2. 🔌 HÀM KẾT NỐI GOOGLE SHEETS (HÀN MẠCH THẬT)
# =================================================================
def get_gsheet_client():
    try:
        json_info = json.loads(get_config("SERVICE_ACCOUNT_JSON"))
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(json_info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google: {str(e)}")
        return None

def get_config(key_name):
    df = st.session_state['df_Dashboard']
    try:
        row = df[df.iloc[:,0].str.lower().str.contains(key_name.lower(), na=False)]
        return str(row.iloc[0,1]).strip()
    except: return ""

# =================================================================
# 3. ☁️ CHỨC NĂNG ĐẨY/KÉO DỮ LIỆU (REAL ACTION)
# =================================================================
def sync_to_cloud():
    client = get_gsheet_client()
    if not client: return
    sheet_id = get_config("GOOGLE_SHEET_ID")
    try:
        sh = client.open_by_key(sheet_id)
        for tab in TABS:
            ws = sh.worksheet(tab)
            ws.clear() # Xóa cũ
            df = st.session_state[f"df_{tab}"]
            ws.update([df.columns.values.tolist()] + df.fillna("").values.tolist())
        st.success("✅ Đã đồng bộ toàn bộ 7 Tab lên Google Sheets!")
    except Exception as e:
        st.error(f"❌ Lỗi khi Update Cloud: {str(e)}")

def restore_from_cloud():
    client = get_gsheet_client()
    if not client: return
    sheet_id = get_config("GOOGLE_SHEET_ID")
    try:
        sh = client.open_by_key(sheet_id)
        for tab in TABS:
            ws = sh.worksheet(tab)
            data = ws.get_all_records()
            st.session_state[f"df_{tab}"] = pd.DataFrame(data)
        st.success("🔄 Đã kéo dữ liệu mới nhất từ Sheets về Web!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Lỗi khi Restore Cloud: {str(e)}")

# =================================================================
# 4. 🎨 GIAO DIỆN & NAVIGATION
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ Master", page_icon=" taxi", layout="wide")

st.markdown("""<style> .stApp { background-color: #000; color: white; } header { visibility: hidden; } [data-testid="stSidebar"] { display: none !important; } div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button { width: 100% !important; height: 50px !important; border-radius: 0px !important; margin: 0px !important; background-color: #111 !important; border: 1px solid #222 !important; color: #888 !important; text-align: left !important; padding-left: 20px !important; } .active-btn div[data-testid="stButton"] button { background-color: #ffd700 !important; color: #000 !important; font-weight: 700 !important; border-left: 8px solid #fff !important; } .btn-red button { background-color: #ff0000 !important; } .btn-blue button { background-color: #0055ff !important; } </style>""", unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")
with nav_col:
    st.markdown("<h3 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ SEO</h3>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"): st.session_state['active_tab'] = key; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"#### 📍 Tab: {tab}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("☁️ UPDATE TO CLOUD"): sync_to_cloud()
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE FROM CLOUD"): restore_from_cloud()
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=700, hide_index=True)

st.caption("🚀 v4600.0 | Real Cloud Sync | Gspread Integrated | Anti-Spam SEO Engine")
