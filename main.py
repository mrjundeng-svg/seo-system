import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, json, math
from datetime import datetime, timedelta, timezone

# --- 1. TIỆN ÍCH HỆ THỐNG & LÀM SẠCH DỮ LIỆU ---
st.set_page_config(page_title="LAIHO.VN - MASTER V7", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def clean_str(s):
    """TRIM siêu cấp: Loại bỏ khoảng trắng và ký tự 'rác' tàng hình"""
    if not s: return ""
    return str(s).strip().replace('\u200b', '').replace('\xa0', '')

def get_creds():
    """HÀM CHÌA KHÓA: Đã fix lỗi 'get_creds is not defined'"""
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(
            info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
    except Exception as e:
        st.error(f"Lỗi cấu hình Secrets: {e}"); return None

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

# --- 2. CÁC HÀM GỌI NÃO BỘ (FIX LỖI AUTH HEADER) ---

def call_openrouter(api_key, model_name, prompt):
    """Cổng vạn năng: Fix lỗi 'No cookie auth' bằng cách thêm đầy đủ Header"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    # TRỌNG TÂM: Header phải chuẩn 100%
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://laiho.vn", # Bắt buộc hoặc tùy chọn để OpenRouter định danh
        "X-Title": "Laiho SEO Robot"
    }
    payload = {
        "model": model_name.strip(),
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        return f"Lỗi OpenRouter: {res_json.get('error', {}).get('message', 'Lỗi không xác định')}"
    except Exception as e:
        return f"Lỗi kết nối OpenRouter: {str(e)}"

def call_gemini(api_key, model_name, prompt):
    """Google Gemini trực tiếp"""
    try:
        genai.configure(api_key=api_key.strip())
        m_path = f"models/{model_name.strip()}" if "models/" not in model_name else model_name
        model = genai.GenerativeModel(m_path)
        return model.generate_content(prompt).text
    except Exception as e:
        return f"Lỗi Google 404/Auth: {str(e)}"

# --- 3. TRUNG TÂM VIẾT BÀI AI (POPUP) ---
@st.dialog("⚙️ TRUNG TÂM VIẾT BÀI AI", width="large")
def run_ai_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang kiểm tra rổ từ khóa & đạn dược...**")
    kw_main = "Dịch vụ lái xe hộ chuyên nghiệp" # Demo bốc từ khóa
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    content_raw = ""
    # Lấy danh sách mẫu từ ô MODEL_VERSION
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    for m_name in models_to_try:
        m_lower = m_name.lower()
        
        # Nhánh 1: OpenRouter (Khi có dấu '/')
        if '/' in m_lower:
            st.write(f"🌐 Đang gọi OpenRouter: `{m_name}`")
            keys = [k.strip() for k in v('OPENROUTER_API_KEY').split(',') if k.strip()]
            for ok in keys:
                res = call_openrouter(ok, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {ok[:8]}...: {res}")
        
        # Nhánh 2: Gemini trực tiếp
        elif 'gemini' in m_lower:
            st.write(f"🧬 Đang gọi Gemini: `{m_name}`")
            keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
            for gk in keys:
                res = call_gemini(gk, m_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {gk[:8]}...: {res}")
        
        if content_raw: break

    if content_raw:
        st.success("✅ **SUCCESS!** Robot đã xuất bản nội dung thành công.")
        st.text_area("Bản thảo", content_raw, height=300)
    else:
        st.error("💀 **CẠN KIỆT:** Vui lòng nạp thêm tiền vào OpenRouter hoặc đổi Key mới.")

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_ai_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
