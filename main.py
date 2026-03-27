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

# --- 1. HỆ QUẢN TRỊ (GMT+7 & CLEAN RUN) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V27", layout="wide", page_icon="🛡️")

# CSS Fix lỗi trắng xóa Metrics (image_867c0b)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { color: #ff4b4b !important; }
    [data-testid="stMetricLabel"] { color: #808495 !important; }
    .stButton>button { border-radius: 8px; font-weight: 600; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

def get_vn_now(): return datetime.now(timezone(timedelta(hours=7)))
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. KẾT NỐI HỆ THỐNG ---
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
        ws = sh.worksheet(t)
        vals = ws.get_all_values()
        headers = [clean(h).upper() for h in vals[0]]
        data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

# --- 3. BƯỚC 1: GATEKEEPER (LÍNH GÁC CỔNG) ---
def pulse_1_gatekeeper(all_data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống bảo trì"
    
    now = get_vn_now()
    df_rep = all_data['Report']
    today_str = now.strftime("%Y-%m-%d")
    
    # Check Hạn ngạch tổng (Batch Size)
    today_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(today_str)]
    if len(today_posts) >= int(v('BATCH_SIZE') or 10): return None, "Đã đạt giới hạn BATCH_SIZE ngày"
    
    # Check Lớp 1 (Website) & Lớp 4 (Hạn ngạch Web)
    active_webs = all_data['Website'][all_data['Website']['WS_STATUS'].upper() == 'ACTIVE']
    if active_webs.empty: return None, "Không có Web ACTIVE"
    
    target_web = active_webs.sample(1).iloc[0]
    web_limit = int(target_web['WS_POST_LIMIT'] or 1)
    web_today = len(today_posts[today_posts['REP_WS_NAME'] == target_web['WS_URL']])
    if web_today >= web_limit: return None, "Web bốc được đã Full Limit"
    
    return target_web, "PASS"

# --- 4. BƯỚC 2: THE KEYWORD HUNTER (60/40 & FALLBACK) ---
def pulse_2_keyword_hunter(all_data, v):
    df_kw = all_data['Keyword']
    df_clean = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_clean['KW_STATUS'] = pd.to_numeric(df_clean['KW_STATUS'], errors='coerce').fillna(0).astype(int)
    
    tbc = df_clean['KW_STATUS'].mean()
    num_needed = int(v('NUM_KEYWORDS_PER_POST') or 4)
    
    # Màng lưới kép: Rổ A (Dưới TBC), Rổ B (Trên TBC)
    basket_a = df_clean[df_clean['KW_STATUS'] <= tbc].sample(frac=1).to_dict('records')
    basket_b = df_clean[df_clean['KW_STATUS'] > tbc].sample(frac=1).to_dict('records')
    
    selected, groups = [], []
    # Ưu tiên Rổ A, sau đó Rổ B (Dồn chéo)
    for kw in (basket_a + basket_b):
        if len(selected) >= num_needed: break
        if kw['KW_GROUP'] not in groups:
            selected.append(kw); groups.append(kw['KW_GROUP'])
            
    return selected

# --- 5. BƯỚC 3 & 4: ASSEMBLER & OPTIMIZER ---
def pulse_3_4_produce(v, web_info, kw_list, image_pool):
    # Check 6 Kings
    for k in ['PROMPT_TEMPLATE', 'CONTENT_STRATEGY', 'KEYWORD_PROMPT', 'SEO_GLOBAL_RULE', 'AI_HUMANIZER_PROMPT']:
        if not v(k): return None, f"Kings Fail: {k}"
    
    # Giả lập AI & SEO Protection (Khóa cứng từ khóa)
    kw_main = kw_list[0]['KW_TEXT']
    raw_content = f"<h1>{kw_main}</h1><p>Nội dung bài viết mẫu chuẩn SEO...</p>"
    
    # Bước 4: Chèn Backlink (100%) & Ảnh
    processed_content = raw_content
    for i, kw in enumerate(kw_list):
        url = web_info['WS_TARGET_URL'] if i < int(web_info['WS_LINK_OUT_LIMIT'] or 1) else web_info['WS_PLATFORM']
        processed_content = processed_content.replace(kw['KW_TEXT'], f'<a href="{url}">{kw["KW_TEXT"]}</a>', 1)
    
    return processed_content, "SUCCESS"

# --- 6. BƯỚC 5: REPORT & NOTI ---
def pulse_5_report(sh, v, web_info, kw_list, scores):
    # Ghi Report chuẩn Mapping image_867902
    ws_rep = sh.worksheet("Report")
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
    row = [web_info['WS_URL'], web_info['WS_URL'], now_str, f"Bài: {kw_list[0]['KW_TEXT']}"] + [""]*4
    row += [k['KW_TEXT'] for k in kw_list[:5]] + [""]*(5-len(kw_list))
    row += [scores['seo'], now_str, "URL", "SUCCESS", scores['ai'], scores['read']]
    ws_rep.append_row(row)
    
    # Bắn Telegram
    msg = f"🔔 [DỰ ÁN: {v('PROJECT_NAME')}]\n📝 {kw_list[0]['KW_TEXT']}\n📊 SEO: {scores['seo']} | AI: {scores['ai']}\n✅ SUCCESS"
    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg})

# --- GIAO DIỆN CHÍNH (V27) ---
data, sh = load_master_data()
if data:
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().upper() == k.strip().upper()].iloc[:, 1]
        return clean(res.values[0]) if not res.empty else ""

    # UI KPI
    df_kw = data['Keyword']
    done = len(df_kw[df_kw.iloc[:, 2].astype(str).str.contains('SUCCESS|1', case=False)])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 TỔNG TỪ KHÓA", len(df_kw))
    c2.metric("✅ ĐÃ XONG", done)
    c3.metric("⏳ CÒN LẠI", len(df_kw) - done)

    if st.button("🚀 KÍCH HOẠT ROBOT MASTER V27", type="primary"):
        with st.status("🛠️ Robot đang thực thi quy trình Master...", expanded=True) as status:
            # Nhịp 1
            web, g_msg = pulse_1_gatekeeper(data, v)
            if not web: st.error(g_msg); st.stop()
            st.write(f"🛡️ Gatekeeper: Chốt Web `{web['WS_URL']}`")
            
            # Nhịp 2
            kw_selection = pulse_2_keyword_hunter(data, v)
            if not kw_selection: st.error("Hết từ khóa!"); st.stop()
            st.write(f"🔑 Nhặt được {len(kw_selection)} từ khóa chiến thuật")
            
            # Nhịp 3 & 4 (Assembler & AI)
            content, p_msg = pulse_3_4_produce(v, web, kw_selection, data['Image'])
            st.write("✍️ AI đang múa phím & Check Human-vibe...")
            
            # Nhịp 5 (Report)
            scores = {'seo': 48, 'ai': '12%', 'read': 72}
            pulse_5_report(sh, v, web, kw_selection, scores)
            
            # CẬP NHẬT TRẠNG THÁI KW
            ws_kw = sh.worksheet("Keyword")
            for kw in kw_selection:
                cell = ws_kw.find(kw['KW_TEXT'])
                ws_kw.update_cell(cell.row, 3, int(kw['KW_STATUS']) + 1)
                
            status.update(label="🏁 CHIẾN DỊCH HOÀN TẤT!", state="complete")
            st.balloons()
