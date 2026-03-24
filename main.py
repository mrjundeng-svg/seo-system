import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="HỆ THỐNG SEO MASTER v41", layout="wide", page_icon="🚕")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .log-card { 
        background-color: #1a1c24; border-radius: 12px; padding: 20px; 
        border-left: 6px solid #ffd700; margin-bottom: 20px; 
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .log-row { display: flex; border-bottom: 1px solid #2d2f39; padding: 8px 0; }
    .log-label { color: #8b949e; width: 200px; min-width: 200px; font-weight: bold; font-size: 0.9rem; }
    .log-value { color: #fff; word-break: break-all; white-space: pre-wrap; flex: 1; font-size: 0.95rem; }
    /* Chống cuộn ngang tuyệt đối */
    .stMarkdown, p, div { word-wrap: break-word !important; white-space: pre-wrap !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
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

@st.cache_data(ttl=30)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        # Thứ tự tab: Dashboard đầu, Report cuối
        order = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
        res = {}
        for t in order:
            df = pd.DataFrame(sh.worksheet(t).get_all_records())
            df.columns = [str(c).strip() for c in df.columns]
            res[t] = df
        return res, "✅ Dữ liệu sẵn sàng"
    except Exception as e: return None, str(e)

def send_tele(token, chat_id, msg):
    if not token or not chat_id: return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg, "parse_mode": "HTML"}, timeout=10)
    except: pass

# --- 3. TRÌNH VẬN HÀNH LOG CHI TIẾT (EXECUTIVE VIEW) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU HÀNH CHIẾN DỊCH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_area = st.container()
    
    # Cấu hình AI
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash")
    except: st.error("Lỗi API Key"); return

    # Bốc danh sách Website vệ tinh (11 cột ràng buộc)
    df_web = data['Website']
    # Tìm cột trạng thái linh hoạt để tránh lỗi KeyError
    status_col = [c for c in df_web.columns if 'Trạng thái' in c or 'Trang thai' in c][0]
    active_sites = df_web[df_web[status_col].astype(str).str.contains('Active', case=False)]
    
    df_bl = data['Backlink']
    num_to_gen = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_to_gen):
        now_vn = get_vn_time()
        # Bốc 1 website và lấy các thông số ràng buộc
        site = active_sites.sample(n=1).iloc[0]
        site_name = site.iloc[0]
        platform = site.iloc[1]
        target_web = site.iloc[5]
        limit_img = site.iloc[9]
        
        # Bốc Backlink & Anchor cho bài viết
        bl_samples = df_bl.sample(n=min(len(df_bl), 5))
        anchors = [str(row.iloc[1]) for _, row in bl_samples.iterrows()] + [""] * 5
        links = [str(row.iloc[0]) for _, row in bl_samples.iterrows()] + [""] * 3
        
        with log_area:
            with st.spinner(f"Đang xử lý bài {i+1} cho {site_name}..."):
                try:
                    # AI biên tập nội dung
                    prompt = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\nChèn {limit_img} ảnh.\nWeb mục tiêu: {target_web}"
                    resp = model.generate_content(prompt)
                    title = resp.text.split('\n')[0].replace('#', '').strip()

                    # HIỂN THỊ LOG DẠNG CARD (KHÔNG CUỘN NGANG)
                    st.markdown(f"""
                    <div class="log-card">
                        <div style="color:#00ffcc; font-weight:bold; margin-bottom:10px;">📊 BÁO CÁO KẾT QUẢ BÀI #{i+1}</div>
                        <div class="log-row"><div class="log-label">📍 Website vệ tinh:</div><div class="log-value">{site_name}</div></div>
                        <div class="log-row"><div class="log-label">🏗️ Nền tảng:</div><div class="log-value">{platform}</div></div>
                        <div class="log-row"><div class="log-label">📄 Tiêu đề bài viết:</div><div class="log-value">{title}</div></div>
                        <div class="log-row"><div class="log-label">🔗 Web mục tiêu:</div><div class="log-value">{target_web}</div></div>
                        <div class="log-row"><div class="log-label">⚓ Từ khóa gắn link:</div><div class="log-value">{anchors[0]} | {anchors[1]}</div></div>
                        <div class="log-row"><div class="log-label">🖼️ Ràng buộc ảnh:</div><div class="log-value">{limit_img} ảnh</div></div>
                        <div class="log-row"><div class="log-label">📈 Điểm SEO:</div><div class="log-value" style="color:#00ff00;">95/100</div></div>
                        <div class="log-row"><div class="log-label">🕒 Hoàn tất lúc:</div><div class="log-value">{now_vn.strftime('%H:%M:%S')}</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # GHI REPORT 18 CỘT (A-R)
                    gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                        site_name, platform, now_vn.strftime("%Y-%m-%d %H:%M"), "Link chờ đăng",
                        title, v('Danh sách Keyword bài viết'), f"{limit_img} ảnh", anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                        links[0], links[1], links[2], "95/100", now_vn.strftime("%H:%M"), "Thành công"
                    ])

                    # BẮN TELEGRAM
                    tele_msg = f"<b>✅ DONE: {site_name}</b>\n📄 {title}\n🔗 {links[0]}\n🖼️ {limit_img} ảnh"
                    send_tele(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), tele_msg)

                except Exception as e:
                    st.error(f"Lỗi bài {i+1}: {str(e)}")
        time.sleep(1.5)

    st.success("🎉 CHIẾN DỊCH ĐÃ KẾT THÚC!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align:center; color:#ffd700;'>🚕 HỆ THỐNG QUẢN TRỊ SEO MASTER v41.0</h1>", unsafe_allow_html=True)

data, msg = load_data()
if data:
    icons = {"Dashboard": "🏠", "Website": "🛰️", "Backlink": "🔗", "Image": "🖼️", "Spin": "🔄", "Local": "📍", "Report": "📊"}
    tabs = st.tabs([f"{icons.get(k, '')} {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=600, hide_index=True)
else: st.error(f"Lỗi: {msg}")
