import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, re, io, smtplib
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS", layout="wide")

def get_vn_now():
    return datetime.now(VN_TZ)

def clean(s):
    return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_range_val(val, default=1):
    s = clean(str(val))
    if not s: return default
    if '-' in s:
        try:
            parts = s.split('-')
            low = int(re.sub(r'\D', '', parts[0]))
            high = int(re.sub(r'\D', '', parts[1]))
            return random.randint(min(low, high), max(low, high))
        except: return default
    try: return int(re.sub(r'\D', '', s))
    except: return default

def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

def load_all_tabs():
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

def pulse_1_gatekeeper(data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "MAINTENANCE"
    now = get_vn_now()
    df_rep = data['Report']
    batch_size = get_range_val(v('BATCH_SIZE'), 5)
    for i in range(get_range_val(v('MAX_SCHEDULE_DAYS'), 30)):
        target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(target_date)]
        if len(day_posts) >= batch_size: continue
        active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
        if active_webs.empty: return None, "NO_ACTIVE_WEB"
        web_row = active_webs.sample(1).iloc[0].to_dict()
        web_limit = get_range_val(web_row['WS_POST_LIMIT'], 1)
        web_today = len(day_posts[day_posts['REP_WS_NAME'] == web_row['WS_URL']])
        if web_today < web_limit:
            return {"web": web_row, "date": target_date, "batch": batch_size}, "PASS"
    return None, "FULL_SLOT"

def pulse_2_hunter(data, v):
    df_kw = data['Keyword']
    df_p = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    if df_p.empty: return []
    df_p['KW_STATUS'] = pd.to_numeric(df_p['KW_STATUS'], errors='coerce').fillna(0).astype(int)
    tbc = df_p['KW_STATUS'].mean()
    basket_a = df_p[df_p['KW_STATUS'] <= tbc].to_dict('records')
    basket_b = df_p[df_p['KW_STATUS'] > tbc].to_dict('records')
    num_needed = get_range_val(v('NUM_KEYWORDS_PER_POST'), 4)
    quota_a = int(num_needed * 0.6)
    selected, groups = [], []
    def pick(basket, limit):
        random.shuffle(basket)
        for kw in basket:
            if len(selected) >= limit: break
            g = kw['KW_GROUP'].strip().lower()
            if g not in groups:
                selected.append(kw); groups.append(g)
    pick(basket_a, quota_a)
    pick(basket_a + basket_b, num_needed)
    return selected

def pulse_5_report(sh, v, web, kw_list, content, scores):
    kw_main = kw_list[0]['KW_TEXT']
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
    report_row = [
        web.get('WS_URL', ''), web.get('WS_PLATFORM', ''), now_str, f"Bài: {kw_main}", 
        content[:300], "1", "YES", "NO", kw_list[0]['KW_TEXT'],
        kw_list[1]['KW_TEXT'] if len(kw_list)>1 else "",
        kw_list[2]['KW_TEXT'] if len(kw_list)>2 else "",
        kw_list[3]['KW_TEXT'] if len(kw_list)>3 else "",
        kw_list[4]['KW_TEXT'] if len(kw_list)>4 else "",
        scores.get('seo', 0), scores.get('ai', '0%'), scores.get('read', 0), now_str, "SUCCESS", "SUCCESS"
    ]
    try:
        sh.worksheet("Report").append_row(report_row)
        ws_kw = sh.worksheet("Keyword")
        cell = ws_kw.find(kw_main)
        if cell: ws_kw.update_cell(cell.row, 3, get_range_val(kw_list[0].get('KW_STATUS', 0)) + 1)
    except: pass
    try:
        requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                      json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": f"✅ {kw_main}\n📊 {web.get('WS_URL')}", "parse_mode": "Markdown"})
    except: pass
    try:
        sender, pw, rec = v('SENDER_EMAIL'), v('SENDER_PASSWORD'), v('RECEIVER_EMAIL')
        msg = MIMEMultipart()
        msg['Subject'] = f"🚀 {kw_main}"
        msg.attach(MIMEText(content[:500], 'html'))
        doc = Document(); doc.add_heading(kw_main, 0); doc.add_paragraph(content)
        w_io = io.BytesIO(); doc.save(w_io); w_io.seek(0)
        part = MIMEBase('application', 'octet-stream'); part.set_payload(w_io.read()); encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="SEO_{kw_main}.docx"'); msg.attach(part)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, pw); s.sendmail(sender, rec, msg.as_string())
    except: pass

data, sh = load_all_tabs()
if data:
    df_d = data['Dashboard']
    def v(key):
        row = df_d[df_d.iloc[:, 0].str.strip().str.upper() == key.strip().upper()]
        return clean(row.iloc[0, 1]) if not row.empty else ""
    st.title("LAIHO SEO OS")
    if st.button("🚀 KÍCH HOẠT ROBOT"):
        slot, g_msg = pulse_1_gatekeeper(data, v)
        if not slot: st.error(g_msg); st.stop()
        kw_list = pulse_2_hunter(data, v)
        if not kw_list: st.error("EMPTY_KW"); st.stop()
        pulse_5_report(sh, v, slot['web'], kw_list, "Nội dung AI...", {'seo': 48, 'ai': '12%', 'read': 70})
        st.success("DONE")
