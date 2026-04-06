import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time, datetime, pytz, requests, json, os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# 1. CẤU HÌNH BẢO MẬT 
# ==========================================
def get_secret(key):
    val = os.environ.get(key)
    if val: return val
    try:
        import streamlit as st
        return st.secrets.get(key)
    except: return None

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw'
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
def get_vn_now(): return datetime.datetime.now(VN_TZ)

# ==========================================
# 2. CÁC HÀM XỬ LÝ LÕI
# ==========================================
def get_google_sheet():
    creds_json = get_secret("service_account")
    
    # KHIÊN CHỐNG ĐẠN 1: Báo lỗi tiếng Việt nếu GitHub bị mất Secret
    if not creds_json or str(creds_json).strip() == "":
        print("🚨 LỖI BẢO MẬT: GitHub đang không tìm thấy Secret 'service_account'.")
        print("➤ Cách sửa: Vào Settings -> Secrets and variables -> Actions -> Tạo lại Repository secret!")
        return None

    if isinstance(creds_json, str):
        try:
            info = json.loads(creds_json)
        except Exception as e:
            # KHIÊN CHỐNG ĐẠN 2: Báo lỗi nếu Sếp dán nhầm text không phải JSON
            print(f"🚨 LỖI ĐỊNH DẠNG: Cái dán trong Secret không phải là chuẩn JSON. Lỗi chi tiết: {e}")
            return None
    else:
        info = dict(creds_json)
        
    creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/spreadsheets'])
    return gspread.authorize(creds).open_by_key(SHEET_ID)

def post_to_cms(website_row, title, html_content, dash_config):
    blog_receiver = str(website_row.get('WS_BLOG_CONTENT', '')).strip()
    u = str(website_row.get('WS_LOGIN_USER', '')).strip()
    p = str(website_row.get('WS_LOGIN_PASS', '')).strip()
    
    if "@blogger.com" in blog_receiver.lower():
        s_mail = dash_config.get('EMAIL_SENDER', '').strip()
        s_pass = dash_config.get('EMAIL_SENDER_PASSWORD', '').strip()
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = s_mail, blog_receiver, title
            msg.attach(MIMEText(html_content, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(s_mail, s_pass)
            server.send_message(msg)
            server.quit()
            return True, "Bắn Blogspot OK"
        except Exception as e: return False, str(e)
    else:
        domain = str(website_row.get('WS_LINK_IN_BACKLINK', '')).split(',')[0].strip()
        try:
            res = requests.post(f"{domain.rstrip('/')}/wp-json/wp/v2/posts", auth=(u, p), json={'title': title, 'content': html_content, 'status': 'publish'}, timeout=30)
            if res.status_code in [200, 201]: return True, "Đăng WP OK"
            return False, res.text[:100]
        except Exception as e: return False, str(e)

def send_telegram_noti(dash_config, msg_text):
    token = dash_config.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = dash_config.get('TELEGRAM_CHAT_ID', '').strip()
    if token and chat_id:
        try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"}, timeout=5)
        except: pass

def run_job():
    now = get_vn_now()
    print(f"[{now.strftime('%H:%M:%S')}] 🔍 Bắt đầu quét bài PENDING...")
    
    ss = get_google_sheet()
    if not ss: 
        print("🛑 Tiến trình hủy bỏ vì không có quyền truy cập Google Sheet.")
        return

    ws_report = ss.worksheet('REPORT')
    data_report = ws_report.get_all_values()
    
    dash_data = ss.worksheet('DASHBOARD').get_all_values()
    dash_dict = {str(k).strip(): str(v).strip() for k, v in zip(pd.DataFrame(dash_data[1:])[0], pd.DataFrame(dash_data[1:])[1])}
    
    web_data = ss.worksheet('WEBSITE').get_all_values()
    df_web = pd.DataFrame(web_data[1:], columns=[str(h).strip() for h in web_data[0]])

    headers = [str(h).strip() for h in data_report[0]]
    idx_res = headers.index('REP_RESULT')
    idx_pub = headers.index('REP_PUBLISH_DATE')
    idx_html = headers.index('REP_HTML'); idx_log = headers.index('REP_LOG')
    idx_ws = headers.index('REP_WS_NAME'); idx_title = headers.index('REP_TITLE')

    upd = []
    found_any = False
    
    for i, row in enumerate(data_report[1:], 2):
        if row[idx_res].strip() == 'PENDING':
            try: pub_dt = VN_TZ.localize(datetime.datetime.strptime(row[idx_pub].strip(), '%Y-%m-%d %H:%M'))
            except: continue
            
            if pub_dt <= now:
                found_any = True
                ws_name = row[idx_ws]; title = row[idx_title]; html_content = row[idx_html]
                print(f"➤ Đang xử lý: '{title}' lên Web: {ws_name}")
                
                web_info = df_web[df_web['WS_NAME'].astype(str).str.strip() == ws_name.strip()]
                if not web_info.empty:
                    success, msg = post_to_cms(web_info.iloc[0], title, html_content, dash_dict)
                    if success:
                        print(f"✅ Thành công: {msg}")
                        upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_res+1)}', 'values': [['DONE']]})
                        upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_html+1)}', 'values': [['']]})
                        upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_log+1)}', 'values': [['']]})
                        send_telegram_noti(dash_dict, f"⏰ <b>AUTO PUBLISH</b>\n✅ Web: {ws_name}\n📑 {title}")
                    else:
                        print(f"🛑 Thất bại: {msg}")
                else:
                    print(f"⚠️ Cảnh báo: Không tìm thấy web {ws_name} trong bảng cấu hình.")

    if upd: 
        ws_report.batch_update(upd)
        print("🎉 Đã lưu thay đổi trạng thái vào Google Sheet.")
    elif not found_any:
        print("💤 Không có bài nào tới giờ đăng. Robot đi ngủ tiếp.")

if __name__ == "__main__":
    run_job()
