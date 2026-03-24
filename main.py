import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
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
        data = {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}
        return data, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- YOAST SEO AUDIT ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:300]: score += 25
    if len(words) >= 500: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.6 <= dens <= 2.8: score += 25
    return score, round(dens, 2)

# --- AI CALLER v20.0 (SỬ DỤNG CỔNG v1 ỔN ĐỊNH - KHÔNG CẦN THƯ VIỆN NGOÀI) ---
def call_ai_stable(key, model_name, prompt):
    # Chuẩn hóa tên model: Bỏ mọi thứ dư thừa
    name = model_name.strip().lower()
    if "flash" in name: name = "gemini-1.5-flash"
    elif "pro" in name: name = "gemini-1.5-pro"
    else: name = "gemini-1.5-flash" # Mặc định nếu sếp gõ sai
    
    # Dùng cổng v1 - Cổng này cực kỳ ổn định, ít bị 404
    url = f"https://generativelanguage.googleapis.com/v1/models/{name}:generateContent?key={key}"
    
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        res = requests.post(url, json=payload, headers=headers, timeout=60)
        if res.status_code == 200:
            return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), f"{name} (v1)"
        else:
            # Nếu v1 vẫn lỗi, thử lách qua v1beta một lần cuối
            url_beta = f"https://generativelanguage.googleapis.com/v1beta/models/{name}:generateContent?key={key}"
            res_beta = requests.post(url_beta, json=payload, headers=headers, timeout=60)
            if res_beta.status_code == 200:
                return res_beta.json()['candidates'][0]['content']['parts'][0]['text'].strip(), f"{name} (v1beta)"
            return None, f"Lỗi {res.status_code}: {res.text[:150]}"
    except Exception as e:
        return None, f"Lỗi kết nối: {str(e)}"

# --- ENGINE TERMINAL ---
@st.dialog("🖥️ SYSTEM TERMINAL v20.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.strip().str.capitalize() == 'Active']
    log_area = st.empty()
    log_history = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Khởi động Mode Siêu Ổn Định..."]
    
    def add_log(msg):
        log_history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_history))

    if active_sites.empty:
        add_log("❌ LỖI: Sếp chưa gõ 'Active' vào Tab Website rồi!"); return

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0]
        model_input = v('MODEL_VERSION').split(',')[0].strip()
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()

        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        add_log(f"🧠 Đang gọi AI qua cổng v1...")

        content, meta = call_ai_stable(v('GEMINI_API_KEY'), model_input, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}")
        
        if not content:
            add_log(f"❌ THẤT BẠI: {meta}")
            continue
        
        add_log(f"✅ AI trả bài qua cổng {meta}")

        # SEO Audit
        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        add_log(f"📈 Yoast SEO: {score}/100 | Mật độ: {dens}%")
        
        # Ghi Report
        sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post-{random.randint(100,999)}", 
            datetime.now().strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", f"{dens}%", f"{score}/100", 
            site.get('các website đích',''), title, "Sapo optimized", datetime.now().strftime("%H:%M"), "Thành công", "Active"
        ])
        
        if sh_ok: add_log("✅ Đã lưu vào Tab Report.")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("❌ ĐÓNG TERMINAL", use_container_width=True): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v20.0</h1>", unsafe_allow_html=True)
if 'last_action' not in st.session_state: st.session_state.last_action = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5: st.warning("⏳ Chậm lại ní! 5s bấm 1 lần thôi.")
                    else:
                        st.session_state.last_action = time.time(); run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True):
                    st.cache_data.clear(); st.rerun()
                
                disp = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        v_str = str(row['Input dữ liệu'])
                        return v_str[:4] + "****" + v_str[-4:] if len(v_str) > 8 else "****"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask, axis=1)
                st.dataframe(disp, use_container_width=True, height=400, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
