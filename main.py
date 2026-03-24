import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import re
import time
import requests
import random
from datetime import datetime

# ==========================================
# 🛡️ KẾT NỐI HẦM BÍ MẬT (STREAMLIT SECRETS)
# ==========================================
# Code này sẽ tự lấy thông tin từ mục "Secrets" khi Ní Deploy lên Cloud
try:
    SERVICE_ACCOUNT_INFO = st.secrets["service_account"]
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
except Exception as e:
    st.error("❌ Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title="LÁI HỘ SEO MASTER", layout="wide")

# ==========================================
# 🛰️ HÀM KẾT NỐI GOOGLE SHEET
# ==========================================
@st.cache_data(ttl=60)
def load_all_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        data = {}
        tabs = ["Dashboard", "Website", "Backlink", "Report", "Image"]
        for tab in tabs:
            worksheet = sh.worksheet(tab)
            df = pd.DataFrame(worksheet.get_all_records())
            data[tab] = df
        return data, "✅ Đồng bộ dữ liệu từ Google Sheet thành công!"
    except Exception as e:
        return None, f"❌ Lỗi kết nối Sheet: {str(e)}"

# [Các hàm call_gemini_ai, send_telegram, run_robot_logic giữ nguyên như bản v12.5]
# ... (Tui rút gọn để Ní tập trung vào phần kết nối Cloud) ...
# ==========================================
# 🧠 AI & SEO LOGIC (BẢN VÍT GA)
# ==========================================
def call_gemini_ai(api_key, model_name, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7}}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        return f"LỖI API {response.status_code}"
    except: return "LỖI KẾT NỐI AI"

def send_telegram(token, chat_id, msg):
    if not token or "********" in token: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML", "link_preview_options": {"is_disabled": True}})

@st.dialog("🤖 ROBOT VẬN HÀNH TỰ ĐỘNG", width="large")
def run_robot_logic(data):
    df_dash = data['Dashboard']
    def get_v(k): 
        try: return str(df_dash.loc[df_dash['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
        except: return ""

    api_key = get_v('GEMINI_API_KEY')
    proj_name = get_v('PROJECT_NAME')
    raw_models = get_v('MODEL_VERSION')
    tele_token = get_v('TELEGRAM_BOT_TOKEN')
    tele_chat_id = get_v('TELEGRAM_CHAT_ID')
    
    terminal = st.empty()
    log = f"root@{proj_name.lower()}:~# Đang khởi động hệ thống...\n"
    terminal.code(log, language="bash")

    # [Logic Loop chạy bài y chang bản trước...]
    # Ní cứ dán tiếp phần logic cũ vào đây nhé
    st.success("🎉 TIẾN TRÌNH HOÀN TẤT!")

# ==========================================
# GIAO DIỆN CHÍNH (UI)
# ==========================================
st.markdown(f"<h1 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER Cloud v1.0</h1>", unsafe_allow_html=True)

data, msg = load_all_data()

if data:
    st.toast(msg)
    tabs = st.tabs(list(data.keys()))
    for i, tab_name in enumerate(data.keys()):
        with tabs[i]:
            df_display = data[tab_name].copy()
            if tab_name == "Dashboard":
                if st.button("🚀 KÍCH HOẠT ROBOT VÍT GA", type="primary", use_container_width=True):
                    run_robot_logic(data)
            st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)
