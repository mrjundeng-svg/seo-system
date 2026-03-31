import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import toml
import os
import time

print("🚀 Khởi động Robot Shipper (Bản gọn)...")

# 1. Kết nối Google Sheet
try:
    secrets = toml.load(".streamlit/secrets.toml")
    s_creds = secrets["service_account"]
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
    client = gspread.authorize(creds)
    SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw'
    spreadsheet = client.open_by_key(SHEET_ID)
except Exception as e:
    print(f"❌ Lỗi kết nối Google Sheet: {e}")
    exit()

# 2. Lấy dữ liệu bài viết
ws_report = spreadsheet.worksheet('REPORT')
df_report = pd.DataFrame(ws_report.get_all_records())
ws_website = spreadsheet.worksheet('WEBSITE')
df_website = pd.DataFrame(ws_website.get_all_records())
ws_dashboard = spreadsheet.worksheet('DASHBOARD')
dashboard = {str(row['DATA_KEY']).strip(): str(row['DATA_CONTENT']).strip() for row in ws_dashboard.get_all_records()}

email_sender = dashboard.get('EMAIL_SENDER', '').strip()
email_pwd = dashboard.get('EMAIL_SENDER_PASSWORD', '').replace(' ', '').strip()

# 3. Quét bài PENDING tới giờ đăng
now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
headers = ws_report.row_values(1)
res_col_idx = headers.index('REP_RESULT') + 1

for idx, row in df_report.iterrows():
    if str(row.get('REP_RESULT', '')).strip() == 'PENDING':
        pub_date_str = str(row.get('REP_PUBLISH_DATE', '')).strip()
        try:
            pub_date = datetime.datetime.strptime(pub_date_str, '%Y-%m-%d %H:%M')
            if now >= pub_date:
                ws_name = str(row.get('REP_WS_NAME', '')).strip()
                title = str(row.get('REP_TITLE', '')).strip()
                html_content = str(row.get('REP_HTML', '')).strip()

                target_email = str(df_website[df_website['WS_NAME'] == ws_name].iloc[0].get('WS_BLOG_CONTENT', ''))
                
                if '@' in target_email:
                    print(f"⏳ Đang gửi mail cho bài: {title}")
                    msg = MIMEMultipart()
                    msg['From'], msg['To'], msg['Subject'] = email_sender, target_email, title
                    msg.attach(MIMEText(html_content, 'html'))

                    server = smtplib.SMTP('smtp.gmail.com', 587)
                    server.starttls()
                    server.login(email_sender, email_pwd)
                    server.send_message(msg)
                    server.quit()

                    ws_report.update_cell(idx + 2, res_col_idx, 'DONE')
                    print(f"✅ Đã đăng thành công!")
        except Exception as e:
            print(f"❌ Lỗi: {e}")

print("🏁 Hoàn tất!")
