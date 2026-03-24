import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re, json
from datetime import datetime

# --- KẾT NỐI HỆ THỐNG ---
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

# --- YOAST SEO AUDIT ---
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

# --- AI CALLER VỚI CHI TIẾT LỖI ---
def call_ai_with_debug(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        status_code = res.status_code
        res_json = res.json()
        
        if status_code == 200:
            return res_json['candidates'][0]['content']['parts'][0]['text'].strip(), "OK"
        else:
            # Phân tích lý do lỗi từ Google
            error_msg = res_json.get('error', {}).get('message', 'Không rõ nguyên nhân')
            if status_code == 429: reason = f"Lỗi 429: Hết hạn mức (Quota Exceeded)"
            elif status_code == 400: reason = f"Lỗi 400: API Key sai hoặc Model không hỗ trợ"
            else: reason = f"Lỗi {status_code}: {error_msg}"
            return None, reason
    except Exception as e:
        return None, f"Lỗi kết nối: {str(e)}"

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

# --- ENGINE LOGGING TỪNG DÒNG ---
@st.dialog("🖥️ SYSTEM TERMINAL (DEEP DEBUG)", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    log_area = st.empty() 
    log_lines = [f"<b>[{datetime.now().strftime('%H:%M:%S')}] root@seo-system:~# Bắt đầu vận hành...</b>"]
    
    def print_log(msg):
        log_lines.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.markdown(f"<pre style='white-space: pre-wrap; word-wrap: break-word;'>{chr(10).join(log_lines)}</pre>", unsafe_allow_html=True)

    num_to_gen = int(v('Số lượng bài cần tạo') or 1)
    
    for i in range(num_to_gen):
        print_log(f"━━━━━━━━━━━━━━━━━━ [BÀI {i+1}/{num_to_gen}] ━━━━━━━━━━━━━━━━━━")
        
        # 1. Khởi tạo dữ liệu
        site = active_sites.sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()])
        kws = v('Danh sách Keyword bài viết')
        main_kw = kws.split('|')[0].strip()
        
        print_log(f"🛰 Vệ tinh: <b>{site['Tên web']}</b>")
        print_log(f"🔑 Keyword: {main_kw}")

        # 2. Xử lý Local
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
            print_log(f"📍 Chế độ Local: {l['Cung đường']}")
        else:
            print_log(f"🌐 Chế độ: Global SEO")

        # 3. Gọi AI Gen Content
        print_log(f"🧠 AI ({model}): Đang tạo nội dung...")
        content, err = call_ai_with_debug(v('GEMINI_API_KEY'), model, f"{v('PROMPT_TEMPLATE')}\nKWS: {kws}\n{loc_str}")
        
        if not content:
            print_log(f"❌ <b>STUCK! LÝ DO: {err}</b>")
            continue # Nhảy sang bài tiếp theo nếu lỗi

        # 4. Spin Humanize
        if v('SPIN_MODE') == "ON":
            print_log(f"🔄 Spin: Đang humanize để lách AI Detection...")
            content, err = call_ai_with_debug(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string()}\nContent: {content}")
            if not content:
                print_log(f"  ❌ Spin thất bại: {err}")
                continue

        # 5. Chấm điểm Yoast SEO
        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        print_log(f"📊 Yoast SEO Audit: <b>{score}/100</b> | Mật độ: {dens}%")

        # 6. Ghi Report
        print_log(f"📝 Report: Đang lưu dữ liệu vào Google Sheet...")
        now_date = datetime.now().strftime("%Y-%m-%d")
        now_time = datetime.now().strftime("%H:%M")
        
        report_row = [
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post-{random.randint(1000,9999)}", 
            now_date, kws, loc_str, "✅ Pass", f"{dens}%", f"{score}/100",
            site.get('các website đích',''), title, "Sapo optimized", now_time, "Thành công", "Active"
        ]
        
        if update_report(report_row):
            print_log(f"  ✅ Ghi Sheet thành công.")
        else:
            print_log(f"  ❌ Lỗi: Không thể ghi Sheet (Kiểm tra quyền Editor hoặc mạng).")

        # 7. Bắn Telegram
        print_log(f"📲 Telegram: Đang gửi thông báo về máy...")
        tele_msg = (f"🚀 <b>SEO REPORT</b>\n🛰 Vệ tinh: {site['Tên web']}\n🎯 Bắn về: {site.get('các website đích', 'N/A')}\n"
                    f"⏱ Thời gian: {now_date} {now_time}\n🔑 Từ khoá: {main_kw}\n📈 SEO: {score}/100\n✅ Trạng thái: Thành công")
        send_telegram(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), tele_msg)
        
        print_log(f"✨ <b>HOÀN TẤT BÀI {i+1}!</b>")
        time.sleep(1)

    st.success("🎉 TẤT CẢ TIẾN TRÌNH KẾT THÚC!")
    if st.button("KẾT THÚC & ĐÓNG"): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v16.5</h1>", unsafe_allow_html=True)
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
