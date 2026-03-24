import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import random
import time
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide")

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
    except Exception as e:
        st.error(f"❌ Lỗi Secrets: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_data():
    try:
        creds = get_creds()
        if not creds: return None, "Lỗi xác thực"
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])
        data = {}
        for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]:
            try: data[t] = pd.DataFrame(sh.worksheet(t).get_all_records())
            except: data[t] = pd.DataFrame()
        return data, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

# --- ENGINE ---
@st.dialog("🤖 ROBOT VÍT GA", width="large")
def run_robot(data):
    df = data['Dashboard']
    def v(k): return str(df.loc[df['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
    
    term = st.empty()
    log = f"root@{v('PROJECT_NAME').lower()}:~# Starting...\n"
    
    for i in range(int(v('Số lượng bài cần tạo') or 1)):
        site = data['Website'][data['Website']['Trạng thái'] == 'Active'].sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',')])
        
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        log += f"[+] Bài {i+1}: {site['Tên web']} | {model} | {'LOCAL' if loc_str else 'GLOBAL'}\n"
        term.code(log, language="bash")

        # Draft -> Humanize
        p1 = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\n{loc_str}"
        draft = call_ai(v('GEMINI_API_KEY'), model, p1)
        
        if v('SPIN_MODE') == "ON" and not data['Spin'].empty:
            rules = data['Spin'].to_string(index=False)
            p2 = f"{v('AI_HUMANIZER_PROMPT')}\nRules: {rules}\nContent: {draft}"
            final = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", p2)
        else: final = draft

        log += "  .. Xong!\n"
        term.code(log, language="bash")
        time.sleep(1)
    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v13.4</h1>", unsafe_allow_html=True)
data, err = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 START ROBOT", type="primary", use_container_width=True): run_robot(data)
            st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else: st.error(f"❌ Lỗi: {err}")
