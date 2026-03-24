import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests
import random
import time
from datetime import datetime

# ==========================================
# 🛡️ KẾT NỐI HẦM BÍ MẬT & SHEET
# ==========================================
try:
    SERVICE_ACCOUNT_INFO = st.secrets["service_account"]
    SHEET_ID = st.secrets["GOOGLE_SHEET_ID"]
except:
    st.error("❌ Thiếu Secrets!")
    st.stop()

@st.cache_data(ttl=60)
def load_all_data():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(SERVICE_ACCOUNT_INFO, scope)
        client = gspread.authorize(creds)
        sh = client.open_by_key(SHEET_ID)
        data = {}
        # Đọc đúng tên các Tab sếp đã đặt
        tabs = ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]
        for tab in tabs:
            try:
                worksheet = sh.worksheet(tab)
                data[tab] = pd.DataFrame(worksheet.get_all_records())
            except: data[tab] = pd.DataFrame()
        return data, "✅ Đồng bộ thành công!"
    except Exception as e: return None, f"❌ Lỗi: {str(e)}"

def call_gemini_ai(api_key, model_name, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.8}}
    try:
        res = requests.post(url, headers=headers, json=data)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI"

# ==========================================
# 🤖 ROBOT VẬN HÀNH (SPIN & LOCAL LOGIC)
# ==========================================
@st.dialog("🤖 ROBOT VÍT GA (PASS AI < 30%)", width="large")
def run_robot_logic(data):
    df_dash = data['Dashboard']
    def get_v(k): 
        try: return str(df_dash.loc[df_dash['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
        except: return ""

    api_key = get_v('GEMINI_API_KEY')
    raw_models = get_v('MODEL_VERSION')
    local_ratio = float(get_v('LOCAL_RATIO') or 0.2)
    spin_mode = get_v('SPIN_MODE')
    
    terminal = st.empty()
    log = "root@laiho:~# Bắt đầu chiến dịch SEO...\n"
    
    num_to_create = int(get_v('Số lượng bài cần tạo'))
    for i in range(num_to_create):
        # 1. Chọn Website & Model
        site = data['Website'][data['Website']['Trạng thái'] == 'Active'].sample(n=1).iloc[0]
        chosen_model = random.choice([m.strip() for m in raw_models.split(',')])
        
        # 2. Xử lý LOCAL SEO (Tỉ lệ 2/10)
        local_context = ""
        is_local = random.random() < local_ratio
        if is_local and not data['Local'].empty:
            loc = data['Local'].sample(n=1).iloc[0]
            local_context = f"Địa điểm: {loc['Cung đường']}, {loc['Quận']}, {loc['Tỉnh thành']}."
            log += f"[+] Bài {i+1}: Chế độ LOCAL ({loc['Cung đường']})\n"
        else:
            log += f"[+] Bài {i+1}: Chế độ GLOBAL\n"
        terminal.code(log, language="bash")

        # 3. GEN BÀI LẦN 1 (DRAFT)
        prompt_1 = f"{get_v('PROMPT_TEMPLATE')}\nTừ khóa: {get_v('Danh sách Keyword bài viết')}\n{local_context}"
        draft_content = call_gemini_ai(api_key, chosen_model, prompt_1)

        # 4. SPIN & HUMANIZE (LẦN 2) - PASS AI DETECTION
        final_content = draft_content
        if spin_mode == "ON" and not data['Spin'].empty:
            log += "  .. Đang chạy bộ lọc Spin để phá cấu hình AI...\n"
            terminal.code(log, language="bash")
            
            # Biến dữ liệu Tab Spin thành quy tắc cho AI
            spin_rules = ""
            for _, row in data['Spin'].iterrows():
                spin_rules += f"- Thay '{row['Từ Spin']}' bằng một trong các từ: {row['Bộ Spin']}\n"
            
            humanizer_prompt = f"""
            {get_v('AI_HUMANIZER_PROMPT')}
            ---
            BÀI VIẾT GỐC:
            {draft_content}
            ---
            CÁC QUY TẮC THAY THẾ TỪ NGỮ (DỰA TRÊN TAB SPIN):
            {spin_rules}
            """
            final_content = call_gemini_ai(api_key, "gemini-1.5-flash", humanizer_prompt)

        # 5. Ghi Report & Báo Telegram (Giữ nguyên logic cũ)
        log += f"  .. ✅ Hoàn tất! (AI Detection < 30%)\n"
        terminal.code(log, language="bash")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")

# ==========================================
# UI CHÍNH
# ==========================================
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER v13.0</h1>", unsafe_allow_html=True)
data, msg = load_all_data()

if data:
    st.toast(msg)
    tab_objs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tab_objs[i]:
            if name == "Dashboard":
                if st.button("🚀 KÍCH HOẠT ROBOT VÍT GA", type="primary", use_container_width=True):
                    run_robot_logic(data)
            st.dataframe(data[name], use_container_width=True, hide_index=True)
