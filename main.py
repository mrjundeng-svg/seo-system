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

# --- 1. SETUP & TIMESTAMP ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V93 - ALL PROMPT", layout="wide")
def get_ts(): return datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M")

# --- 2. HÀM DÒ CỘT DYNAMIC (CHỐNG CHEAT) ---
def get_col_map(ws):
    headers = ws.row_values(1)
    return {h.strip().upper(): i + 1 for i, h in enumerate(headers)}

def update_gsheet_v93(ws, find_val, update_dict):
    try:
        cell = ws.find(find_val)
        if not cell: return
        m = get_col_map(ws)
        for col_name, val in update_dict.items():
            idx = m.get(col_name.upper())
            if idx:
                if callable(val):
                    curr = ws.cell(cell.row, idx).value or 0
                    ws.update_cell(cell.row, idx, int(curr) + 1)
                else: ws.update_cell(cell.row, idx, val)
    except: pass

# --- 3. BỘ MÁY ASSEMBLER (GOM TOÀN BỘ PROMPT) ---
def build_master_prompt(v, kw_main, kw_subs, word_count, serp_style=""):
    # Lớp 1: 6 Kings (Bắt buộc)
    template = v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main)
    template = template.replace('{{word_count}}', str(word_count))
    template = template.replace('{{secondary_keywords}}', ", ".join(kw_subs))
    
    # Thứ tự ghép chuỗi theo SIÊU ĐẶC TẢ
    full_p = f"{template}\n\n"
    full_p += f"STRATEGY: {v('CONTENT_STRATEGY')}\n"
    full_p += f"KEYWORD RULE: {v('KEYWORD_PROMPT')}\n"
    full_p += f"STYLE ANCHOR (SERP): {serp_style or v('SERP_STYLE_PROMPT')}\n"
    
    # Lớp 2: 2 Knights (Tùy chọn)
    if v('TABLE_PROMPT'): full_p += f"TABLE INSTRUCTION: {v('TABLE_PROMPT')}\n"
    if v('LOCAL_PROMPT'): full_p += f"LOCAL CONTEXT INSTRUCTION: {v('LOCAL_PROMPT')}\n"
    
    # Lớp 3: Kỷ luật tối thượng (Nằm cuối để ghi đè)
    full_p += f"\nSEO GLOBAL RULE: {v('SEO_GLOBAL_RULE')}\n"
    full_p += f"HUMANIZER FILTERS: {v('AI_HUMANIZER_PROMPT')}"
    
    return full_p

# --- 4. ĐO LƯỜNG & ĐÓNG GÓI ---
def get_metrics(html, kw, title):
    words = re.findall(r'\w+', html)
    sentences = [s for s in re.split(r'[.!?]', html) if len(s.strip()) > 5]
    asl = len(words) / len(sentences) if sentences else 0
    read = round(max(0, min(100, 206.835 - (1.015 * asl) - (84.6 * 1.1))), 1)
    seo = 15
    if title and kw.lower() in title.lower(): seo += 35
    if "<h1>" in html.lower(): seo += 10
    if "<h2>" in html.lower(): seo += 10
    return int(seo), read

def create_word_v93(title, html):
    doc = Document()
    doc.add_heading(title, 0)
    # Loại bỏ HTML tags để Word sạch
    doc.add_paragraph(re.sub('<[^<]+?>', '', html).strip())
    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf

# --- 5. VẬN HÀNH ---
sh_auth = dict(st.secrets["service_account"], private_key=st.secrets["service_account"]["private_key"].replace("\\n", "\n"))
sh = gspread.authorize(Credentials.from_service_account_info(sh_auth, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())

if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report", "Spin"]
    wss = {t: sh.worksheet(t) for t in tabs}
    db = {t: pd.DataFrame(ws.get_all_values()[1:], columns=[h.strip().upper() for h in ws.get_all_values()[0]]) for t, ws in wss.items()}
    def v(k):
        r = db['Dashboard'][db['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V93")

    if st.button("🚀 KÍCH HOẠT ROBOT (ASSEMBLER PROMPT)"):
        with st.status("🤖 Đang gom Prompt & Sản xuất nội dung...") as status:
            try:
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_pool = db['Keyword'][db['Keyword']['KW_STATUS'].astype(int) <= 0].head(1).to_dict('records')

                for kw_item in kw_pool:
                    kw_main = kw_item['KW_TEXT']
                    
                    # 1. GOM PROMPT TỔNG
                    master_p = build_master_prompt(v, kw_main, [], 1100)
                    
                    # 2. AI VIẾT
                    client = Groq(api_key=v('GROQ_API_KEY'))
                    res = client.chat.completions.create(
                        messages=[{"role": "system", "content": "Professional SEO Content Creator. Output HTML body only."},
                                  {"role": "user", "content": master_p}],
                        model="llama-3.3-70b-versatile"
                    )
                    article = res.choices[0].message.content

                    # 3. CHÈN ẢNH & LOG
                    img_row = db['Image'].sort_values('IMG_USED_COUNT').iloc[0]
                    final_art = f"<center><img src='{img_row['IMG_URL']}' width='100%'></center><br>" + article
                    update_gsheet_v93(wss['Image'], img_row['IMG_URL'], {"IMG_USED_COUNT": lambda x: int(x or 0) + 1, "IMG_DATE": get_ts()})

                    # 4. ĐO LƯỜNG & WORD
                    title_m = re.search(r'<h1>(.*?)</h1>', final_art)
                    art_title = title_m.group(1) if title_m else kw_main
                    s_seo, s_read = get_metrics(final_art, kw_main, art_title)
                    word_file = create_word_v93(art_title, final_art)

                    # 5. GIAO HÀNG & UPDATE KW
                    sender, pw = v('SENDER_EMAIL'), v('SENDER_PASSWORD')
                    msg = MIMEMultipart(); msg['Subject'] = f"PUBLISH: {art_title}"
                    msg.attach(MIMEText(final_art, 'html'))
                    
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(word_file.read()); encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=f"{kw_main}.docx")
                    msg.attach(part)

                    with smtplib.SMTP('smtp.gmail.com', 587) as s:
                        s.starttls(); s.login(sender, pw)
                        s.sendmail(sender, [v('RECEIVER_EMAIL'), web['WS_SECRET_MAIL']], msg.as_string())
                    
                    update_gsheet_v93(wss['Keyword'], kw_main, {"KW_STATUS": lambda x: int(x or 0) + 1, "KW_DATE": get_ts()})

                    # Ghi Report
                    wss['Report'].append_row([web['WS_URL'], web['WS_PLATFORM'], get_ts(), art_title, final_art[:200], "1", "YES", "NO", kw_main, "", "", "", "", s_seo, "10%", s_read, datetime.now(VN_TZ).strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])

                st.success("🏁 XONG! ĐÃ GOM PROMPT & CẬP NHẬT SHEET DYNAMIC.")
                status.update(label="🏁 HOÀN TÀT!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
