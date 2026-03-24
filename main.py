import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. CẤU HÌNH CƠ BẢN ---
st.set_page_config(page_title="SEO MASTER v51 - FINAL RECOVERY", layout="wide")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

# Hàm load dữ liệu "Nồi đồng cối đá" - Không để mất Tab
def load_tab_data(sheet_name):
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        vals = sh.worksheet(sheet_name).get_all_values()
        if len(vals) < 1: return pd.DataFrame()
        df = pd.DataFrame(vals[1:], columns=vals[0])
        return df.fillna('')
    except: return pd.DataFrame()

# --- 2. TRÌNH VẬN HÀNH (DIỆT 404 & CHÀO SẾP) ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH", width="large")
def run_robot(data_dict):
    df_d = data_dict['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    # FIX 404: Gọi trực tiếp model name chuẩn nhất
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Bạn là máy viết bài SEO. KHÔNG chào hỏi. KHÔNG 'Chào sếp'. Bắt đầu bằng tiêu đề H1 ngay."
        )
    except Exception as e: st.error(f"Lỗi khởi tạo AI: {e}"); return

    # Lấy Website Active (Cột K - Index 10)
    df_web = data_dict['Website']
    if df_web.empty or len(df_web.columns) < 11:
        st.error("Tab Website thiếu cột hoặc không có dữ liệu!"); return
    
    active_sites = df_web[df_web.iloc[:, 10].str.contains('Active', case=False, na=False)]
    df_bl = data_dict['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc Backlink: Cột A(0) là Link, Cột B(1) là Anchor
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        target_links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                prompt = f"Viết bài SEO. Từ khóa: {v('Danh sách Keyword bài viết')}. Chèn link {target_links[0]} vào từ {anchors[0]}. Prompt gốc: {v('PROMPT_TEMPLATE')}"
                resp = model.generate_content(prompt)
                
                # Diệt câu chào xã giao
                lines = [l.strip() for l in resp.text.split('\n') if l.strip()]
                title = "Tiêu đề chưa tối ưu"
                for line in lines:
                    clean = line.replace('#', '').replace('*', '').strip()
                    if not any(x in clean.lower()[:12] for x in ["chào", "kính chào", "hello", "hi "]):
                        title = clean; break

                # GHI REPORT 18 CỘT (ĐÚNG THỨ TỰ A-R)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", 
                    title, v('Danh sách Keyword bài viết'), site.iloc[9], # G: Số ảnh
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4], # H-L: Anchor
                    target_links[0], target_links[1], target_links[2], # M-O: Link
                    "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # BẮN TELEGRAM
                msg = f"<b>✅ DONE: {site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {target_links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Đã xong: {title[:50]}...")

            except Exception as e:
                if "429" in str(e): time.sleep(30)
                st.error(f"Lỗi tại bài {i+1}: {e}")
        time.sleep(1)

    st.success("Chiến dịch hoàn tất!")
    if st.button("Xác nhận và Đóng"): st.rerun()

# --- 3. GIAO DIỆN CHÍNH (HIỆN ĐỦ 100% TAB) ---
st.title("🚀 SEO MASTER v51.0")

# Tự động load tất cả các tab cần thiết
tabs_to_load = ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]
data_all = {name: load_tab_data(name) for name in tabs_to_load}

# Tạo Menu Tab - Dù dữ liệu lỗi thì Tab vẫn phải hiện ra
main_tabs = st.tabs([f"📂 {name}" for name in tabs_to_load])

for i, name in enumerate(tabs_to_load):
    with main_tabs[i]:
        df = data_all[name]
        if name == "Dashboard":
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data_all)
            if c2.button("🔄 LÀM MỚI"): st.cache_data.clear(); st.rerun()
            
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning(f"Tab '{name}' hiện không có dữ liệu hoặc lỗi kết nối. Hãy kiểm tra Google Sheet.")
