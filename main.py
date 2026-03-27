import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
import smtplib, time, random, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V73", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)

def get_range_val(val, default=1):
    nums = re.findall(r'\d+', str(val))
    try:
        return random.randint(int(nums[0]), int(nums[1])) if len(nums) >= 2 else (int(nums[0]) if nums else default)
    except: return default

# --- 2. KẾT NỐI GSHEET (FIX TRIỆT ĐỂ LỖI _AUTH_REQUEST) ---
def get_sh():
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        # Dùng Credentials chính thống để tránh lỗi attribute '_auth_request'
        creds = Credentials.from_service_account_info(info, scopes=scope)
        gc = gspread.authorize(creds)
        return gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"❌ Lỗi GSheet: {e}"); return None

# --- 3. HÀM GỬI MAIL (FIX LỖI 535) ---
def send_mail_final(v_func, subject, content_html):
    try:
        sender = v_func('SENDER_EMAIL')
        # NHẮC: Phải là Mật khẩu ứng dụng 16 ký tự
        pw = v_func('SENDER_PASSWORD') 
        receiver = v_func('RECEIVER_EMAIL')
        
        msg = MIMEMultipart()
        msg['From'] = sender
        msg['To'] = receiver
        msg['Subject'] = f"🚀 [BÀI VIẾT MỚI] {subject}"
        msg.attach(MIMEText(content_html, 'html'))
        
        # Dùng port 587 với STARTTLS cho ổn định nhất
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, pw)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        st.error(f"❌ Lỗi Mail (Check App Password): {e}"); return False

# --- 4. OPTIMIZER BƯỚC 4 (LINK NGOẠI G - LINK NỘI B) ---
def pulse_4_optimize(web_row, kw_list, content, sh, data_tabs):
    out_limit = get_range_val(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', 'https://laiho.vn/')
    platform_url = web_row.get('WS_PLATFORM', '')
    
    optimized = content
    for i, kw in enumerate(kw_list):
        href = target_url if i < out_limit else platform_url
        if href:
            optimized = optimized.replace(kw['KW_TEXT'], f"<a href='{href}'><b>{kw['KW_TEXT']}</b></a>", 1)
            
    # Chèn Ảnh Used Count thấp nhất
    df_img = data_tabs['Image'].copy()
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0)
    valid_imgs = df_img[df_img['IMG_URL'].str.contains('http', na=False)].sort_values('IMG_USED_COUNT')
    
    if not valid_imgs.empty:
        img_url = valid_imgs.iloc[0]['IMG_URL']
        optimized = f"<div style='text-align:center'><img src='{img_url}' width='100%'></div><br>" + optimized
        try:
            ws_i = sh.worksheet("Image")
            cell = ws_i.find(img_url)
            if cell: ws_i.update_cell(cell.row, 2, int(valid_imgs.iloc[0]['IMG_USED_COUNT']) + 1)
        except: pass
    return optimized

# --- 5. VẬN HÀNH ---
sh = get_sh()
if sh:
    # Load data
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report"]
    data = {}
    for t in tabs:
        ws = sh.worksheet(t); vals = ws.get_all_values()
        data[t] = pd.DataFrame(vals[1:], columns=[h.strip().upper() for h in vals[0]]).fillna('')
    
    def v(k):
        r = data['Dashboard'][data['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V73")
    
    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY THẬT)"):
        with st.status("🤖 Đang sản xuất & Giao hàng thực tế...") as status:
            try:
                web = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                num_kw = get_range_val(v('NUM_KEYWORDS_PER_POST'), 4)
                kw_selection = data['Keyword'].sort_values('KW_STATUS').head(num_kw).to_dict('records')
                
                # AI Groq
                client = Groq(api_key=v('GROQ_API_KEY'))
                prompt = f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_selection[0]['KW_TEXT'])}. Viết tiếng Việt, HTML format."
                res = client.chat.completions.create(messages=[{"role":"user","content":prompt}], model="llama-3.3-70b-versatile")
                
                # Bước 4
                final_art = pulse_4_optimize(web, kw_selection, res.choices[0].message.content, sh, data)
                
                # Gửi Mail & Ghi Sheet
                mail_ok = send_mail_final(v, kw_selection[0]['KW_TEXT'], final_art)
                
                row = [web['WS_URL'], web['WS_PLATFORM'], get_vn_now().strftime("%Y-%m-%d %H:%M:%S"), f"Bài: {kw_selection[0]['KW_TEXT']}", final_art[:200], "1", "YES", "NO", kw_selection[0]['KW_TEXT'], "", "", "", "", "48", "12%", "70", get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"]
                sh.worksheet("Report").append_row(row)
                
                st.markdown(final_art, unsafe_allow_html=True)
                if mail_ok: st.success(f"📧 Đã gửi bài về Mail thành công!")
                status.update(label="🏁 XONG! KIỂM TRA MAIL VÀ SHEET NGAY!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
