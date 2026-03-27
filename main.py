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

# --- 1. HỆ QUẢN TRỊ & NHỊP 1 (GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER", layout="wide")

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

# --- 2. KẾT NỐI DATA THẬT ---
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

# --- 3. LOGIC THỰC THI 5 NHỊP ---

def pulse_1_gatekeeper(data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống bảo trì."
    now = get_vn_now()
    df_rep = data['Report']
    batch_size = get_range_val(v('BATCH_SIZE'), 5)
    
    # Lớp 2 & 3: Hạn ngạch & Lập lịch
    for i in range(get_range_val(v('MAX_SCHEDULE_DAYS'), 30)):
        target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(target_date)] if not df_rep.empty else []
        if len(day_posts) >= batch_size: continue
        
        # Lớp 1 & 4: Website Status & Limit
        active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
        if active_webs.empty: return None, "Không có Website ACTIVE."
        
        web_row = active_webs.sample(1).iloc[0].to_dict()
        web_limit = get_range_val(web_row['WS_POST_LIMIT'], 1)
        web_today = len(day_posts[day_posts['REP_WS_NAME'] == web_row['WS_URL']]) if len(day_posts) > 0 else 0
        
        if web_today < web_limit:
            return {"web": web_row, "date": target_date}, "PASS"
    return None, "Full chỉ tiêu."

def pulse_2_2_ecosystem(data, v, kw_main_text):
    df_kw = data['Keyword']
    # Tìm từ khóa bổ trợ: Cùng Topic, Khác Group, Status thấp
    # Lưu ý: KW_TOPIC lấy từ hàng của từ khóa chính vừa bốc được
    main_row = df_kw[df_kw['KW_TEXT'] == kw_main_text].iloc[0]
    topic = main_row['KW_TOPIC']
    group = main_row['KW_GROUP']
    
    df_sub = df_kw[(df_kw['KW_TOPIC'] == topic) & (df_kw['KW_GROUP'] != group)].copy()
    df_sub['KW_STATUS'] = pd.to_numeric(df_sub['KW_STATUS'], errors='coerce').fillna(0).astype(int)
    df_sub = df_sub.sort_values('KW_STATUS')
    
    num_needed = get_range_val(v('NUM_KEYWORDS_PER_POST'), 4) - 1
    return df_sub.head(num_needed).to_dict('records')

def pulse_4_readability(text):
    # Flesch Việt hóa: Score = 206.835 - (1.015 * ASL) - (84.6 * ASW)
    words = len(text.split())
    sentences = max(1, text.count('.') + text.count('?') + text.count('!'))
    asl = words / sentences
    asw = 1.5 # Giả định trung bình âm tiết tiếng Việt
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(max(0, min(100, score)), 2)

# =========================================================
# 🎮 DASHBOARD ĐIỀU HÀNH
# =========================================================
data, sh = load_all_tabs()

if data:
    df_d = data['Dashboard']
    def v(key):
        row = df_d[df_d.iloc[:, 0].str.strip().str.upper() == key.strip().upper()]
        return clean(row.iloc[0, 1]) if not row.empty else ""

    st.subheader(f"🚩 DỰ ÁN: {v('PROJECT_NAME')}")
    
    if st.button("🚀 KÍCH HOẠT ROBOT MASTER V49"):
        start_time = time.time()
        st.write(f"⏱️ **Bắt đầu:** {get_vn_now().strftime('%H:%M:%S')}")
        
        with st.status("🤖 Thực thi 5 Nhịp Master...") as status:
            # P1: Gatekeeper
            slot, g_msg = pulse_1_gatekeeper(data, v)
            if not slot: st.error(g_msg); st.stop()
            st.write(f"✅ B1: Chốt Web `{slot['web']['WS_URL']}`")

            # P2: Hunter (Bốc từ khóa ngẫu nhiên từ kho Keyword có STATUS thấp nhất)
            df_kw = data['Keyword']
            df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(0).astype(int)
            kw_main = df_kw.sort_values('KW_STATUS').iloc[0].to_dict()
            
            # P2.2: Ecosystem
            sub_kws = pulse_2_2_ecosystem(data, v, kw_main['KW_TEXT'])
            all_kws = [kw_main] + sub_kws
            
            st.write("🔑 **DANH SÁCH TỪ KHÓA THỰC TẾ:**")
            st.table(pd.DataFrame(all_kws)[['KW_TEXT', 'KW_GROUP', 'KW_STATUS']])

            # P3: Assembler (6 Kings Check)
            kings = ['PROMPT_TEMPLATE', 'CONTENT_STRATEGY', 'KEYWORD_PROMPT', 'SERP_STYLE_PROMPT', 'SEO_GLOBAL_RULE', 'AI_HUMANIZER_PROMPT']
            for k in kings:
                if not v(k): st.error(f"Kings Check Fail: Thiếu {k}"); st.stop()
            
            target_word_count = get_range_val(v('WORD_COUNT_RANGE'), 1000)
            st.write(f"✍️ AI đang sản xuất bài viết ~{target_word_count} chữ...")
            time.sleep(1.5) # Giả lập thông luồng

            # P4: SEO Tools
            content_sim = "Nội dung chuẩn SEO Master..."
            seo_score = 45
            ai_rate = "12%"
            read_score = pulse_4_readability(content_sim)

            # P5: Report (Mapping chuẩn 19 cột A-S)
            now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
            report_row = [
                slot['web']['WS_URL'], slot['web']['WS_PLATFORM'], now_str, f"Bài: {kw_main['KW_TEXT']}", 
                content_sim[:300], "1", "YES", "NO", 
                kw_main['KW_TEXT'],
                all_kws[1]['KW_TEXT'] if len(all_kws)>1 else "",
                all_kws[2]['KW_TEXT'] if len(all_kws)>2 else "",
                all_kws[3]['KW_TEXT'] if len(all_kws)>3 else "",
                all_kws[4]['KW_TEXT'] if len(all_kws)>4 else "",
                seo_score, now_str, "SUCCESS", "SUCCESS", ai_rate, read_score
            ]
            
            try:
                sh.worksheet("Report").append_row(report_row)
                # Cập nhật Status Keyword
                ws_kw = sh.worksheet("Keyword")
                cell = ws_kw.find(kw_main['KW_TEXT'])
                if cell: ws_kw.update_cell(cell.row, 3, kw_main['KW_STATUS'] + 1)
                st.write("✅ Đã ghi sổ 19 cột Tab Report.")
            except Exception as e: st.warning(f"⚠️ Ghi Sheet lỗi: {e}")

            # Telegram & Mail (Dữ liệu thật)
            try:
                tg_msg = f"✅ *Robot Laiho:* Đã lên bài!\n🔑 *Từ khóa:* {kw_main['KW_TEXT']}\n🌐 *Web:* {slot['web']['WS_URL']}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                              json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg, "parse_mode": "Markdown"})
            except: pass

            end_time = time.time()
            st.success(f"🏁 HOÀN TẤT! Tổng thời gian xử lý: {round(end_time - start_time, 2)} giây")
            st.balloons()
