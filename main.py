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
    
    # --- FIX: Đọc cột 'Input dữ liệu' theo hình image_e560e5.png ---
    def v(k):
        try:
            res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
            if not res.empty: return str(res.values[0]).strip()
            return ""
        except: return ""

    if not v('GEMINI_API_KEY'):
        st.error("❌ Không tìm thấy giá trị GEMINI_API_KEY. Ní kiểm tra lại cột 'Input dữ liệu' nhé!"); return
    
    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    if active_sites.empty:
        st.error("❌ Không có website nào 'Active'!"); return

    term = st.empty(); log = f"root@{v('PROJECT_NAME').lower() or 'bot'}:~# Đang vít ga...\n"
    
    num_to_gen = v('Số lượng bài cần tạo')
    num_to_gen = int(num_to_gen) if num_to_gen.isdigit() else 1

    for i in range(num_to_gen):
        site = active_sites.sample(n=1).iloc[0]
        model_v = v('MODEL_VERSION') or "gemini-1.5-flash"
        model = random.choice([m.strip() for m in model_v.split(',') if m.strip()])
        
        log += f"[+] Đang gen bài {i+1}: {site['Tên web']}\n"; term.code(log, language="bash")
        
        # Local SEO
        loc_str = ""
        l_ratio = v('LOCAL_RATIO')
        l_ratio = float(l_ratio) if l_ratio else 0.2
        if random.random() < l_ratio and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 Địa điểm: {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        # Gen Content
        prompt = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\n{loc_str}"
        content = call_ai(v('GEMINI_API_KEY'), model, prompt)
        
        if v('SPIN_MODE') == "ON" and not data['Spin'].empty:
            log += "  .. Đang chạy Spin lọc AI Detection...\n"; term.code(log, language="bash")
            rules = data['Spin'].to_string(index=False)
            content = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {rules}\nContent: {content}")

        # Ghi Report (Dùng cột 'các website đích' theo image_e559de.png)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        update_report([
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post", 
            now, "", "", "", "", "", 
            site.get('các website đích', ''), 
            "Tiêu đề", "Sapo", now, "✅ Thành công", "85"
        ])
        
        log += "  .. Xong! Check Tab Report nhé.\n"; term.code(log, language="bash")
        time.sleep(1)
    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v14.5</h1>", unsafe_allow_html=True)
data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 KÍCH HOẠT VÍT GA", type="primary", use_container_width=True): run_robot(data)
            st.dataframe(data[name], use_container_width=True, height=400, hide_index=True)
else: st.error(f"Lỗi kết nối: {msg}")
