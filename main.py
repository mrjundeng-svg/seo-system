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

# --- 1. SETUP HỆ THỐNG (MÚI GIỜ GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - V38", layout="wide", page_icon="🛡️")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def safe_int(val, default=1):
    try:
        s = clean(str(val))
        return int(s) if s.isdigit() else default
    except: return default

# --- 2. KẾT NỐI DATA (AUTO-RECOVERY) ---
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
        try:
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame(); continue
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# =========================================================
# 🧱 BƯỚC 5: HỆ THỐNG BÁO CÁO (FIX LỖI BIẾN V_FUNC)
# =========================================================

def pulse_5_reporting(v_logic, slot, kw_list, content, scores):
    """v_logic chính là hàm v() được truyền vào để lấy config"""
    kw_main = kw_list[0]['KW_TEXT']
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")

    # 5.1 Ghi Sheet
    try:
        sh_live = get_sh()
        if sh_live:
            ws_rep = sh_live.worksheet("Report")
            rep_row = [slot['web']['WS_URL'], slot['web']['WS_URL'], now_str, f"Bài: {kw_main}"] + [""]*4
            rep_row += [k['KW_TEXT'] for k in kw_list[:5]] + [""]*(5-len(kw_list))
            rep_row += [scores['seo'], now_str, "URL", "SUCCESS", scores['ai'], scores['read']]
            ws_rep.append_row(rep_row)
            
            ws_kw = sh_live.worksheet("Keyword")
            for kw in kw_list:
                cell = ws_kw.find(kw['KW_TEXT'])
                if cell: ws_kw.update_cell(cell.row, 3, safe_int(kw['KW_STATUS']) + 1)
            st.success("📊 Đã cập nhật Google Sheet.")
    except: st.warning("⚠️ Lỗi ghi Sheet, đang thử báo cáo kênh khác...")

    # 5.2 Bắn Telegram
    try:
        token = v_logic('TELEGRAM_BOT_TOKEN')
        chat_id = v_logic('TELEGRAM_CHAT_ID')
        msg = f"🔔 *[LAIHO.VN] XUẤT BẢN*\n📝 *Bài:* {kw_main}\n📊 SEO: {scores['seo']} | AI: {scores['ai']}\n✅ SUCCESS"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        st.success("✅ Đã bắn Telegram.")
    except: st.error("❌ Lỗi gửi Telegram.")

    # 5.3 Gửi Gmail + Word
    try:
        sender = v_logic('SENDER_EMAIL')
        pw = v_logic('SENDER_PASSWORD')
        receiver = v_logic('RECEIVER_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = f"Laiho Robot <{sender}>"; msg['To'] = receiver
        msg['Subject'] = f"[HỆ THỐNG PBN] {kw_main} - 🚀 XONG"
        msg.attach(MIMEText(f"🚀 {kw_main}\n\n{content[:500]}...", 'html'))

        doc = Document(); doc.add_heading(kw_main, 0); doc.add_paragraph(content)
        word_io = io.BytesIO(); doc.save(word_io); word_io.seek(0)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(word_io.read()); encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="SEO_{kw_main}.docx"')
        msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, pw); s.sendmail(sender, receiver, msg.as_string())
        st.success("✅ Đã gửi Gmail.")
    except: st.error("❌ Lỗi gửi Gmail.")

# =========================================================
# 🎮 DASHBOARD THỰC THI (FIXED SCOPE)
# =========================================================
data, sh = load_master_data()

if data:
    df_d = data['Dashboard']
    def v(key): # Đồng nhất tên hàm là v
        try:
            row = df_d[df_d.iloc[:, 0].str.strip().upper() == key.strip().upper()]
            return clean(row.iloc[0, 1]) if not row.empty else ""
        except: return ""

    st.sidebar.title("🛡️ LAIHO MASTER")
    if st.button("🚀 CHẠY CHIẾN DỊCH V38", type="primary"):
        # [PULSE 1 -> 4 CHẠY Ở ĐÂY - GIẢ ĐỊNH THÀNH CÔNG]
        # Giả lập data cho Pulse 5:
        kw_demo = [{"KW_TEXT": "Saycar", "KW_STATUS": "0", "KW_GROUP": "1"}]
        web_demo = {"web": {"WS_URL": "laiho.vn", "WS_TARGET_URL": "https://laiho.vn"}}
        content_demo = "Nội dung bài viết mẫu..."
        scores_demo = {'seo': 48, 'ai': '12%', 'read': 70}

        with st.status("🛠️ Đang thực thi báo cáo 5 Bước...") as status:
            # GỌI PULSE 5 VỚI HÀM v ĐÃ ĐỊNH NGHĨA CHUẨN
            pulse_5_reporting(v, web_demo, kw_demo, content_demo, scores_demo)
            status.update(label="🏁 HOÀN TẤT!", state="complete")
            st.balloons()
