import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG & TRIM DỮ LIỆU ---
st.set_page_config(page_title="LAIHO.VN - AI SEO MASTER", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def clean_str(s):
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

# --- 2. CÁC HÀM GỌI API (GROQ + OPENROUTER) ---

def call_ai(api_key, model_name, prompt, provider="groq"):
    if provider == "groq":
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    else: # OpenRouter
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json", "HTTP-Referer": "https://laiho.vn"}
    
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60).json()
        return resp['choices'][0]['message']['content']
    except Exception as e:
        return f"❌ Lỗi {provider}: {str(e)}"

# --- 3. TRUNG TÂM VIẾT BÀI AI (POPUP) ---
@st.dialog("⚙️ HỆ THỐNG VIẾT BÀI AI (AUTO REPORT)", width="large")
def run_hybrid_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang nhặt từ khóa và chuẩn bị não bộ...**")
    
    # 🛠️ TỰ ĐỘNG NHẶT TỪ KHÓA TỪ TAB KEYWORD (Ưu tiên từ chưa chạy)
    df_kw = all_data['Keyword']
    available_kw = df_kw[df_kw['KW_STATUS'] != 'SUCCESS']
    if available_kw.empty:
        st.warning("Hết từ khóa rồi Kỹ sư trưởng ơi!"); return
    
    target_row = available_kw.iloc[0]
    kw_main = target_row['KW_NAME']
    st.info(f"🔑 Từ khóa mục tiêu: **{kw_main}**")

    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"
    content_raw = ""
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    for m_name in models_to_try:
        m_lower = m_name.lower()
        if any(x in m_lower for x in ['llama', 'mixtral']) and '/' not in m_lower:
            st.write(f"🚀 Đang dùng Groq: `{m_name}`")
            res = call_ai(v('GROQ_API_KEY'), m_name, prompt_final, "groq")
            if "❌" not in res: content_raw = res; break
        elif '/' in m_lower:
            st.write(f"🌐 Đang dùng OpenRouter: `{m_name}`")
            res = call_ai(v('OPENROUTER_API_KEY'), m_name, prompt_final, "openrouter")
            if "❌" not in res: content_raw = res; break
            
    if content_raw:
        st.success("✅ **VIẾT BÀI XONG!** Đang lưu trữ...")
        
        # 📝 GHI VÀO TAB REPORT
        ws_rep = sh.worksheet("Report")
        new_row = [get_vn_time().strftime("%Y-%m-%d %H:%M:%S"), kw_main, content_raw[:100] + "...", "SUCCESS"]
        ws_rep.append_row(new_row)
        
        # ✅ CẬP NHẬT TRẠNG THÁI TAB KEYWORD
        ws_kw = sh.worksheet("Keyword")
        # Tìm dòng của từ khóa để update (giả sử cột đầu là tên)
        cell = ws_kw.find(kw_main)
        ws_kw.update_cell(cell.row, 2, "SUCCESS") # Giả sử cột 2 là trạng thái
        
        st.balloons()
        st.markdown(content_raw)
    else:
        st.error("💀 Không súng nào nổ. Kiểm tra lại tiền ví và Key!")

# --- 4. GIAO DIỆN CHÍNH ---
data, sh = load_all_tabs()
if data:
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_hybrid_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
