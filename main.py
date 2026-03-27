import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, smtplib, io
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- 1. SETUP HỆ THỐNG (GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - V37", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. HÀM KẾT NỐI (ĐẢM BẢO KHÔNG THÀNH NONE) ---
def get_sh_immortal():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}")
        return None

# =========================================================
# 🧱 BƯỚC 5: HỆ THỐNG BÁO CÁO ĐA KÊNH (PULSE 5)
# =========================================================

def pulse_5_master_reporting(v_func, slot, kw_list, content, scores):
    """Đảm bảo báo cáo bắn ra kể cả khi Sheet lỗi"""
    kw_main = kw_list[0]['KW_TEXT']
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")

    # --- NHỊP 5.1: GHI SHEET (CÓ BẢO VỆ) ---
    st.write("⏳ Đang ghi sổ Google Sheet...")
    try:
        sh = get_sh_immortal()
        if sh:
            ws_rep = sh.worksheet("Report")
            # Mapping chuẩn image_867902
            rep_row = [slot['web']['WS_URL'], slot['web']['WS_URL'], now_str, f"Bài: {kw_main}"] + [""]*4
            rep_row += [k['KW_TEXT'] for k in kw_list[:5]] + [""]*(5-len(kw_list))
            rep_row += [scores['seo'], now_str, "URL", "SUCCESS", scores['ai'], scores['read']]
            ws_rep.append_row(rep_row)
            
            # Cập nhật Status Keyword
            ws_kw = sh.worksheet("Keyword")
            for kw in kw_list:
                cell = ws_kw.find(kw['KW_TEXT'])
                if cell: ws_kw.update_cell(cell.row, 3, int(kw['KW_STATUS']) + 1)
            st.success("✅ Đã lưu dữ liệu vào Google Sheet.")
    except Exception as e:
        st.warning(f"⚠️ Ghi Sheet thất bại nhưng vẫn tiếp tục báo cáo: {e}")

    # --- NHỊP 5.2: BẮN TELEGRAM (ĐỘC LẬP) ---
    st.write("📡 Đang bắn tin Telegram...")
    try:
        token = v_func('TELEGRAM_BOT_TOKEN')
        chat_id = v_func('TELEGRAM_CHAT_ID')
        tg_msg = f"🔔 *[LAIHO.VN] THÔNG BÁO XUẤT BẢN*\n\n📝 *Bài:* {kw_main}\n📊 *SEO:* {scores['seo']} | *AI:* {scores['ai']}\n✅ Trạng thái: SUCCESS"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": tg_msg, "parse_mode": "Markdown"}, timeout=10)
        st.success("✅ Đã báo cáo qua Telegram.")
    except:
        st.error("❌ Lỗi gửi Telegram.")

    # --- NHỊP 5.3: GỬI GMAIL + WORD (ĐỘC LẬP) ---
    st.write("📧 Đang soạn Gmail kèm file Word...")
    try:
        sender = v_func('SENDER_EMAIL')
        pw = v_func('SENDER_PASSWORD') # Viết liền như bồ nói
        receiver = v_func('RECEIVER_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = f"Laiho Robot <{sender}>"; msg['To'] = receiver
        msg['Subject'] = f"[HỆ THỐNG PBN] {kw_main} - 🚀 THÀNH CÔNG"
        
        html = f"<h3>🚀 {kw_main}</h3><p>Đã xuất bản thành công.</p><hr><i>{content[:500]}...</i>"
        msg.attach(MIMEText(html, 'html'))

        doc = Document(); doc.add_heading(kw_main, 0); doc.add_paragraph(content)
        word_io = io.BytesIO(); doc.save(word_io); word_io.seek(0)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(word_io.read()); encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="SEO_{kw_main}.docx"')
        msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, pw); s.sendmail(sender, receiver, msg.as_string())
        st.success("✅ Đã gửi báo cáo Gmail.")
    except Exception as e:
        st.error(f"❌ Lỗi Gmail: {e}")

# =========================================================
# 🎮 DASHBOARD THỰC THI (KHI BẤM NÚT)
# =========================================================
# (Giả sử bồ đã load data thành công ở đầu app)

if st.button("🚀 KÍCH HOẠT ROBOT MASTER V37", type="primary"):
    # [BƯỚC 1 -> 4 CHẠY Ở ĐÂY]
    # ...
    
    # BƯỚC 5: THỰC THI BÁO CÁO (TÍCH HỢP TOÀN DIỆN)
    scores_demo = {'seo': 48, 'ai': '12%', 'read': 70}
    pulse_5_master_reporting(v_func, slot, kw_selection, content_ai, scores_demo)
    
    st.balloons()
