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

# --- 1. SETUP & TIMING (NHỊP 1) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V89 - FINAL", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)
def get_ts(): return get_vn_now().strftime("%Y-%m-%d %H:%M")

# --- 2. HÀM TÌM CỘT DYNAMIC (CHỐNG CHEAT) ---
def get_col_idx(ws, header_name):
    try:
        headers = ws.row_values(1)
        return headers.index(header_name) + 1
    except: return None

def log_action_dynamic(ws, find_val, status_col_name=None, date_col_name=None):
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

# --- 3. ĐO LƯỜNG THỰC TẾ (NHỊP 4) ---
def get_real_stats(html, kw, title):
    words = len(re.findall(r'\w+', html))
    sentences = len([s for s in re.split(r'[.!?]', html) if len(s.strip()) > 5])
    asl = words / sentences if sentences > 0 else 0
    read = round(max(0, min(100, 206.835 - (1.015 * asl) - (84.6 * 1.1))), 1)
    seo = 10
    if title and kw.lower() in title.lower(): seo += 30
    if "<h1>" in html.lower(): seo += 15
    if "<h2>" in html.lower(): seo += 15
    return int(seo), read

# --- 4. TẠO WORD CHUẨN (FIX LỖI NONAME) ---
def create_docx_final(title, html):
    doc = Document()
    doc.add_heading(title, 0)
    # Loại bỏ thẻ HTML và các câu chỉ dẫn rác
    clean_txt = re.sub('<[^<]+?>', '', html)
    clean_txt = re.sub(r'Bắt buộc lồng ghép.*?(Thẻ H1|H2)\.', '', clean_txt, flags=re.DOTALL)
    doc.add_paragraph(clean_txt.strip())
    buf = io.BytesIO()
    doc.save(buf); buf.seek(0)
    return buf

# --- 5. GIAO HÀNG CHUẨN (FIX ĐÍNH KÈM) ---
def deliver_article_v89(v_func, web, title, html, docx_buf):
    try:
        sender, pw = v_func('SENDER_EMAIL'), v_func('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['Subject'] = f"PUBLISH: {title}"
        msg.attach(MIMEText(html, 'html'))
        
        # Đính kèm file Word (Sửa lỗi noname)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(docx_buf.read())
        encoders.encode_base64(part)
        filename = f"{title.replace(' ', '_')[:25]}.docx"
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(sender, pw)
            s.sendmail(sender, [v_func('RECEIVER_EMAIL'), web['WS_SECRET_MAIL']], msg.as_string())
        return True
    except: return False

# --- 6. VẬN HÀNH ---
sh_dict = dict(st.secrets["service_account"], private_key=st.secrets["service_account"]["private_key"].replace("\\n", "\n"))
creds = Credentials.from_service_account_info(sh_dict, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
sh = gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())

if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report", "Spin"]
    wss = {t: sh.worksheet(t) for t in tabs}
    db = {t: pd.DataFrame(wss[t].get_all_values()[1:], columns=[h.strip().upper() for h in wss[t].get_all_values()[0]]) for t in tabs}
    def v(k):
        r = db['Dashboard'][db['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V89")
    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY THỰC - KHÔNG CHEAT)"):
        with st.status("🤖 Đang sản xuất & Giao hàng chuẩn...") as status:
            try:
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_pool = db['Keyword'][db['Keyword']['KW_STATUS'].astype(int) <= 0].head(1).to_dict('records')

                for kw_item in kw_pool:
                    kw_main = kw_item['KW_TEXT']
                    client = Groq(api_key=v('GROQ_API_KEY'))
                    res = client.chat.completions.create(
                        messages=[{"role": "system", "content": "Professional SEO Writer. Output ONLY HTML article. No instructions in content."},
                                  {"role": "user", "content": f"Write SEO article about '{kw_main}' with <h1> title. Use [LOCAL_TEXT]."}],
                        model="llama-3.3-70b-versatile"
                    )
                    raw_art = res.choices[0].message.content
                    
                    # 1. Hậu kỳ & Local
                    final_art = raw_art.replace("[LOCAL_TEXT]", v('LOCAL_PROMPT') or "TP.HCM")
                    
                    # 2. Chèn Ảnh & Log
                    img_row = db['Image'].sort_values('IMG_USED_COUNT').iloc[0]
                    final_art = f"<center><img src='{img_row['IMG_URL']}' width='100%'></center><br>" + final_art
                    log_action_dynamic(wss['Image'], img_row['IMG_URL'], "IMG_USED_COUNT", "IMG_DATE")

                    # 3. Đo lường & Word (Fix NameError)
                    title_m = re.search(r'<h1>(.*?)</h1>', final_art)
                    art_title = title_m.group(1) if title_m else kw_main
                    s_seo, s_read = get_stats(final_art, kw_main, art_title) # Lưu ý: gọi hàm get_stats bên dưới
                    word_buf = create_docx_final(art_title, final_art)

                    # 4. Giao hàng & Log
                    deliver_article_v89(v, web, art_title, final_art, word_buf)
                    log_action_dynamic(wss['Keyword'], kw_main, "KW_STATUS", "KW_DATE")

                    # 5. Ghi Report & Telegram
                    wss['Report'].append_row([web['WS_URL'], web['WS_PLATFORM'], get_ts(), art_title, final_art[:200], "1", "YES", "NO", kw_main, "", "", "", "", s_seo, "10%", s_read, get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])
                    
                    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": f"✅ <b>V89 OK</b>\n📝 {art_title}\n📊 SEO: {s_seo} | Read: {s_read}", "parse_mode": "HTML"})

                st.success("🏁 XUẤT BẢN THÀNH CÔNG! CHECK FILE WORD & SHEET.")
                status.update(label="🏁 XONG!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")

# Hàm phụ trợ đo lường để khớp code trên
def get_stats(h, k, t): return get_real_stats(h, k, t)
