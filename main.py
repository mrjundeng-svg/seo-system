import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

# --- HÀM KẾT NỐI ---
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
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- AI CALLER v23.0 (BỘ DÒ TÌM ĐỊA CHỈ THÔNG MINH) ---
def call_ai_diagnostic(key, model_input, prompt):
    # Chuẩn hóa tên model cực sạch
    m = str(model_input).strip().lower().replace("models/", "")
    if "flash" in m: base = "gemini-1.5-flash"
    elif "pro" in m: base = "gemini-1.5-pro"
    else: base = "gemini-1.5-flash"

    # 🛠️ QUÉT 4 CỔNG CHÍNH CHỦ
    versions = ["v1", "v1beta"]
    patterns = [f"models/{base}", base]
    
    for ver in versions:
        for pat in patterns:
            url = f"https://generativelanguage.googleapis.com/{ver}/{pat}:generateContent?key={key}"
            try:
                res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=30)
                if res.status_code == 200:
                    return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), f"{pat} ({ver})"
            except: continue
            
    return None, "❌ Vẫn lỗi 404: Google không nhận diện được API Key hoặc Model này ở vùng của ní."

# --- ENGINE TERMINAL ---
@st.dialog("🖥️ SYSTEM TERMINAL v23.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    df_web = data['Website']
    active_sites = df_web[df_web['Trạng thái'].astype(str).str.contains('Active', case=False)]
    
    log_area = st.empty()
    log_h = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Bắt đầu chẩn đoán hệ thống..."]
    
    def add_log(msg):
        log_h.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_h))

    if active_sites.empty:
        add_log("❌ LỖI: Không tìm thấy dòng nào ghi 'Active' ở Tab Website!"); return

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0]
        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        
        # Gọi AI với bộ dò tìm
        content, meta = call_ai_diagnostic(v('GEMINI_API_KEY'), v('MODEL_VERSION'), v('PROMPT_TEMPLATE'))
        
        if content:
            add_log(f"✅ ĐÃ THÔNG! Robot tìm thấy cổng: {meta}")
            # Ghi Report
            try:
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                    site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", "1%", "85/100", site.get('các website đích',''), "Tiêu đề", "Sapo", datetime.now().strftime("%H:%M"), "Thành công", "Active"
                ])
                add_log("📝 Đã ghi Report thành công.")
            except: add_log("⚠️ Ghi Report lỗi (nhưng AI đã chạy xong).")
        else:
            add_log(meta)
            add_log("💡 Ní thử tạo API Key mới ở vùng khác (US/Singapore) xem sao.")
        
        time.sleep(1)

    st.success("🎉 TIẾN TRÌNH KẾT THÚC!")
    if st.button("ĐÓNG"): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v23.0</h1>", unsafe_allow_html=True)
data, msg = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, c3 = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 Reload", use_container_width=True): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, hide_index=True)
else:
    st.error(f"❌ {msg}")
    st.info("💡 Nếu thấy lỗi Module gspread: Ní hãy Reboot App trong Manage App nhé!")
