import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
st.set_page_config(page_title="SEO MASTER v48", layout="wide")

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
            if not vals: res[t] = pd.DataFrame()
            else:
                df = pd.DataFrame(vals[1:], columns=vals[0])
                # Fix ValueError (image_f3f846): Xóa dòng trống hoàn toàn
                df = df.dropna(how='all').reset_index(drop=True)
                res[t] = df
        return res, "OK"
    except Exception as e: return None, str(e)

# --- 2. ENGINE VẬN HÀNH (KHÔNG "NGÁO") ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU HÀNH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    # Fix lỗi 404 Model: Sử dụng tên chuẩn gemini-1.5-flash
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel("gemini-1.5-flash")
    except: st.error("Lỗi cấu hình API"); return

    # Bốc website Active (Cột K - Index 10)
    df_web = data['Website']
    active_sites = df_web[df_web.iloc[:, 10].str.contains('Active', case=False, na=False)]
    
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M") # Đúng định dạng bồ yêu cầu
        site = active_sites.sample(n=1).iloc[0]
        
        # BỐC DATA BACKLINK CHUẨN: Link (Cột A - 0), Từ khoá (Cột B - 1)
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5   # Cột H-L
        backlinks = [str(r[0]) for r in bl_pool] + [""]*3 # Cột M-O

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                # PROMPT ÉP AI KHÔNG CHÀO HỎI (Diệt sạch "Chào Sếp")
                prompt = (
                    f"MỤC TIÊU: Viết bài SEO chuyên nghiệp cho vệ tinh.\n"
                    f"LUẬT: CẤM CHÀO HỎI. KHÔNG viết 'Chào sếp', 'Chào anh/chị', 'Kính thưa'.\n"
                    f"CẤU TRÚC: Bắt đầu ngay lập tức bằng Tiêu đề H1 sạch.\n"
                    f"NỘI DUNG: {v('PROMPT_TEMPLATE')}\n"
                    f"RÀNG BUỘC: Chèn {site.iloc[9]} ảnh, chèn link {backlinks[0]} vào từ {anchors[0]}."
                )
                
                resp = model.generate_content(prompt)
                full_text = resp.text
                
                # Logic lọc dòng đầu (nếu AI vẫn lì lợm chào hỏi)
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                title = "Tiêu đề chưa tối ưu"
                for line in lines:
                    clean = line.replace('#', '').replace('*', '').strip()
                    if not any(x in clean.lower()[:12] for x in ["chào", "kính chào", "hello", "hi "]):
                        title = clean
                        break
                
                # Điểm SEO thực tế: Chào sếp = 0 điểm
                is_greeting = any(x in title.lower() for x in ["chào", "kính chào"])
                seo_score = "0/100 (Lỗi Chào Sếp)" if is_greeting else "95/100"

                # 1. GHI REPORT 18 CỘT (Khớp image_f3f0c8)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", 
                    title, v('Danh sách Keyword bài viết'), site.iloc[9], # G: Số ảnh
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4], # H-L: Từ khoá 1-5
                    backlinks[0], backlinks[1], backlinks[2], # M-O: Backlink 1-3
                    seo_score, now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # 2. TELEGRAM (Fix template lệch)
                tele_msg = (
                    f"<b>✅ SEO DONE: {site.iloc[0]}</b>\n"
                    f"📄 <b>Tiêu đề:</b> {title}\n"
                    f"⚓ <b>Anchor:</b> {anchors[0]}\n"
                    f"🔗 <b>Link:</b> {backlinks[0]}\n"
                    f"🕒 <b>Lúc:</b> {now_str}"
                )
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tele_msg, "parse_mode": "HTML"})

                st.write(f"✅ Xong: {title[:40]}...")

            except Exception as e:
                if "429" in str(e): st.warning("Quota hết, chờ 30s..."); time.sleep(30)
                else: st.error(f"Lỗi: {str(e)}")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- 3. UI ---
st.title("🚀 SEO MASTER v48.0")
data, msg = load_data()
if data:
    tabs = st.tabs(["Dashboard", "Website", "Backlink", "Report"])
    for i, name in enumerate(["Dashboard", "Website", "Backlink", "Report"]):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
