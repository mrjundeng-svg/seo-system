import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
st.set_page_config(page_title="LAIHO.VN HYBRID ROBOT", layout="wide")

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
    except: return None, None

# --- 2. LOGIC GỌI API DỰ PHÒNG (GEMINI & GROQ) ---

def call_groq_api(api_key, model_name, prompt):
    # Groq API cực nhanh, dùng Llama 3 làm dự phòng
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    data = {
        "model": model_name or "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, json=data, timeout=30)
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Lỗi Groq: {str(e)}"

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN HYBRID", width="large")
def run_robot_hybrid(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Khởi động Robot...**")
    
    # [Logic Bốc từ khóa A/B giữ nguyên như bản trước]
    # ... (Giả sử kw_main và kw_subs đã được chọn xong) ...
    kw_main = "Dịch vụ lái xe hộ" # Demo
    kw_subs = ["thuê tài xế", "lái xe đi tỉnh"] # Demo
    
    prompt_final = f"Viết bài SEO về {kw_main}. Từ khóa phụ: {', '.join(kw_subs)}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    content_raw = ""

    # --- ƯU TIÊN 1: THỬ TOÀN BỘ KEY GEMINI ---
    gemini_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
    models_gemini = [m.strip() for m in v('MODEL_VERSION').split(',') if 'gemini' in m.lower()]
    
    st.write("🩺 **Đang thử nghiệm với hệ Gemini...**")
    for g_key in gemini_keys:
        genai.configure(api_key=g_key)
        for m_name in models_gemini:
            try:
                full_path = f"models/{m_name}" if not m_name.startswith("models/") else m_name
                st.write(f"⏳ Thử Gemini: `{full_path}`")
                model = genai.GenerativeModel(full_path)
                resp = model.generate_content(prompt_final)
                if resp.text:
                    content_raw = resp.text; break
            except Exception as e:
                st.warning(f"⚠️ Gemini lỗi: {str(e)[:50]}...")
                continue
        if content_raw: break

    # --- ƯU TIÊN 2 (FAILOVER): NẾU GEMINI TẠCH, THỬ SANG GROQ ---
    if not content_raw:
        st.error("🆘 Gemini thất thủ! Chuyển sang dự phòng Groq (Llama 3)...")
        groq_keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
        models_groq = [m.strip() for m in v('MODEL_VERSION').split(',') if 'llama' in m.lower() or 'mixtral' in m.lower()]
        
        for q_key in groq_keys:
            # Nếu Dashboard không ghi model Groq, dùng mặc định
            target_q_model = models_groq[0] if models_groq else "llama-3.1-70b-versatile"
            st.write(f"🚀 Thử Groq: `{target_q_model}`")
            res_groq = call_groq_api(q_key, target_q_model, prompt_final)
            if "Lỗi Groq:" not in res_groq:
                content_raw = res_groq; break
            else:
                st.warning(f"⚠️ Groq lỗi: {res_groq[:50]}...")

    if not content_raw:
        st.error("💀 **CẠN KIỆT NGUỒN LỰC:** Cả Gemini và Groq đều không chạy được!"); return

    # --- BƯỚC TIẾP THEO: TỐI ƯU & GHI REPORT ---
    st.write("✅ **Đã có nội dung! Đang ghi báo cáo...**")
    # ... [Logic ghi Sheet và bắn Telegram giữ nguyên] ...
    st.success("HOÀN THÀNH CHIẾN DỊCH!")

# --- 4. GIAO DIỆN CHÍNH ---
data, sh = load_all_tabs()
if data:
    if st.button("🚀 KÍCH HOẠT ROBOT HYBRID", type="primary"):
        run_robot_hybrid(data, sh)
    
    st.divider()
    # Hiển thị dữ liệu các Tab...
    st.tabs([f"📂 {n}" for n in data.keys()])
