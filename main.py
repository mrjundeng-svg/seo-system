import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, json, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & AGGRESSIVE TRIM (HÀM GỌT SẠCH TUYỆT ĐỐI) ---
st.set_page_config(page_title="LAIHO.VN - HỆ THỐNG VIẾT BÀI AI", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def clean_str(s):
    """Gọt sạch sành sanh khoảng trắng và ký tự lạ"""
    if not s: return ""
    return str(s).strip().replace('\u200b', '').replace('\xa0', '')

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        client = gspread.authorize(get_creds())
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

# --- 2. CÁC HÀM GỌI API (TAM TRỤ) ---

def call_openrouter(api_key, model_name, prompt):
    """Cổng vạn năng: Giải pháp chống 404 tốt nhất"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, json=payload, timeout=45).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi OpenRouter: {resp.get('error', {}).get('message', 'Nạp thêm tiền hoặc kiểm tra Key')}"
    except Exception as e: return f"Lỗi kết nối: {str(e)}"

# --- 3. TRUNG TÂM POPUP "VIẾT BÀI AI" ---
@st.dialog("⚙️ TRUNG TÂM VIẾT BÀI AI", width="large")
def run_ai_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang kiểm tra 'đạn dược' và rổ từ khóa...**")
    
    # Check lỗi REP_CREATED_AT (Headers đã được clean_str nên chắc chắn khớp)
    df_rep = all_data['Report']
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    # 1. Bốc từ khóa và chuẩn bị Prompt (Giữ nguyên logic rổ A/B của bồ)
    kw_main = "Tài xế lái hộ chuyên nghiệp" # Demo
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    content_raw = ""
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    # --- VÒNG LẶP XOAY VÒNG THÔNG MINH ---
    for m_name in models_to_try:
        m_lower = m_name.lower()
        
        # PHÂN LOẠI 1: OPENROUTER (ƯU TIÊN CỨU CÁNH)
        if '/' in m_lower or 'openrouter' in m_lower:
            st.write(f"🌐 Đang thử OpenRouter: `{m_name}`")
            or_keys = [k.strip() for k in v('OPENROUTER_API_KEY').split(',') if k.strip()]
            for ok in or_keys:
                res = call_openrouter(ok, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {ok[:8]}...: {res}")
        
        # PHÂN LOẠI 2: GEMINI TRỰC TIẾP
        elif 'gemini' in m_lower:
            st.write(f"🧬 Đang thử Gemini: `{m_name}`")
            g_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
            for gk in g_keys:
                try:
                    genai.configure(api_key=gk)
                    model = genai.GenerativeModel(f"models/{m_name}" if "models/" not in m_name else m_name)
                    res = model.generate_content(prompt_final).text
                    if res: content_raw = res; break
                except Exception as e:
                    st.error(f"❌ Key {gk[:8]}...: {str(e)[:100]}")
        
        if content_raw: break

    if content_raw:
        st.success("✅ **THÀNH CÔNG!** Robot đã tìm ra não bộ hoạt động.")
        st.text_area("Bản thảo sơ bộ", content_raw, height=200)
        # [Ghi Report và Telegram...]
    else:
        st.error("💀 **CẠN KIỆT:** Đã thử mọi cách nhưng API vẫn từ chối. Hãy nạp Key OpenRouter để 'bất tử'.")

# --- 4. GIAO DIỆN TRANG CHỦ ---
data, sh = load_all_tabs()
if data:
    # NÚT BẤM "VIẾT BÀI AI"
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_ai_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    # Hiển thị dữ liệu các Tab
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
