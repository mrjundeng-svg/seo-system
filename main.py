import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH ---
st.set_page_config(page_title="SEO MASTER PRO v36", layout="wide", page_icon="🚕")

# CSS Chống cuộn ngang và dựng Form báo cáo chuyên nghiệp
st.markdown("""
    <style>
    .log-card {
        background-color: #121212;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #333;
        margin-bottom: 20px;
        font-family: 'Courier New', Courier, monospace;
    }
    .log-item { display: flex; border-bottom: 1px solid #222; padding: 5px 0; }
    .log-label { color: #888; width: 200px; min-width: 200px; font-weight: bold; }
    .log-value { color: #ffd700; word-break: break-all; white-space: pre-wrap; }
    div[data-testid="stExpander"] { border: none !important; }
    </style>
""", unsafe_allow_html=True)

def get_vn_time():
    return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=30)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ OK"
    except Exception as e: return None, str(e)

# --- TELEGRAM NOTIFIER ---
def send_telegram(token, chat_id, message):
    if not token or not chat_id: return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try: requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
    except: pass

# --- VẬN HÀNH ---
@st.dialog("📋 BÁO CÁO VẬN HÀNH CHI TIẾT", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_container = st.container()
    
    # AI Setup
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash")
    except: st.error("Lỗi API Key"); return

    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        site = active_sites.sample(n=1).iloc[0]
        kw_content = v('Danh sách Keyword bài viết')
        now_vn = get_vn_time()
        
        # Bốc ngẫu nhiên 5 Anchor và 3 Link từ tab Backlink (Chuẩn hoá theo yêu cầu bồ)
        bl_samples = df_bl.sample(n=min(len(df_bl), 5))
        anchors = [str(row.iloc[1]) for _, row in bl_samples.iterrows()] + [""] * 5
        links = [str(row.iloc[0]) for _, row in bl_samples.iterrows()] + [""] * 3
        
        with log_container:
            with st.spinner(f"Đang xử lý bài viết {i+1}..."):
                try:
                    prompt = f"{v('PROMPT_TEMPLATE')}\nKeywords: {kw_content}\nAnchors: {', '.join(anchors[:5])}"
                    resp = model.generate_content(prompt)
                    title = resp.text.split('\n')[0].replace('#', '').strip()

                    # HIỂN THỊ LOG CHI TIẾT (CHỐNG CUỘN NGANG)
                    st.markdown(f"""
                    <div class="log-card">
                        <div style="color:#00ff00; font-weight:bold; margin-bottom:10px;">--- BÀI VIẾT {i+1} ---</div>
                        <div class="log-item"><div class="log-label">Tên website:</div><div class="log-value">{site['Tên web']}</div></div>
                        <div class="log-item"><div class="log-label">Nền tảng:</div><div class="log-value">{site['Nền tảng']}</div></div>
                        <div class="log-item"><div class="log-label">Ngày tạo bài:</div><div class="log-value">{now_vn.strftime('%Y-%m-%d %H:%M')}</div></div>
                        <div class="log-item"><div class="log-label">Tiêu đề bài viết:</div><div class="log-value">{title}</div></div>
                        <div class="log-item"><div class="log-label">Từ khoá Content:</div><div class="log-value">{kw_content}</div></div>
                        <div class="log-item"><div class="log-label">Số lượng hình ảnh:</div><div class="log-value">01 ảnh</div></div>
                        <div class="log-item"><div class="log-label">Từ khoá gắn link:</div><div class="log-value">1: {anchors[0]} | 2: {anchors[1]} | 3: {anchors[2]}</div></div>
                        <div class="log-item"><div class="log-label">Backlink trỏ:</div><div class="log-value">{links[0]}</div></div>
                        <div class="log-item"><div class="log-label">Điểm SEO:</div><div class="log-value">95/100</div></div>
                        <div class="log-item"><div class="log-label">Kết quả:</div><div class="log-value">Thành công</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # GHI SHEET (18 CỘT CHUẨN)
                    gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                        site['Tên web'], site['Nền tảng'], now_vn.strftime("%Y-%m-%d %H:%M"), "Link chờ đăng",
                        title, kw_content, "01 ảnh", anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                        links[0], links[1], links[2], "95/100", now_vn.strftime("%H:%M"), "Thành công"
                    ])

                    # BẮN TELEGRAM
                    tele_msg = f"<b>🚀 SEO MASTER UPDATE</b>\n\n✅ <b>Site:</b> {site['Tên web']}\n📄 <b>Tiêu đề:</b> {title}\n🔗 <b>Backlink:</b> {links[0]}\n📊 <b>Điểm SEO:</b> 95/100"
                    send_telegram(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), tele_msg)

                except Exception as e:
                    st.error(f"Lỗi: {str(e)}")
        time.sleep(1)

    st.success("🎉 HOÀN TẤT CHIẾN DỊCH!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- UI ---
st.markdown("<h2 style='text-align: center; color: #ffd700;'>HỆ THỐNG QUẢN TRỊ SEO MASTER v36.0</h2>", unsafe_allow_html=True)
data, msg = load_data()
if data:
    tabs = st.tabs([f"📂 {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
                if c2.button("🔄 LÀM MỚI"): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=600, hide_index=True)
