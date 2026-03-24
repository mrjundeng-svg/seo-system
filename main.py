import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. GIAO DIỆN HỆ THỐNG ---
st.set_page_config(page_title="SEO MASTER PRO v42", layout="wide", page_icon="🚕")

st.markdown("""
    <style>
    .report-card { background: #1a1c24; border-radius: 12px; padding: 20px; border-left: 6px solid #ffd700; margin-bottom: 20px; }
    .data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; border-top: 1px solid #333; pt: 10px; mt: 10px; }
    .data-item { font-size: 0.9rem; }
    .label { color: #888; font-weight: bold; }
    .value { color: #fff; word-break: break-all; }
    /* Chống cuộn ngang */
    .stMarkdown, p, div { word-wrap: break-word !important; white-space: pre-wrap !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. HÀM HỖ TRỢ ---
def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

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
        order = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
        res = {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in order}
        for k in res: res[k].columns = [str(c).strip() for c in res[k].columns]
        return res, "✅ Hệ thống sẵn sàng"
    except Exception as e: return None, str(e)

# --- 3. ENGINE VẬN HÀNH (FIX 404 & 429) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU HÀNH SEO v42", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_area = st.container()
    
    # Khởi tạo AI - Tự động dò Model sống để né 404
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in available_models else available_models[0]
        model_ai = genai.GenerativeModel(target_model.replace("models/", ""))
    except: st.error("Lỗi API Key"); return

    # Lọc vệ tinh Active (11 cột chuẩn)
    df_web = data['Website']
    active_sites = df_web[df_web.iloc[:, 10].astype(str).str.contains('Active', case=False)]
    
    df_bl = data['Backlink']
    num_to_gen = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_to_gen):
        if active_sites.empty: st.error("Hết website Active!"); break
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc ngẫu nhiên 5 Anchor & 3 Link cho Report 18 cột
        bl_samples = df_bl.sample(n=min(len(df_bl), 5))
        anchors = [str(row.iloc[1]) for _, row in bl_samples.iterrows()] + [""]*5
        links = [str(row.iloc[0]) for _, row in bl_samples.iterrows()] + [""]*3

        with log_area:
            with st.spinner(f"Đang xử lý bài {i+1}..."):
                success = False
                while not success:
                    try:
                        prompt = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\nGiới hạn ảnh: {site.iloc[9]}"
                        resp = model_ai.generate_content(prompt)
                        title = resp.text.split('\n')[0].replace('#', '').strip()
                        
                        now_vn = get_vn_time()
                        # LOG Card View (Phẳng - Chống cuộn)
                        st.markdown(f"""
                        <div class="report-card">
                            <div style="color:#ffd700; font-weight:bold;">📄 BÀI VIẾT #{i+1} - HOÀN TẤT</div>
                            <div class="data-grid">
                                <div class="data-item"><span class="label">Website:</span> <span class="value">{site.iloc[0]}</span></div>
                                <div class="data-item"><span class="label">Nền tảng:</span> <span class="value">{site.iloc[1]}</span></div>
                                <div class="data-item"><span class="label">Tiêu đề:</span> <span class="value">{title[:60]}...</span></div>
                                <div class="data-item"><span class="label">Mục tiêu:</span> <span class="value">{site.iloc[5]}</span></div>
                                <div class="data-item"><span class="label">Anchor 1:</span> <span class="value">{anchors[0]}</span></div>
                                <div class="data-item"><span class="label">Link 1:</span> <span class="value">{links[0]}</span></div>
                                <div class="data-item"><span class="label">Hình ảnh:</span> <span class="value">{site.iloc[9]} ảnh</span></div>
                                <div class="data-item"><span class="label">Thời gian:</span> <span class="value">{now_vn.strftime('%H:%M:%S')}</span></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # GHI SHEET 18 CỘT (Khớp image_f197ac)
                        gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                            site.iloc[0], site.iloc[1], now_vn.strftime("%Y-%m-%d %H:%M"), "Chờ đăng",
                            title, v('Danh sách Keyword bài viết'), f"{site.iloc[9]} ảnh", 
                            anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                            links[0], links[1], links[2], "95/100", now_vn.strftime("%H:%M"), "Thành công"
                        ])
                        
                        # Telegram Noti
                        t_msg = f"<b>✅ SEO DONE: {site.iloc[0]}</b>\n📄 {title}\n🔗 {links[0]}"
                        requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": t_msg, "parse_mode": "HTML"})
                        
                        success = True
                    except Exception as e:
                        if "429" in str(e):
                            st.warning("⏳ Chạm giới hạn API. Robot nghỉ 30 giây..."); time.sleep(32)
                        else: st.error(f"Lỗi: {str(e)}"); break
        time.sleep(1)
    st.success("🎉 CHIẾN DỊCH KẾT THÚC!")

# --- 4. GIAO DIỆN CHÍNH ---
st.markdown("<h2 style='text-align:center; color:#ffd700;'>HỆ THỐNG SEO MASTER v42.0</h2>", unsafe_allow_html=True)
data, msg = load_data()
if data:
    icons = {"Dashboard": "🏠", "Website": "🛰️", "Backlink": "🔗", "Image": "🖼️", "Spin": "🔄", "Local": "📍", "Report": "📊"}
    tabs = st.tabs([f"{icons.get(k, '')} {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
                if c2.button("🔄 LÀM MỚI"): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=550, hide_index=True)
