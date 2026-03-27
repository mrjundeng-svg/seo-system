import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json

# --- 1. TIỆN ÍCH HỆ THỐNG & FIX LỖI "GET_CREDS" ---
st.set_page_config(page_title="LAIHO.VN - TEST GROQ ENGINE", layout="wide")

def clean_str(s):
    """Hàm TRIM: Gọt sạch khoảng trắng để trị lỗi Invalid Key"""
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

# --- 2. HÀM GỌI GROQ (SÚNG CHÍNH HIỆN TẠI) ---
def call_groq(api_key, model_name, prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    # Nếu bồ để trống model, tui lấy con Llama 3 ổn định nhất cho bồ
    target_model = model_name.strip() if model_name else "llama-3.1-70b-versatile"
    
    payload = {
        "model": target_model,
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

    st.write("🔄 **Đang kiểm tra chìa khóa Groq...**")
    
    # Giả lập prompt
    kw_main = "Dịch vụ thuê tài xế lái xe hộ" 
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    api_key = v('GROQ_API_KEY')
    model_name = v('MODEL_VERSION')

    st.info(f"🚀 Đang dùng não bộ Groq: `{model_name if model_name else 'llama-3.1-70b-versatile'}`")
    
    with st.spinner("Groq đang viết bài cực nhanh..."):
        content = call_groq(api_key, model_name, prompt_final)
        
        if "❌" in content:
            st.error(content)
            st.warning("👉 Kiểm tra lại Key Groq (phải bắt đầu bằng gsk_) hoặc đổi Model khác.")
        else:
            st.success("✅ THÀNH CÔNG RỰC RỠ!")
            st.text_area("Bản thảo AI (Groq)", content, height=450)

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
