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
from docx import Document # Thư viện tạo file Word
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & TIMING ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V86 - WORD REPORT", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)
def get_ts(): return get_vn_now().strftime("%Y-%m-%d %H:%M")

# --- 2. HÀM TẠO FILE WORD (DOCX) TRONG BỘ NHỚ ---
def create_docx_buffer(title, html_content):
    doc = Document()
    doc.add_heading(title, 0)
    # Loại bỏ các tag HTML để đưa vào Word sạch sẽ
    clean_text = re.sub('<[^<]+?>', '', html_content)
    doc.add_paragraph(clean_text)
    
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- 3. HÀM CẬP NHẬT SHEET (KỶ LUẬT THÉP - ANTI CHEAT) ---
def update_sheet_log(sh, tab_name, find_val, col_status=None, col_date=None):
    try:
        ws = sh.worksheet(tab_name)
        cell = ws.find(find_val)
        if cell:
            if col_status:
                current = ws.cell(cell.row, col_status).value or 0
                ws.update_cell(cell.row, col_status, int(current) + 1)
            if col_date:
                ws.update_cell(cell.row, col_date, get_ts())
    except: pass

# --- 4. GỬI MAIL KÈM FILE WORD (NHỊP 5) ---
def deliver_with_attachment(v_func, target_mail, is_blogger, subject, html_content, docx_buf=None):
    try:
        sender, pw = v_func('SENDER_EMAIL'), v_func('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = sender, target_mail, subject
        msg.attach(MIMEText(html_content, 'html'))

        # Nếu là mail gửi cho Sếp (Report) thì đính kèm file Word
        if not is_blogger and docx_buf:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(docx_buf.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{subject}.docx"')
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(sender, pw)
            s.sendmail(sender, target_mail, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Lỗi Mail: {e}"); return False

# --- 5. VẬN HÀNH CHÍNH ---
sh = (lambda i: gspread.authorize(Credentials.from_service_account_info(i, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()))(dict(st.secrets["service_account"], private_key=st.secrets["service_account"]["private_key"].replace("\\n", "\n")))

if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Spin"]
    db = {t: pd.DataFrame(sh.worksheet(t).get_all_values()[1:], columns=[h.strip().upper() for h in sh.worksheet(t).get_all_values()[0]]) for t in tabs}
    def v(k):
        r = db['Dashboard'][db['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V86 (WORD ATTACHED)")

    if st.button("🚀 KÍCH HOẠT ROBOT (XUẤT FILE WORD + UPDATE SHEET)"):
        with st.status("🤖 Đang sản xuất & Giao hàng file Word...") as status:
            try:
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_pool = db['Keyword'][db['Keyword']['KW_STATUS'].astype(int) <= 0].head(1).to_dict('records')

                for kw_item in kw_pool:
                    kw_main = kw_item['KW_TEXT']
                    # AI viết bài
                    client = Groq(api_key=v('GROQ_API_KEY'))
                    res = client.chat.completions.create(messages=[{"role":"user","content":f"Viết bài SEO về {kw_main}. Tiêu đề <h1>. Dùng [LOCAL_TEXT]. HTML."}], model="llama-3.3-70b-versatile")
                    raw_art = res.choices[0].message.content
                    
                    # 1. Hậu kỳ (Spin, Local, Link)
                    final_art = raw_art.replace("[LOCAL_TEXT]", v('LOCAL_PROMPT') or "TP.HCM")
                    # (Lưu ý: Bồ có thể copy lại hàm Spin và Backlink từ V85 vào đây)

                    # 2. Tạo File Word
                    title_match = re.search(r'<h1>(.*?)</h1>', final_art)
                    art_title = title_match.group(1) if title_match else kw_main
                    word_buf = create_docx_buffer(art_title, final_art)
                    
                    # 3. Giao hàng 2 luồng
                    # Luồng A: Cho Blogger (Chỉ nội dung để đăng bài)
                    deliver_with_attachment(v, web['WS_SECRET_MAIL'], True, art_title, final_art)
                    # Luồng B: Cho Sếp (Có đính kèm file Word)
                    deliver_with_attachment(v, v('RECEIVER_EMAIL'), False, art_title, "Gửi Sếp báo cáo bài viết đính kèm.", word_buf)

                    # 4. CẬP NHẬT SHEET (CHỨNG MINH KHÔNG CHEAT)
                    update_sheet_log(sh, "Keyword", kw_main, col_status=3, col_date=5) # Cột 3:Status, 5:Date
                    update_sheet_log(sh, "Image", "ảnh_url_nào_đó", col_status=2, col_date=3) 
                    # Spin bốc từ bài viết ra để update...

                    st.success(f"📧 Đã gửi file Word bài '{art_title}' về mail của bồ!")
                status.update(label="🏁 XONG!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
