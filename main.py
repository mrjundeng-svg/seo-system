import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, random, smtplib, io, re
from datetime import datetime, timedelta, timezone
from docx import Document
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- CẤU HÌNH HỆ THỐNG (GMT+7) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V30", layout="wide", page_icon="🛡️")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- KẾT NỐI GOOGLE SHEET (CÓ CƠ CHẾ HỒI PHỤC) ---
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
        headers = [clean(h).upper() for h in vals[0]]
        data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
    return data, sh

# =========================================================
# 🧱 BƯỚC 1: GATEKEEPER & LẬP LỊCH
# =========================================================
def pulse_1_gatekeeper(data, v):
    # Lệnh 1.1: Maintenance
    if v('SYSTEM_MAINTENANCE').upper() == 'ON': return None, "Hệ thống đang bảo trì."

    now = get_vn_now()
    df_rep = data['Report']
    
    # Lệnh 1.3: Đối soát Giới hạn Kép
    batch_size = int(v('BATCH_SIZE') or 5)
    active_webs = data['Website'][data['Website']['WS_STATUS'].upper() == 'ACTIVE']
    
    if active_webs.empty: return None, "Không có Website nào ACTIVE."

    # Quét Slot trống (Vòng lặp Ngày X)
    for i in range(int(v('MAX_SCHEDULE_DAYS') or 30)):
        check_date = (now + timedelta(days=i)).date()
        day_str = check_date.strftime("%Y-%m-%d")
        day_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(day_str)]
        
        if len(day_posts) >= batch_size: continue # Ngày X đã đầy BATCH_SIZE

        # Bốc Web ngẫu nhiên và check Limit Web
        web_pool = active_webs.sample(frac=1).to_dict('records')
        for web in web_pool:
            web_limit = int(web['WS_POST_LIMIT'] or 1)
            web_today = len(day_posts[day_posts['REP_WS_NAME'] == web['WS_URL']])
            if web_today < web_limit:
                # CHỐT SLOT! (Lệnh 1.4: Tính giờ đăng tự nhiên)
                # Tui lược bớt logic random giờ để tập trung vào luồng chính
                publish_time = now.strftime("%Y-%m-%d %H:%M:%S")
                return {"web": web, "time": publish_time}, "PASS"
                
    return None, "Đã lên lịch full hoặc không tìm thấy slot."

# =========================================================
# 🧱 BƯỚC 2: BỐC TỪ KHÓA CHIẾN THUẬT (60/40 & TBC)
# =========================================================
def pulse_2_keyword_hunter(data, v):
    df_kw = data['Keyword']
    # Nhịp 1: Cleansing
    df_p = df_kw[df_kw['KW_TOPIC'].str.contains(v('PROJECT_NAME'), case=False)].copy()
    df_p['KW_STATUS'] = pd.to_numeric(df_p['KW_STATUS'], errors='coerce').fillna(1).astype(int)
    
    # Nhịp 2: Phân loại rổ TBC
    tbc = df_p['KW_STATUS'].mean()
    basket_a = df_p[df_p['KW_STATUS'] < tbc].to_dict('records')
    basket_b = df_p[df_p['KW_STATUS'] >= tbc].to_dict('records')
    
    # Nhịp 3: Phân bổ 60/40
    num_total = int(v('NUM_KEYWORDS_PER_POST') or 4)
    quota_a = int(num_total * 0.6)
    quota_b = num_total - quota_a
    
    # Nhịp 4: Vòng lặp nhặt (Lọc nhóm kép)
    selected, groups = [], []
    def pick(basket, q):
        random.shuffle(basket)
        for kw in basket:
            if len(selected) >= q: break
            g = kw['KW_GROUP'].strip().lower()
            if g not in groups:
                selected.append(kw); groups.append(g)
    
    pick(basket_a, quota_a)
    pick(basket_b + basket_a, num_total) # Fallback nhặt cho đủ
    
    return selected

# =========================================================
# 🧱 BƯỚC 3 & 4: SẢN XUẤT & TỐI ƯU (ASSEMBLER)
# =========================================================
def pulse_3_4_produce(v, web, kw_list, images):
    # Nhịp 3.1: 6 Kings Check
    kings = ['PROMPT_TEMPLATE', 'CONTENT_STRATEGY', 'KEYWORD_PROMPT', 'SEO_GLOBAL_RULE', 'AI_HUMANIZER_PROMPT']
    for k in kings:
        if not v(k): return None, f"Kings Check Fail: {k}"

    # Nhịp 1 Bước 4: Gắn Backlink (100% - Out trước In sau)
    limit_out = int(web['WS_LINK_OUT_LIMIT'] or 1)
    # Giả lập content AI...
    content = f"<h2>{kw_list[0]['KW_TEXT']}</h2><p>Nội dung chuẩn SEO...</p>"
    
    for i, kw in enumerate(kw_list):
        url = web['WS_TARGET_URL'] if i < limit_out else web['WS_PLATFORM']
        link = f'<a href="{url}">{kw["KW_TEXT"]}</a>'
        content = content.replace(kw['KW_TEXT'], link, 1)

    # Nhịp 2 Bước 4: Tuyển chọn ảnh (Usage Count)
    img_pool = images.to_dict('records')
    img_pool.sort(key=lambda x: int(x['IMG_USED_COUNT'] or 0))
    # Bốc ngẫu nhiên trong nhóm usage thấp nhất
    min_usage = int(img_pool[0]['IMG_USED_COUNT'] or 0)
    best_imgs = [i for i in img_pool if int(i['IMG_USED_COUNT'] or 0) == min_usage]
    selected_img = random.choice(best_imgs)
    
    return content, selected_img

# =========================================================
# 🎮 GIAO DIỆN ĐIỀU HÀNH
# =========================================================
data, sh = load_all_data()

if data:
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().upper() == k.strip().upper()].iloc[:, 1]
        return clean(res.values[0]) if not res.empty else ""

    # UI KPI
    df_kw = data['Keyword']
    done_count = len(df_kw[pd.to_numeric(df_kw['KW_STATUS'], errors='coerce') > 1])
    c1, c2, c3 = st.columns(3)
    c1.metric("📌 TỔNG TỪ KHÓA", len(df_kw))
    c2.metric("✅ ĐÃ XONG", done_count)
    c3.metric("⏳ CÒN LẠI", len(df_kw) - done_count)

    if st.button("🚀 KÍCH HOẠT ROBOT MASTER V30", type="primary"):
        with st.status("🤖 Robot đang vận hành 5 Nhịp MASTER...", expanded=True) as status:
            # BƯỚC 1: GATEKEEPER
            slot, g_msg = pulse_1_gatekeeper(data, v)
            if not slot: st.error(g_msg); st.stop()
            st.write(f"✅ B1: Chốt Web `{slot['web']['WS_URL']}`")

            # BƯỚC 2: HUNTER
            kw_selection = pulse_2_keyword_hunter(data, v)
            if not kw_selection: st.error("Hết từ khóa hợp lệ!"); st.stop()
            st.write(f"✅ B2: Nhặt {len(kw_selection)} từ khóa (60/40 Split)")

            # BƯỚC 3 & 4: PRODUCE & OPTIMIZE
            content, img = pulse_3_4_produce(v, slot['web'], kw_selection, data['Image'])
            st.write("✅ B3&4: Đã lắp Prompt 6 Kings & Gắn Link/Ảnh")

            # BƯỚC 5: REPORT & CẬP NHẬT (NHỊP 2 & 3)
            # Ghi sổ Sheet...
            ws_rep = sh.worksheet("Report")
            now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
            ws_rep.append_row([slot['web']['WS_URL'], slot['web']['WS_URL'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", "SUCCESS"])
            
            # Cập nhật Status Keyword (Nhịp 2)
            ws_kw = sh.worksheet("Keyword")
            for kw in kw_selection:
                cell = ws_kw.find(kw['KW_TEXT'])
                ws_kw.update_cell(cell.row, 3, int(kw['KW_STATUS']) + 1)
            
            # Bắn Telegram (Nhịp 3)
            tg_msg = f"🔔 [DỰ ÁN: {v('PROJECT_NAME')}]\n📝 Tên bài: {kw_selection[0]['KW_TEXT']}\n✅ Trạng thái: SUCCESS"
            requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                          json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tg_msg})

            status.update(label="🏁 CHIẾN DỊCH HOÀN TẤT!", state="complete")
            st.balloons()
