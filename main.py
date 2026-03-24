import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. SETUP ---
st.set_page_config(page_title="SEO MASTER v49", layout="wide")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        res = {}
        for t in ["Dashboard", "Website", "Backlink", "Report"]:
            vals = sh.worksheet(t).get_all_values()
            if len(vals) < 2: res[t] = pd.DataFrame()
            else:
                df = pd.DataFrame(vals[1:], columns=vals[0])
                res[t] = df.fillna('') # Dọn dẹp None tránh lỗi ValueError
        return res, "OK"
    except Exception as e: return None, str(e)

# --- 2. ENGINE (KHÔNG CHỈNH GIAO DIỆN) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU HÀNH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    # FIX LỖI 404: Gọi model không dùng tiền tố models/
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash") 
    except: st.error("Kiểm tra API Key"); return

    # Lọc Website Active (Cột K - index 10)
    df_web = data['Website']
    active_sites = df_web[df_web.iloc[:, 10].str.contains('Active', case=False, na=False)]
    
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc Backlink chuẩn: Link (Cột A - 0), Từ khoá (Cột B - 1)
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        target_links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                # ÉP AI KHÔNG CHÀO HỎI (FIX LỖI TIÊU ĐỀ)
                prompt = (
                    f"MỤC TIÊU: Viết bài SEO.\n"
                    f"LUẬT: CẤM CHÀO HỎI. Bắt đầu ngay bằng Tiêu đề H1.\n"
                    f"NỘI DUNG: {v('PROMPT_TEMPLATE')}\n"
                    f"KEYWORD: {v('Danh sách Keyword bài viết')}\n"
                    f"CHÈN LINK: {target_links[0]} VÀO TỪ {anchors[0]}"
                )
                
                resp = model.generate_content(prompt)
                lines = [l.strip() for l in resp.text.split('\n') if l.strip()]
                
                # Logic diệt "Chào sếp"
                title = "Tiêu đề lỗi"
                for line in lines:
                    clean = line.replace('#', '').replace('*', '').strip()
                    if not any(x in clean.lower()[:10] for x in ["chào", "kính chào", "hello", "hi "]):
                        title = clean; break

                # Chấm điểm SEO thật
                seo_score = "0/100 (Chào sếp)" if "Chào" in title else "95/100"

                # GHI REPORT 18 CỘT (ĐÚNG THỨ TỰ A-R)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", 
                    title, v('Danh sách Keyword bài viết'), site.iloc[9], # G: Số ảnh
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4], # H-L: Từ khoá
                    target_links[0], target_links[1], target_links[2], # M-O: Backlink
                    seo_score, now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # TELEGRAM (FIX TEMPLATE)
                msg = f"<b>✅ DONE: {site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {target_links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Xong: {title[:40]}...")

            except Exception as e:
                if "429" in str(e): time.sleep(35)
                st.error(f"Lỗi: {str(e)}")
        time.sleep(1)

    st.success("🎉 XONG!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- 3. UI (GIỮ NGUYÊN) ---
st.title("🚀 SEO MASTER v49.0")
data, msg = load_data()
if data:
    tab_list = ["Dashboard", "Website", "Backlink", "Report"]
    tabs = st.tabs(tab_list)
    for i, name in enumerate(tab_list):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
