import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json

# --- 1. SETUP HỆ THỐNG & GỌT SẠCH KHOẢNG TRẮNG ---
st.set_page_config(page_title="LAIHO.VN - ONE PIPE AI", layout="wide")

def clean_str(s):
    if not s: return ""
    return str(s).strip().replace('\u200b', '').replace('\xa0', '')

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
        st.error(f"Lỗi Sheet: {e}"); return None, None

# --- 2. HÀM GỌI AI DUY NHẤT (OPENROUTER) ---
def call_openrouter(api_key, model_name, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://laiho.vn",
        "X-Title": "Laiho SEO Robot"
    }
    # Chỉ bốc 1 cái tên model sạch sẽ
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        res_json = response.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        return f"❌ Lỗi: {res_json.get('error', {}).get('message', 'Unknown Error')}"
    except Exception as e:
        return f"❌ Lỗi kết nối: {str(e)}"

# --- 3. POPUP VIẾT BÀI AI ---
@st.dialog("⚙️ TRUNG TÂM VIẾT BÀI AI", width="large")
def run_ai_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang chuẩn bị luồng chạy đơn...**")
    kw_main = "Dịch vụ lái xe hộ" 
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    # LẤY CHÍNH XÁC 1 MODEL ĐẦU TIÊN
    raw_models = v('MODEL_VERSION')
    first_model = raw_models.split(',')[0].strip() if ',' in raw_models else raw_models.strip()
    
    # Nếu trống, ép dùng model FREE để test
    final_model = first_model if first_model else "meta-llama/llama-3.2-1b-instruct:free"

    st.info(f"🤖 Đang gọi não bộ: `{final_model}`")
    with st.spinner("Đang sản xuất nội dung..."):
        content = call_openrouter(v('OPENROUTER_API_KEY'), final_model, prompt_final)
        
        if "❌" in content:
            st.error(content)
            st.warning("👉 Kiểm tra MODEL_VERSION trên Sheet xem có đúng định dạng chưa.")
        else:
            st.success("✅ THÀNH CÔNG!")
            st.text_area("Bản thảo", content, height=400)

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    c1, _, _ = st.columns([1.5, 1, 4])
    if c1.button("Viết bài AI", type="primary", use_container_width=True):
        run_ai_popup(data, sh)
    st.divider()
    st.dataframe(data['Dashboard'], use_container_width=True, hide_index=True)
