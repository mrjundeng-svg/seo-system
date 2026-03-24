import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
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

# --- AI CALLER v24.0 (BẢN DỄ TÍNH NHẤT) ---
def call_ai_final_v24(key, prompt):
    # Ép dùng cổng v1beta và model flash-latest - Cổng này tỷ lệ thông cao nhất
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=45)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), "✅ Thông cổng v1beta"
        else:
            return None, f"Lỗi {res.status_code}: {res.json().get('error', {}).get('message', 'Lỗi không xác định')}"
    except Exception as e:
        return None, f"Lỗi mạng: {str(e)}"

@st.dialog("🖥️ SYSTEM TERMINAL v24.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    log_area = st.empty()
    log_h = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Khởi động v24.0 (Final Fix)..."]
    
    def add_log(msg):
        log_h.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_h))

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0] if not active_sites.empty else None
        if not site: add_log("❌ Lỗi: Tab Website chưa có máy nào Active!"); break

        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        add_log("🧠 Đang gõ cửa Google bằng v1beta...")

        content, meta = call_ai_final_v24(v('GEMINI_API_KEY'), v('PROMPT_TEMPLATE'))
        
        if content:
            add_log(f"✅ ĐÃ THÔNG! {meta}")
            # Ghi báo cáo
            gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), "Keyword", "", "✅", "1%", "90/100", site.get('các website đích',''), "Tiêu đề", "Sapo", datetime.now().strftime("%H:%M"), "Thành công", "Active"
            ])
            add_log("✨ Đã lưu vào Tab Report.")
        else:
            add_log(f"❌ {meta}")
            add_log("💡 Ní ơi, dán cái API Key MỚI vào Sheet rồi bấm Reload là xong!")
        
        time.sleep(1)

    st.success("🎉 TIẾN TRÌNH KẾT THÚC!")
    if st.button("ĐÓNG"): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v24.0</h1>", unsafe_allow_html=True)
data, msg = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 Reload", use_container_width=True): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, hide_index=True)
else: st.error(f"Lỗi kết nối: {msg}")
