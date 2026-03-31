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

print("🚀 Khởi động Robot Shipper & Vệ sinh kho bãi...")

# 1. Kết nối Google Sheet
try:
    secrets = toml.load(".streamlit/secrets.toml")
    s_creds = secrets["service_account"]
    scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
    client = gspread.authorize(creds)
    SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw'
    spreadsheet = client.open_by_key(SHEET_ID)
except Exception as e:
    print(f"❌ Lỗi kết nối Google Sheet: {e}")
    exit()

# 2. Lấy dữ liệu
ws_report = spreadsheet.worksheet('REPORT')
try:
    ws_archive = spreadsheet.worksheet('ARCHIVE_REPORT')
except:
    print("⚠️ Chưa có tab ARCHIVE_REPORT. Đang tự tạo...")
    ws_archive = spreadsheet.add_worksheet(title="ARCHIVE_REPORT", rows="100", cols="20")
    ws_archive.append_row(ws_report.row_values(1)) # Copy tiêu đề

df_report = pd.DataFrame(ws_report.get_all_records())
ws_website = spreadsheet.worksheet('WEBSITE')
df_website = pd.DataFrame(ws_website.get_all_records())

ws_dashboard = spreadsheet.worksheet('DASHBOARD')
dash_data = ws_dashboard.get_all_records()
dashboard = {str(row['DATA_KEY']).strip(): str(row['DATA_CONTENT']).strip() for row in dash_data}

email_sender = dashboard.get('EMAIL_SENDER', '').strip()
email_pwd = dashboard.get('EMAIL_SENDER_PASSWORD', '').replace(' ', '').strip()

# 3. Quét bài PENDING
now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
headers = ws_report.row_values(1)
res_col_idx = headers.index('REP_RESULT') + 1
url_col_idx = headers.index('REP_POST_URL') + 1

rows_to_archive = [] # Danh sách hàng sẽ được chuyển đi sau khi xong

for idx, row in df_report.iterrows():
    if str(row.get('REP_RESULT', '')).strip() == 'PENDING':
        pub_date_str = str(row.get('REP_PUBLISH_DATE', '')).strip()
        try:
            pub_date = datetime.datetime.strptime(pub_date_str, '%Y-%m-%d %H:%M')
            if now >= pub_date:
                ws_name = str(row.get('REP_WS_NAME', '')).strip()
                title = str(row.get('REP_TITLE', '')).strip()
                html_content = str(row.get('REP_HTML', '')).strip()

                target_row = df_website[df_website['WS_NAME'].astype(str).str.strip() == ws_name]
                if not target_row.empty:
                    target_email = str(target_row.iloc[0].get('WS_BLOG_CONTENT', '')).strip()
                    
                    if target_email and '@' in target_email:
                        print(f"⏳ Đang đẩy bài qua Blogger: {title}")
                        
                        msg = MIMEMultipart()
                        msg['From'] = email_sender
                        msg['To'] = target_email
                        msg['Subject'] = title
                        msg.attach(MIMEText(html_content, 'html'))

                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(email_sender, email_pwd)
                        server.send_message(msg)
                        server.quit()

                        # Cập nhật trạng thái
                        sheet_row_num = idx + 2
                        ws_report.update_cell(sheet_row_num, res_col_idx, 'DONE')
                        ws_report.update_cell(sheet_row_num, url_col_idx, 'Đã đẩy qua Blogger')
                        
                        # Thêm vào danh sách chờ dọn dẹp
                        rows_to_archive.append(sheet_row_num)
                        print(f"✅ Xong bài: {title}")
        except Exception as e:
            print(f"❌ Lỗi bài '{row.get('REP_TITLE', '')}': {e}")

# 4. ROBOT VỆ SINH: Chuyển bài DONE sang ARCHIVE
if rows_to_archive:
    print(f"🧹 Đang dọn dẹp {len(rows_to_archive)} bài đã hoàn thành sang kho lưu trữ...")
    # Lấy lại data mới nhất sau khi đã update DONE
    updated_values = ws_report.get_all_values()
    
    # Duyệt ngược từ dưới lên để xoá hàng không bị lệch chỉ số
    for row_num in sorted(rows_to_archive, reverse=True):
        row_data = updated_values[row_num - 1]
        ws_archive.append_row(row_data) # Dán vào kho lưu trữ
        ws_report.delete_rows(row_num) # Xoá khỏi tab chính
    
    print("✨ Kho bãi đã sạch sẽ!")

print("🏁 Kết thúc phiên làm việc.")
