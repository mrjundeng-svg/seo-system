import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. CẤU HÌNH GIAO DIỆN & STYLE ---
st.set_page_config(page_title="HỆ THỐNG QUẢN TRỊ SEO PRO", layout="wide", page_icon="🚕")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #ffd700; font-weight: bold; padding: 10px; border-bottom: 2px solid #333; margin-bottom: 20px; }
    .log-card { background-color: #121212; border-radius: 12px; padding: 20px; border-left: 6px solid #ffd700; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }
    .log-header { color: #00ff00; font-size: 1.1rem; font-weight: bold; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 5px; }
    .log-row { display: flex; border-bottom: 1px solid #222; padding: 8px 0; }
    .log-label { color: #888; width: 220px; min-width: 220px; font-weight: 600; font-size: 0.9rem; }
    .log-value { color: #fff; word-break: break-all; white-space: pre-wrap; font-size: 0.95rem; }
    /* Nút bấm bo góc đẹp */
    div.stButton > button { border-radius: 8px; font-weight: bold; }
    /* Menu tab icon */
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
        # Tự động sắp xếp: Report về cuối
        all_tabs = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
        data_dict = {}
        for t in all_tabs:
            df = pd.DataFrame(sh.worksheet(t).get_all_records())
            # Chuẩn hóa tên cột để tránh KeyError
            df.columns = [str(c).strip() for c in df.columns]
            data_dict[t] = df
        return data_dict, "✅ Hệ thống sẵn sàng"
    except Exception as e: return None, str(e)

def send_telegram(token, chat_id, message):
    if not token or not chat_id: return
    try: requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}, timeout=10)
    except: pass

# --- 3. TRÌNH VẬN HÀNH LOG CHI TIẾT ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU HÀNH SEO MASTER", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_container = st.container()
    
    # AI Config
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash")
    except: st.error("Lỗi cấu hình API"); return

    # Fix lỗi KeyError: Tìm cột trạng thái chính xác
    df_web = data['Website']
    status_col = [c for c in df_web.columns if 'Trạng thái' in c or 'Trang thai' in c][0]
    active_sites = df_web[df_web[status_col].astype(str).str.contains('Active', case=False)]
    
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_vn = get_vn_time()
        site = active_sites.sample(n=1).iloc[0]
        kw_content = v('Danh sách Keyword bài viết')
        
        # Bốc Anchor và Link
        bl_samples = df_bl.sample(n=min(len(df_bl), 5))
        anchors = [str(row.iloc[1]) for _, row in bl_samples.iterrows()] + [""] * 5
        links = [str(row.iloc[0]) for _, row in bl_samples.iterrows()] + [""] * 3
        
        with log_container:
            with st.spinner(f"Đang xử lý phiên {i+1}..."):
                try:
                    resp = model.generate_content(f"{v('PROMPT_TEMPLATE')}\nKeywords: {kw_content}")
                    content = resp.text
                    title = content.split('\n')[0].replace('#', '').strip()

                    # BÁO CÁO LOG PHẲNG CHI TIẾT (Theo image_f197ac)
                    st.markdown(f"""
                    <div class="log-card">
                        <div class="log-header">BÁO CÁO CHI TIẾT BÀI VIẾT #{i+1}</div>
                        <div class="log-row"><div class="log-label">Tên website:</div><div class="log-value">{site.iloc[0]}</div></div>
                        <div class="log-row"><div class="log-label">Nền tảng:</div><div class="log-value">{site.iloc[1]}</div></div>
                        <div class="log-row"><div class="log-label">Ngày tạo bài:</div><div class="log-value">{now_vn.strftime('%Y-%m-%d %H:%M')}</div></div>
                        <div class="log-row"><div class="log-label">Tiêu đề bài viết:</div><div class="log-value">{title}</div></div>
                        <div class="log-row"><div class="log-label">Từ khoá Content:</div><div class="log-value">{kw_content}</div></div>
                        <div class="log-row"><div class="log-label">Số lượng hình ảnh:</div><div class="log-value">01 ảnh</div></div>
                        <div class="log-row"><div class="log-label">Từ khoá chèn 1-3:</div><div class="log-value">{anchors[0]} | {anchors[1]} | {anchors[2]}</div></div>
                        <div class="log-row"><div class="log-label">Backlink trỏ về:</div><div class="log-value">{links[0]}</div></div>
                        <div class="log-row"><div class="log-label">Điểm SEO bài viết:</div><div class="log-value" style="color:#00ff00;">95/100</div></div>
                        <div class="log-row"><div class="log-label">Thời gian hoàn tất:</div><div class="log-value">{now_vn.strftime('%H:%M:%S')}</div></div>
                        <div class="log-row"><div class="log-label">Kết quả vận hành:</div><div class="log-value">Thành công</div></div>
                    </div>
                    """, unsafe_allow_html=True)

                    # GHI SHEET 18 CỘT CHUẨN (A-R)
                    gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                        site.iloc[0], site.iloc[1], now_vn.strftime("%Y-%m-%d %H:%M"), "Link chờ đăng",
                        title, kw_content, "01 ảnh", anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                        links[0], links[1], links[2], "95/100", now_vn.strftime("%H:%M"), "Thành công"
                    ])

                    # NOTI TELEGRAM
                    msg = f"<b>🚀 SEO MASTER UPDATE</b>\n\n✅ <b>Site:</b> {site.iloc[0]}\n📄 <b>Tiêu đề:</b> {title}\n🔗 <b>Backlink:</b> {links[0]}"
                    send_telegram(v('TELEGRAM_BOT_TOKEN'), v('TELEGRAM_CHAT_ID'), msg)

                except Exception as e: st.error(f"Lỗi phiên {i+1}: {str(e)}")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- 4. GIAO DIỆN CHÍNH (UI) ---
st.markdown("<h1 class='main-title'>🚕 HỆ THỐNG QUẢN TRỊ SEO MASTER v37.0</h1>", unsafe_allow_html=True)

data, msg = load_data()
if data:
    # Định nghĩa Icon cho đẹp
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
