import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH CƠ BẢN ---
st.set_page_config(page_title="SEO MASTER v50", layout="wide")

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
            if len(vals) < 1: res[t] = pd.DataFrame()
            else: res[t] = pd.DataFrame(vals[1:], columns=vals[0]).fillna('')
        return res, "OK"
    except Exception as e: return None, str(e)

# --- TRÌNH CHẠY ROBOT ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    # FIX LỖI 404 (Triệt để): Thử cấu hình theo chuẩn mới nhất
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        # Không dùng tiền tố models/ để tránh lỗi 404 trên một số vùng
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Bạn là máy viết bài SEO. KHÔNG chào hỏi. KHÔNG 'Chào sếp'. Bắt đầu bằng tiêu đề H1 ngay."
        )
    except Exception as e: st.error(f"Lỗi khởi tạo AI: {e}"); return

    # Lấy danh sách Web Active (Cột K - Index 10)
    df_web = data['Website']
    active_sites = df_web[df_web.iloc[:, 10].str.contains('Active', case=False, na=False)]
    
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc Backlink: Cột A (0) là Link, Cột B (1) là Anchor
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        target_links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                # ÉP AI VIẾT NỘI DUNG (DIỆT CHÀO SẾP)
                prompt = f"Viết bài về: {v('PROMPT_TEMPLATE')}. Từ khóa: {v('Danh sách Keyword bài viết')}. Chèn link {target_links[0]} vào từ {anchors[0]}."
                resp = model.generate_content(prompt)
                
                # Làm sạch tiêu đề
                lines = [l.strip() for l in resp.text.split('\n') if l.strip()]
                title = "Tiêu đề chưa tối ưu"
                for line in lines:
                    clean = line.replace('#', '').replace('*', '').strip()
                    if not any(x in clean.lower()[:12] for x in ["chào", "kính chào", "hello", "hi "]):
                        title = clean; break

                # GHI REPORT 18 CỘT (Đúng index từ A-R)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", 
                    title, v('Danh sách Keyword bài viết'), site.iloc[9], # G: Số ảnh
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4], # H-L: Anchor
                    target_links[0], target_links[1], target_links[2], # M-O: Link
                    "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # BẮN TELEGRAM
                msg = f"✅ <b>{site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {target_links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Đã xong: {title[:50]}...")

            except Exception as e:
                if "429" in str(e): st.warning("Chờ 30s do hết Quota..."); time.sleep(30)
                else: st.error(f"Lỗi: {e}")
        time.sleep(1)

    st.success("Xong chiến dịch!")
    if st.button("Xác nhận và Đóng"): st.rerun()

# --- GIAO DIỆN ---
st.title("🚀 SEO MASTER v50.0")
data, msg = load_data()
if data:
    tabs = st.tabs(["Dashboard", "Website", "Backlink", "Report"])
    with tabs[0]:
        if st.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
        st.dataframe(data["Dashboard"], use_container_width=True, hide_index=True)
    with tabs[1]: st.dataframe(data["Website"], use_container_width=True, hide_index=True)
    with tabs[2]: st.dataframe(data["Backlink"], use_container_width=True, hide_index=True)
    with tabs[3]: st.dataframe(data["Report"], use_container_width=True, hide_index=True)
