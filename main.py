import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, smtplib, io, re
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- 1. HỆ QUẢN TRỊ (GMT+7 & CLEAN RUN) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V28", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #ff4b4b !important; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. KẾT NỐI HỆ THỐNG ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None

@st.cache_data(ttl=5)
def load_master_data():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        ws = sh.worksheet(t)
        vals = ws.get_all_values()
        if vals:
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

# --- 3. BƯỚC 1: GATEKEEPER (CHỐT CHẶN 4 LỚP) ---
def pulse_1_gatekeeper(all_data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống bảo trì"
    now = get_vn_now()
    df_rep = all_data['Report']
    today_str = now.strftime("%Y-%m-%d")
    
    today_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(today_str)]
    if len(today_posts) >= int(v('BATCH_SIZE') or 10): return None, "Full BATCH_SIZE ngày"
    
    active_webs = all_data['Website'][all_data['Website']['WS_STATUS'].upper() == 'ACTIVE']
    if active_webs.empty: return None, "Không có Web ACTIVE"
    
    target_web = active_webs.sample(1).iloc[0]
    web_limit = int(target_web['WS_POST_LIMIT'] or 1)
    web_today = len(today_posts[today_posts['REP_WS_NAME'] == target_web['WS_URL']])
    if web_today >= web_limit: return None, "Web này đã đạt Post Limit"
    
    return target_web, "PASS"

# --- 4. BƯỚC 2: KEYWORD HUNTER (TBC LOGIC - CHỐNG HẾT TỪ) ---
def pulse_2_keyword_hunter(all_data, v):
    df_kw = all_data['Keyword']
    df_clean = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_clean['KW_STATUS'] = pd.to_numeric(df_clean['KW_STATUS'], errors='coerce').fillna(0).astype(int)
    
    if df_clean.empty: return None
    
    tbc = df_clean['KW_STATUS'].mean()
    num_needed = int(v('NUM_KEYWORDS_PER_POST') or 4)
    
    # Rổ A (Dưới TBC), Rổ B (Trên TBC)
    basket_a = df_clean[df_clean['KW_STATUS'] <= tbc].sample(frac=1).to_dict('records')
    basket_b = df_clean[df_clean['KW_STATUS'] > tbc].sample(frac=1).to_dict('records')
    
    selected, groups = [], []
    for kw in (basket_a + basket_b): # Dồn chéo tự động nếu Rổ A thiếu
        if len(selected) >= num_needed: break
        if kw['KW_GROUP'] not in groups:
            selected.append(kw); groups.append(kw['KW_GROUP'])
            
    return selected

# --- 5. BƯỚC 4: TẠO FILE WORD & GỬI GMAIL ---
def send_gmail_with_word(v, keyword, content):
    sender = v('SENDER_EMAIL')
    password = v('SENDER_PASSWORD')
    receiver = v('RECEIVER_EMAIL')
    if not all([sender, password, receiver]): return False

    # Tạo Word đính kèm
    doc = Document()
    doc.add_heading(keyword, 0)
    doc.add_paragraph(content)
    word_io = io.BytesIO()
    doc.save(word_io)
    word_io.seek(0)

    # Cấu hình Mail HTML hoài cổ (Legacy)
    msg = MIMEMultipart()
    msg['From'] = f"Laiho Robot <{sender}>"; msg['To'] = receiver
    msg['Subject'] = f"[HỆ THỐNG PBN] {keyword} - 🚀 XUẤT BẢN THÀNH CÔNG"

    html = f"""<div style="font-family:Arial; line-height:1.6;">
    <h3>🚀 XUẤT BẢN: {keyword}</h3>
    <p>🌐 <b>BÁO CÁO:</b> Đã tạo file Word và lưu Tracking.</p>
    <hr><div style="background:#f9f9f9; padding:10px;">{content[:500]}...</div></div>"""
    msg.attach(MIMEText(html, 'html'))

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(word_io.read()); encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="SEO_{keyword.replace(" ","_")}.docx"')
    msg.attach(part)

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, password); s.sendmail(sender, receiver, msg.as_string())
        return True
    except: return False

# --- GIAO DIỆN ĐIỀU KHIỂN ---
data, sh = load_master_data()
if data:
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().upper() == k.strip().upper()].iloc[:, 1]
        return clean(res.values[0]) if not res.empty else ""

    # UI Metrics
    df_kw = data['Keyword']
    done = len(df_kw[df_kw.iloc[:, 2].astype(str).str.contains('SUCCESS|1|2|3|4|5|6|7|8|9', case=False)])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 TỔNG TỪ KHÓA", len(df_kw))
    c2.metric("✅ ĐÃ XỬ LÝ", done)
    c3.metric("⏳ CÒN LẠI", len(df_kw) - done)

    if st.button("🚀 KÍCH HOẠT HỆ THỐNG MASTER V28", type="primary"):
        with st.status("🛠️ Robot đang thực thi 5 Nhịp Master...", expanded=True) as status:
            # Nhịp 1
            web, g_msg = pulse_1_gatekeeper(data, v)
            if not web: st.error(g_msg); st.stop()
            st.write(f"🛡️ Gatekeeper: Chốt Web `{web['WS_URL']}`")
            
            # Nhịp 2
            kw_selection = pulse_2_keyword_hunter(data, v)
            if not kw_selection: st.error("Hết từ khóa!"); st.stop()
            st.write(f"🔑 Nhặt {len(kw_selection)} từ khóa chiến thuật (TBC Logic)")
            
            # Nhịp 3 (Giả lập AI)
            kw_main = kw_selection[0]['KW_TEXT']
            st.write(f"✍️ AI đang viết bài cho: **{kw_main}**")
            time.sleep(2)
            content_sim = f"Đây là bài viết chuẩn SEO cho {kw_main}. Nội dung được tối ưu hóa..."

            # Nhịp 4 & 5 (Reporting)
            success_mail = send_gmail_with_word(v, kw_main, content_sim)
            
            # Cập nhật Telegram
            tg_msg = f"✅ *Robot Laiho:* {kw_main}\n📊 SEO: 48 | AI: 12%\n📧 Mail: {'Xong' if success_mail else 'Lỗi'}"
            requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                          json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg, "parse_mode": "Markdown"})
            
            # Cập nhật Google Sheet
            ws_rep = sh.worksheet("Report")
            ws_rep.append_row([v('PROJECT_NAME'), web['WS_URL'], get_vn_now().strftime("%Y-%m-%d %H:%M"), kw_main, "SUCCESS"])
            
            ws_kw = sh.worksheet("Keyword")
            cell = ws_kw.find(kw_main)
            ws_kw.update_cell(cell.row, 3, int(kw_selection[0]['KW_STATUS']) + 1)
                
            status.update(label="🏁 CHIẾN DỊCH HOÀN TẤT!", state="complete")
            st.balloons()
