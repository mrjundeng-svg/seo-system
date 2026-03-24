import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime

# --- CẤU HÌNH ---
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

# --- YOAST SEO ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:300]: score += 25
    if len(words) >= 500: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.6 <= dens <= 2.8: score += 25
    return score, round(dens, 2)

# --- AI CALLER v19.0 (DÙNG SDK CHÍNH CHỦ GOOGLE) ---
def call_gemini_sdk(key, model_name, prompt):
    try:
        genai.configure(api_key=key)
        # Tự động fix tên model
        m_name = model_name.strip().lower().replace("models/", "")
        if "flash" in m_name: m_name = "gemini-1.5-flash"
        elif "pro" in m_name: m_name = "gemini-1.5-pro"
        
        model = genai.GenerativeModel(m_name)
        response = model.generate_content(prompt)
        return response.text.strip(), f"{m_name} (SDK)"
    except Exception as e:
        return None, f"Lỗi Google SDK: {str(e)}"

# --- ENGINE TERMINAL ---
@st.dialog("🖥️ SYSTEM TERMINAL v19.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    # Fix lỗi bốc Website (xử lý khoảng trắng/hoa thường)
    df_web = data['Website']
    active_sites = df_web[df_web['Trạng thái'].astype(str).str.strip().str.capitalize() == 'Active']
    
    log_area = st.empty()
    log_history = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Khởi động hàng chính hãng Google..."]
    
    def add_log(msg):
        log_history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_history))

    if active_sites.empty:
        add_log("❌ LỖI: Không tìm thấy Website nào ghi 'Active'!"); return

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0]
        model_input = v('MODEL_VERSION').split(',')[0].strip()
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()

        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        add_log(f"🧠 Đang gọi AI qua SDK...")

        content, meta = call_gemini_sdk(v('GEMINI_API_KEY'), model_input, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}")
        
        if not content:
            add_log(f"❌ THẤT BẠI: {meta}")
            continue
        
        add_log(f"✅ AI trả bài mượt mà ({meta})")

        # SEO Audit
        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        add_log(f"📈 Yoast SEO: {score}/100 | Mật độ: {dens}%")
        
        # Ghi Report
        now = datetime.now()
        sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/p{random.randint(100,999)}", 
            now.strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", f"{dens}%", f"{score}/100", 
            site.get('các website đích',''), title, "Sapo", now.strftime("%H:%M"), "Thành công", "Active"
        ])
        
        if sh_ok: add_log("✅ Đã ghi danh vào Report.")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("❌ ĐÓNG TERMINAL", use_container_width=True): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v19.0</h1>", unsafe_allow_html=True)
if 'last_action' not in st.session_state: st.session_state.last_action = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5: st.warning("⏳ Đợi 5s!")
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
