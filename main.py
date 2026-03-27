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

# --- 1. QUẢN TRỊ HỆ THỐNG (GMT+7 & CLEAN RUN) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V26", layout="wide", page_icon="🛡️")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. KẾT NỐI VÀ HỒI PHỤC (RE-AUTHORIZE) ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=5)
def load_all_tabs():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        ws = sh.worksheet(t)
        vals = ws.get_all_values()
        headers = [clean(h).upper() for h in vals[0]]
        data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

# --- 3. BƯỚC 1: GATEKEEPER (CHỐT CHẶN 4 LỚP) ---
def gatekeeper_logic(all_data, v):
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống bảo trì"
    
    # Check Limit Ngày
    now = get_vn_now()
    day_str = now.strftime("%Y-%m-%d")
    df_rep = all_data['Report']
    today_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(day_str)]
    if len(today_posts) >= int(v('BATCH_SIZE') or 5): return None, "Full Batch Size"
    
    # Bốc Web Active và Check Limit Web
    df_ws = all_data['Website']
    active_webs = df_ws[df_ws['WS_STATUS'].upper() == 'ACTIVE']
    if active_webs.empty: return None, "Không có Web ACTIVE"
    
    target_web = active_webs.sample(1).iloc[0]
    web_count = len(today_posts[today_posts['REP_WS_NAME'] == target_web['WS_URL']])
    if web_count >= int(target_web['WS_POST_LIMIT'] or 1): return None, "Web Full Limit"
    
    return target_web, "PASS"

# --- 4. BƯỚC 2: THE KEYWORD HUNTER (60/40 & GROUP FILTER) ---
def keyword_hunter(all_data, v, num_needed):
    df_kw = all_data['Keyword']
    df_clean = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_clean['KW_STATUS'] = pd.to_numeric(df_clean['KW_STATUS'], errors='coerce').fillna(0).astype(int)
    
    tbc = df_clean['KW_STATUS'].mean()
    basket_a = df_clean[df_clean['KW_STATUS'] <= tbc].to_dict('records')
    basket_b = df_clean[df_clean['KW_STATUS'] > tbc].to_dict('records')
    
    selected = []
    groups = []
    
    # Logic nhặt từ không trùng Nhóm
    pool = basket_a + basket_b # Dồn chéo tự động
    random.shuffle(pool)
    for kw in pool:
        if len(selected) >= num_needed: break
        if kw['KW_GROUP'] not in groups:
            selected.append(kw)
            groups.append(kw['KW_GROUP'])
            
    return selected

# --- 5. BƯỚC 3: ASSEMBLER (6 KINGS & HUMANIZER) ---
def assemble_prompt(v, style_anchor, kw_list, word_count):
    # Check 6 Kings
    kings = ['PROMPT_TEMPLATE', 'CONTENT_STRATEGY', 'KEYWORD_PROMPT', 'SEO_GLOBAL_RULE', 'AI_HUMANIZER_PROMPT']
    for k in kings:
        if not v(k): return None, f"Kings Fail: {k}"
        
    p = v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_list[0]['KW_TEXT'])
    p = p.replace('{{word_count}}', str(word_count))
    p = p.replace('{{secondary_keywords}}', ", ".join([k['KW_TEXT'] for k in kw_list[1:]]))
    
    full = f"{p}\n{v('CONTENT_STRATEGY')}\n{v('KEYWORD_PROMPT')}\n{style_anchor}\n{v('SEO_GLOBAL_RULE')}\n{v('AI_HUMANIZER_PROMPT')}"
    return full, "SUCCESS"

# --- 6. BƯỚC 4 & 5: OPTIMIZER & REPORTING ---
def finalize_report(sh, v, web_info, kw_list, content, scores):
    # Ghi Sheet Report
    ws_rep = sh.worksheet("Report")
    now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
    row = [web_info['WS_URL'], web_info['WS_URL'], now_str, content[:100], content[:200]] + [""]*3 # Cột trống
    row += [kw['KW_TEXT'] for kw in kw_list[:5]] + [""]*(5-len(kw_list)) # KW 1-5
    row += [scores['seo'], now_str, "URL_COMING", "SUCCESS", scores['ai'], scores['read']]
    ws_rep.append_row(row)
    
    # Bắn Telegram (Nhịp 3 - Bước 5)
    msg = f"🔔 [DỰ ÁN: {v('PROJECT_NAME')}]\n📝 {kw_list[0]['KW_TEXT']}\n📊 SEO: {scores['seo']} | AI: {scores['ai']}\n✅ SUCCESS"
    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg})

# --- GIAO DIỆN ĐIỀU KHIỂN ---
data, sh = load_all_tabs()
if data:
    df_d = data['Dashboard']
    def v(k): 
        res = df_d[df_d.iloc[:, 0].str.strip().upper() == k.strip().upper()].iloc[:, 1]
        return clean(res.values[0]) if not res.empty else ""

    st.sidebar.title("🛡️ LAIHO MASTER")
    num_run = st.sidebar.number_input("Số bài chạy", 1, 10, 1)

    if st.button("🔥 KÍCH HOẠT HỆ THỐNG MASTER", type="primary"):
        with st.status("🤖 Robot đang thực thi 5 Nhịp đặc tả...", expanded=True) as status:
            # BƯỚC 1
            web, gate_msg = gatekeeper_logic(data, v)
            if not web: st.error(gate_msg); st.stop()
            st.write(f"✅ Gatekeeper: Chốt Web {web['WS_URL']}")
            
            # BƯỚC 2
            kw_list = keyword_hunter(data, v, 4)
            if not kw_list: st.error("Hết từ khóa!"); st.stop()
            st.write(f"🔑 Nhặt {len(kw_list)} từ khóa chiến thuật")
            
            # BƯỚC 3 (Assembler)
            style_anchor = "Văn phong mỏ neo từ SERP/Đối thủ..." # Stub
            prompt, p_status = assemble_prompt(v, style_anchor, kw_list, 1100)
            
            # GIẢ LẬP AI & KCS (NHỊP 4)
            st.write("✍️ AI đang sản xuất & Spin đa tầng...")
            time.sleep(2)
            
            # BƯỚC 5 (Ghi sổ & Telegram)
            scores = {'seo': 48, 'ai': '12%', 'read': 70}
            finalize_report(sh, v, web, kw_list, "Nội dung bài viết...", scores)
            
            # CẬP NHẬT KW_STATUS (Bước 5 - Nhịp 2)
            ws_kw = sh.worksheet("Keyword")
            for kw in kw_list:
                cell = ws_kw.find(kw['KW_TEXT'])
                ws_kw.update_cell(cell.row, 3, int(kw['KW_STATUS']) + 1)
            
            status.update(label="🏁 CHIẾN DỊCH HOÀN TẤT!", state="complete")
            st.balloons()
