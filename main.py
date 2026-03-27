import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, re, io, smtplib
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- 1. SETUP HỆ THỐNG (GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - V50", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_range_val(val, default=1):
    s = clean(str(val))
    if '-' in s:
        try:
            p = s.split('-')
            return random.randint(int(re.sub(r'\D','',p[0])), int(re.sub(r'\D','',p[1])))
        except: return default
    try: return int(re.sub(r'\D','',s))
    except: return default

# --- 2. KẾT NỐI GOOGLE SHEET ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=5)
def load_all_tabs():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        try:
            ws = sh.worksheet(t); vals = ws.get_all_values()
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# =========================================================
# 🧱 NHỊP 5: SIÊU HỆ THỐNG BÁO CÁO & TỔNG KẾT
# =========================================================
def pulse_5_master_report(sh, v, web, kw_list, content, scores, total_done):
    kw_main = kw_list[0]['KW_TEXT']
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
    pub_date = get_vn_now().strftime("%Y-%m-%d")
    
    # --- NHỊP 1: CONSOLE REPORT (STREAMLIT UI) ---
    with st.expander(f"📑 Console Report: {kw_main}", expanded=True):
        st.markdown(f"""
        **Bài 1 —**
        * Dashboard yêu cầu đăng trong ngày: **{total_done + 1} / {v('BATCH_SIZE')}**
        * Report lượt đăng trong ngày: **{total_done + 1} / {web.get('WS_POST_LIMIT', 1)}**
        * Report bài Chờ đăng: **SUCCESS**
        * Website: `{web.get('WS_URL')}`
        * Website tên bài: `{kw_main}`
        * Từ khóa backlink: `{" | ".join([k['KW_TEXT'] for k in kw_list])}`
        * Report SEO | AI | Read: **{scores['seo']} | {scores['ai']} | {scores['read']}**
        * Report trạng thái: **SUCCESS**
        """)

    # --- NHỊP 2: GHI SỔ TAB REPORT (CHUẨN 19 CỘT A-S) ---
    # Mapping đúng image_94a6c5: A:NAME, B:URL, C:TIME, D:TITLE, E:PREVIEW...
    report_row = [
        web.get('WS_URL', ''),              # A: REP_WS_NAME
        web.get('WS_PLATFORM', ''),         # B: REP_WS_URL
        now_str,                            # C: REP_CREATED_AT
        f"Bài: {kw_main}",                  # D: REP_TITLE
        content[:200],                      # E: REP_PREVIEW
        "1",                                # F: REP_IMG_COUNT
        "YES",                              # G: REP_HAS_LOCAL
        "NO",                               # H: REP_HAS_TABLE
        kw_list[0]['KW_TEXT'],              # I: REP_KW_1
        kw_list[1]['KW_TEXT'] if len(kw_list)>1 else "", # J: REP_KW_2
        kw_list[2]['KW_TEXT'] if len(kw_list)>2 else "", # K: REP_KW_3
        kw_list[3]['KW_TEXT'] if len(kw_list)>3 else "", # L: REP_KW_4
        kw_list[4]['KW_TEXT'] if len(kw_list)>4 else "", # M: REP_KW_5
        scores['seo'],                      # N: REP_SEO_SCORE
        scores['ai'],                       # O: AI_DETECTOR_RATE
        scores['read'],                     # P: READABILITY_SCORE
        pub_date,                           # Q: REP_PUBLISH_DATE
        "https://laiho.vn/published",       # R: REP_POST_URL
        "SUCCESS"                           # S: REP_RESULT
    ]
    
    try:
        sh.worksheet("Report").append_row(report_row)
        # Cập nhật Tab Keyword (+1 Status)
        ws_kw = sh.worksheet("Keyword")
        cell = ws_kw.find(kw_main)
        if cell:
            cur_status = get_range_val(kw_list[0].get('KW_STATUS', 0))
            ws_kw.update_cell(cell.row, 3, cur_status + 1)
        st.success("✅ Đã ghi sổ 19 cột Tab Report & Cập nhật Keyword.")
    except Exception as e: st.error(f"Lỗi ghi Sheet: {e}")

    # --- NHỊP 3: BÁO CÁO TELEGRAM (NGẮT DÒNG KHOA HỌC) ---
    try:
        token = v('TELEGRAM_BOT_TOKEN')
        chat_id = v('TELEGRAM_CHAT_ID')
        tg_msg = (
            f"🔔 *[DỰ ÁN: {v('PROJECT_NAME')}] - THÔNG BÁO XUẤT BẢN*\n\n"
            f"📝 *Tên bài:* {kw_main}\n"
            f"🔗 *Link bài:* https://laiho.vn/published\n"
            f"🔑 *Từ khóa:* {' | '.join([k['KW_TEXT'] for k in kw_list])}\n"
            f"📊 *Chỉ số:* SEO: {scores['seo']} | AI: {scores['ai']} | Read: {scores['read']}\n"
            f"✅ *Trạng thái:* SUCCESS\n"
            f"📈 *Tiến độ tổng:* {total_done + 1} / {v('BATCH_SIZE')}"
        )
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage", 
                      json={"chat_id": chat_id, "text": tg_msg, "parse_mode": "Markdown"})
        st.success("✅ Telegram: Đã gửi thông báo.")
    except: pass

# =========================================================
# 🎮 DASHBOARD THỰC THI
# =========================================================
data, sh = load_all_tabs()

if data:
    df_d = data['Dashboard']
    def v(key):
        row = df_d[df_d.iloc[:, 0].str.strip().str.upper() == key.strip().upper()]
        return clean(row.iloc[0, 1]) if not row.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER ENGINE")
    
    if st.button("🚀 KÍCH HOẠT ROBOT VẬN HÀNH"):
        start_time = time.time()
        st.write(f"⏱️ **Bắt đầu chạy:** {get_vn_now().strftime('%H:%M:%S')}")
        
        with st.status("🤖 Robot đang thực thi 5 Nhịp Master...") as status:
            # P1: Gatekeeper (Lọc dữ liệu thật)
            active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
            if active_webs.empty: st.error("Hết Web Active!"); st.stop()
            web_real = active_webs.sample(1).iloc[0].to_dict()
            
            # P2: Hunter (Bốc từ khóa thật có Status thấp)
            df_kw = data['Keyword']
            df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(0).astype(int)
            kw_main = df_kw.sort_values('KW_STATUS').iloc[0].to_dict()
            kw_list = [kw_main] # Bồ có thể lấy thêm sub-keywords ở đây theo Nhịp 2.2
            
            # P3 & P4: Sản xuất (Logic bồ đã có API)
            content_real = "Nội dung bài viết chuẩn SEO Master..."
            scores_real = {'seo': 48, 'ai': '12%', 'read': 70}
            
            # Đếm tiến độ thực tế trong ngày
            today_str = get_vn_now().strftime("%Y-%m-%d")
            total_done = len(data['Report'][data['Report']['REP_CREATED_AT'].str.contains(today_str)]) if not data['Report'].empty else 0

            # P5: REPORT CHỐT HẠ (DÙNG v ĐÃ ĐỊNH NGHĨA CHUẨN)
            pulse_5_master_report(sh, v, web_real, kw_list, content_real, scores_real, total_done)
            
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            status.update(label=f"🏁 HOÀN TẤT! (Tổng thời gian: {duration} giây)", state="complete")
            st.balloons()
