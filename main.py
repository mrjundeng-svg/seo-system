import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

# --- CẤU HÌNH ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=60)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- YOAST SEO ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:300]: score += 25
    if len(words) >= 500: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.6 <= dens <= 2.5: score += 25
    return score, round(dens, 2)

# --- AI CALLER (BẢN VÁ LỖI 404 TOÀN DIỆN) ---
def call_ai_robust(key, model_name, prompt):
    name = model_name.strip().lower()
    if "models/" in name: name = name.split("/")[-1]
    
    # 🛠️ Thử lần lượt các cổng v1 và v1beta để né lỗi 404
    for version in ["v1", "v1beta"]:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{name}:generateContent?key={key}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), "OK"
            elif res.status_code == 404:
                continue # Thử cổng tiếp theo
            else:
                return None, f"Lỗi {res.status_code}: {res.text[:150]}"
        except: continue
        
    return None, f"Lỗi 404: Google không tìm thấy Model '{name}'. Ní check lại tên trong Sheet nhé!"

def update_report(row):
    try:
        sh = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
        return True
    except: return False

# --- ENGINE TERMINAL ---
@st.dialog("🖥️ SYSTEM TERMINAL", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    log_placeholder = st.empty()
    log_list = [f"[{datetime.now().strftime('%H:%M:%S')}] root@seo:~# Initializing..."]
    
    def add_log(msg):
        log_list.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_placeholder.code("\n".join(log_list))

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0]
        chosen_model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()])
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()

        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        add_log(f"🧠 AI: Đang vít {chosen_model}...")

        # Gọi AI với bộ vá lỗi 404
        content, err = call_ai_robust(v('GEMINI_API_KEY'), chosen_model, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}")
        
        if not content:
            add_log(f"❌ THẤT BẠI: {err}")
            continue

        if v('SPIN_MODE') == "ON":
            add_log("🔄 Spin: Đang humanize...")
            content_s, _ = call_ai_robust(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string()}\nContent: {content}")
            content = content_s if content_s else content

        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        add_log(f"📊 Yoast SEO: {score}/100 | Density: {dens}%")
        
        if update_report([site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", f"{dens}%", f"{score}/100", site.get('các website đích',''), title, "Sapo optimized", datetime.now().strftime("%H:%M"), "Thành công", "Active"]):
            add_log("✅ Đã ghi danh vào Report.")
        
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("❌ ĐÓNG TERMINAL", use_container_width=True):
        st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v17.6</h1>", unsafe_allow_html=True)
if 'last_action' not in st.session_state: st.session_state.last_action = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5: st.warning("⏳ Chậm thôi ní!")
                    else:
                        st.session_state.last_action = time.time()
                        run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True):
                    st.cache_data.clear(); st.rerun()
                
                disp = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask, axis=1)
                st.dataframe(disp, use_container_width=True, height=400, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
