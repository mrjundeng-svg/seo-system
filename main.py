import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import random
import time
from datetime import datetime

# ==========================================
# 🛡️ KẾT NỐI HẦM BÍ MẬT & GOOGLE SHEET
# ==========================================
try:
    SERVICE_ACCOUNT_INFO = st.secrets["service_account"]
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
except:
    st.error("❌ Thiếu cấu hình Secrets trên Streamlit Cloud!")
    st.stop()

st.set_page_config(page_title="LÁI HỘ SEO MASTER", layout="wide")

@st.cache_data(ttl=60)
def load_all_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        
        data = {}
        # Danh sách Tab chuẩn của sếp
        tabs = ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]
        for tab in tabs:
            try:
                worksheet = sh.worksheet(tab)
                df = pd.DataFrame(worksheet.get_all_records())
                data[tab] = df
            except Exception as e:
                data[tab] = pd.DataFrame() # Tạo bảng trống nếu thiếu Tab
        return data, "✅ Kết nối thành công!"
    except Exception as e:
        return None, str(e)

# ==========================================
# 🧠 AI ENGINE (GEMINI)
# ==========================================
def call_gemini_ai(api_key, model_name, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.8}}
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI: Vui lòng kiểm tra API Key hoặc Quota."

# ==========================================
# 🤖 ROBOT VÍT GA (SPIN & LOCAL LOGIC)
# ==========================================
@st.dialog("🤖 HỆ THỐNG ĐANG CHẠY TỰ ĐỘNG", width="large")
def run_robot_logic(data):
    df_dash = data['Dashboard']
    def get_v(k): 
        try: return str(df_dash.loc[df_dash['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
        except: return ""

    api_key = get_v('GEMINI_API_KEY')
    raw_models = get_v('MODEL_VERSION')
    local_ratio = float(get_v('LOCAL_RATIO') or 0.2)
    
    terminal = st.empty()
    log = f"root@{get_v('PROJECT_NAME').lower()}:~# Khởi tạo chiến dịch...\n"
    
    num_to_create = int(get_v('Số lượng bài cần tạo') or 1)
    for i in range(num_to_create):
        site = data['Website'][data['Website']['Trạng thái'] == 'Active'].sample(n=1).iloc[0]
        model_list = [m.strip() for m in raw_models.split(',')]
        chosen_model = random.choice(model_list)
        
        # 📍 Logic Local (Tỉ lệ vàng)
        loc_str = ""
        if random.random() < local_ratio and not data['Local'].empty:
            loc = data['Local'].sample(n=1).iloc[0]
            loc_str = f"Địa danh: {loc['Cung đường']}, {loc['Quận']}, {loc['Tỉnh thành']}."
            log += f"[+] Bài {i+1}: Chế độ LOCAL SEO ({loc['Cung đường']})\n"
        else:
            log += f"[+] Bài {i+1}: Chế độ GENERAL SEO\n"
        terminal.code(log, language="bash")

        # 📝 Bước 1: Tạo bài viết gốc
        prompt_1 = f"{get_v('PROMPT_TEMPLATE')}\nKeywords: {get_v('Danh sách Keyword bài viết')}\n{loc_str}"
        raw_article = call_gemini_ai(api_key, chosen_model, prompt_1)

        # 🔄 Bước 2: Humanize bằng Tab Spin (Bypass AI < 30%)
        if not data['Spin'].empty:
            log += "  .. Đang chạy bộ lọc Spin để phá cấu trúc AI...\n"
            terminal.code(log, language="bash")
            spin_data = data['Spin'].to_string(index=False)
            human_prompt = f"{get_v('AI_HUMANIZER_PROMPT')}\nQuy tắc thay thế: {spin_data}\nNội dung: {raw_article}"
            final_article = call_gemini_ai(api_key, "gemini-1.5-flash", human_prompt)
        else:
            final_article = raw_article

        log += f"  .. ✅ Hoàn tất! (Model: {chosen_model})\n"
        terminal.code(log, language="bash")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH ĐÃ HOÀN TẤT!")

# ==========================================
# 🖥️ GIAO DIỆN NGƯỜI DÙNG (UI)
# ==========================================
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER v13.1</h1>", unsafe_allow_html=True)

with st.spinner("Đang hút dữ liệu từ Google Sheet..."):
    data, error_msg = load_all_data()

if data:
    st.toast("Kết nối Google Sheet thành công!")
    tab_objs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tab_objs[i]:
            if name == "Dashboard":
                col1, col2 = st.columns([3, 1])
                with col1: st.info("Hệ thống đã sẵn sàng vít ga!")
                with col2: 
                    if st.button("🚀 START ROBOT", type="primary", use_container_width=True):
                        run_robot_logic(data)
            
            # Hiển thị bảng dữ liệu
            st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else:
    st.error(f"❌ Không thể tải dữ liệu: {error_msg}")
    st.info("Kiểm tra: 1. Đã Share Sheet cho Email Robot? 2. SHEET_ID trong Secrets đúng chưa?")
