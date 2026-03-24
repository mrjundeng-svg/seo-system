import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

def load_data():
    try:
        # Xử lý chìa khóa an toàn
        s_acc = dict(st.secrets["service_account"])
        s_acc["private_key"] = s_acc["private_key"].replace("\\n", "\n").strip()
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(s_acc, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        
        data = {}
        for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]:
            try: data[t] = pd.DataFrame(sh.worksheet(t).get_all_records())
            except: data[t] = pd.DataFrame()
        return data, "✅ Đồng bộ thành công"
    except Exception as e: return None, f"Lỗi kết nối: {str(e)}"

def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

# --- ROBOT ENGINE ---
@st.dialog("🤖 ROBOT ĐANG CHẠY", width="large")
def run_robot(data):
    df = data['Dashboard']
    def v(k): return str(df.loc[df['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
    
    term = st.empty()
    log = f"root@{v('PROJECT_NAME').lower()}:~# Vít ga...\n"
    
    for i in range(int(v('Số lượng bài cần tạo') or 1)):
        site = data['Website'][data['Website']['Trạng thái'] == 'Active'].sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',')])
        
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 Địa điểm: {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        log += f"[+] Bài {i+1}: {site['Tên web']} | {model} | {'LOCAL' if loc_str else 'GLOBAL'}\n"
        term.code(log, language="bash")

        # Draft & Humanize
        p1 = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\n{loc_str}"
        content = call_ai(v('GEMINI_API_KEY'), model, p1)
        
        if v('SPIN_MODE') == "ON" and not data['Spin'].empty:
            rules = data['Spin'].to_string(index=False)
            p2 = f"{v('AI_HUMANIZER_PROMPT')}\nRules: {rules}\nContent: {content}"
            content = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", p2)

        log += "  .. Xong!\n"
        term.code(log, language="bash")
        time.sleep(1)
    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v13.5</h1>", unsafe_allow_html=True)
data, msg = load_data()

if data:
    st.toast(msg)
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 START ROBOT", type="primary", use_container_width=True): run_robot(data)
            st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else:
    st.error(f"❌ {msg}")
    st.info("💡 Ní hãy Reboot App trong mục Manage App để xóa cache lỗi nhé!")
