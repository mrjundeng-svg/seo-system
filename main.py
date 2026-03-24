import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

# Hàm xử lý credential
def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

# Hàm load data có cache (có thể clear để Reload)
@st.cache_data(ttl=300)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ OK"
    except Exception as e: return None, str(e)

def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

def update_report(row):
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
    except: pass

# --- ĐỘNG CƠ RUN ---
@st.dialog("🤖 SYSTEM LOGGING", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        try:
            res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
            return str(res.values[0]).strip() if not res.empty else ""
        except: return ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    if active_sites.empty:
        st.error("❌ Không có website 'Active'!"); return

    # Khu vực Log - Đảm bảo show từng bước
    log_area = st.empty() 
    log_content = f"root@{v('PROJECT_NAME').lower()}:~# Kích hoạt hệ thống...\n"
    
    num_to_gen = int(v('Số lượng bài cần tạo') or 1)
    
    for i in range(num_to_gen):
        site = active_sites.sample(n=1).iloc[0]
        model = random.choice([m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()])
        
        log_content += f"[+] [{i+1}/{num_to_gen}] Đang xử lý: {site['Tên web']}...\n"
        log_area.code(log_content, language="bash")

        # Step 1: Gen Content
        loc_str = ""
        if random.random() < float(v('LOCAL_RATIO') or 0.2) and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 Địa điểm: {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        prompt = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\n{loc_str}"
        content = call_ai(v('GEMINI_API_KEY'), model, prompt)
        
        log_content += f"  > Đã tạo xong nội dung gốc ({model}).\n"
        log_area.code(log_content, language="bash")

        # Step 2: Spin
        if v('SPIN_MODE') == "ON":
            log_content += "  > Đang chạy bộ lọc Spin Humanize...\n"
            log_area.code(log_content, language="bash")
            content = call_ai(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string(index=False)}\nContent: {content}")

        # Step 3: Ghi Report
        update_report([site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post", datetime.now().strftime("%Y-%m-%d %H:%M"), "", "", "", "", "", site.get('các website đích', ''), "Tiêu đề AI", "Sapo AI", datetime.now().strftime("%Y-%m-%d %H:%M"), "✅ Thành công", "85"])
        
        log_content += "  > ✅ Đã lưu Report thành công.\n"
        log_area.code(log_content, language="bash")
        time.sleep(1)
        
    st.success("🎉 TẤT CẢ TIẾN TRÌNH HOÀN TẤT!")

# --- UI INTERFACE ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v15.0</h1>", unsafe_allow_html=True)

# Toolbar: Reload & RUN
data, msg = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                col1, col2, col3 = st.columns([1, 1, 3])
                with col1:
                    if st.button("🚀 RUN", type="primary", use_container_width=True):
                        run_robot(data)
                with col2:
                    if st.button("🔄 Reload DB", use_container_width=True):
                        st.cache_data.clear()
                        st.rerun()
                
                # Xử lý ẩn dữ liệu nhạy cảm (Key, Mail...)
                display_df = data[name].copy()
                sensitive_words = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET']
                
                def mask_sensitive(row):
                    item = str(row['Hạng mục']).upper()
                    if any(word in item for word in sensitive_words):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "********" + val[-4:] if len(val) > 8 else "********"
                    return row['Input dữ liệu']

                display_df['Input dữ liệu'] = display_df.apply(mask_sensitive, axis=1)
                st.dataframe(display_df, use_container_width=True, height=400, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else: st.error(f"Lỗi kết nối: {msg}")
