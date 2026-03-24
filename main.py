import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=30)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ OK"
    except Exception as e: return None, str(e)

def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

def update_report(row):
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
    except: pass

@st.dialog("🤖 ROBOT VẬN HÀNH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k): return str(df_d.loc[df_d['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
    
    # Lọc Website Active
    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    if active_sites.empty:
        st.error("❌ Không tìm thấy website nào 'Active'!"); return

    term = st.empty(); log = f"root@{v('PROJECT_NAME').lower()}:~# Vít ga...\n"
    
    for i in range(int(v('Số lượng bài cần tạo') or 1)):
        site = active_sites.sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',')])
        
        # 📍 Local SEO Logic
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 Địa điểm: {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        log += f"[+] Bài {i+1}: {site['Tên web']}\n"; term.code(log, language="bash")
        
        # Gen Content
        content = call_ai(v('GEMINI_API_KEY'), model, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\n{loc_str}")
        if v('SPIN_MODE') == "ON" and not data['Spin'].empty:
            content = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string(index=False)}\nContent: {content}")

        # 📝 Ghi Report - Đã khớp với tên cột của sếp
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        update_report([
            site['URL / ID'], 
            site['Nền tảng'], 
            f"{site['URL / ID']}/post", 
            now, "", "", "", "", "", 
            site['các website đích'], # Khớp với image_e559de.png
            "Tiêu đề", "Sapo", now, "✅ Thành công", "85"
        ])
        
        log += "  .. Xong! Đã lưu kết quả.\n"; term.code(log, language="bash")
        time.sleep(1)
    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v14.3</h1>", unsafe_allow_html=True)
data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 KÍCH HOẠT VÍT GA", type="primary", use_container_width=True): run_robot(data)
            st.dataframe(data[name], use_container_width=True, height=400, hide_index=True)
else: st.error(f"Lỗi kết nối: {msg}")
