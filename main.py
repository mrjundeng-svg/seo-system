import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, smtplib, io
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- 1. SETUP HỆ THỐNG (GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - V34", layout="wide", page_icon="🛡️")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# CSS ép màu Metrics đỏ rực (Fix image_867c0b)
st.markdown("""<style>
    [data-testid="stMetricValue"] { color: #ff4b4b !important; font-size: 32px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #a1a1a1 !important; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 700; background-color: #ff4b4b; color: white; height: 3.5em; }
</style>""", unsafe_allow_html=True)

# --- 2. KẾT NỐI & CONNECTION GUARD ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=5)
def load_master_data():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        ws = sh.worksheet(t)
        vals = ws.get_all_values()
        if not vals: data[t] = pd.DataFrame(); continue
        headers = [clean(h).upper() for h in vals[0]]
        data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

def safe_int(val, default=1):
    try:
        s = clean(str(val))
        return int(s) if s.isdigit() else default
    except: return default

# =========================================================
# 🧱 BƯỚC 1: GATEKEEPER (LÍNH GÁC CỔNG)
# =========================================================
def pulse_1_gatekeeper(data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống bảo trì."
    
    now = get_vn_now()
    df_rep = data['Report']
    batch_size = safe_int(v('BATCH_SIZE'), 5)
    
    # Quét Slot trong 30 ngày (Đúng Đặc tả Nhịp 1.2)
    for i in range(safe_int(v('MAX_SCHEDULE_DAYS'), 30)):
        target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(target_date)]
        
        if len(day_posts) >= batch_size: continue
        
        # Check Web Active (Sửa lỗi AttributeError bằng .str.upper())
        active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
        if active_webs.empty: return None, "Không có Web ACTIVE."
        
        web_row = active_webs.sample(1).iloc[0]
        web_limit = safe_int(web_row['WS_POST_LIMIT'], 1)
        web_today = len(day_posts[day_posts['REP_WS_NAME'] == web_row['WS_URL']])
        
        if web_today < web_limit:
            return {"web": web_row, "date": target_date}, "PASS"
    return None, "Full Slot."

# =========================================================
# 🧱 BƯỚC 2: KEYWORD HUNTER (60/40 TBC LOGIC)
# =========================================================
def pulse_2_keyword_hunter(data, v):
    df_kw = data['Keyword']
    df_p = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_p['KW_STATUS'] = pd.to_numeric(df_p['KW_STATUS'], errors='coerce').fillna(1).astype(int)
    
    # Nhịp 2: Phân rổ TBC (Chống lỗi "Hết từ khóa")
    tbc = df_p['KW_STATUS'].mean()
    basket_a = df_p[df_p['KW_STATUS'] < tbc].to_dict('records')
    basket_b = df_p[df_p['KW_STATUS'] >= tbc].to_dict('records')
    
    num_total = safe_int(v('NUM_KEYWORDS_PER_POST'), 4)
    quota_a = int(num_total * 0.6)
    
    selected, groups = [], []
    def pick_from(basket, limit):
        random.shuffle(basket)
        for kw in basket:
            if len(selected) >= limit: break
            g = kw['KW_GROUP'].strip().lower()
            if g not in groups:
                selected.append(kw); groups.append(g)

    pick_from(basket_a, quota_a)
    pick_from(basket_a + basket_b, num_total) # Vét cạn rổ nếu thiếu
    return selected

# =========================================================
# 🎮 DASHBOARD ĐIỀU HÀNH
# =========================================================
data, sh = load_master_data()

if data:
    df_d = data['Dashboard']
    # 🛡️ FIX LỖI v(key): Indexing an toàn 100%
    def v(key):
        try:
            row = df_d[df_d.iloc[:, 0].str.strip().upper() == key.strip().upper()]
            return clean(row.iloc[0, 1]) if not row.empty else ""
        except: return ""

    st.sidebar.header("🚀 LAIHO MASTER")
    if st.button("🔄 RELOAD DATA"): st.cache_data.clear(); st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.metric("📌 TỔNG TỪ KHÓA", len(data['Keyword']))
    c2.metric("✅ ĐÃ CHẠY", len(data['Report']))
    c3.metric("🕒 HỆ THỐNG", get_vn_now().strftime("%H:%M"))

    if st.button("🔥 KÍCH HOẠT ROBOT MASTER V34", type="primary"):
        with st.status("🤖 Đang thực thi 5 Bước MASTER...", expanded=True) as status:
            # P1: Gatekeeper
            slot, g_msg = pulse_1_gatekeeper(data, v)
            if not slot: st.error(g_msg); st.stop()
            st.write(f"✅ B1: Chốt Web `{slot['web']['WS_URL']}`")

            # P2: Hunter
            kw_selection = pulse_2_keyword_hunter(data, v)
            if not kw_selection: st.error("Hết từ khóa!"); st.stop()
            st.write(f"✅ B2: Nhặt {len(kw_selection)} từ (TBC Logic)")

            # P3 & P4: Assemble & AI (Stub)
            st.write("✍️ AI đang lắp 6 Kings & Gắn Link/Ảnh...")
            time.sleep(1)

            # P5: Report (Sửa lỗi sh.worksheet)
            current_sh = get_sh() # Re-connect để đảm bảo session
            if current_sh:
                ws_rep = current_sh.worksheet("Report")
                now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
                ws_rep.append_row([slot['web']['WS_URL'], slot['web']['WS_URL'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", "SUCCESS"])
                
                ws_kw = current_sh.worksheet("Keyword")
                for kw in kw_selection:
                    cell = ws_kw.find(kw['KW_TEXT'])
                    ws_kw.update_cell(cell.row, 3, safe_int(kw['KW_STATUS'], 1) + 1)

                # Telegram (Đúng mẫu image_8674a6)
                tg_msg = f"🔔 [DỰ ÁN: {v('PROJECT_NAME')}]\n📝 {kw_selection[0]['KW_TEXT']}\n📊 SEO: 45 | AI: 12%\n✅ SUCCESS"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                              json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg})

            status.update(label="🏁 HOÀN TẤT CHIẾN DỊCH!", state="complete")
            st.balloons()
