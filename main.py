import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
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
                # ÉP TRIM TOÀN BỘ ĐỂ TRÁNH LỖI KHOẢNG TRẮNG
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. CƠ CHẾ GỌI NÃO DỰ PHÒNG (GROQ) ---
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

# --- 3. TRUNG TÂM ĐIỀU KHIỂN POPUP ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN HYBRID", width="large")
def run_robot_hybrid(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔄 **Khởi động luồng chạy Hybrid...**")
    
    # 1. Kiểm tra hạn ngạch
    df_rep = all_data['Report']
    df_rep.columns = [c.strip() for c in df_rep.columns] # Sửa lỗi REP_CREATED_AT
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    today_count = 0
    if 'REP_CREATED_AT' in df_rep.columns:
        today_count = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.contains(today_str)])
    
    if today_count >= batch_size:
        st.warning(f"Đã đạt giới hạn ngày ({today_count}/{batch_size})"); return

    # 2. Bốc từ khóa (Logic Rổ A/B rút gọn)
    st.write("🔍 **Đang nhặt từ khóa chiến thuật...**")
    kw_main = "Tài xế lái hộ chuyên nghiệp" # Giả lập logic bốc từ khóa của bồ
    kw_subs = ["lái xe hộ", "thuê tài xế"]
    
    prompt_final = f"Viết bài SEO về {kw_main}. Từ khóa phụ: {', '.join(kw_subs)}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    content_raw = ""

    # --- NHÁNH 1: THỬ GEMINI (ƯU TIÊN) ---
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
                st.error(f"❌ Gemini tạch: {str(e)[:100]}")
                continue
        if content_raw: break

    # --- NHÁNH 2: THỬ GROQ (DỰ PHÒNG) ---
    if not content_raw:
        st.markdown("### 🚀 Hệ thống Groq (Failover)")
        groq_keys = [k.strip() for k in v('GROQ_API_KEY').split(',') if k.strip()]
        models_groq = [m.strip() for m in v('MODEL_VERSION').split(',') if any(x in m.lower() for x in ['llama', 'mixtral'])]
        
        for qk in groq_keys:
            target_q = models_groq[0] if models_groq else "llama-3.1-70b-versatile"
            st.write(f"⏳ Thử Groq: `{target_q}` | Key: `{qk[:8]}...`")
            res_groq = call_groq_api(qk, target_q, prompt_final)
            if "Lỗi" not in res_groq:
                content_raw = res_groq; break
            else:
                st.error(f"❌ Groq tạch: {res_groq}")

    if not content_raw:
        st.error("💀 **CẠN KIỆT NGUỒN LỰC!** Cả Google và Groq đều từ chối yêu cầu."); return

    # --- BƯỚC 4 & 5: TỐI ƯU & GHI CHÉP ---
    st.success("✅ **Lấy nội dung thành công!** Đang ghi báo cáo...")
    # ... [Đoạn logic Ghi Report, Bắn Telegram bồ giữ nguyên bản Master] ...
    
    st.info("Chiến dịch hoàn tất. Bồ có thể copy lỗi ở trên nếu cần.")
    if st.button("Xác nhận & Đóng"): st.rerun()

# --- 4. GIAO DIỆN HOME (CHÍNH) ---
data, sh = load_all_tabs()

if data:
    # NÚT BẤM TO RÕ TẠI HOME
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("🚀 KÍCH HOẠT ROBOT HYBRID", type="primary", use_container_width=True):
            run_robot_hybrid(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    # Hiển thị dữ liệu các Tab để bồ đối soát
    tab_names = ["Dashboard", "Website", "Keyword", "Image", "Spin", "Local", "Report"]
    st_tabs = st.tabs([f"📂 {n}" for n in tab_names])
    for i, name in enumerate(tab_names):
        with st_tabs[i]:
            st.dataframe(data[name], use_container_width=True, hide_index=True)
