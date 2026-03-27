import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json

# --- 1. TIỆN ÍCH HỆ THỐNG & FIX LỖI "GET_CREDS" ---
st.set_page_config(page_title="LAIHO.VN - DUAL HYBRID AI", layout="wide")

def clean_str(s):
    """Gọt sạch khoảng trắng và ký tự lạ"""
    return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(
            info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
    except Exception as e:
        st.error(f"Lỗi Secrets: {e}"); return None

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        creds = get_creds()
        if not creds: return None, None
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        tabs = ["Dashboard", "Website", "Keyword", "Image", "Report"]
        data = {}
        for t in tabs:
            ws = sh.worksheet(t.strip())
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame()
            else:
                headers = [clean_str(h) for h in vals[0]]
                rows = [[clean_str(cell) for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. CÁC HÀM GỌI API RIÊNG BIỆT ---

def call_groq(api_key, model_name, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30).json()
        return resp['choices'][0]['message']['content'] if 'choices' in resp else f"❌ Groq: {resp.get('error', {}).get('message')}"
    except: return "❌ Lỗi kết nối Groq"

def call_openrouter(api_key, model_name, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://laiho.vn"
    }
    payload = {"model": model_name, "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60).json()
        return resp['choices'][0]['message']['content'] if 'choices' in resp else f"❌ OpenRouter: {resp.get('error', {}).get('message')}"
    except: return "❌ Lỗi kết nối OpenRouter"

# --- 3. TRUNG TÂM VIẾT BÀI AI (POPUP) ---
@st.dialog("⚙️ TRUNG TÂM VIẾT BÀI AI (DUAL HYBRID)", width="large")
def run_hybrid_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang quét danh sách Model & Key...**")
    kw_main = "Dịch vụ lái xe hộ chuyên nghiệp"
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"
    
    content_raw = ""
    # Tách danh sách model từ Sheet
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    for m_name in models_to_try:
        m_lower = m_name.lower()
        
        # Nhánh 1: Gọi Groq (Nếu là Llama đời mới hoặc Mixtral)
        if any(x in m_lower for x in ['llama', 'mixtral']) and '/' not in m_lower:
            st.write(f"🚀 Thử Groq: `{m_name}`")
            res = call_groq(v('GROQ_API_KEY'), m_name, prompt_final)
            if "❌" not in res: content_raw = res; break
            else: st.error(res)

        # Nhánh 2: Gọi OpenRouter (Nếu có dấu /)
        elif '/' in m_lower:
            st.write(f"🌐 Thử OpenRouter: `{m_name}`")
            res = call_openrouter(v('OPENROUTER_API_KEY'), m_name, prompt_final)
            if "❌" not in res: content_raw = res; break
            else: st.error(res)
            
    if content_raw:
        st.success("✅ **THÀNH CÔNG!**")
        st.markdown(content_raw)
    else:
        st.error("💀 **CẠN KIỆT:** Không súng nào bắn ra chữ. Hãy kiểm tra lại Key và Tiền ví.")

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    if st.button("Viết bài AI", type="primary", use_container_width=True):
        run_hybrid_popup(data, sh)
    st.divider()
    st.dataframe(data['Dashboard'], use_container_width=True, hide_index=True)
