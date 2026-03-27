import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json

# --- 1. TIỆN ÍCH HỆ THỐNG & FIX LỖI "GET_CREDS" ---
st.set_page_config(page_title="LAIHO.VN - GROQ AI WRITER", layout="wide")

def clean_str(s):
    """Hàm TRIM: Gọt sạch khoảng trắng để trị lỗi Invalid Key/Model"""
    return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_creds():
    """Hàm mở cửa Google Sheet - Đã fix lỗi Undefined"""
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

# --- 2. HÀM GỌI GROQ (SỨC MẠNH CHÍNH) ---
def call_groq(api_key, model_name, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "Bạn là chuyên gia viết bài SEO chuyên nghiệp cho laiho.vn"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        res_json = response.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        return f"❌ Lỗi Groq: {res_json.get('error', {}).get('message', 'Lỗi không xác định')}"
    except Exception as e:
        return f"❌ Lỗi kết nối: {str(e)}"

# --- 3. TRUNG TÂM VIẾT BÀI AI (POPUP) ---
@st.dialog("⚙️ HỆ THỐNG VIẾT BÀI AI (GROQ MODE)", width="large")
def run_groq_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang kiểm tra chìa khóa và từ khóa...**")
    
    # Logic bốc từ khóa (Demo)
    kw_main = "Dịch vụ lái xe hộ chuyên nghiệp" 
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    # 🛠️ LOGIC TÁCH MODEL THÔNG MINH
    raw_models = v('MODEL_VERSION')
    # Tìm model đầu tiên có chứa chữ 'llama' hoặc 'mixtral' (Model của Groq)
    model_list = [m.strip() for m in raw_models.split(',') if m.strip()]
    target_model = next((m for m in model_list if any(x in m.lower() for x in ['llama', 'mixtral'])), "llama-3.1-70b-versatile")

    st.info(f"🚀 Đang triệu hồi Groq: `{target_model}`")
    
    with st.spinner("Groq đang 'múa phím' bài viết..."):
        content = call_groq(v('GROQ_API_KEY'), target_model, prompt_final)
        
        if "❌" in content:
            st.error(content)
            st.warning("👉 Kiểm tra Key Groq (gsk_...) hoặc danh sách Model trên Sheet.")
        else:
            st.success("✅ THÀNH CÔNG RỰC RỠ!")
            st.text_area("Bản thảo từ Groq", content, height=450)

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_groq_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    st.dataframe(data['Dashboard'], use_container_width=True, hide_index=True)
