import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. SETUP CƠ BẢN ---
st.set_page_config(page_title="SEO MASTER v57.0", layout="wide")

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
        if not vals: return pd.DataFrame()
        return pd.DataFrame(vals[1:], columns=vals[0]).fillna('')
    except: return pd.DataFrame()

# --- 2. TRÌNH VẬN HÀNH (TẬP TRUNG FIX 404) ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH", width="large")
def run_robot(data_dict):
    df_d = data_dict['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    # --- FIX 404 TẠI ĐÂY ---
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        # Giải pháp: Gọi tên model trực tiếp, không dùng biến trung gian hay tiền tố
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        st.error(f"Lỗi khởi tạo AI: {e}"); return

    # Lọc Website (Cột K - Index 10)
    df_web = data_dict['Website']
    active_sites = df_web[df_web.iloc[:, 10].str.strip().str.contains('Active', case=False, na=False)]
    
    if active_sites.empty:
        st.error("Không có Website nào 'Active' ở cột K!"); return

    df_bl = data_dict['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # Backlink: Cột A(0) là Link, Cột B(1) là Anchor
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang chạy bài {i+1}...", expanded=True):
            try:
                prompt = f"Viết bài SEO. Từ khóa: {v('Danh sách Keyword bài viết')}. Chèn link {links[0]} vào từ {anchors[0]}. Prompt: {v('PROMPT_TEMPLATE')}"
                
                # Thực thi Generate
                resp = model.generate_content(prompt)
                title = resp.text.split('\n')[0].replace('#', '').replace('*', '').strip()

                # GHI REPORT 18 CỘT CHUẨN (A-R)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", title, 
                    v('Danh sách Keyword bài viết'), site.iloc[9],
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                    links[0], links[1], links[2], "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # TELEGRAM
                msg = f"✅ <b>{site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Xong bài {i+1}: {title[:50]}...")
            except Exception as e:
                st.error(f"Lỗi tại bài {i+1}: {e}")
        time.sleep(1)

    st.success("Xong!")
    if st.button("ĐÓNG"): st.rerun()

# --- 3. UI ---
st.title("🚀 SEO MASTER v57.0 - FIX 404")

# Report nằm cuối cùng
tab_names = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
all_data = {n: load_tab(n) for n in tab_names}

tabs = st.tabs([f"📂 {n}" for n in tab_names])

for i, name in enumerate(tab_names):
    with tabs[i]:
        df = all_data[name]
        if name == "Dashboard":
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("🚀 VẬN HÀNH", type="primary"): run_robot(all_data)
            if c2.button("🔄 LÀM MỚI"): st.cache_data.clear(); st.rerun()
            
            # MÃ HÓA BẢO MẬT DASHBOARD
            if not df.empty:
                display_df = df.copy()
                sensitive = ["KEY", "PASSWORD", "TOKEN", "API"]
                mask = display_df.iloc[:, 0].str.contains('|'.join(sensitive), case=False, na=False)
                display_df.loc[mask, display_df.columns[1]] = "********"
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=500, hide_index=True)
            else:
                st.info(f"Tab '{name}' trống hoặc chưa có dữ liệu.")
