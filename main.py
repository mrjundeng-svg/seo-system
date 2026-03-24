import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

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

# --- AI CALLER v22.0 (THE URL HUNTER) ---
def call_ai_god_mode(key, model_input, prompt):
    m = model_input.strip().lower().replace("models/", "")
    if "flash" in m: base = "gemini-1.5-flash"
    elif "pro" in m: base = "gemini-1.5-pro"
    else: base = "gemini-1.5-flash"

    # Thử mọi tổ hợp cổng có thể có của Google
    attempts = [
        f"https://generativelanguage.googleapis.com/v1beta/models/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1/models/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1beta/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1/{base}:generateContent"
    ]
    
    for url in attempts:
        try:
            res = requests.post(f"{url}?key={key}", json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=45)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), "✅"
            if res.status_code == 403: return None, "🔑 Lỗi 403: API Key của ní bị Google từ chối (Sai Key hoặc bị khóa)."
        except: continue
    return None, "❌ Lỗi 404: Vẫn không tìm thấy cổng. Ní kiểm tra lại API Key có copy dư khoảng trắng không nhé!"

@st.dialog("🖥️ SYSTEM TERMINAL v22.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    log_area = st.empty()
    log_h = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Khởi động hệ thống..."]
    
    def add_log(msg):
        log_h.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_h))

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0]
        content, meta = call_ai_god_mode(v('GEMINI_API_KEY'), v('MODEL_VERSION'), v('PROMPT_TEMPLATE') + "\nKeywords: " + v('Danh sách Keyword bài viết'))
        
        if content:
            add_log(f"✅ Thành công! Đang ghi Report cho {site['Tên web']}...")
            gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", "1%", "85/100", site.get('các website đích',''), "Tiêu đề", "Sapo", datetime.now().strftime("%H:%M"), "Thành công", "Active"
            ])
            add_log(f"✨ Xong bài {i+1}!")
        else: add_log(meta)
        time.sleep(1)

    st.success("🎉 TẤT CẢ ĐÃ XONG!")
    if st.button("ĐÓNG"): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v22.0</h1>", unsafe_allow_html=True)
data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, hide_index=True)
else: st.error(f"Lỗi: {msg}")
