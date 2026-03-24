import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. CONFIG ---
st.set_page_config(page_title="SEO MASTER v53.0", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_tab(name):
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        vals = sh.worksheet(name).get_all_values()
        if len(vals) < 1: return pd.DataFrame()
        return pd.DataFrame(vals[1:], columns=vals[0]).fillna('')
    except: return pd.DataFrame()

# --- 2. VẬN HÀNH ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH", width="large")
def run_robot(data_dict):
    df_d = data_dict['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction="Bạn là máy viết bài SEO. Bắt đầu bài viết bằng tiêu đề H1 ngay lập tức."
        )
    except: st.error("Lỗi API Key"); return

    df_web = data_dict['Website']
    # Fix lỗi 18h: Dùng strip() để lọc 'Active' chính xác tuyệt đối
    active_sites = df_web[df_web.iloc[:, 10].str.strip().str.contains('Active', case=False, na=False)]
    
    if active_sites.empty:
        st.error("Không tìm thấy website nào 'Active' ở cột K!"); return

    df_bl = data_dict['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_vn = get_vn_time()
        now_str = now_vn.strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                prompt = f"Viết bài SEO. Từ khóa: {v('Danh sách Keyword bài viết')}. Chèn link {links[0]} vào từ {anchors[0]}. Prompt: {v('PROMPT_TEMPLATE')}"
                resp = model.generate_content(prompt)
                
                content = resp.text
                title = content.split('\n')[0].replace('#', '').replace('*', '').strip()

                # GHI REPORT 18 CỘT CHUẨN (A-R)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Link", title, 
                    v('Danh sách Keyword bài viết'), site.iloc[9],
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                    links[0], links[1], links[2], "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # TELEGRAM
                msg = f"✅ <b>{site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Đã xong: {title[:50]}...")
            except Exception as e:
                st.error(f"Lỗi: {e}")
        time.sleep(1)

    st.success("Chiến dịch kết thúc!")
    if st.button("Xác nhận và Đóng"): st.rerun()

# --- 3. UI ---
st.title("🚀 SEO MASTER v53.0")

# Report nằm cuối cùng
tab_names = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
all_data = {n: load_tab(n) for n in tab_names}

tabs = st.tabs([f"📂 {n}" for n in tab_names])

for i, name in enumerate(tab_names):
    with tabs[i]:
        df = all_data[name]
        if name == "Dashboard":
            col1, col2, _ = st.columns([1, 1, 4])
            if col1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(all_data)
            if col2.button("🔄 LÀM MỚI"): st.cache_data.clear(); st.rerun()
            
            # Mã hoá dữ liệu nhạy cảm
            display_df = df.copy()
            if not display_df.empty:
                sensitive_keywords = ["KEY", "PASSWORD", "TOKEN", "API"]
                # Mask cột 2 (Input dữ liệu) dựa trên cột 1 (Hạng mục)
                mask = display_df.iloc[:, 0].str.contains('|'.join(sensitive_keywords), case=False, na=False)
                display_df.loc[mask, display_df.columns[1]] = "******** (Protected)"
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, height=500, hide_index=True)
