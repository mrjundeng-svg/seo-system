import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
st.set_page_config(page_title="LAIHO.VN - GMAIL MASTER", layout="wide", page_icon="📧")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))
def clean_str(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. HÀM GỬI EMAIL HTML "GIỐNG NGÀY XƯA" ---
def send_email_report(sender, password, receiver, keyword, content):
    if not sender or not password or not receiver: return False
    
    msg = MIMEMultipart()
    msg['From'] = f"Laiho Robot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"[HỆ THỐNG PBN] {keyword} - 🚀 XUẤT BẢN THÀNH CÔNG"

    # Tính toán thông số nhanh
    word_count = len(content.split())
    
    # Template HTML chuẩn "vibe" bồ yêu cầu
    html = f"""
    <html>
      <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px;">
        <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">🚀 XUẤT BẢN: {keyword}</h2>
        
        <p>🌐 <b>BÁO CÁO PHÂN PHÁT WEB:</b><br>
        Chỉ tạo nội dung (Dữ liệu đã được lưu trữ vào Google Sheet).</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 20px 0;">
          <h3 style="margin-top: 0; color: #202124;">📊 KẾT QUẢ SEO:</h3>
          <ul style="list-style: none; padding-left: 0;">
            <li>📝 <b>Độ dài:</b> ~{word_count} chữ</li>
            <li>🎨 <b>Phong cách:</b> Chuẩn SEO Laiho.vn</li>
            <li>✅ <b>Trạng thái:</b> Đã lưu và cập nhật Tracking</li>
          </ul>
        </div>

        <h3 style="color: #202124;">🔗 CHI TIẾT ĐIỀU HƯỚNG:</h3>
        <p style="font-size: 14px; color: #5f6368;">Hệ thống đã tự động tối ưu hóa cấu trúc liên kết nội bộ.</p>
        
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
        <div style="font-style: italic; color: #555; background: #fffcf0; padding: 10px; border-left: 4px solid #fbbc04;">
          "{content[:400]}..."
        </div>
        
        <p style="margin-top: 25px; font-size: 12px; color: #9aa0a6;">Báo cáo tự động từ Laiho Robot Master V22.</p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
        return True
    except: return False

# --- 3. TIẾN TRÌNH VIẾT BÀI (TÍCH HỢP EMAIL) ---
@st.dialog("🚀 CHIẾN DỊCH VIẾT BÀI & BÁO CÁO", width="large")
def run_batch_popup(all_data, sh_instance, num_posts):
    sh = sh_instance
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().str.upper() == k.strip().upper()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    df_kw = all_data['Keyword']
    name_col = next((c for c in ['KW_TEXT', 'KW_NAME'] if c in df_kw.columns), None)
    status_col = next((c for c in ['KW_STATUS', 'STATUS'] if c in df_kw.columns), None)
    
    todo_list = df_kw[(df_kw[status_col] == '0') | (df_kw[status_col] == '')].head(num_posts)
    if todo_list.empty:
        st.warning("Hết từ khóa rồi bồ ơi!"); return

    # Lấy thông tin Mail từ Dashboard
    mail_sender = v('EMAIL_SENDER')
    mail_pass = v('EMAIL_PASSWORD')
    mail_to = v('EMAIL_RECEIVER')

    progress_bar = st.progress(0)
    for i, (idx, row) in enumerate(todo_list.iterrows()):
        kw_main = row[name_col]
        # [Giả lập gọi AI và ghi Sheet ở đây...]
        content = f"Nội dung bài viết cho {kw_main}..." # Thay bằng hàm call_ai của bồ
        
        # Ghi Sheet xong thì gửi Mail
        success_mail = send_email_report(mail_sender, mail_pass, mail_to, kw_main, content)
        
        if success_mail:
            st.success(f"📧 Đã gửi báo cáo Gmail cho: {kw_main}")
        else:
            st.warning(f"⚠️ Đã viết xong nhưng gửi Mail thất bại (Check App Password).")
            
        progress_bar.progress((i + 1) / len(todo_list))

# --- Phần giao diện Main Dashboard bồ giữ nguyên như bản V21 ---
