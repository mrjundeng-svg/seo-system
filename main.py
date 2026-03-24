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
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- YOAST SEO AUDIT ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:300]: score += 25
    if len(words) >= 600: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.8 <= dens <= 2.5: score += 25
    return score, round(dens, 2)

# --- AI CALLER v18.0 (CHỐNG 404 TUYỆT ĐỐI) ---
def call_ai_ultimate(key, model_name, prompt):
    # Chuẩn hóa tên model
    base_name = model_name.strip().lower().replace("models/", "")
    # Danh sách các "biến thể" để thử nếu bị 404
    attempts = [
        (base_name, "v1"), 
        (base_name, "v1beta"),
        ("gemini-1.5-flash", "v1"), # Dự phòng 1
        ("gemini-1.5-flash-latest", "v1beta") # Dự phòng 2
    ]
    
    last_err = ""
    for name, ver in attempts:
        url = f"https://generativelanguage.googleapis.com/{ver}/models/{name}:generateContent?key={key}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            if res.status_code == 200:
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), f"{name} ({ver})"
            last_err = f"Cổng {ver} báo: {res.text[:100]}"
        except Exception as e:
            last_err = str(e)
            
    return None, f"Cạn kiệt phương án! Lỗi cuối: {last_err}"

def update_report(row):
    try:
        sh = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
        return True
    except: return False

# --- ENGINE TERMINAL (DEEP LOGGING) ---
@st.dialog("🖥️ SYSTEM TERMINAL v18.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    log_area = st.empty()
    log_history = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Khởi động hệ thống..."]
    
    def write_log(msg):
        log_history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_history)) # Nhả log dọc cực chuẩn

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        write_log(f"━━━━━━━━ Bài {i+1}/{num} ━━━━━━━━")
        site = active_sites.sample(n=1).iloc[0]
        model_input = random.choice([m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()])
        raw_kws = v('Danh sách Keyword bài viết')
        main_kw = raw_kws.split('|')[0].strip()

        write_log(f"🛰 Vệ tinh: {site['Tên web']}") # Lấy cột Tên web đúng ý sếp
        write_log(f"🔑 Từ khóa: {main_kw}")

        # AI Generation
        write_log(f"🧠 Đang gọi AI ({model_input})...")
        content, meta = call_ai_ultimate(v('GEMINI_API_KEY'), model_input, f"{v('PROMPT_TEMPLATE')}\nKeywords: {raw_kws}")
        
        if not content:
            write_log(f"❌ THẤT BẠI: {meta}")
            write_log("💡 Gợi ý: Kiểm tra lại API Key trong Dashboard (có dư dấu cách không?)")
            continue
        
        write_log(f"✅ AI phản hồi thành công qua {meta}")

        # Humanize / Spin
        if v('SPIN_MODE') == "ON":
            write_log("🔄 Đang humanize để lách AI Detection...")
            content_s, _ = call_ai_ultimate(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string()}\nContent: {content}")
            content = content_s if content_s else content

        # SEO Audit
        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        write_log(f"📈 Yoast SEO: {score}/100 (Mật độ: {dens}%)")
        
        # Ghi Report
        write_log("📝 Đang ghi báo cáo vào Google Sheet...")
        now = datetime.now()
        sh_ok = update_report([
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/p{random.randint(100,999)}", 
            now.strftime("%Y-%m-%d"), raw_kws, "", "✅", f"{dens}%", f"{score}/100", 
            site.get('các website đích',''), title, "Sapo optimized", now.strftime("%H:%M"), "Thành công", "Active"
        ])
        
        if sh_ok: write_log("✅ Đã lưu Report thành công!")
        write_log(f"✨ HOÀN TẤT BÀI {i+1}!")
        time.sleep(1)

    st.success("🎉 TẤT CẢ TIẾN TRÌNH ĐÃ XONG!")
    if st.button("❌ ĐÓNG TERMINAL", use_container_width=True):
        st.rerun()

# --- GIAO DIỆN UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v18.0</h1>", unsafe_allow_html=True)
if 'last_action' not in st.session_state: st.session_state.last_action = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5: st.warning("⏳ Chậm lại ní! Đợi 5s.")
                    else:
                        st.session_state.last_action = time.time()
                        run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5: st.toast("⚠️ Reload quá nhanh!")
                    else:
                        st.session_state.last_action = time.time()
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
