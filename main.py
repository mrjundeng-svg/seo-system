import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, json, math
from datetime import datetime, timedelta, timezone

# --- 1. THIẾT LẬP HỆ THỐNG & LÀM SẠCH DỮ LIỆU ---
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
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame()
            else:
                # ÉP TRIM: Xử lý triệt để dấu cách thừa gây lỗi 404/KeyError
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}"); return None, None

# --- 2. CÁC HÀM GỌI API RIÊNG BIỆT (TÁCH BIỆT 3 CỔNG) ---

def call_gemini(api_key, model_name, prompt):
    """Cổng 1: Google Gemini trực tiếp"""
    try:
        genai.configure(api_key=api_key.strip())
        full_name = f"models/{model_name.strip()}" if not model_name.startswith("models/") else model_name
        model = genai.GenerativeModel(full_name.strip())
        resp = model.generate_content(prompt)
        return resp.text if resp.text else "Rỗng"
    except Exception as e:
        return f"Lỗi Google: {str(e)}"

def call_groq(api_key, model_name, prompt):
    """Cổng 2: Groq API (Dùng Llama/Mixtral)"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        resp = requests.post(url, json=payload, timeout=30).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi Groq: {resp.get('error', {}).get('message', 'Sai Key hoặc Hết hạn')}"
    except Exception as e:
        return f"Lỗi kết nối Groq: {str(e)}"

def call_openrouter(api_key, model_name, prompt):
    """Cổng 3: OpenRouter (Cổng vạn năng)"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}]}
    try:
        resp = requests.post(url, json=payload, timeout=30).json()
        if 'choices' in resp: return resp['choices'][0]['message']['content']
        return f"Lỗi OpenRouter: {resp.get('error', {}).get('message', 'Kiểm tra tiền trong ví')}"
    except Exception as e:
        return f"Lỗi kết nối OpenRouter: {str(e)}"

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP (TRỊ LỖI 404/INVALID) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN TAM TRỤ", width="large")
def run_robot_master_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Đang phân tích ADN Model để chọn súng...**")
    
    # [Giả sử logic bốc từ khóa và tạo prompt_final đã xong]
    kw_main = "Dịch vụ lái xe hộ" # Demo
    prompt_final = f"Viết bài SEO về {kw_main}..." # Demo prompt

    content_raw = ""
    models_all = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    # --- VÒNG LẶP XOAY VÒNG THÔNG MINH (TRIPLE FAILOVER) ---
    for model_name in models_all:
        m_lower = model_name.lower()
        
        # PHÂN LOẠI 1: GOOGLE GEMINI (Khi bồ ghi 'gemini' và không có dấu '/')
        if 'gemini' in m_lower and '/' not in m_lower:
            st.write(f"🧬 Đang gọi Google Gemini cho mẫu: `{model_name}`")
            g_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
            for gk in g_keys:
                res = call_gemini(gk, model_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {gk[:8]}...: {res}")
        
        # PHÂN LOẠI 2: GROQ (Khi bồ ghi 'llama', 'mixtral', 'gemma')
        elif any(x in m_lower for x in ['llama', 'mixtral', 'gemma']):
            st.write(f"🚀 Đang gọi Groq cho mẫu: `{model_name}`")
            q_keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
            for qk in q_keys:
                res = call_groq(qk, model_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {qk[:8]}...: {res}")

        # PHÂN LOẠI 3: OPENROUTER (Khi bồ ghi mẫu có dấu '/' đặc trưng)
        elif '/' in m_lower:
            st.write(f"🌐 Đang gọi OpenRouter cho mẫu: `{model_name}`")
            or_keys = [k.strip() for k in v('OPENROUTER_API_KEY').split(',') if k.strip()]
            for ok in or_keys:
                res = call_openrouter(ok, model_name, prompt_final)
                if "Lỗi" not in res: content_raw = res; break
                else: st.error(f"❌ Key {ok[:8]}...: {res}")

        if content_raw: break # Đã lấy được bài, dừng toàn bộ vòng lặp

    if content_raw:
        st.success("✅ **THÀNH CÔNG!** Robot đã vượt rào lỗi để lấy nội dung.")
        # [Ghi Report & Bắn Telegram tại đây...]
    else:
        st.error("💀 **CẠN KIỆT:** Đã thử mọi cách nhưng không API nào phản hồi bài viết.")

# --- 4. GIAO DIỆN TRANG CHỦ ---
data, sh = load_all_tabs()
if data:
    # NÚT BẤM TO RÕ NGAY TẠI HOME
    c1, c2, _ = st.columns([2, 1, 4])
    with c1:
        if st.button("🚀 KÍCH HOẠT ROBOT MASTER", type="primary", use_container_width=True):
            run_robot_master_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    # Hiển thị các Tab dữ liệu bên dưới để bồ đối soát
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
