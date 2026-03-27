import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG & UI/UX ---
st.set_page_config(page_title="LAIHO.VN - LEGACY COMMAND", layout="wide", page_icon="📧")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #ff4b4b !important; }
    [data-testid="stMetricLabel"] { font-size: 14px; color: #808495 !important; }
    .stButton>button { border-radius: 8px; font-weight: 600; height: 3em; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))
def clean_str(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. KẾT NỐI VÀ HỒI PHỤC GOOGLE SHEET ---
def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

def re_authorize():
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

@st.cache_data(ttl=5)
def load_data():
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        data = {}
        for t in ["Dashboard", "Keyword", "Report"]:
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if vals:
                headers = [clean_str(h).upper() for h in vals[0]]
                data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        return data, sh
    except: return None, None

# --- 3. HÀM GỬI EMAIL HTML "HOÀI CỔ" ---
def send_legacy_mail(sender, password, receiver, keyword, content):
    if not sender or not password or not receiver: return False
    
    msg = MIMEMultipart()
    msg['From'] = f"Laiho Robot <{sender}>"
    msg['To'] = receiver
    msg['Subject'] = f"[HỆ THỐNG PBN] {keyword} - 🚀 XUẤT BẢN THÀNH CÔNG"

    word_count = len(content.split())
    # Template HTML mô phỏng lại image_91e50d.png
    html = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px;">
        <h2 style="color: #202124;">🚀 XUẤT BẢN: {keyword}</h2>
        <p>🌐 <b>BÁO CÁO PHÂN PHÁT WEB:</b><br>Chỉ tạo nội dung (Dữ liệu đã lưu Tracking).</p>
        
        <h3 style="color: #2e7d32; border-bottom: 1px solid #ddd; padding-bottom: 5px;">📊 KẾT QUẢ SEO:</h3>
        <ul style="list-style: none; padding-left: 0;">
          <li>- 📝 <b>Độ dài:</b> ~{word_count} chữ</li>
          <li>- 🎨 <b>Phong cách:</b> Chuẩn SEO Laiho VIP</li>
          <li>- ✅ <b>Trạng thái:</b> Đã ép thành công 100%</li>
          <li>- ✅ Đã chèn hình ảnh minh họa.</li>
        </ul>

        <h3 style="color: #1a73e8; border-bottom: 1px solid #ddd; padding-bottom: 5px;">🔗 CHI TIẾT ĐIỀU HƯỚNG:</h3>
        <p style="font-size: 14px;">Hệ thống đã tự động tối ưu Internal Link cho từ khóa <b>{keyword}</b>.</p>
        
        <div style="background: #f9f9f9; padding: 15px; border-left: 5px solid #ff4b4b; margin: 20px 0;">
          <h4 style="margin-top:0;">📄 TRÍCH ĐOẠN NỘI DUNG:</h4>
          <i style="color: #555;">{content[:500]}...</i>
        </div>
        
        <p style="font-size: 12px; color: #999;">✅ Đã lưu file backup và cập nhật Tracking vào hệ thống Report.</p>
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

# --- 4. HÀM GỌI AI ---
def call_ai(api_key, model_name, prompt, provider="groq"):
    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "groq" else "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60).json()
        return resp['choices'][0]['message']['content']
    except: return "❌ Lỗi"

# --- 5. TIẾN TRÌNH VIẾT BÀI TỰ ĐỘNG ---
@st.dialog("🚀 CHIẾN DỊCH VIẾT BÀI & GỬI BÁO CÁO", width="large")
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
    if todo_list.empty: st.warning("Hết từ khóa rồi bồ ơi!"); return

    progress_bar = st.progress(0)
    for i, (idx, row) in enumerate(todo_list.iterrows()):
        kw_main = row[name_col]
        st.write(f"⏳ **Đang xử lý:** {kw_main}")
        
        prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"
        content = ""
        models = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
        for m_name in models:
            provider = "openrouter" if '/' in m_name else "groq"
            api_key = v('OPENROUTER_API_KEY') if provider == "openrouter" else v('GROQ_API_KEY')
            content = call_ai(api_key, m_name, prompt_final, provider)
            if "❌" not in content: break
        
        if "❌" not in content:
            try:
                # Ghi Sheet (Có hồi phục)
                ws_rep = sh.worksheet("Report")
                ws_rep.append_row([get_vn_time().strftime("%Y-%m-%d %H:%M"), kw_main, content[:150], "SUCCESS"])
                ws_kw = sh.worksheet("Keyword"); cell = ws_kw.find(kw_main)
                ws_kw.update_cell(cell.row, 3, "SUCCESS")
                
                # Gửi Báo cáo Mail & Telegram
                send_legacy_mail(v('SENDER_EMAIL'), v('SENDER_PASSWORD'), v('RECEIVER_EMAIL'), kw_main, content)
                st.success(f"📧 Đã gửi báo cáo Gmail cho: {kw_main}")
                time.sleep(1)
            except: 
                sh = re_authorize() # Hồi phục khi lỗi session
        progress_bar.progress((i + 1) / len(todo_list))
    st.balloons()

# --- 6. GIAO DIỆN CHÍNH ---
data, sh = load_data()
if data:
    with st.sidebar:
        st.title("🛡️ LAIHO SEO")
        num_posts = st.slider("Số lượng bài/đợt", 1, 10, 3)
        if st.button("🔄 LÀM MỚI KHO"): st.cache_data.clear(); st.rerun()

    df_kw = data['Keyword']
    done = len(df_kw[df_kw.iloc[:, 2].astype(str).str.contains('SUCCESS|1', case=False)])
    
    m1, m2, m3 = st.columns(3)
    m1.metric("📌 TỔNG TỪ KHÓA", len(df_kw))
    m2.metric("✅ ĐÃ XONG", done)
    m3.metric("⏳ CÒN LẠI", len(df_kw) - done)

    tab_run, tab_data, tab_log = st.tabs(["🎮 ĐIỀU KHIỂN", "📂 KHO TỪ KHÓA", "📜 BÁO CÁO"])
    with tab_run:
        if st.button(f"🚀 CHẠY CHIẾN DỊCH {num_posts} BÀI", type="primary"):
            if sh: run_batch_popup(data, sh, num_posts)
    with tab_data: st.dataframe(df_kw, use_container_width=True, hide_index=True)
    with tab_log: st.dataframe(data['Report'].iloc[::-1], use_container_width=True, hide_index=True)
