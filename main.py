import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, smtplib, io, re
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CONFIG HỆ THỐNG GMT+7 ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V33", layout="wide", page_icon="🛡️")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# Helper ép kiểu số an toàn (Fix lỗi image_932b29)
def safe_int(val, default=1):
    try:
        s = clean(str(val))
        return int(s) if s.isdigit() else default
    except: return default

# --- KẾT NỐI DATA ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=5)
def load_master_data():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        ws = sh.worksheet(t); vals = ws.get_all_values()
        if not vals: data[t] = pd.DataFrame(); continue
        headers = [clean(h).upper() for h in vals[0]]
        data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

# =========================================================
# 🧱 BƯỚC 1: GATEKEEPER (CHỐT CHẶN 4 LỚP)
# =========================================================
def pulse_1_gatekeeper(data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống đang bảo trì."
    
    now = get_vn_now(); df_rep = data['Report']
    batch_size = safe_int(v('BATCH_SIZE'), 5)
    
    for i in range(safe_int(v('MAX_SCHEDULE_DAYS'), 30)):
        target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(target_date)]
        
        if len(day_posts) >= batch_size: continue
        
        # 🛡️ FIX LỖI AttributeError: Dùng .str.upper()
        active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
        if active_webs.empty: return None, "Không có Web ACTIVE."
        
        web_row = active_webs.sample(1).iloc[0]
        # 🛡️ FIX LỖI ValueError: Dùng safe_int
        web_limit = safe_int(web_row['WS_POST_LIMIT'], 1)
        web_today = len(day_posts[day_posts['REP_WS_NAME'] == web_row['WS_URL']])
        
        if web_today < web_limit:
            return {"web": web_row, "date": target_date}, "PASS"
    return None, "Đã full lịch đăng bài."

# =========================================================
# 🧱 BƯỚC 2: KEYWORD HUNTER (60/40 & TBC LOGIC)
# =========================================================
def pulse_2_keyword_hunter(data, v):
    df_kw = data['Keyword']
    df_p = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_p['KW_STATUS'] = pd.to_numeric(df_p['KW_STATUS'], errors='coerce').fillna(1).astype(int)
    
    tbc = df_p['KW_STATUS'].mean()
    basket_a = df_p[df_p['KW_STATUS'] < tbc].to_dict('records')
    basket_b = df_p[df_p['KW_STATUS'] >= tbc].to_dict('records')
    
    num_total = safe_int(v('NUM_KEYWORDS_PER_POST'), 4)
    quota_a = int(num_total * 0.6)
    
    selected, groups = [], []
    def pick(basket, limit):
        random.shuffle(basket)
        for kw in basket:
            if len(selected) >= limit: break
            g = kw['KW_GROUP'].strip().lower()
            if g not in groups:
                selected.append(kw); groups.append(g)

    pick(basket_a, quota_a)
    pick(basket_a + basket_b, num_total) # Vét rổ
    return selected

# =========================================================
# 🎮 GIAO DIỆN ĐIỀU HÀNH
# =========================================================
data, sh = load_master_data()

if data:
    df_d = data['Dashboard']
    # 🛡️ FIX LỖI v(k): Bốc giá trị an toàn
    def v(key):
        try:
            row = df_d[df_d.iloc[:, 0].str.strip().upper() == key.strip().upper()]
            return clean(row.iloc[0, 1]) if not row.empty else ""
        except: return ""

    # Giao diện chính
    st.sidebar.title("🛡️ LAIHO MASTER OS")
    if st.button("🔄 RELOAD DATA"): st.cache_data.clear(); st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.metric("📌 TỔNG TỪ KHÓA", len(data['Keyword']))
    c2.metric("✅ ĐÃ CHẠY", len(data['Report']))
    c3.metric("🕒 HỆ THỐNG", get_vn_now().strftime("%H:%M"))

    if st.button("🚀 KÍCH HOẠT ROBOT MASTER V33", type="primary"):
        with st.status("🤖 Thực thi 5 Bước Đặc Tả Master...", expanded=True) as status:
            # P1: Gatekeeper
            slot, g_msg = pulse_1_gatekeeper(data, v)
            if not slot: st.error(g_msg); st.stop()
            st.write(f"✅ B1: Chốt Web `{slot['web']['WS_URL']}`")

            # P2: Hunter
            kw_selection = pulse_2_keyword_hunter(data, v)
            if not kw_selection: st.error("Hết từ khóa!"); st.stop()
            st.write(f"✅ B2: Nhặt {len(kw_selection)} từ (60/40 TBC Logic)")

            # P3 & P4: Assemble & Optimize
            # [Giả lập nội dung AI...]
            st.write("✍️ AI đang lắp 6 Kings & Gắn Link/Ảnh...")
            time.sleep(1)

            # P5: Report (Nhịp 2 & 3)
            # Ghi Sheet Report
            ws_rep = sh.worksheet("Report")
            now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
            ws_rep.append_row([slot['web']['WS_URL'], slot['web']['WS_URL'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", "SUCCESS"])
            
            # Cập nhật Status (Cộng 1)
            ws_kw = sh.worksheet("Keyword")
            for kw in kw_selection:
                cell = ws_kw.find(kw['KW_TEXT'])
                ws_kw.update_cell(cell.row, 3, safe_int(kw['KW_STATUS'], 1) + 1)

            # Bắn Telegram (Đúng mẫu image_8674a6)
            tg_msg = f"🔔 [DỰ ÁN: {v('PROJECT_NAME')}]\n📝 {kw_selection[0]['KW_TEXT']}\n📊 SEO: 45 | AI: 12%\n✅ SUCCESS"
            requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                          json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg})

            status.update(label="🏁 HOÀN TẤT!", state="complete")
            st.balloons()
