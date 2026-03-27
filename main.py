import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, json, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & LÀM SẠCH DỮ LIỆU TỪ NGUỒN (LOAD TIME) ---
st.set_page_config(page_title="LAIHO.VN MASTER ENGINE", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        tabs = ["Dashboard", "Website", "Keyword", "Image", "Spin", "Local", "Report"]
        data = {}
        for t in tabs:
            ws = sh.worksheet(t.strip()) # TRIM tên tab
            vals = ws.get_all_values()
            if not vals: 
                data[t] = pd.DataFrame()
            else:
                # 🛠️ TRIM TOÀN BỘ: Cắt khoảng trắng tiêu đề và toàn bộ ô dữ liệu
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. CÁC HÀM GỌI API (TRIM CẢ KEY VÀ MODEL) ---

def call_gemini(api_key, model_name, prompt):
    try:
        genai.configure(api_key=api_key.strip()) # TRIM Key
        m_name = model_name.strip() # TRIM Model
        full_path = f"models/{m_name}" if not m_name.startswith("models/") else m_name
        model = genai.GenerativeModel(full_path)
        resp = model.generate_content(prompt)
        return resp.text if resp.text else "Rỗng"
    except Exception as e: return f"Lỗi Gemini: {str(e)}"

def call_groq(api_key, model_name, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    data = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, json=data, timeout=30).json()
        return resp['choices'][0]['message']['content']
    except: return "Lỗi Groq"

def call_openrouter(api_key, model_name, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    data = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, json=data, timeout=30).json()
        return resp['choices'][0]['message']['content']
    except: return "Lỗi OpenRouter"

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP ---
@st.dialog("⚙️ TRUNG TÂM VIẾT BÀI AI", width="large")
def run_robot_master_popup(all_data, sh):
    df_d = all_data['Dashboard']
    # 🛠️ Hàm tra cứu Dashboard siêu sạch (Trim cả khóa và giá trị)
    def v(k):
        key_search = k.strip()
        res = df_d[df_d.iloc[:, 0].str.strip() == key_search].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Đang kiểm tra dữ liệu sạch...**")
    
    # Check Report để tránh lỗi REP_CREATED_AT
    df_rep = all_data['Report']
    df_rep.columns = [c.strip() for c in df_rep.columns] # Ép sạch tên cột lần nữa
    
    # [Giả sử bốc từ khóa và tạo prompt_final xong...]
    kw_main = "Dịch vụ lái xe hộ" 
    prompt_final = f"Viết bài SEO về {kw_main}..."

    content_raw = ""
    # 🛠️ Tách và TRIM danh sách model dự phòng
    models_all = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    for m_name in models_all:
        m_lower = m_name.lower()
        # Phân loại súng dựa trên ADN của Model
        if 'gemini' in m_lower and '/' not in m_lower:
            keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
            for k in keys:
                res = call_gemini(k, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
        elif any(x in m_lower for x in ['llama', 'mixtral']):
            keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
            for k in keys:
                res = call_groq(k, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
        elif '/' in m_lower:
            keys = [k.strip() for k in v('OPENROUTER_API_KEY').split(',') if k.strip()]
            for k in keys:
                res = call_openrouter(k, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
        
        if content_raw: break

    if content_raw:
        st.success("✅ Thành công! Dữ liệu đã được quét sạch khoảng trắng.")
        # [Tiếp tục logic Ghi Sheet & Bắn Telegram]
    else:
        st.error("❌ Thất bại: Đã thử mọi cách nhưng API vẫn từ chối.")

# --- 4. GIAO DIỆN TRANG CHỦ ---
data, sh = load_all_tabs()
if data:
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        # 🛠️ Đổi tên nút theo yêu cầu của Kỹ sư trưởng
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_robot_master_popup(data, sh)
    with c2:
        if st.button("🔄 Làm mới kho", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    # Hiển thị các Tab dữ liệu
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
