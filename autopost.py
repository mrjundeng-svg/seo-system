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

print("🚀 Khởi động Robot Shipper (Bản chuẩn GitHub)...")

# 1. KẾT NỐI GOOGLE SHEET QUA SECRETS
try:
    # Đọc cấu hình từ file .streamlit/secrets.toml mà GitHub Actions vừa tạo ra
    secrets = toml.load(".streamlit/secrets.toml")
    s_creds = secrets["service_account"]
    
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
    client = gspread.authorize(creds)
    
    # ID file Google Sheet của Sếp
    SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw'
    spreadsheet = client.open_by_key(SHEET_ID)
    print("✅ Kết nối Google Sheet thành công!")
except Exception as e:
    print(f"❌ Lỗi kết nối: {e}")
    exit()

# 2. LẤY DỮ LIỆU TỪ CÁC TAB
try:
    ws_report = spreadsheet.worksheet('REPORT')
    df_report = pd.DataFrame(ws_report.get_all_records())
    
    ws_website = spreadsheet.worksheet('WEBSITE')
    df_website = pd.DataFrame(ws_website.get_all_records())
    
    ws_dashboard = spreadsheet.worksheet('DASHBOARD')
    dashboard = {str(row['DATA_KEY']).strip(): str(row['DATA_CONTENT']).strip() for row in ws_dashboard.get_all_records()}
    
    email_sender = dashboard.get('EMAIL_SENDER', '').strip()
    email_pwd = dashboard.get('EMAIL_SENDER_PASSWORD', '').replace(' ', '').strip()
    
    if not email_sender or not email_pwd:
        print("❌ Lỗi: Thiếu cấu hình Email Sender hoặc App Password trong tab DASHBOARD.")
        exit()
except Exception as e:
    print(f"❌ Lỗi đọc dữ liệu các Tab: {e}")
    exit()

# 3. QUÉT BÀI VIẾT PENDING ĐÃ ĐẾN GIỜ ĐĂNG
# Lấy giờ hiện tại Việt Nam (UTC+7)
now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
print(f"🕒 Giờ hệ thống hiện tại (VN): {now.strftime('%Y-%m-%d %H:%M')}")

headers = ws_report.row_values(1)
res_col_idx = headers.index('REP_RESULT') + 1
url_col_idx = headers.index('REP_POST_URL') + 1

posted_count = 0

for idx, row in df_report.iterrows():
    # Kiểm tra trạng thái PENDING
    if str(row.get('REP_RESULT', '')).strip() == 'PENDING':
        pub_date_str = str(row.get('REP_PUBLISH_DATE', '')).strip()
        
        try:
            # Chuyển đổi chuỗi ngày tháng sang đối tượng datetime để so sánh
            pub_date = datetime.datetime.strptime(pub_date_str, '%Y-%m-%d %H:%M')
            
            # Nếu giờ hiện tại >= giờ hẹn đăng
            if now >= pub_date:
                ws_name = str(row.get('REP_WS_NAME', '')).strip()
                title = str(row.get('REP_TITLE', '')).strip()
                html_content = str(row.get('REP_HTML', '')).strip()

                # Kiểm tra nội dung HTML (Tránh gửi bài trống)
                if len(html_content) < 100:
                    print(f"⚠️ Bỏ qua bài '{title}': Nội dung HTML quá ngắn hoặc trống.")
                    continue

                # Tìm Email đích của Blogger trong tab WEBSITE
                target_web = df_website[df_website['WS_NAME'].astype(str).str.strip() == ws_name]
                if not target_web.empty:
                    target_email = str(target_web.iloc[0].get('WS_BLOG_CONTENT', '')).strip()
                    
                    if target_email and '@' in target_email:
                        print(f"📧 Đang gửi bài '{title}' tới {target_email}...")
                        
                        # Khởi tạo Email
                        msg = MIMEMultipart()
                        msg['From'] = email_sender
                        msg['To'] = target_email
                        msg['Subject'] = title
                        msg.attach(MIMEText(html_content, 'html'))

                        # Gửi Email qua SMTP Gmail
                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(email_sender, email_pwd)
                        server.send_message(msg)
                        server.quit()

                        # Cập nhật kết quả lên Sheet
                        sheet_row_num = idx + 2
                        ws_report.update_cell(sheet_row_num, res_col_idx, 'DONE')
                        ws_report.update_cell(sheet_row_num, url_col_idx, 'Đã đẩy qua Mail2Blogger')
                        
                        print(f"✅ Đăng bài thành công: {title}")
                        posted_count += 1
                        time.sleep(2) # Nghỉ 2s giữa các bài để tránh spam
                else:
                    print(f"⚠️ Không tìm thấy cấu hình website cho: {ws_name}")
        except Exception as e:
            print(f"❌ Lỗi xử lý hàng {idx+2}: {e}")

if posted_count == 0:
    print("ℹ️ Không có bài viết nào khớp điều kiện đăng lúc này.")
else:
    print(f"🎉 Hoàn tất! Đã đăng tổng cộng {posted_count} bài.")

print("🏁 Kết thúc Robot.")
