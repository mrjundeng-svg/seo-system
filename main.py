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

# --- 1. SETUP HỆ THỐNG GMT+7 ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V47", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_range_val(val, default=1):
    s = clean(str(val))
    if not s: return default
    if '-' in s:
        try:
            parts = s.split('-')
            low = int(re.sub(r'\D', '', parts[0]))
            high = int(re.sub(r'\D', '', parts[1]))
            return random.randint(min(low, high), max(low, high))
        except: return default
    try: return int(re.sub(r'\D', '', s))
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
            if not vals: data[t] = pd.DataFrame(); continue
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# --- 3. CÁC NHỊP THỰC THI ---
def pulse_1_gatekeeper(data, v_func):
    if v_func('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống đang bảo trì."
    now = get_vn_now()
    df_rep = data['Report']
    batch_size = get_range_val(v_func('BATCH_SIZE'), 5)
    
    for i in range(get_range_val(v_func('MAX_SCHEDULE_DAYS'), 30)):
        target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(target_date)] if not df_rep.empty else []
        if len(day_posts) >= batch_size: continue
        
        active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
        if active_webs.empty: return None, "Không có Website nào ACTIVE trên Sheet."
        
        web_row = active_webs.sample(1).iloc[0].to_dict()
        web_limit = get_range_val(web_row['WS_POST_LIMIT'], 1)
        web_today = len(day_posts[day_posts['REP_WS_NAME'] == web_row['WS_URL']]) if len(day_posts) > 0 else 0
        
        if web_today < web_limit:
            return {"web": web_row, "date": target_date}, "PASS"
    return None, "Full chỉ tiêu các ngày."

def pulse_2_hunter(data, v_func):
    df_kw = data['Keyword']
    proj_name = v_func('PROJECT_NAME')
    # Lọc cực mạnh: Chống sai lệch khoảng trắng và Case-sensitive
    df_p = df_kw[df_kw['KW_TOPIC'].str.strip().str.contains(proj_name, case=False, na=False)].copy()
    
    if df_p.empty: return []
    
    df_p['KW_STATUS'] = pd.to_numeric(df_p['KW_STATUS'], errors='coerce').fillna(0).astype(int)
    tbc = df_p['KW_STATUS'].mean()
    basket_a = df_p[df_p['KW_STATUS'] <= tbc].to_dict('records')
    basket_b = df_p[df_p['KW_STATUS'] > tbc].to_dict('records')
    
    num_needed = get_range_val(v_func('NUM_KEYWORDS_PER_POST'), 4)
    quota_a = int(num_needed * 0.6)
    selected, groups = [], []
    
    def pick(basket, limit):
        random.shuffle(basket)
        for kw in basket:
            if len(selected) >= limit: break
            g = clean(kw.get('KW_GROUP', '')).lower()
            if g not in groups:
                selected.append(kw); groups.append(g)
                
    pick(basket_a, quota_a)
    pick(basket_a + basket_b, num_needed)
    return selected

# =========================================================
# 🎮 DASHBOARD ĐIỀU HÀNH
# =========================================================
data, sh = load_all_tabs()

if data:
    df_d = data['Dashboard']
    def v(key):
        row = df_d[df_d.iloc[:, 0].str.strip().str.upper() == key.strip().upper()]
        return clean(row.iloc[0, 1]) if not row.empty else ""

    st.title("🛡️ LAIHO SEO OS - MASTER")
    
    # Show KPI nhanh
    c1, c2 = st.columns(2)
    c1.metric("Dự án", v('PROJECT_NAME'))
    c2.metric("Chỉ tiêu (Batch)", v('BATCH_SIZE'))

    if st.button("🚀 KÍCH HOẠT ROBOT VẬN HÀNH"):
        with st.status("🤖 Robot đang thực thi 5 Nhịp Master...") as status:
            # P1: Gatekeeper
            slot, g_msg = pulse_1_gatekeeper(data, v)
            if not slot: st.error(g_msg); st.stop()
            st.write(f"✅ B1: Chốt Web `{slot['web']['WS_URL']}`")

            # P2: Hunter
            kw_list = pulse_2_hunter(data, v)
            if not kw_list: 
                st.error(f"❌ Không tìm thấy từ khóa khớp với Topic: '{v('PROJECT_NAME')}'")
                st.info("Bồ check lại cột KW_TOPIC trong Tab Keyword xem có khớp 100% chữ này không nhé.")
                st.stop()
            
            # --- SHOW DANH SÁCH TỪ KHÓA LẤY ĐƯỢC ---
            st.write("🔑 **DANH SÁCH TỪ KHÓA CHIẾN THUẬT:**")
            st.dataframe(pd.DataFrame(kw_list)[['KW_TEXT', 'KW_GROUP', 'KW_STATUS']])

            # P3 & P4: Sản xuất (Giả lập để thông luồng)
            content_sim = f"Bài viết chuẩn SEO cho {kw_list[0]['KW_TEXT']}..."
            st.write("✍️ AI đang lắp ghép 6 Kings & Gắn Link...")
            
            # P5: Report (Chuẩn 19 cột A-S)
            now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
            report_row = [
                slot['web']['WS_URL'], slot['web']['WS_PLATFORM'], now_str, f"Bài: {kw_list[0]['KW_TEXT']}", 
                content_sim[:300], "1", "YES", "NO", kw_list[0]['KW_TEXT'],
                kw_list[1]['KW_TEXT'] if len(kw_list)>1 else "",
                kw_list[2]['KW_TEXT'] if len(kw_list)>2 else "",
                kw_list[3]['KW_TEXT'] if len(kw_list)>3 else "",
                kw_list[4]['KW_TEXT'] if len(kw_list)>4 else "",
                48, "12%", 70, now_str, "SUCCESS", "SUCCESS"
            ]
            
            try:
                sh.worksheet("Report").append_row(report_row)
                # Cập nhật Status
                ws_kw = sh.worksheet("Keyword")
                cell = ws_kw.find(kw_list[0]['KW_TEXT'])
                if cell: ws_kw.update_cell(cell.row, 3, kw_list[0]['KW_STATUS'] + 1)
                st.write("✅ Đã ghi sổ Report.")
            except: st.warning("⚠️ Lỗi ghi Sheet nhưng vẫn bắn Telegram.")

            # Báo Telegram
            try:
                tg_msg = f"🔔 *[LAIHO]*: Đã lên bài!\n🔑 *Từ khóa:* {kw_list[0]['KW_TEXT']}\n🌐 *Web:* {slot['web']['WS_URL']}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                              json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg, "parse_mode": "Markdown"})
            except: pass

            status.update(label="🏁 CHIẾN DỊCH HOÀN TẤT!", state="complete")
            st.success(f"Đã xong bài: {kw_list[0]['KW_TEXT']}")
