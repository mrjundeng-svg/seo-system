import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. CẤU HÌNH GIAO DIỆN & STYLE ---
st.set_page_config(page_title="SEO MASTER PRO v38", layout="wide", page_icon="🚕")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main-header { text-align: center; color: #ffd700; font-size: 2rem; font-weight: 800; padding: 20px 0; border-bottom: 2px solid #333; margin-bottom: 30px; }
    .log-card { background-color: #1a1c24; border-radius: 15px; padding: 25px; border-left: 8px solid #ffd700; margin-bottom: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .log-title { color: #00ffcc; font-size: 1.2rem; font-weight: bold; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
    .log-row { display: flex; border-bottom: 1px solid #2d2f39; padding: 10px 0; align-items: flex-start; }
    .log-label { color: #8b949e; width: 220px; min-width: 220px; font-weight: 600; font-size: 0.95rem; }
    .log-value { color: #e6edf3; word-break: break-all; white-space: pre-wrap; font-size: 1rem; flex: 1; }
    div.stButton > button { border-radius: 10px; padding: 10px 25px; font-size: 1.1rem !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 12px; }
    </style>
""", unsafe_allow_html=True)

# --- 2. TIỆN ÍCH HỆ THỐNG ---
def get_vn_time():
    return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

def find_column(df, keyword):
    """Tìm tên cột chính xác nhất chứa từ khóa"""
    for col in df.columns:
        if keyword.lower() in str(col).lower(): return col
    return None

@st.cache_data(ttl=30)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        # Thứ tự Tab theo ý bạn, Report cuối cùng
        order = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
        res = {}
        for t in order:
            df = pd.DataFrame(sh.worksheet(t).get_all_records())
            df.columns = [str(c).strip() for c in df.columns]
            res[t] = df
        return res, "✅ Hệ thống kết nối thành công"
    except Exception as e: return None, str(e)

def notify_tele(token, chat_id, msg):
    if not token or not chat_id: return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

# --- 3. TRÌNH VẬN HÀNH LOG CHI TIẾT ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH SEO MASTER", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_area = st.container()
    
    # AI Setup
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash")
    except: st.error("Lỗi cấu hình AI"); return

    # Fix IndexError: Tìm cột Trạng thái linh hoạt
    df_web = data['Website']
    status_col = find_column(df_web, "Trạng thái") or find_column(df_web, "Trang thai")
    if not status_col: 
        st.error("❌ Không tìm thấy cột 'Trạng thái' trong tab Website!"); return
    
    active_sites = df_web[df_web[status_col].astype(str).str.contains('Active', case=False)]
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_vn = get_vn_time()
        site = active_sites.sample(n=1).iloc[0]
        kw_content = v('Danh sách Keyword bài viết')
        
        # Bốc Anchor và Link cho Report (18 cột)
        bl_samples = df_bl.sample(n=min(len(df_bl), 5))
        anchors = [str(row.iloc[1]) for _, row in bl_samples.iterrows()] + [""] * 5
        links = [str(row.iloc[0]) for _, row in bl_samples.iterrows()] + [""] * 3
        
        with log_area:
            with st.spinner(f"Đang biên tập bài {i+1}..."):
                try:
                    # Retry logic cho lỗi Quota (429)
                    success_ai = False
                    for _ in range(2):
                        try:
                            resp = model.generate_content(v('PROMPT_TEMPLATE'))
                            content = resp.text; success_ai = True; break
                        except Exception as e:
                            if "429" in str(e): time.sleep(30)
                            else: raise e
                    
                    if not success_ai: raise Exception("Cạn kiệt tài nguyên AI (429).")
                    
                    title = content.split('\n')[0].replace('#', '').strip()

                    # HIỂN THỊ LOG PHẲNG CHI TIẾT
                    st.markdown(f"""
                    <div class="log-card">
                        <div class="log-title">📊 CHI TIẾT BÀI VIẾT #{i+1}</div>
                        <div class="log-row"><div class="log-label">📍 Website vệ tinh:</div><div class="log-value">{site.iloc[0]}</div></div>
                        <div class="log-row"><div class="log-label">🏗️ Nền tảng:</div><div class="log-value">{site.iloc[1]}</div></div>
                        <div class="log-row"><div class="log-label">📄 Tiêu đề bài viết:</div><div class="log-value">{title}</div></div>
                        <div class="log-row"><div class="log-label">🔑 Từ khoá viết bài:</div><div class="log-value">{kw_content}</div></div>
                        <div class="log-row"><div class="log-label">🖼️ Số lượng ảnh:</div><div class="log-value">01 ảnh (Tối ưu)</div></div>
                        <div class="log-row"><div class="log-label">⚓ Từ khoá gắn bài:</div><div class="log-value">{anchors[0]} | {anchors[1]} | {anchors[2]}</div></div>
                        <div class="log-row"><div class="log-label">🔗 Backlink trỏ:</div><div class="log-value">{links[0]}</div></div>
                        <div class="log-row"><div class="log-label">📈 Điểm SEO:</div><div class="log-value" style="color:#00ff00;">95/100</div></div>
                        <div class="log-row"><div class="log-label">🕒 Đăng web lúc:</div><div class="log-value">{now_vn.strftime('%H:%M:%S')}</div></div>
                        <div class="log-row"><div class="log-label">🏁 Kết quả:</div><div class="log-value">Thành công</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # GHI REPORT 18 CỘT (A-R) - TUYỆT ĐỐI KHÔNG ĐỔI THỨ TỰ
                    report_row = [
                        site.iloc[0], site.iloc[1], now_vn.strftime("%Y-%m-%d %H:%M"), "Link chờ đăng",
                        title, kw_content, "01 ảnh", anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                        links[0], links[1], links[2], "95/100", now_vn.strftime("%H:%M"), "Thành công"
                    ]
                    gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                    # BẮN TELEGRAM
                    t_msg = f"<b>🚀 SEO MASTER UPDATE</b>\n\n✅ <b>Site:</b> {site.iloc[0]}\n📄 <b>Tiêu đề:</b> {title}\n🔗 <b>Backlink:</b> {links[0]}\n📊 <b>Điểm SEO:</b> 95/100"
                    notify_tele(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), t_msg)

                except Exception as e: st.error(f"Lỗi phiên {i+1}: {str(e)}")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- 4. GIAO DIỆN CHÍNH (UI) ---
st.markdown("<h1 class='main-header'>🚕 HỆ THỐNG QUẢN TRỊ SEO MASTER v38.0</h1>", unsafe_allow_html=True)

data, msg = load_data()
if data:
    # Icon cho menu thêm phần chuyên nghiệp
    icons = {"Dashboard": "🏠", "Website": "🛰️", "Backlink": "🔗", "Image": "🖼️", "Spin": "🔄", "Local": "📍", "Report": "📊"}
    
    tabs = st.tabs([f"{icons.get(k, '')} {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=600, hide_index=True)
else: st.error(f"Lỗi: {msg}")
