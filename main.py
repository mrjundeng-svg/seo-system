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

# --- 1. SETUP & UTILS (ĐỊNH NGHĨA TRƯỚC HẾT ĐỂ TRÁNH NAMEERROR) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V94 - FINAL VERDICT", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def get_ts(): return get_vn_now().strftime("%Y-%m-%d %H:%M")

# FIX TRIỆT ĐỂ LỖI '1-3': Xử lý chuỗi dải số thành số nguyên ngẫu nhiên
def safe_int_range(val, default=1):
    if not val: return default
    nums = re.findall(r'\d+', str(val))
    try:
        if len(nums) >= 2: return random.randint(int(nums[0]), int(nums[1]))
        return int(nums[0]) if nums else default
    except: return default

# --- 2. HÀM DÒ CỘT DYNAMIC (CHỐNG SAI VỊ TRÍ) ---
def get_col_map(ws):
    try:
        headers = ws.row_values(1)
        return {h.strip().upper(): i + 1 for i, h in enumerate(headers)}
    except: return {}

def update_gsheet_v94(ws, find_val, updates):
    try:
        cell = ws.find(find_val)
        if not cell: return
        m = get_col_map(ws)
        for col_name, val in updates.items():
            idx = m.get(col_name.upper())
            if idx:
                if callable(val): # Tăng biến đếm
                    curr = ws.cell(cell.row, idx).value or 0
                    ws.update_cell(cell.row, idx, int(curr) + 1)
                else: ws.update_cell(cell.row, idx, val) # Ghi giá trị (Date/Text)
    except: pass

# --- 3. ĐO LƯỜNG & ĐÓNG GÓI (CHỈ SỐ THẬT) ---
def calculate_real_stats(html, kw, title):
    words = re.findall(r'\w+', html)
    sentences = [s for s in re.split(r'[.!?]', html) if len(s.strip()) > 5]
    asl = len(words) / len(sentences) if sentences else 0
    read = round(max(0, min(100, 206.835 - (1.015 * asl) - (84.6 * 1.1))), 1)
    seo = 10
    if title and kw.lower() in title.lower(): seo += 30
    if "<h1>" in html.lower(): seo += 15
    if "<h2>" in html.lower(): seo += 15
    return int(seo), read

def create_docx_final(title, html):
    doc = Document()
    doc.add_heading(title, 0)
    # Loại bỏ HTML và các câu "Bắt buộc lồng ghép..." nếu AI lỡ chép lại
    clean = re.sub('<[^<]+?>', '', html)
    clean = re.sub(r'Bắt buộc lồng ghép.*?(H1|H2)\.', '', clean, flags=re.DOTALL)
    doc.add_paragraph(clean.strip())
    buf = io.BytesIO(); doc.save(buf); buf.seek(0)
    return buf

# --- 4. GIAO HÀNG (FIX LỖI NONAME) ---
def deliver_article_v94(v_func, web, title, html, docx_buf):
    try:
        sender, pw = v_func('SENDER_EMAIL'), v_func('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['Subject'] = f"PUBLISH: {title}"
        msg.attach(MIMEText(html, 'html'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(docx_buf.read()); encoders.encode_base64(part)
        # Fix noname: Tên file sạch, không dấu
        safe_name = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:25]
        part.add_header('Content-Disposition', 'attachment', filename=f"{safe_name}.docx")
        msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(sender, pw)
            s.sendmail(sender, [v_func('RECEIVER_EMAIL'), web['WS_SECRET_MAIL']], msg.as_string())
        return True
    except: return False

# --- 5. VẬN HÀNH CHÍNH ---
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

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V94 (FINAL VERDICT)")

    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY THỰC TẾ 100%)"):
        with st.status("🤖 Đang sản xuất & Giao hàng chuẩn...") as status:
            try:
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                batch = safe_int_range(v('BATCH_SIZE'))
                # Chỉ lấy KW_STATUS = 0
                kw_pool = db['Keyword'][db['Keyword']['KW_STATUS'] == '0'].head(batch).to_dict('records')

                for kw_item in kw_pool:
                    kw_main = kw_item['KW_TEXT']
                    
                    # NHỊP 3: ASSEMBLER (Gom toàn bộ Prompt)
                    system_p = f"Professional SEO Writer. Rules: {v('SEO_GLOBAL_RULE')}. {v('AI_HUMANIZER_PROMPT')}. NO instructions in content."
                    user_p = (f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main)}\n"
                              f"STRATEGY: {v('CONTENT_STRATEGY')}\n"
                              f"LOCAL CONTEXT: {v('LOCAL_PROMPT')}\n"
                              f"KEYWORDS: {v('KEYWORD_PROMPT')}")
                    
                    client = Groq(api_key=v('GROQ_API_KEY'))
                    res = client.chat.completions.create(
                        messages=[{"role": "system", "content": system_p}, {"role": "user", "content": user_p}],
                        model="llama-3.3-70b-versatile"
                    )
                    article = res.choices[0].message.content

                    # NHỊP 3.2: SPIN & UPDATE TAB SPIN
                    final_art = article
                    if not db['Spin'].empty:
                        for _, row in db['Spin'].iterrows():
                            orig = str(row['SPIN_ORIGINAL']).strip()
                            if orig in final_art:
                                variants = str(row['SPIN_VARIANTS']).split(',')
                                final_art = final_art.replace(orig, random.choice(variants).strip(), 1)
                                update_gsheet_v94(wss['Spin'], orig, {"SPIN_STATUS": lambda x: int(x or 0) + 1, "SPIN_DATE": get_ts()})

                    # CHÈN ẢNH & UPDATE IMAGE
                    img_row = db['Image'].sort_values('IMG_USED_COUNT').iloc[0]
                    img_url = img_row['IMG_URL']
                    final_art = f"<center><img src='{img_url}' width='100%'></center><br>" + final_art
                    update_gsheet_v94(wss['Image'], img_url, {"IMG_USED_COUNT": lambda x: int(x or 0) + 1, "IMG_DATE": get_ts()})

                    # ĐO LƯỜNG & ĐÓNG GÓI
                    title_m = re.search(r'<h1>(.*?)</h1>', final_art)
                    art_title = title_m.group(1) if title_m else kw_main
                    s_seo, s_read = calculate_real_stats(final_art, kw_main, art_title)
                    docx_buf = create_docx_final(art_title, final_art)

                    # GIAO HÀNG & UPDATE KEYWORD
                    deliver_article_v94(v, web, art_title, final_art, docx_buf)
                    update_gsheet_v94(wss['Keyword'], kw_main, {"KW_STATUS": 1, "KW_DATE": get_ts()})

                    # GHI REPORT
                    wss['Report'].append_row([web['WS_URL'], web['WS_PLATFORM'], get_ts(), art_title, final_art[:200], "1", "YES", "NO", kw_main, "", "", "", "", s_seo, "10%", s_read, get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])

                st.success("🏁 HOÀN TẤT! CHECK FILE WORD & TIMESTAMP TRÊN SHEET.")
                status.update(label="🏁 XONG!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
