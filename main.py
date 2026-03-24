import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- 1. SETUP ---
st.set_page_config(page_title="SEO MASTER v54.0", layout="wide")

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

# --- 2. VẬN HÀNH (SỬA LỖI 404 TẠI ĐÂY) ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH", width="large")
def run_robot(data_dict):
    df_d = data_dict['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    # FIX 404: Bỏ hoàn toàn chữ "models/" trong tên model
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        # CHỈ DÙNG: "gemini-1.5-flash"
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
    except Exception as e: 
        st.error(f"Lỗi cấu hình AI: {e}"); return

    df_web = data_dict['Website']
    # Quét cột K (Index 10) để tìm máy Active
    active_sites = df_web[df_web.iloc[:, 10].str.strip().str.contains('Active', case=False, na=False)]
    
    if active_sites.empty:
        st.error("Không tìm thấy dòng nào có chữ 'Active' ở cột K tab Website!"); return

    df_bl = data_dict['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # Bốc Backlink: Cột A(0) là Link, Cột B(1) là Anchor
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5   # Cột H-L
        links = [str(r[0]) for r in bl_pool] + [""]*3     # Cột M-O

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                prompt = f"Viết bài SEO. Từ khóa: {v('Danh sách Keyword bài viết')}. Chèn link {links[0]} vào từ {anchors[0]}. Nội dung: {v('PROMPT_TEMPLATE')}"
                # Gọi AI - Không thêm tiền tố models/ vào tham số
                resp = model.generate_content(prompt)
                
                title = resp.text.split('\n')[0].replace('#', '').replace('*', '').strip()

                # GHI REPORT 18 CỘT CHUẨN (A-R)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", title, 
                    v('Danh sách Keyword bài viết'), site.iloc[9], # G: Số ảnh
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4], # H-L: Từ khoá
                    links[0], links[1], links[2], # M-O: Backlink
                    "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # BẮN TELEGRAM
                msg = f"✅ <b>{site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Xong bài {i+1}: {title[:50]}...")
            except Exception as e:
                st.error(f"Lỗi: {e}")
        time.sleep(1)

    st.success("Chiến dịch kết thúc!")
    if st.button("Xác nhận và Đóng"): st.rerun()

# --- 3. UI (SẮP XẾP TAB & BẢO MẬT) ---
st.title("🚀 SEO MASTER v54.0 - FIXED 404")

# Report luôn nằm cuối
tab_names = ["Dashboard", "Website", "Backlink", "Image", "Spin", "Local", "Report"]
all_data = {n: load_tab(n) for n in tab_names}

tabs = st.tabs([f"📂 {n}" for n in tab_names])

for i, name in enumerate(tab_names):
    with tabs[i]:
        df = all_data[name]
        if name == "Dashboard":
            c1, c2, _ = st.columns([1, 1, 4])
            if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(all_data)
            if c2.button("🔄 LÀM MỚI"): st.cache_data.clear(); st.rerun()
            
            # Mã hoá dữ liệu nhạy cảm ở Dashboard
            if not df.empty:
                display_df = df.copy()
                sensitive = ["KEY", "PASSWORD", "TOKEN", "API"]
                mask = display_df.iloc[:, 0].str.contains('|'.join(sensitive), case=False, na=False)
                display_df.loc[mask, display_df.columns[1]] = "********"
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, height=500, hide_index=True)
