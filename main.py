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

@st.cache_data(ttl=60)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- SEO AUDIT YOAST STYLE ---
def yoast_seo_audit(content, keyword, title):
    score = 0
    kw = keyword.lower().strip()
    c_low = content.lower()
    t_low = title.lower()
    words = content.split()
    
    if kw in t_low: score += 20
    if kw in c_low[:300]: score += 20
    if len(words) >= 600: score += 20
    density = (c_low.count(kw) / len(words)) * 100 if len(words) > 0 else 0
    if 0.5 <= density <= 2.5: score += 20
    if "##" in content or "<h3>" in c_low: score += 20
    return score, round(density, 2)

# --- UTILS ---
def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

def send_telegram(token, chat_id, msg):
    if not token or not chat_id: return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
    except: pass

def update_report(row):
    try:
        sh = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
        return True
    except: return False

# --- ENGINE VỚI REAL-TIME LOG ---
@st.dialog("🖥️ SYSTEM TERMINAL (DEEP LOGGING)", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    log_area = st.empty() 
    log_content = f"<b>[{datetime.now().strftime('%H:%M:%S')}] root@seo-system:~# Khởi động Robot...</b>\n"
    
    num_to_gen = int(v('Số lượng bài cần tạo') or 1)
    
    for i in range(num_to_gen):
        log_content += f"━━━━━━━━━━━━━ [BÀI {i+1}/{num_to_gen}] ━━━━━━━━━━━━━\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)

        # 1. Chọn Site & Keyword
        site = active_sites.sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()])
        raw_kws = v('Danh sách Keyword bài viết')
        main_kw = raw_keywords = raw_kws.split('|')[0].strip()

        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 🛰️ Chọn vệ tinh: {site['Tên web']}\n"
        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 🔑 Keyword chính: {main_kw}\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)

        # 2. Xử lý Local
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
            log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 📍 Chế độ: LOCAL SEO ({l['Cung đường']})\n"
        else:
            log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 🌐 Chế độ: GLOBAL SEO\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)

        # 3. Gọi AI Gen
        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 AI ({model}): Đang tạo nội dung...\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)
        raw_content = call_ai(v('GEMINI_API_KEY'), model, f"{v('PROMPT_TEMPLATE')}\nKWS: {raw_kws}\n{loc_str}")
        
        if "LỖI AI" in raw_content:
            log_content += f"  ❌ LỖI: Không thể tạo nội dung từ AI!\n"
            log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)
            continue

        # 4. Chạy Spin Humanize
        if v('SPIN_MODE') == "ON":
            log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 🔄 SPIN: Đang lách AI Detection...\n"
            log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)
            raw_content = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string()}\nContent: {raw_content}")

        # 5. SEO Audit & Ghi Sheet
        title = raw_content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(raw_content, main_kw, title)
        
        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 📊 SEO: {score}/100 | Density: {dens}%\n"
        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 📝 Sheet: Đang ghi vào Tab Report...\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)
        
        ok = update_report([site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), raw_kws, loc_str, "✅", f"{dens}%", f"{score}/100", site.get('các website đích',''), title, "Sapo optimized", datetime.now().strftime("%H:%M"), "Thành công", "Active"])
        
        if ok: log_content += f"  ✅ Đã ghi Sheet thành công.\n"
        else: log_content += f"  ❌ LỖI: Không thể ghi vào Google Sheet!\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)

        # 6. Telegram
        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] 📲 Telegram: Đang gửi thông báo...\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)
        
        tele_msg = (f"🚀 <b>SEO REPORT</b>\n🛰 Vệ tinh: {site['Tên web']}\n🎯 Link về: {site.get('các website đích', 'N/A')}\n"
                    f"🔑 Từ khoá: {main_kw}\n📈 SEO: {score}/100\n✅ Trạng thái: Thành công")
        send_telegram(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), tele_msg)
        
        log_content += f"[{datetime.now().strftime('%H:%M:%S')}] ✨ HOÀN TẤT BÀI {i+1}!\n"
        log_area.markdown(f"<pre>{log_content}</pre>", unsafe_allow_html=True)
        time.sleep(1)

    st.success("🎉 TẤT CẢ TIẾN TRÌNH ĐÃ KẾT THÚC!")
    if st.button("Đóng Terminal"): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v16.2</h1>", unsafe_allow_html=True)
data, msg = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True): st.cache_data.clear(); st.rerun()
                
                disp_df = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
                    return row['Input dữ liệu']
                disp_df['Input dữ liệu'] = disp_df.apply(mask, axis=1)
                st.dataframe(disp_df, use_container_width=True, height=400, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else: st.error(f"Lỗi: {msg}")
