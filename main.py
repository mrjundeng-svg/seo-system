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
st.set_page_config(page_title="LAIHO SEO OS - V39", layout="wide", page_icon="🛡️")

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
            ws = sh.worksheet(t); vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame(); continue
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# =========================================================
# 🧱 HỆ THỐNG BÁO CÁO ĐA KÊNH (PULSE 5)
# =========================================================
def pulse_5_reporting(v, slot, kw_list, content, scores):
    """Sử dụng biến v đồng nhất để lấy config từ Dashboard"""
    kw_main = kw_list[0]['KW_TEXT']
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")

    # 5.1 Ghi Sheet (Mapping Chuẩn)
    try:
        sh_live = get_sh()
        if sh_live:
            ws_rep = sh_live.worksheet("Report")
            rep_row = [v('PROJECT_NAME'), slot['web']['WS_URL'], now_str, f"Bài: {kw_main}"] + [""]*4
            rep_row += [k['KW_TEXT'] for k in kw_list[:5]] + [""]*(5-len(kw_list))
            rep_row += [scores['seo'], now_str, "URL", "SUCCESS", scores['ai'], scores['read']]
            ws_rep.append_row(rep_row)
            
            ws_kw = sh_live.worksheet("Keyword")
            for kw in kw_list:
                cell = ws_kw.find(kw['KW_TEXT'])
                if cell: ws_kw.update_cell(cell.row, 3, safe_int(kw['KW_STATUS']) + 1)
            st.success("📊 Sheet: OK")
    except: st.warning("⚠️ Sheet: Fail (Nhưng vẫn bắn Tele/Mail)")

    # 5.2 Telegram Noti
    try:
        token = v('TELEGRAM_BOT_TOKEN')
        chat_id = v('TELEGRAM_CHAT_ID')
        msg = f"🔔 *[LAIHO.VN] THÀNH CÔNG*\n📝 *Bài:* {kw_main}\n📊 SEO: {scores['seo']} | AI: {scores['ai']}\n📈 Tiến độ: {slot['done_today']}/{v('BATCH_SIZE')}"
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"}, timeout=10)
        st.success("✅ Telegram: OK")
    except: st.error("❌ Telegram: Fail")

    # 5.3 Gmail + Word đính kèm
    try:
        sender = v('SENDER_EMAIL')
        pw = v('SENDER_PASSWORD')
        receiver = v('RECEIVER_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = f"Laiho Robot <{sender}>"; msg['To'] = receiver
        msg['Subject'] = f"[HỆ THỐNG PBN] {kw_main} - 🚀 XUẤT BẢN THÀNH CÔNG"
        msg.attach(MIMEText(f"<h3>{kw_main}</h3><br>{content[:800]}...", 'html'))

        doc = Document(); doc.add_heading(kw_main, 0); doc.add_paragraph(content)
        word_io = io.BytesIO(); doc.save(word_io); word_io.seek(0)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(word_io.read()); encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="SEO_{kw_main}.docx"')
        msg.attach(part)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as s:
            s.login(sender, pw); s.sendmail(sender, receiver, msg.as_string())
        st.success("✅ Gmail: OK")
    except: st.error("❌ Gmail: Fail")

# =========================================================
# 🎮 DASHBOARD ĐIỀU HÀNH
# =========================================================
data, sh = load_master_data()

if data:
    df_d = data['Dashboard']
    def v(key): # Định nghĩa hàm v đồng nhất
        try:
            row = df_d[df_d.iloc[:, 0].str.strip().upper() == key.strip().upper()]
            return clean(row.iloc[0, 1]) if not row.empty else ""
        except: return ""

    st.sidebar.title("🛡️ LAIHO MASTER")
    if st.button("🚀 CHẠY CHIẾN DỊCH V39", type="primary"):
        # [PULSE 1 -> 4 THỰC THI THEO ĐẶC TẢ CỦA BỒ]
        # Giả định Robot đã hoàn thành các bước Gatekeeper, Hunter, Assemble...
        
        # Dữ liệu giả lập để test Pulse 5
        kw_test = [{"KW_TEXT": "Dịch vụ lái xe hộ", "KW_STATUS": "0"}]
        web_test = {"web": {"WS_URL": "laiho.vn"}, "done_today": 1}
        scores_test = {'seo': 48, 'ai': '12%', 'read': 70}
        content_test = "Nội dung chuẩn SEO đã qua Spin đa tầng..."

        with st.status("🛠️ Đang thực thi 5 Nhịp MASTER...") as status:
            pulse_5_reporting(v, web_test, kw_test, content_test, scores_test)
            status.update(label="🏁 HOÀN TẤT!", state="complete")
            st.balloons()
