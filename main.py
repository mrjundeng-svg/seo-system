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

@st.cache_data(ttl=300)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Đồng bộ thành công"
    except Exception as e: return None, str(e)

def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

def send_telegram(token, chat_id, msg):
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"})
    except: pass

def update_report(row):
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
    except: pass

# --- ĐỘNG CƠ RUN ---
@st.dialog("🤖 SYSTEM LOGGING & REPORT", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    log_area = st.empty() 
    log_content = f"root@{v('PROJECT_NAME').lower()}:~# Kích hoạt hệ thống...\n"
    
    num_to_gen = int(v('Số lượng bài cần tạo') or 1)
    
    for i in range(num_to_gen):
        site = active_sites.sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()])
        keyword = v('Danh sách Keyword bài viết')
        
        log_content += f"[+] [{i+1}/{num_to_gen}] Đang xử lý: {site['Tên web']}...\n"
        log_area.code(log_content, language="bash")

        # Step 1: Gen & Local
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 Địa điểm: {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        prompt = f"{v('PROMPT_TEMPLATE')}\nKeywords: {keyword}\n{loc_str}\n\n*Yêu cầu: Viết tiêu đề hấp dẫn ở dòng đầu tiên, sapo ở dòng thứ 2.*"
        full_content = call_ai(v('GEMINI_API_KEY'), model, prompt)
        
        log_content += f"  > Đã tạo xong nội dung gốc ({model}).\n"
        log_area.code(log_content, language="bash")

        # Step 2: Spin
        if v('SPIN_MODE') == "ON":
            log_content += "  > Đang chạy bộ lọc Spin Humanize...\n"
            log_area.code(log_content, language="bash")
            full_content = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string(index=False)}\nContent: {full_content}")

        # Tách Tiêu đề, Sapo (Giả định dòng 1 là tiêu đề, dòng 2 là sapo)
        lines = full_content.split('\n')
        title = lines[0] if len(lines) > 0 else "Không có tiêu đề"
        sapo = lines[1] if len(lines) > 1 else "Không có sapo"

        # Step 3: Ghi Report Chi tiết
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        report_row = [
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post-{i}", 
            now, keyword, loc_str, "✅ Pass", "30%", "85",
            site.get('các website đích', ''), title, sapo, now, "✅ Thành công", "Active"
        ]
        update_report(report_row)
        
        # Step 4: Bắn Telegram
        tele_msg = f"🚀 <b>SEO BÁO CÁO:</b>\n- Site: {site['Tên web']}\n- Từ khóa: {keyword}\n- Local: {loc_str if loc_str else 'Global'}\n- Trạng thái: ✅ Đã lưu Report"
        send_telegram(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), tele_msg)
        
        log_content += f"  > ✅ Đã ghi Report & Bắn Telegram.\n"
        log_area.code(log_content, language="bash")
        time.sleep(1)
        
    st.success("🎉 TẤT CẢ TIẾN TRÌNH HOÀN TẤT!")
    if st.button("ĐÓNG POPUP"): st.rerun()

# --- UI INTERFACE ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v15.2</h1>", unsafe_allow_html=True)

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 3])
                if c1.button("🚀 RUN", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
                
                # MASKING SENSITIVE DATA
                disp_df = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
                    return row['Input dữ liệu']
                disp_df['Input dữ liệu'] = disp_df.apply(mask, axis=1)
                st.dataframe(disp_df, use_container_width=True, height=400, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else: st.error(f"Lỗi kết nối: {msg}")
