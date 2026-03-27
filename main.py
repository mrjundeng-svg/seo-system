import streamlit as st
import pandas as pd
import gspread
from groq import Groq
import smtplib, time, random, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V72 - DELIVERY", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)

def get_range_val(val, default=1):
    nums = re.findall(r'\d+', str(val))
    try:
        return random.randint(int(nums[0]), int(nums[1])) if len(nums) >= 2 else (int(nums[0]) if nums else default)
    except: return default

# --- 2. HÀM GỬI MAIL (NHỊP CỨU SINH - KHÔNG CHEAT) ---
def send_report_email(v_func, subject, body_html):
    try:
        sender = v_func('SENDER_EMAIL')
        pw = v_func('SENDER_PASSWORD')
        receiver = v_func('RECEIVER_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"🚀 [REPORT] {subject} - {get_vn_now().strftime('%d/%m/%Y')}"
        
        msg.attach(MIMEText(body_html, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, pw)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except Exception as e:
        st.error(f"❌ Lỗi gửi Mail: {e}"); return False

# --- 3. AUTH & LOAD DATA ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return gspread.service_account_from_dict(info).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=2)
def load_all_tabs():
    sh = get_sh(); data = {}
    if not sh: return None, None
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        ws = sh.worksheet(t); vals = ws.get_all_values()
        data[t] = pd.DataFrame(vals[1:], columns=[h.strip().upper() for h in vals[0]]).fillna('')
    return data, sh

# --- 4. OPTIMIZER (BƯỚC 4: ĐÚNG CỘT G & B) ---
def pulse_4_optimize(web_row, kw_list, content, data_tabs, sh):
    out_limit = get_range_val(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', 'https://laiho.vn/')
    platform_url = web_row.get('WS_PLATFORM', '')
    
    optimized_content = content
    for i, kw in enumerate(kw_list):
        href = target_url if i < out_limit else platform_url
        if href:
            anchor = f"<a href='{href}'><b>{kw['KW_TEXT']}</b></a>"
            optimized_content = optimized_content.replace(kw['KW_TEXT'], anchor, 1)

    df_img = data_tabs['Image'].copy()
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0)
    valid_imgs = df_img[df_img['IMG_URL'].str.contains('http', na=False)].sort_values('IMG_USED_COUNT')
    
    if not valid_imgs.empty:
        img_url = valid_imgs.iloc[0]['IMG_URL']
        optimized_content = f"<center><img src='{img_url}' width='100%'></center><br>" + optimized_content
        try:
            ws_i = sh.worksheet("Image")
            cell = ws_i.find(img_url)
            if cell: ws_i.update_cell(cell.row, 2, int(valid_imgs.iloc[0]['IMG_USED_COUNT']) + 1)
        except: pass
    return optimized_content

# --- 5. DASHBOARD ---
data, sh = load_all_tabs()
if data:
    def v(k):
        r = data['Dashboard'][data['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V72")
    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY THẬT)"):
        with st.status("🤖 Đang sản xuất & Giao hàng...") as status:
            try:
                web = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_selection = data['Keyword'].sort_values('KW_STATUS').head(get_range_val(v('NUM_KEYWORDS_PER_POST'), 4)).to_dict('records')
                
                # AI Viết (Groq)
                client = Groq(api_key=v('GROQ_API_KEY'))
                prompt = f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_selection[0]['KW_TEXT'])}. Viết tiếng Việt, HTML format."
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.3-70b-versatile")
                
                final_art = pulse_4_optimize(web, kw_selection, res.choices[0].message.content, data, sh)
                
                # GỬI MAIL THẬT (NHỊP QUAN TRỌNG NHẤT)
                mail_sent = send_report_email(v, kw_selection[0]['KW_TEXT'], final_art)
                
                # Ghi Sheet
                now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
                rep_row = [web['WS_URL'], web['WS_PLATFORM'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", 
                           final_art[:300], "1", "YES", "NO", kw_selection[0]['KW_TEXT'], "", "", "", "", "48", "12%", "70", 
                           get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"]
                sh.worksheet("Report").append_row(rep_row)
                
                st.markdown(final_art, unsafe_allow_html=True)
                if mail_sent: st.success(f"📧 Đã gửi bài viết về: {v('RECEIVER_EMAIL')}")
                status.update(label="🏁 HOÀN TẤT & ĐÃ GỬI MAIL!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
