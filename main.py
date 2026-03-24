import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import random
import time
from datetime import datetime

# --- CONFIG & CONNECTION ---
try:
    SERVICE_ACCOUNT_INFO = st.secrets["service_account"]
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
except:
    st.error("❌ Secrets trống! Ní dán cấu hình vào Settings > Secrets nhé.")
    st.stop()

st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide")

@st.cache_data(ttl=60)
def load_all_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # 🛠️ TỰ ĐỘNG FIX LỖI KÝ TỰ XUỐNG DÒNG (\n)
        info = dict(SERVICE_ACCOUNT_INFO)
        if "private_key" in info:
            info["private_key"] = info["private_key"].replace("\\n", "\n")
            
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        data = {}
        for tab in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]:
            try:
                data[tab] = pd.DataFrame(sh.worksheet(tab).get_all_records())
            except: data[tab] = pd.DataFrame()
        return data, "✅ Đồng bộ thành công"
    except Exception as e: 
        return None, f"Lỗi kết nối: {str(e)}"

# --- FUNCTIONS ---
def call_gemini_ai(api_key, model_name, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.8}}
    try:
        res = requests.post(url, json=payload, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

# --- CORE LOGIC ---
@st.dialog("🤖 ROBOT RUNNING", width="large")
def run_robot(data):
    df_dash = data['Dashboard']
    def get_v(k): return str(df_dash.loc[df_dash['Hạng mục'] == k, 'Giá trị thực tế'].values[0])

    api_key, models, proj = get_v('GEMINI_API_KEY'), get_v('MODEL_VERSION'), get_v('PROJECT_NAME')
    ratio = float(get_v('LOCAL_RATIO') or 0.2)
    
    term = st.empty()
    log = f"root@{proj.lower()}:~# Starting...\n"
    
    for i in range(int(get_v('Số lượng bài cần tạo') or 1)):
        site = data['Website'][data['Website']['Trạng thái'] == 'Active'].sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in models.split(',')])
        
        loc_txt = ""
        if random.random() < ratio and not data['Local'].empty:
            loc = data['Local'].sample(n=1).iloc[0]
            loc_txt = f"📍 Địa điểm: {loc['Cung đường']}, {loc['Quận']}, {loc['Tỉnh thành']}."
        
        log += f"[+] Bài {i+1}: {site['Tên web']} | {model} | {'LOCAL' if loc_txt else 'GLOBAL'}\n"
        term.code(log, language="bash")

        p1 = f"{get_v('PROMPT_TEMPLATE')}\nKeywords: {get_v('Danh sách Keyword bài viết')}\n{loc_txt}"
        draft = call_gemini_ai(api_key, model, p1)

        if not data['Spin'].empty and get_v('SPIN_MODE') == "ON":
            rules = data['Spin'].to_string(index=False)
            p2 = f"{get_v('AI_HUMANIZER_PROMPT')}\nRules: {rules}\nContent: {draft}"
            final = call_gemini_ai(api_key, "gemini-1.5-flash", p2)
        else: final = draft

        log += "  .. Done!\n"
        term.code(log, language="bash")
        time.sleep(1)
    st.success("🎉 HOÀN TẤT!")

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v13.3</h1>", unsafe_allow_html=True)
data, err = load_all_data()

if data:
    st.toast(err)
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 START ROBOT", type="primary", use_container_width=True): run_robot(data)
            st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else:
    st.error(f"❌ {err}")
    st.info("💡 Ní thử: 1. Share Sheet quyền Editor. 2. Reboot App trong Manage App.")
