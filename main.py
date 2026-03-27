import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG & LÀM SẠCH DỮ LIỆU ---
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
                # ÉP TRIM: Xử lý triệt để lỗi KeyError: 'REP_CREATED_AT'
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheet: {e}"); return None, None

# --- 2. HÀM GỌI NÃO DỰ PHÒNG (GROQ) ---
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
        return f"Lỗi Groq API: {res_json.get('error', {}).get('message', 'Unknown Error')}"
    except Exception as e:
        return f"Lỗi kết nối Groq: {str(e)}"

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP (ST.DIALOG) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN ROBOT", width="large")
def run_robot_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Khởi động luồng chạy Hybrid...**")
    
    # Check Batch Size & Today (Trị lỗi REP_CREATED_AT)
    df_rep = all_data['Report']
    df_rep.columns = [c.strip() for c in df_rep.columns] # Đảm bảo cột sạch
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    today_count = 0
    if 'REP_CREATED_AT' in df_rep.columns:
        today_count = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.contains(today_str)])
    
    if today_count >= batch_size:
        st.warning(f"Đã đạt chỉ tiêu ngày ({today_count}/{batch_size})!"); return

    # Bốc từ khóa (Dùng logic rổ A/B của bồ)
    st.write("🔍 **Đang nhặt từ khóa chiến thuật...**")
    kw_main = "Dịch vụ lái xe hộ uy tín" # Demo
    kw_subs = ["thuê tài xế", "lái xe đi tỉnh"]
    
    prompt_final = f"Viết bài SEO về {kw_main}. Từ khóa phụ: {', '.join(kw_subs)}. Quy tắc: {v('SEO_GLOBAL_RULE')}"
    content_raw = ""

    # --- NHÁNH 1: THỬ TOÀN BỘ KEY GEMINI ---
    st.markdown("### 🧬 Hệ thống Gemini")
    gemini_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
    models_gemini = [m.strip() for m in v('MODEL_VERSION').split(',') if 'gemini' in m.lower()]
    
    for gk in gemini_keys:
        genai.configure(api_key=gk)
        for gm in models_gemini:
            try:
                full_gm = f"models/{gm}" if not gm.startswith("models/") else gm
                st.write(f"⏳ Thử Gemini: `{full_gm}` | Key: `{gk[:8]}...`")
                model = genai.GenerativeModel(full_gm)
                resp = model.generate_content(prompt_final)
                if resp.text: content_raw = resp.text; break
            except Exception as e:
                st.error(f"❌ Gemini tạch: {str(e)[:150]}") # Bồ copy lỗi tại đây
                continue
        if content_raw: break

    # --- NHÁNH 2: THỬ TOÀN BỘ KEY GROQ (FAILOVER) ---
    if not content_raw:
        st.markdown("### 🚀 Hệ thống Groq (Dự phòng)")
        groq_keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
        models_groq = [m.strip() for m in v('MODEL_VERSION').split(',') if any(x in m.lower() for x in ['llama', 'mixtral'])]
        
        for qk in groq_keys:
            target_q = models_groq[0] if models_groq else "llama-3.1-70b-versatile"
            st.write(f"🚀 Thử Groq: `{target_q}` | Key: `{qk[:8]}...`")
            res_groq = call_groq_api(qk, target_q, prompt_final)
            if "Lỗi" not in res_groq:
                content_raw = res_groq; break
            else:
                st.error(f"❌ Groq tạch: {res_groq}") # Bồ copy lỗi tại đây

    if not content_raw:
        st.error("💀 **CẠN KIỆT NGUỒN LỰC!** Cả Google và Groq đều từ chối."); return

    st.success("✅ **Thành công!** Đang ghi báo cáo...")
    # ... [Đoạn logic Ghi Sheet & Bắn Telegram giữ nguyên] ...
    if st.button("Xác nhận & Đóng"): st.rerun()

# --- 4. GIAO DIỆN CHÍNH (HOME) ---
data, sh = load_all_tabs()

if data:
    # NÚT BẤM TO RÕ TẠI HOME
    c1, c2, _ = st.columns([2, 1, 4])
    with c1:
        if st.button("🚀 KÍCH HOẠT ROBOT HYBRID", type="primary", use_container_width=True):
            run_robot_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    
    # Hiển thị các Tab để bồ đối soát dữ liệu
    tab_list = ["Dashboard", "Website", "Keyword", "Image", "Spin", "Local", "Report"]
    st_tabs = st.tabs([f"📂 {n}" for n in tab_list])
    for i, name in enumerate(tab_list):
        with st_tabs[i]:
            st.dataframe(data[name], use_container_width=True, hide_index=True)
