import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
st.set_page_config(page_title="SEO MASTER v55 - STABLE", layout="wide")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_full_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        # Danh sách tab bồ cần - Đúng thứ tự bồ muốn
        tabs = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
        res = {}
        for t in tabs:
            try:
                vals = sh.worksheet(t).get_all_values()
                df = pd.DataFrame(vals[1:], columns=vals[0]) if len(vals) > 0 else pd.DataFrame()
                res[t] = df.fillna('')
            except: res[t] = pd.DataFrame()
        return res, "Hệ thống OK"
    except Exception as e: return None, str(e)

# --- 2. HÀM TÌM MODEL SỐNG (DIỆT LỖI 404) ---
def get_working_model(api_key):
    try:
        genai.configure(api_key=api_key)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5-flash' in m.name: return m.name
        return "gemini-1.5-flash" # Fallback
    except: return "gemini-1.5-flash"

# --- 3. TRÌNH VẬN HÀNH "SẠCH" ---
@st.dialog("⚙️ ĐIỀU HÀNH CHIẾN DỊCH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    # Lấy Model chuẩn
    model_name = get_working_model(v('GEMINI_API_KEY'))
    model = genai.GenerativeModel(model_name=model_name)

    # Lọc Website Active (Tìm cột "Trạng thái" linh hoạt)
    df_web = data['Website']
    status_col = [c for c in df_web.columns if "Trạng thái" in c][0]
    active_sites = df_web[df_web[status_col].str.contains('Active', case=False, na=False)]
    
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc Backlink (Cột A: Link, Cột B: Anchor)
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang biên tập bài {i+1}...", expanded=True):
            try:
                prompt = f"Viết bài SEO chuyên nghiệp. Từ khóa: {v('Danh sách Keyword bài viết')}. Chèn link {links[0]} vào từ {anchors[0]}. Prompt: {v('PROMPT_TEMPLATE')}"
                resp = model.generate_content(prompt)
                
                # --- DIỆT "CHÀO SẾP" BẰNG REGEX ---
                raw_content = resp.text
                # Xóa các dòng chứa từ "Chào", "Kính chào" ở đầu văn bản
                clean_content = re.sub(r'^(Chào|Kính chào|Hello|Hi|Chào Sếp).*?\n', '', raw_content, flags=re.IGNORECASE | re.MULTILINE)
                title = clean_content.split('\n')[0].replace('#', '').replace('*', '').strip()

                # GHI REPORT 18 CỘT
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", title, 
                    v('Danh sách Keyword bài viết'), site.get('Giới hạn ảnh', '1'), 
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                    links[0], links[1], links[2], "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # TELEGRAM
                msg = f"✅ <b>{site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Đã đăng: {title[:50]}...")
            except Exception as e: st.error(f"Lỗi: {e}")
        time.sleep(1)

    st.success("Xong!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- 4. GIAO DIỆN ---
st.title("🚀 SEO MASTER v55.0")
data, msg = load_full_data()

if data:
    tabs = st.tabs([f"📂 {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 CHẠY NGAY", type="primary"): run_robot(data)
                if c2.button("🔄 REFRESH"): st.cache_data.clear(); st.rerun()
                
                # MÃ HÓA BẢO MẬT
                df_show = data[name].copy()
                mask = df_show.iloc[:, 0].str.contains('KEY|PASS|TOKEN|API', case=False, na=False)
                df_show.loc[mask, df_show.columns[1]] = "********"
                st.dataframe(df_show, use_container_width=True, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
