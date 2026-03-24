import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="SEO MASTER v47.0", layout="wide")

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
                # Dọn dẹp dòng trống để tránh lỗi ValueError (image_f3f846)
                df = df.dropna(how='all').reset_index(drop=True)
                res[t] = df
        return res, "OK"
    except Exception as e: return None, str(e)

# --- 2. TRÌNH VẬN HÀNH (THIẾT QUÂN LUẬT) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU HÀNH CHIẾN DỊCH", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    # Fix lỗi 404 Model (image_fdd6c7): Sử dụng model chuẩn
    genai.configure(api_key=v('GEMINI_API_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Bốc website Active (Cột K - Index 10)
    active_sites = data['Website'][data['Website'].iloc[:, 10].str.contains('Active', case=False, na=False)]
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M") # Fix định dạng Năm-Tháng-Ngày (Cột C, Q)
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc ngẫu nhiên Backlink: Link (Cột A - r[0]), Anchor (Cột B - r[1])
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5   # Cho cột H-L
        backlinks = [str(r[0]) for r in bl_pool] + [""]*3 # Cho cột M-O

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                # PROMPT SIÊU NGHIÊM NGẶT ĐỂ DIỆT "CHÀO SẾP"
                prompt = (
                    f"MỤC TIÊU: Viết bài SEO chất lượng cao.\n"
                    f"LUẬT: TUYỆT ĐỐI KHÔNG CHÀO HỎI. KHÔNG viết 'Chào sếp', 'Chào anh chị'.\n"
                    f"CẤU TRÚC: Bắt đầu ngay bằng Tiêu đề H1 (không chứa ký tự đặc biệt như #, *).\n"
                    f"NỘI DUNG: {v('PROMPT_TEMPLATE')}\n"
                    f"TỪ KHÓA CHÍNH: {v('Danh sách Keyword bài viết')}\n"
                    f"YÊU CẦU: Chèn {site.iloc[9]} ảnh, chèn link {backlinks[0]} vào từ {anchors[0]}."
                )
                
                resp = model.generate_content(prompt)
                lines = [l.strip() for l in resp.text.split('\n') if l.strip()]
                
                # Logic lọc tiêu đề sạch (image_f3e8e3)
                title = "Tiêu đề chưa tối ưu"
                for line in lines:
                    clean = line.replace('#', '').replace('*', '').strip()
                    if not any(x in clean.lower()[:10] for x in ["chào", "kính chào", "hello"]):
                        title = clean
                        break
                
                # Chấm điểm SEO thực tế
                kw_main = v('Danh sách Keyword bài viết').split(',')[0].lower()
                seo_score = "95/100" if kw_main in title.lower() else "70/100 (Cần tối ưu title)"

                # 1. GHI REPORT 18 CỘT (Khớp image_f3f0c8)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", 
                    title, v('Danh sách Keyword bài viết'), site.iloc[9],
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                    backlinks[0], backlinks[1], backlinks[2],
                    seo_score, now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # 2. BẮN TELEGRAM CHUẨN (Fix image_f3e1da)
                tele_msg = (
                    f"<b>🚀 SEO DONE: {site.iloc[0]}</b>\n"
                    f"📄 <b>Tiêu đề:</b> {title}\n"
                    f"⚓ <b>Anchor:</b> {anchors[0]}\n"
                    f"🔗 <b>Link:</b> {backlinks[0]}\n"
                    f"🕒 <b>Giờ:</b> {now_str}"
                )
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tele_msg, "parse_mode": "HTML"})

                st.write(f"✅ Xong bài {i+1}: {title[:50]}...")

            except Exception as e: st.error(f"Lỗi: {str(e)}")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- 3. GIAO DIỆN CHÍNH ---
st.title("🚕 SEO MASTER v47.0 - THE FINAL RULE")
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
