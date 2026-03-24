import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re
from datetime import datetime, timedelta, timezone

# --- 1. SETUP ---
st.set_page_config(page_title="SEO MASTER", layout="wide")

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
        if len(vals) < 2: return pd.DataFrame(columns=vals[0] if vals else [])
        return pd.DataFrame(vals[1:], columns=vals[0]).fillna('')
    except: return pd.DataFrame()

# --- 2. ENGINE (TỰ ĐỘNG TÌM MODEL - CHỐNG 404) ---
@st.dialog("⚙️ TRUNG TÂM VẬN HÀNH", width="large")
def run_robot(data_dict):
    df_d = data_dict['Dashboard']
    def v(k):
        try:
            res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
            return str(res.values[0]).strip() if not res.empty else ""
        except: return ""

    api_key = v('GEMINI_API_KEY')
    if not api_key:
        st.error("Thiếu API Key trong Dashboard!")
        return

    # Khởi tạo AI bằng cách lấy đúng tên do Google cấp
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            st.error("API Key của bồ bị Google chặn hoặc không hỗ trợ tạo text!")
            return
            
        # Ưu tiên lấy dòng flash, không có thì lấy dòng pro
        target_model = next((m for m in available_models if 'flash' in m), None)
        if not target_model:
            target_model = next((m for m in available_models if 'pro' in m), available_models[0])
            
        model = genai.GenerativeModel(target_model)
    except Exception as e:
        st.error(f"Lỗi cấu hình AI: {e}")
        return

    # Lọc Website
    df_web = data_dict['Website']
    if df_web.empty:
        st.error("Tab Website trống!"); return
        
    active_sites = df_web[df_web.iloc[:, 10].astype(str).str.strip().str.contains('Active', case=False, na=False)]
    if active_sites.empty:
        st.error("Không tìm thấy website nào 'Active' ở cột K!"); return

    df_bl = data_dict['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist() if not df_bl.empty else []
        anchors = [str(r[1]) if len(r)>1 else "" for r in bl_pool] + [""]*5
        links = [str(r[0]) if len(r)>0 else "" for r in bl_pool] + [""]*3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                kw = v('Danh sách Keyword bài viết')
                prompt = f"Viết bài SEO. Từ khóa: {kw}. Chèn link {links[0]} vào từ {anchors[0]}. Prompt: {v('PROMPT_TEMPLATE')}. Yêu cầu: KHÔNG chào hỏi."
                
                resp = model.generate_content(prompt)
                
                # Cắt bỏ dòng chào hỏi dư thừa (nếu có)
                clean_text = re.sub(r'^(Chào|Kính chào|Hello|Hi |Dạ |Vâng).*?\n', '', resp.text, flags=re.IGNORECASE).strip()
                title = clean_text.split('\n')[0].replace('#', '').replace('*', '').strip()

                # Report 18 Cột
                limit_img = site.iloc[9] if len(site.iloc) > 9 else "1"
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", title, 
                    kw, limit_img,
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                    links[0], links[1], links[2], "95/100", now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # Bắn Telegram
                msg = f"✅ <b>{site.iloc[0]}</b>\n📄 {title}\n⚓ {anchors[0]}\n🔗 {links[0]}"
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

                st.write(f"Đã xong: {title[:50]}...")
            except Exception as e:
                st.error(f"Lỗi bài {i+1}: {e}")
        time.sleep(1)

    st.success("Chiến dịch kết thúc!")
    if st.button("Xác nhận và Đóng"): st.rerun()

# --- 3. UI ---
st.title("🚀 SEO MASTER - FULL STABLE")

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
            
            # Che Key/Token
            if not df.empty:
                display_df = df.copy()
                mask = display_df.iloc[:, 0].astype(str).str.contains('KEY|PASSWORD|TOKEN|API', case=False, na=False)
                display_df.loc[mask, display_df.columns[1]] = "********"
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            if not df.empty:
                st.dataframe(df, use_container_width=True, height=500, hide_index=True)
            else:
                st.info(f"Tab '{name}' trống.")
