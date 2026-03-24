import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re
from datetime import datetime, timedelta, timezone

# --- 1. CONFIG UI ---
st.set_page_config(page_title="SEO MASTER v45.0", layout="wide")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=10)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        tabs = ["Dashboard", "Website", "Backlink", "Report"]
        return {t: pd.DataFrame(sh.worksheet(t).get_all_values()) for t in tabs}, "OK"
    except Exception as e: return None, str(e)

# --- 2. ENGINE VẬN HÀNH (KHÔNG NGÁO) ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH CHUẨN", width="large")
def run_robot(data):
    df_d = pd.DataFrame(data['Dashboard'][1:], columns=data['Dashboard'][0])
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    genai.configure(api_key=v('GEMINI_API_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Dữ liệu Website (11 cột) & Backlink (Cột A: Link, Cột B: Anchor)
    df_web = pd.DataFrame(data['Website'][1:], columns=data['Website'][0])
    active_sites = df_web[df_web.iloc[:, 10].str.contains('Active', case=False, na=False)]
    
    df_bl = pd.DataFrame(data['Backlink'][1:], columns=data['Backlink'][0])
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # BỐC DỮ LIỆU BACKLINK CHUẨN: Link (Cột A - r[0]), Anchor (Cột B - r[1])
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5  # Từ khoá 1-5
        backlinks = [str(r[0]) for r in bl_pool] + [""]*3 # Backlink 1-3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                # ÉP AI KHÔNG CHÀO HỎI - CHỈ VIẾT NỘI DUNG
                prompt = (
                    f"SYSTEM: Bạn là chuyên gia viết bài SEO. TUYỆT ĐỐI KHÔNG chào hỏi, không 'Chào Sếp', không dẫn nhập.\n"
                    f"Bắt đầu ngay lập tức bằng Tiêu đề H1 chứa từ khóa chính.\n"
                    f"TỪ KHÓA: {v('Danh sách Keyword bài viết')}\n"
                    f"YÊU CẦU: Viết bài dài, sâu sắc, chèn link {backlinks[0]} vào từ {anchors[0]}.\n"
                    f"PROMPT: {v('PROMPT_TEMPLATE')}"
                )
                
                resp = model.generate_content(prompt)
                full_text = resp.text
                
                # Làm sạch tiêu đề (Xóa dấu #, *, chào hỏi dư thừa)
                lines = [l.strip() for l in full_text.split('\n') if l.strip() and "Chào" not in l[:10]]
                title = lines[0].replace('#', '').replace('*', '') if lines else "Tiêu đề lỗi"

                # Chấm điểm SEO (Thực tế hơn)
                kw_main = v('Danh sách Keyword bài viết').split(',')[0].lower()
                score = 95 if kw_main in title.lower() else 65

                # 1. POPUP LOG (Đúng như bồ muốn)
                st.write(f"✅ **Xong bài {i+1}**")
                st.write(f"- Website: {site.iloc[0]}")
                st.write(f"- Tiêu đề: {title}")
                st.write(f"- Anchor 1: {anchors[0]} | Link 1: {backlinks[0]}")

                # 2. GHI REPORT 18 CỘT (Khớp image_f3f0c8)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", title, 
                    v('Danh sách Keyword bài viết'), site.iloc[9], # G: Số ảnh
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4], # H-L: Từ khoá 1-5
                    backlinks[0], backlinks[1], backlinks[2], # M-O: Backlink 1-3
                    f"{score}/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # 3. BẮN TELEGRAM (Đúng thông tin)
                tele_msg = (
                    f"<b>✅ SEO DONE: {site.iloc[0]}</b>\n"
                    f"📄 <b>Tiêu đề:</b> {title}\n"
                    f"⚓ <b>Anchor:</b> {anchors[0]}\n"
                    f"🔗 <b>Backlink:</b> {backlinks[0]}\n"
                    f"🕒 <b>Thời gian:</b> {now_str}"
                )
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tele_msg, "parse_mode": "HTML"})

            except Exception as e: st.error(f"Lỗi: {str(e)}")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- 3. UI CHÍNH ---
st.title("🚀 SEO MASTER v45.0 - FINAL")
data, msg = load_data()
if data:
    tab_list = ["Dashboard", "Website", "Backlink", "Report"]
    tabs = st.tabs(tab_list)
    for i, name in enumerate(tab_list):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
                st.dataframe(pd.DataFrame(data[name][1:], columns=data[name][0]), use_container_width=True, hide_index=True)
            else:
                st.dataframe(pd.DataFrame(data[name][1:], columns=data[name][0]), use_container_width=True, height=500, hide_index=True)
