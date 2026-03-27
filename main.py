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

# --- 2. HÀM GỬI EMAIL "GIỐNG NGÀY XƯA" ---
def send_email_report(sender, password, receiver, keyword, content):
    if not sender or not password or not receiver: return
    
    msg = MIMEMultipart()
    msg['From'] = f"Laiho Robot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"[HỆ THỐNG PBN] {keyword} - 🚀 XUẤT BẢN THÀNH CÔNG"

    # Tạo nội dung HTML giống như xưa
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2 style="color: #2e7d32;">🚀 XUẤT BẢN: {keyword}</h2>
        <p>🌐 <b>BÁO CÁO PHÂN PHÁT WEB:</b><br>Nội dung đã được lưu trữ và sẵn sàng đăng tải.</p>
        <hr>
        <p>📊 <b>KẾT QUẢ SEO:</b><br>
        - Độ dài: ~{len(content.split())} chữ<br>
        - Trạng thái: <b>Thành công 100%</b></p>
        <div style="background: #f4f4f4; padding: 15px; border-radius: 5px; border-left: 5px solid #ff4b4b;">
          <i>{content[:500]}...</i>
        </div>
        <br>
        <p>✅ <b>Đã lưu dữ liệu và cập nhật Tracking.</b></p>
      </body>
    </html>
    """
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender, password)
            server.sendmail(sender, receiver, msg.as_string())
    except Exception as e:
        st.error(f"Lỗi gửi Email: {e}")

# --- 3. TIẾN TRÌNH BATCH (TÍCH HỢP EMAIL) ---
@st.dialog("🚀 CHIẾN DỊCH VIẾT BÀI & GỬI MAIL", width="large")
def run_batch_popup(all_data, sh, num_posts):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().str.upper() == k.strip().upper()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    # ... (Phần nhặt từ khóa và gọi AI giữ nguyên như V21)
    # Giả sử sau khi call_ai thành công và ghi Sheet xong:
    
    # [TRÍCH ĐOẠN LOGIC TRONG VÒNG LẶP]
    # if "❌" not in content:
    #    ... Ghi Sheet xong ...
    #    # 📧 BẮT ĐẦU GỬI MAIL
    #    send_email_report(
    #        v('EMAIL_SENDER'), 
    #        v('EMAIL_PASSWORD'), 
    #        v('EMAIL_RECEIVER'), 
    #        kw_main, 
    #        content
    #    )
    #    st.success(f"📧 Đã gửi báo cáo mail cho: {kw_main}")

# --- Giao diện Home bồ giữ nguyên bản V21 ---
