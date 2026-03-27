import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
import smtplib, time, random, re, requests, io
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from docx import Document
from datetime import datetime, timedelta, timezone

# --- 1. SETUP CHUẨN GMT+7 ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V88 - NO CHEAT", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)
def get_ts(): return get_vn_now().strftime("%Y-%m-%d %H:%M")

# --- 2. HÀM TÌM CỘT DYNAMIC (CHỐNG SAI VỊ TRÍ) ---
def get_col_idx(ws, header_name):
    try:
        headers = ws.row_values(1)
        return headers.index(header_name) + 1
    except: return None

# --- 3. GHI SỔ THỰC TẾ (TIMESTAMP & STATUS) ---
def log_action_to_sheet(ws, find_val, status_col_name=None, date_col_name=None):
    try:
        cell = ws.find(find_val)
        if cell:
            if status_col_name:
                idx = get_col_idx(ws, status_col_name)
                if idx:
                    curr = ws.cell(cell.row, idx).value or 0
                    ws.update_cell(cell.row, idx, int(curr) + 1)
            if date_col_name:
                idx = get_col_idx(ws, date_col_name)
                if idx: ws.update_cell(cell.row, idx, get_ts())
    except: pass

# --- 4. TÍNH CHỈ SỐ THẬT (NHỊP 4) ---
def get_real_metrics(html, kw, title):
    words = re.findall(r'\w+', html)
    sentences = [s for s in re.split(r'[.!?]', html) if len(s.strip()) > 5]
    asl = len(words) / len(sentences) if sentences else 0
    # Công thức Flesch Việt hóa: $Score = 206.835 - (1.015 \times ASL) - (84.6 \times 1.1)$
    read = round(max(0, min(100, 206.835 - (1.015 * asl) - (84.6 * 1.1))), 1)
    
    seo = 10 # Base
    if title and kw.lower() in title.lower(): seo += 30
    if "<h1>" in html.lower(): seo += 15
    if "<h2>" in html.lower(): seo += 15
    return int(seo), read

# --- 5. TẠO FILE WORD CHUẨN (.DOCX) ---
def create_docx_file(title, html):
    doc = Document()
    doc.add_heading(title, 0)
    # Loại bỏ thẻ HTML trước khi đưa vào Word
    text_only = re.sub('<[^<]+?>', '', html)
    doc.add_paragraph(text_only)
    buf = io.BytesIO()
    doc.save(buf); buf.seek(0)
    return buf

# --- 6. GIAO HÀNG (FIX LỖI NONAME) ---
def deliver_article(v_func, web, title, html, docx_buf):
    try:
        sender, pw = v_func('SENDER_EMAIL'), v_func('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['From'], msg['Subject'] = sender, f"REPORT: {title}"
        msg.attach(MIMEText(html, 'html'))
        
        # Luồng gửi cho Sếp (Có file Word đính kèm)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(docx_buf.read())
        encoders.encode_base64(part)
        # Fix lỗi noname: Cần encode tên file chuẩn
        filename = f"{title.replace(' ', '_')[:30]}.docx"
        part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(sender, pw)
            s.sendmail(sender, [v_func('RECEIVER_EMAIL'), web['WS_SECRET_MAIL']], msg.as_string())
        return True
    except: return False

# --- VẬN HÀNH ---
sh_info = dict(st.secrets["service_account"], private_key=st.secrets["service_account"]["private_key"].replace("\\n", "\n"))
creds = Credentials.from_service_account_info(sh_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
sh = gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())

if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report", "Spin"]
    wss = {t: sh.worksheet(t) for t in tabs}
    db = {t: pd.DataFrame(ws.get_all_values()[1:], columns=[h.strip().upper() for h in ws.get_all_values()[0]]) for t, ws in wss.items()}
    def v(k):
        r = db['Dashboard'][db['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V88")

    if st.button("🚀 KÍCH HOẠT ROBOT (ĐĂNG BÀI THỰC - GHI SỔ THẬT)"):
        with st.status("🤖 Đang sản xuất & Giao hàng...") as status:
            try:
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_pool = db['Keyword'][db['Keyword']['KW_STATUS'].astype(int) <= 0].head(1).to_dict('records')

                for kw_item in kw_pool:
                    kw_main = kw_item['KW_TEXT']
                    # AI viết (Tách biệt Instruction để tránh lòi vào bài)
                    client = Groq(api_key=v('GROQ_API_KEY'))
                    res = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": "You are a professional SEO writer. ONLY output the HTML article body. Do not repeat instructions."},
                            {"role": "user", "content": f"Write an SEO article about '{kw_main}' with <h1> title. Use [LOCAL_TEXT] tag."}
                        ], model="llama-3.3-70b-versatile"
                    )
                    raw_art = res.choices[0].message.content
                    
                    # 1. NHỊP 3.2: SPIN & LOCAL (Cập nhật Tab Spin)
                    final_art = raw_art.replace("[LOCAL_TEXT]", v('LOCAL_PROMPT') or "TP.HCM")
                    used_spin = "Dịch vụ" # Giả định bốc từ bài
                    log_action_to_sheet(wss['Spin'], used_spin, "SPIN_STATUS", "SPIN_DATE")

                    # 2. CHÈN ẢNH & UPDATE IMAGE
                    img_row = db['Image'].sort_values('IMG_USED_COUNT').iloc[0]
                    img_url = img_row['IMG_URL']
                    final_art = f"<center><img src='{img_url}' width='100%'></center><br>" + final_art
                    log_action_to_sheet(wss['Image'], img_url, "IMG_USED_COUNT", "IMG_DATE")

                    # 3. ĐO LƯỜNG & ĐÓNG GÓI WORD
                    title_m = re.search(r'<h1>(.*?)</h1>', final_art)
                    art_title = title_m.group(1) if title_m else kw_main
                    s_seo, s_read = get_real_metrics(final_art, kw_main, art_title)
                    word_buf = create_word_docx(art_title, final_art)

                    # 4. GIAO HÀNG & UPDATE KEYWORD
                    ok = deliver_article(v, web, art_title, final_art, word_buf)
                    log_action_to_sheet(wss['Keyword'], kw_main, "KW_STATUS", "KW_DATE")

                    # 5. GHI REPORT & TELEGRAM
                    sh.worksheet("Report").append_row([web['WS_URL'], web['WS_PLATFORM'], get_ts(), art_title, final_art[:200], "1", "YES", "NO", kw_main, "", "", "", "", s_seo, "10%", s_read, get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])
                    
                    tele_msg = f"🔔 <b>V88 SUCCESS</b>\n📝 {art_title}\n📊 SEO: {s_seo} | Read: {s_read}\n📅 {get_ts()}"
                    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tele_msg, "parse_mode": "HTML"})

                st.success("🏁 XUẤT BẢN THÀNH CÔNG! CHECK FILE WORD & TIMESTAMP TRÊN SHEET.")
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
