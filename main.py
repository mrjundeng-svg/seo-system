import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import datetime
import toml
import os

print("🚀 Khởi động Robot đăng bài Mail2Blogger...")

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

# 2. Tải dữ liệu từ Sheet
ws_report = spreadsheet.worksheet('REPORT')
df_report = pd.DataFrame(ws_report.get_all_records())

ws_website = spreadsheet.worksheet('WEBSITE')
df_website = pd.DataFrame(ws_website.get_all_records())

ws_dashboard = spreadsheet.worksheet('DASHBOARD')
dash_data = ws_dashboard.get_all_records()
dashboard = {str(row['DATA_KEY']).strip(): str(row['DATA_CONTENT']).strip() for row in dash_data}

email_sender = dashboard.get('EMAIL_SENDER', '').strip()
email_pwd = dashboard.get('EMAIL_SENDER_PASSWORD', '').replace(' ', '').strip()

if not email_sender or not email_pwd:
    print("❌ Lỗi: Chưa cấu hình EMAIL_SENDER hoặc EMAIL_SENDER_PASSWORD trong tab DASHBOARD.")
    exit()

# 3. Quét các bài viết PENDING đã tới giờ lên sóng
now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
headers = ws_report.row_values(1)
res_col_idx = headers.index('REP_RESULT') + 1
url_col_idx = headers.index('REP_POST_URL') + 1

for idx, row in df_report.iterrows():
    if str(row.get('REP_RESULT', '')).strip() == 'PENDING':
        pub_date_str = str(row.get('REP_PUBLISH_DATE', '')).strip()
        try:
            pub_date = datetime.datetime.strptime(pub_date_str, '%Y-%m-%d %H:%M')
            if now >= pub_date:
                ws_name = str(row.get('REP_WS_NAME', '')).strip()
                title = str(row.get('REP_TITLE', '')).strip()
                html_content = str(row.get('REP_HTML', '')).strip()

                # Tìm email bí mật của Blogger trong tab WEBSITE
                target_row = df_website[df_website['WS_NAME'].astype(str).str.strip() == ws_name]
                if not target_row.empty:
                    target_email = str(target_row.iloc[0].get('WS_BLOG_CONTENT', '')).strip()
                    
                    if target_email and '@' in target_email:
                        print(f"⏳ Đang gửi bài '{title}' sang Blogger ({target_email})...")
                        
                        # Đóng gói Email chứa mã HTML
                        msg = MIMEMultipart()
                        msg['From'] = email_sender
                        msg['To'] = target_email
                        msg['Subject'] = title
                        msg.attach(MIMEText(html_content, 'html'))

                        # Khởi động máy bay đi đưa thư
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(email_sender, email_pwd)
                        server.send_message(msg)
                        server.quit()

                        # Cập nhật trạng thái Sheet sang DONE
                        sheet_row = idx + 2
                        ws_report.update_cell(sheet_row, res_col_idx, 'DONE')
                        ws_report.update_cell(sheet_row, url_col_idx, 'Đã đẩy qua Mail2Blogger')
                        print(f"✅ Lên sóng thành công!")
                    else:
                        print(f"⚠️ Cảnh báo: Web '{ws_name}' thiếu cấu hình email ở cột WS_BLOG_CONTENT.")
        except Exception as e:
            print(f"❌ Lỗi khi xử lý bài '{row.get('REP_TITLE', 'Unknown')}': {e}")

print("🏁 Hoàn tất phiên kiểm tra!")
