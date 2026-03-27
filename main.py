import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, json, math
from datetime import datetime, timedelta, timezone

# --- 1. KHỞI TẠO & LÀM SẠCH DỮ LIỆU ---
st.set_page_config(page_title="LAIHO.VN - TRIPLE HYBRID SEO", layout="wide")

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
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame()
            else:
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. CÁC HÀM GỌI API RIÊNG BIỆT (ĐÃ TÁCH MÃ NGUỒN) ---

def call_gemini(api_key, model_name, prompt):
    """Gọi trực tiếp Google Gemini API"""
    try:
        genai.configure(api_key=api_key.strip())
        full_name = f"models/{model_name.strip()}" if not model_name.startswith("models/") else model_name
        model = genai.GenerativeModel(full_name.strip())
        resp = model.generate_content(prompt)
        return resp.text if resp.text else "Rỗng"
    except Exception as e:
        return f"Lỗi Gemini: {str(e)}"

def call_groq(api_key, model_name, prompt):
    """Gọi trực tiếp Groq API (Siêu tốc)"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    data = {
        "model": model_name.strip(),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        resp = requests.post(url, json=data, timeout=30).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi Groq: {resp.get('error', {}).get('message', 'Unknown')}"
    except Exception as e:
        return f"Lỗi kết nối Groq: {str(e)}"

def call_openrouter(api_key, model_name, prompt):
    """Gọi qua OpenRouter (Bộ chuyển đổi vạn năng)"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    data = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, json=data, timeout=30).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi OpenRouter: {resp.get('error', {}).get('message', 'Unknown')}"
    except Exception as e:
        return f"Lỗi kết nối OpenRouter: {str(e)}"

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP ---
@st.dialog("⚙️ ĐIỀU KHIỂN ROBOT TAM TRỤ", width="large")
def run_robot_triple_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Đang phân tích danh sách Model & Key...**")
    
    # [Giả định bốc từ khóa kw_main và tạo prompt_final xong]
    kw_main = "Dịch vụ lái xe hộ" # Demo
    prompt_final = f"Viết bài SEO về {kw_main}..." # Demo prompt

    content_raw = ""
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    # --- VÒNG LẶP XOAY VÒNG THÔNG MINH ---
    for model_name in models_to_try:
        m_lower = model_name.lower()
        
        # PHÂN LOẠI 1: GOOGLE GEMINI (Trực tiếp)
        if 'gemini' in m_lower and '/' not in m_lower:
            st.write(f"🧬 Đang thử Gemini: `{model_name}`")
            g_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
            for gk in g_keys:
                res = call_gemini(gk, model_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {gk[:8]}...: {res}")
        
        # PHÂN LOẠI 2: GROQ (Llama, Mixtral)
        elif any(x in m_lower for x in ['llama', 'mixtral', 'gemma']):
            st.write(f"🚀 Đang thử Groq: `{model_name}`")
            q_keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
            for qk in q_keys:
                res = call_groq(qk, model_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {qk[:8]}...: {res}")

        # PHÂN LOẠI 3: OPENROUTER (Dấu / đặc trưng)
        elif '/' in m_lower:
            st.write(f"🌐 Đang thử OpenRouter: `{model_name}`")
            or_keys = [k.strip() for k in v('OPENROUTER_API_KEY').split(',') if k.strip()]
            for ok in or_keys:
                res = call_openrouter(ok, model_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {ok[:8]}...: {res}")

        if content_raw: break # Đã lấy được bài, dừng vòng lặp

    if content_raw:
        st.success("✅ **THÀNH CÔNG!** Đã có nội dung bài viết.")
        # [Ghi Report & Bắn Telegram tại đây]
    else:
        st.error("💀 **CẠN KIỆT:** Tất cả các hệ API đều không thể xử lý yêu cầu.")

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("🚀 KÍCH HOẠT ROBOT", type="primary", use_container_width=True):
            run_robot_triple_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    tab_list = ["Dashboard", "Website", "Keyword", "Image", "Report"]
    st_tabs = st.tabs([f"📂 {n}" for n in tab_list])
    for i, name in enumerate(tab_list):
        with st_tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
