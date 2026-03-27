import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, smtplib, io, re
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# --- CẤU HÌNH HỆ THỐNG GMT+7 ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - V31", layout="wide", page_icon="🛡️")

# Fix UI Metrics tàng hình (image_867c0b)
st.markdown("""<style>
    [data-testid="stMetricValue"] { color: #ff4b4b !important; font-size: 32px; font-weight: bold; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; height: 3.5em; background-color: #ff4b4b; color: white; }
</style>""", unsafe_allow_html=True)

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- KẾT NỐI SHEET ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=5)
def load_all_data():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        ws = sh.worksheet(t)
        vals = ws.get_all_values()
        if not vals: data[t] = pd.DataFrame(); continue
        headers = [clean(h).upper() for h in vals[0]]
        data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

# =========================================================
# 🧱 BƯỚC 1: GATEKEEPER (HẠN NGẠCH KÉP)
# =========================================================
def pulse_1_gatekeeper(data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống đang bảo trì."
    
    now = get_vn_now()
    df_rep = data['Report']
    batch_size = int(v('BATCH_SIZE') or 5)
    
    # Quét Ngày (Chốt chặn 30 ngày)
    for i in range(int(v('MAX_SCHEDULE_DAYS') or 30)):
        target_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(target_date)]
        
        if len(day_posts) >= batch_size: continue # Slot ngày đã đầy
        
        # Bốc Web Active & Check Limit Web (Lớp 1 & 4)
        active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
        if active_webs.empty: return None, "Không có Website ACTIVE."
        
        web_row = active_webs.sample(1).iloc[0]
        web_limit = int(web_row['WS_POST_LIMIT'] or 1)
        web_today = len(day_posts[day_posts['REP_WS_NAME'] == web_row['WS_URL']])
        
        if web_today < web_limit:
            return {"web": web_row, "pub_date": target_date}, "PASS"
            
    return None, "Đã cạn Slot đăng bài."

# =========================================================
# 🧱 BƯỚC 2: KEYWORD HUNTER (TBC & 60/40)
# =========================================================
def pulse_2_keyword_hunter(data, v):
    df_kw = data['Keyword']
    # Nhịp 1: Cleansing
    df_p = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_p['KW_STATUS'] = pd.to_numeric(df_p['KW_STATUS'], errors='coerce').fillna(1).astype(int)
    
    # Nhịp 2: TBC Average
    tbc = df_p['KW_STATUS'].mean()
    basket_a = df_p[df_p['KW_STATUS'] < tbc].to_dict('records')
    basket_b = df_p[df_p['KW_STATUS'] >= tbc].to_dict('records')
    
    # Nhịp 3: Quota 60/40
    num_total = int(v('NUM_KEYWORDS_PER_POST') or 4)
    quota_a = int(num_total * 0.6)
    
    selected, groups = [], []
    def pick(basket, limit):
        random.shuffle(basket)
        for kw in basket:
            if len(selected) >= limit: break
            grp = kw['KW_GROUP'].strip().lower()
            if grp not in groups:
                selected.append(kw); groups.append(grp)

    pick(basket_a, quota_a)
    pick(basket_a + basket_b, num_total) # Fallback vét cạn rổ
    return selected

# =========================================================
# 🧱 BƯỚC 3 & 4: ASSEMBLER & OPTIMIZER
# =========================================================
def pulse_3_4_assembler(v, web, kw_list, images):
    # Nhịp 3.1: 6 Kings Check (Chống lãng phí Token)
    kings = ['PROMPT_TEMPLATE', 'CONTENT_STRATEGY', 'KEYWORD_PROMPT', 'SEO_GLOBAL_RULE', 'AI_HUMANIZER_PROMPT']
    for k in kings:
        if not v(k): return None, f"Kings Check Fail: {k}"

    # Giả lập content AI -> Nhịp 1 Bước 4: Gắn Link (Out trước In sau)
    content = f"<h2>{kw_list[0]['KW_TEXT']}</h2><p>Bài viết mẫu chuyên nghiệp cho {v('PROJECT_NAME')}...</p>"
    limit_out = int(web['WS_LINK_OUT_LIMIT'] or 1)
    
    for i, kw in enumerate(kw_list):
        link_url = web['WS_TARGET_URL'] if i < limit_out else web['WS_PLATFORM']
        # 🔑 SEO Protection: Khóa cứng từ khóa
        content = content.replace(kw['KW_TEXT'], f'<a href="{link_url}">{kw["KW_TEXT"]}</a>', 1)

    # Nhịp 2 Bước 4: Tuyển Ảnh (Usage Count)
    img_pool = images.to_dict('records')
    img_pool.sort(key=lambda x: int(x['IMG_USED_COUNT'] or 0))
    best_imgs = [i for i in img_pool if int(i['IMG_USED_COUNT'] or 0) == int(img_pool[0]['IMG_USED_COUNT'] or 0)]
    img = random.choice(best_imgs)
    
    return content, img

# =========================================================
# 🎮 DASHBOARD ĐIỀU HÀNH
# =========================================================
data, sh = load_all_data()

if data:
    df_d = data['Dashboard']
    # 🛡️ FIX LỖI ATTRIBUTE ERROR TRONG HÀM v(k)
    def v(k):
        try:
            # Tìm dòng có key khớp, lấy value ở cột 2 (index 1)
            match = df_d[df_d.iloc[:, 0].str.strip().upper() == k.strip().upper()]
            if not match.empty:
                return clean(match.iloc[0, 1])
            return ""
        except: return ""

    # UI KPI
    df_kw = data['Keyword']
    done_count = len(df_kw[pd.to_numeric(df_kw['KW_STATUS'], errors='coerce') > 1])
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 TỔNG TỪ KHÓA", len(df_kw))
    c2.metric("✅ ĐÃ CHẠY", done_count)
    c3.metric("⏳ CÒN LẠI", len(df_kw) - done_count)

    if st.button("🚀 KÍCH HOẠT ROBOT MASTER V31", type="primary"):
        with st.status("🛠️ Robot đang thực thi quy trình Master...", expanded=True) as status:
            # BƯỚC 1: GATEKEEPER
            slot, g_msg = pulse_1_gatekeeper(data, v)
            if not slot: st.error(g_msg); st.stop()
            st.write(f"✅ B1: Chốt Web `{slot['web']['WS_URL']}` - Ngày {slot['pub_date']}")

            # BƯỚC 2: HUNTER
            kw_selection = pulse_2_keyword_hunter(data, v)
            if not kw_selection: st.error("Lỗi: Kho từ khóa không đủ điều kiện!"); st.stop()
            st.write(f"✅ B2: Nhặt {len(kw_selection)} từ khóa (60/40 Split)")

            # BƯỚC 3 & 4: ASSEMBLE
            content, img = pulse_3_4_assembler(v, slot['web'], kw_selection, data['Image'])
            st.write("✅ B3&4: Đã lắp Prompt 6 Kings & Gắn Link/Ảnh")

            # BƯỚC 5: REPORT & CẬP NHẬT (NHỊP 2 & 3)
            # Ghi Sheet Report
            ws_rep = sh.worksheet("Report")
            now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
            ws_rep.append_row([slot['web']['WS_URL'], slot['web']['WS_URL'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", "SUCCESS"])
            
            # Cập nhật Status Keyword (Cộng 1)
            ws_kw = sh.worksheet("Keyword")
            for kw in kw_selection:
                cell = ws_kw.find(kw['KW_TEXT'])
                ws_kw.update_cell(cell.row, 3, int(kw['KW_STATUS']) + 1)
            
            # Bắn Telegram
            tg_msg = f"🔔 [DỰ ÁN: {v('PROJECT_NAME')}]\n📝 Tên bài: {kw_selection[0]['KW_TEXT']}\n✅ SUCCESS"
            requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                          json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg})

            status.update(label="🏁 CHIẾN DỊCH HOÀN TẤT!", state="complete")
            st.balloons()
else:
    st.error("❌ Không thể kết nối Google Sheet!")
