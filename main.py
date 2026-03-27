import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, json, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & AGGRESSIVE TRIM (HÀM CẮT KHOẢNG TRẮNG TUYỆT ĐỐI) ---
st.set_page_config(page_title="LAIHO.VN - TRUNG TÂM VIẾT BÀI AI", layout="wide")

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
            # TRIM cả tên Tab khi gọi
            ws = sh.worksheet(t.strip()) 
            vals = ws.get_all_values()
            if not vals:
                data[t] = pd.DataFrame()
            else:
                # 🛠️ HÀM TRIM THẦN THÁNH: Cắt sạch khoảng trắng tiêu đề và toàn bộ ô dữ liệu
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. CÁC HÀM GỌI API RIÊNG BIỆT (TÁCH BIỆT 3 CỔNG) ---

def call_gemini(api_key, model_name, prompt):
    try:
        genai.configure(api_key=api_key.strip())
        m_name = model_name.strip()
        full_path = f"models/{m_name}" if not m_name.startswith("models/") else m_name
        model = genai.GenerativeModel(full_path)
        resp = model.generate_content(prompt)
        return resp.text if resp.text else "Rỗng"
    except Exception as e: return f"Lỗi Google: {str(e)}"

def call_groq(api_key, model_name, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    data = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        resp = requests.post(url, json=data, timeout=30).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi Groq: {resp.get('error', {}).get('message', 'Sai Key hoặc Hết hạn')}"
    except Exception as e: return f"Lỗi kết nối Groq: {str(e)}"

def call_openrouter(api_key, model_name, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    data = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, json=data, timeout=30).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi OpenRouter: {resp.get('error', {}).get('message', 'Kiểm tra ví tiền')}"
    except Exception as e: return f"Lỗi kết nối OpenRouter: {str(e)}"

# --- 3. POPUP ĐIỀU KHIỂN (ST.DIALOG) ---
@st.dialog("⚙️ TRUNG TÂM VIẾT BÀI AI", width="large")
def run_robot_master_popup(all_data, sh):
    df_d = all_data['Dashboard']
    # Hàm lấy giá trị Dashboard siêu sạch (Trim cả key lẫn value)
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Đang kiểm tra dữ liệu sạch...**")
    
    # Check lỗi REP_CREATED_AT: Do headers đã được strip() lúc load nên chắc chắn sẽ tìm thấy
    df_rep = all_data['Report']
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    # Kiểm tra hạn ngạch ngày
    if 'REP_CREATED_AT' in df_rep.columns:
        today_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(today_str)]
        if len(today_posts) >= batch_size:
            st.warning(f"Đã đạt chỉ tiêu ngày ({len(today_posts)}/{batch_size})!"); return
    else:
        st.error("❌ Không tìm thấy cột 'REP_CREATED_AT'. Hãy kiểm tra lại tiêu đề trên Sheet!"); return

    # [Logic Bốc từ khóa và tạo Prompt bồ giữ nguyên bản cũ]
    # ... Giả sử kw_main và prompt_final đã sẵn sàng ...
    kw_main = "Dịch vụ lái xe hộ" # Demo
    prompt_final = f"Viết bài SEO về {kw_main} dựa trên quy tắc {v('SEO_GLOBAL_RULE')}"

    content_raw = ""
    # Lấy danh sách mẫu AI và TRIM sạch dấu cách
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    # --- VÒNG LẶP XOAY VÒNG TAM TRỤ (FAILOVER) ---
    for m_name in models_to_try:
        m_lower = m_name.lower()
        # 1. Nhóm Google
        if 'gemini' in m_lower and '/' not in m_lower:
            st.write(f"🧬 Thử Gemini: `{m_name}`")
            keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
            for k in keys:
                res = call_gemini(k, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {k[:8]}...: {res}")
        # 2. Nhóm Groq
        elif any(x in m_lower for x in ['llama', 'mixtral', 'gemma']):
            st.write(f"🚀 Thử Groq: `{m_name}`")
            keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
            for k in keys:
                res = call_groq(k, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {k[:8]}...: {res}")
        # 3. Nhóm OpenRouter
        elif '/' in m_lower:
            st.write(f"🌐 Thử OpenRouter: `{m_name}`")
            keys = [k.strip() for k in v('OPENROUTER_API_KEY').split(',') if k.strip()]
            for k in keys:
                res = call_openrouter(k, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {k[:8]}...: {res}")
        
        if content_raw: break

    if content_raw:
        st.success("✅ **THÀNH CÔNG!** Đã bẻ khóa khoảng trắng và lấy được bài.")
        # [Tiếp tục logic Ghi Sheet & Telegram...]
    else:
        st.error("❌ **THẤT BẠI:** Đã thử mọi cách nhưng API vẫn từ chối. Hãy copy lỗi phía trên để kiểm tra.")

# --- 4. GIAO DIỆN HOME (CHÍNH) ---
data, sh = load_all_tabs()
if data:
    # NÚT BẤM "VIẾT BÀI AI" TẠI HOME
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_robot_master_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    # Hiển thị dữ liệu các Tab
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
