import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & LÀM SẠCH DỮ LIỆU ---
st.set_page_config(page_title="LAIHO.VN HYBRID MASTER", layout="wide")

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
            if not vals or len(vals) == 0: data[t] = pd.DataFrame()
            else:
                # ÉP TRIM CẢ TIÊU ĐỀ VÀ NỘI DUNG ĐỂ TRỊ KEYERROR
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. HỆ THỐNG NÃO BỘ LAI (HYBRID ENGINE) ---

def call_groq_api(api_key, model_name, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {
        "model": model_name.strip() or "llama-3.1-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, json=payload, timeout=30)
        res_json = response.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        else:
            return f"Lỗi Groq API: {res_json.get('error', {}).get('message', 'Không xác định')}"
    except Exception as e:
        return f"Lỗi kết nối Groq: {str(e)}"

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN HYBRID", width="large")
def run_robot_hybrid(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Khởi động luồng chạy Hybrid...**")
    
    # 1. Kiểm tra Report để trị lỗi REP_CREATED_AT
    df_rep = all_data['Report']
    df_rep.columns = [c.strip() for c in df_rep.columns]
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    today_count = 0
    if 'REP_CREATED_AT' in df_rep.columns:
        today_count = len(df_rep[df_rep['REP_CREATED_AT'].str.contains(today_str) & (df_rep['REP_RESULT'] == 'SUCCESS')])
    
    if today_count >= batch_size:
        st.warning(f"Đã xong chỉ tiêu ngày ({today_count}/{batch_size})!"); return

    # 2. Bốc từ khóa (Rổ A/B)
    # ... [Giữ nguyên logic bốc từ khóa đã tối ưu của bồ] ...
    kw_main = "Dịch vụ lái xe hộ" # Demo logic
    kw_subs = ["tài xế lái hộ", "thuê lái xe"]
    prompt_final = f"Viết bài SEO về {kw_main}. Từ khóa phụ: {', '.join(kw_subs)}." # Demo prompt

    content_raw = ""

    # --- NHÁNH 1: GEMINI (ƯU TIÊN) ---
    st.markdown("### 🧬 Hệ thống Gemini")
    g_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
    g_models = [m.strip() for m in v('MODEL_VERSION').split(',') if 'gemini' in m.lower()]
    
    for gk in g_keys:
        genai.configure(api_key=gk)
        for gm in g_models:
            full_gm = f"models/{gm}" if not gm.startswith("models/") else gm
            try:
                st.write(f"⏳ Đang thử: `{full_gm}`")
                model = genai.GenerativeModel(full_gm)
                resp = model.generate_content(prompt_final)
                if resp.text: content_raw = resp.text; break
            except Exception as e:
                st.error(f"❌ Gemini tạch: {str(e)[:100]}")
                continue
        if content_raw: break

    # --- NHÁNH 2: GROQ (DỰ PHÒNG CHIẾN LƯỢC) ---
    if not content_raw:
        st.markdown("### 🚀 Hệ thống Groq (Dự phòng)")
        q_keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
        q_models = [m.strip() for m in v('MODEL_VERSION').split(',') if 'llama' in m.lower() or 'mixtral' in m.lower()]
        
        for qk in q_keys:
            target_q = q_models[0] if q_models else "llama-3.1-70b-versatile"
            st.write(f"⏳ Đang thử Groq: `{target_q}`")
            res = call_groq_api(qk, target_q, prompt_final)
            if "Lỗi" not in res:
                content_raw = res; break
            else:
                st.error(f"❌ Groq tạch: {res}")

    if not content_raw:
        st.error("💀 **CẠN KIỆT NGUỒN LỰC!** Vui lòng kiểm tra lại tất cả Key."); return

    st.success("✅ **Đã lấy được nội dung!** Đang hoàn tất các bước cuối...")
    # ... [Logic Ghi Report & Bắn Telegram] ...

# --- 4. GIAO DIỆN TRANG CHỦ ---
data, sh = load_all_tabs()
if data:
    # NÚT BẤM NGAY TẠI HOME
    col1, col2, _ = st.columns([1.5, 1, 4])
    with col1:
        if st.button("🚀 KÍCH HOẠT ROBOT HYBRID", type="primary", use_container_width=True):
            run_robot_hybrid(data, sh)
    with col2:
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
