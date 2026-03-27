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

# --- 1. SETUP HỆ THỐNG (GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V91 - FINAL JUSTICE", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)
def get_ts(): return get_vn_now().strftime("%Y-%m-%d %H:%M")

# --- 2. HÀM CẬP NHẬT SHEET DYNAMIC (CHỐNG CHEAT) ---
def get_col_map(ws):
    headers = ws.row_values(1)
    return {h.strip().upper(): i + 1 for i, h in enumerate(headers)}

def update_gsheet_dynamic(ws, search_val, updates):
    try:
        cell = ws.find(search_val)
        if not cell: return
        col_map = get_col_map(ws)
        for col_name, new_val in updates.items():
            idx = col_map.get(col_name.upper())
            if idx:
                if callable(new_val): # Nếu là hàm (như tăng biến đếm)
                    current = ws.cell(cell.row, idx).value or 0
                    ws.update_cell(cell.row, idx, new_val(current))
                else: # Nếu là giá trị tĩnh (như Date)
                    ws.update_cell(cell.row, idx, new_val)
    except: pass

# --- 3. ĐO LƯỜNG THỰC TẾ (NHỊP 4) ---
def calculate_real_metrics(html, kw, title):
    words = re.findall(r'\w+', html)
    sentences = [s for s in re.split(r'[.!?]', html) if len(s.strip()) > 5]
    asl = len(words) / len(sentences) if sentences else 0
    read = round(max(0, min(100, 206.835 - (1.015 * asl) - (84.6 * 1.1))), 1)
    seo = 10
    if title and kw.lower() in title.lower(): seo += 30
    if "<h1>" in html.lower(): seo += 15
    if "<h2>" in html.lower(): seo += 15
    return int(seo), read

# --- 4. HẬU KỲ: SPIN & BACKLINK (BƯỚC 4) ---
def apply_spin_and_links(content, kw_list, web_row, spin_df, sh):
    text = content
    # Nhịp 3.2: Spin Tầng 1 (Cập nhật Tab Spin)
    if not spin_df.empty:
        ws_spin = sh.worksheet("Spin")
        for _, row in spin_df.iterrows():
            orig = str(row['SPIN_ORIGINAL']).strip()
            if orig in text:
                variants = str(row['SPIN_VARIANTS']).split(',')
                text = text.replace(orig, random.choice(variants).strip(), 1)
                # Update ngay lập tức (Cột SPIN_STATUS và SPIN_DATE)
                update_gsheet_dynamic(ws_spin, orig, {"SPIN_STATUS": lambda x: int(x or 0) + 1, "SPIN_DATE": get_ts()})

    # Bước 4: Nhịp 1 - Gắn Link (100% Coverage)
    out_limit = int(web_row.get('WS_LINK_OUT_LIMIT', 1))
    for i, kw in enumerate(kw_list):
        href = web_row['WS_TARGET_URL'] if i < out_limit else web_row['WS_PLATFORM']
        pattern = re.compile(re.escape(kw['KW_TEXT']), re.IGNORECASE)
        match = pattern.search(text)
        if match:
            start, end = match.span()
            anchor = f"<a href='{href}' style='color:#007bff;font-weight:bold;'>{match.group()}</a>"
            text = text[:start] + anchor + text[end:]
    return text

# --- 5. VẬN HÀNH ---
sh_info = dict(st.secrets["service_account"], private_key=st.secrets["service_account"]["private_key"].replace("\\n", "\n"))
sh = gspread.authorize(Credentials.from_service_account_info(sh_info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())

if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report", "Spin"]
    wss = {t: sh.worksheet(t) for t in tabs}
    db = {t: pd.DataFrame(wss[t].get_all_values()[1:], columns=[h.strip().upper() for h in wss[t].get_all_values()[0]]) for t in tabs}
    def v(k):
        r = db['Dashboard'][db['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V91 (KỶ LUẬT THÉP)")

    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY THỰC TẾ)"):
        with st.status("🤖 Đang sản xuất & Giao hàng chuẩn...") as status:
            try:
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                batch_size = int(v('BATCH_SIZE') or 1)
                kw_pool = db['Keyword'][db['Keyword']['KW_STATUS'].astype(int) <= 0].head(batch_size).to_dict('records')

                for i, kw_item in enumerate(kw_pool):
                    kw_main = kw_item['KW_TEXT']
                    
                    # NHỊP 3: ASSEMBLER (LOCAL_PROMPT đưa vào làm chỉ thị AI)
                    prompt_total = (f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main)}\n"
                                    f"STRATEGY: {v('CONTENT_STRATEGY')}\n"
                                    f"LOCAL INSTRUCTION: {v('LOCAL_PROMPT')}\n"
                                    f"SEO RULE: {v('SEO_GLOBAL_RULE')}")
                    
                    client = Groq(api_key=v('GROQ_API_KEY'))
                    res = client.chat.completions.create(
                        messages=[{"role": "system", "content": "Professional SEO Writer. Output HTML body only. No instructions in text."},
                                  {"role": "user", "content": prompt_total}],
                        model="llama-3.3-70b-versatile"
                    )
                    raw_art = res.choices[0].message.content

                    # NHỊP 3.2 & BƯỚC 4: SPIN, LINK & ẢNH
                    processed_art = apply_spin_and_links(raw_art, [kw_item], web, db['Spin'], sh)
                    
                    # Chèn Ảnh & Update Image
                    img_row = db['Image'].sort_values('IMG_USED_COUNT').iloc[0]
                    img_url = img_row['IMG_URL']
                    final_art = f"<center><img src='{img_url}' width='100%'></center><br>" + processed_art
                    update_gsheet_dynamic(wss['Image'], img_url, {"IMG_USED_COUNT": lambda x: int(x or 0) + 1, "IMG_DATE": get_ts()})

                    # ĐO LƯỜNG & TẠO WORD
                    title_m = re.search(r'<h1>(.*?)</h1>', final_art)
                    art_title = title_m.group(1) if title_m else kw_main
                    s_seo, s_read = calculate_real_metrics(final_art, kw_main, art_title)
                    
                    # Tạo file Word xịn
                    doc = Document(); doc.add_heading(art_title, 0); doc.add_paragraph(re.sub('<[^<]+?>', '', final_art))
                    word_buf = io.BytesIO(); doc.save(word_buf); word_buf.seek(0)

                    # GIAO HÀNG & UPDATE KEYWORD
                    sender, pw = v('SENDER_EMAIL'), v('SENDER_PASSWORD')
                    msg = MIMEMultipart(); msg['Subject'] = f"PUBLISH: {art_title}"
                    msg.attach(MIMEText(final_art, 'html'))
                    
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(word_buf.read()); encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment', filename=f"{kw_main}.docx")
                    msg.attach(part)

                    with smtplib.SMTP('smtp.gmail.com', 587) as s:
                        s.starttls(); s.login(sender, pw)
                        s.sendmail(sender, [v('RECEIVER_EMAIL'), web['WS_SECRET_MAIL']], msg.as_string())
                    
                    # Update Keyword (STATUS & DATE)
                    update_gsheet_dynamic(wss['Keyword'], kw_main, {"KW_STATUS": lambda x: int(x or 0) + 1, "KW_DATE": get_ts()})

                    # Ghi Report & Telegram
                    wss['Report'].append_row([web['WS_URL'], web['WS_PLATFORM'], get_ts(), art_title, final_art[:200], "1", "YES", "NO", kw_main, "", "", "", "", s_seo, "10%", s_read, get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])
                    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": f"✅ <b>V91 OK</b>\n📝 {art_title}\n📊 SEO: {s_seo} | Read: {s_read}", "parse_mode": "HTML"})

                st.success("🏁 XUẤT BẢN THÀNH CÔNG! CHECK FILE WORD & TIMESTAMP TRÊN SHEET.")
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
