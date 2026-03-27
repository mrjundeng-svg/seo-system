import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG & TRIM DỮ LIỆU ---
st.set_page_config(page_title="LAIHO.VN AI WRITER", layout="wide")

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

# --- 2. HÀM GỌI AI (OPENROUTER DUY NHẤT) ---
def call_openrouter(api_key, model_name, prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://laiho.vn", # Để OpenRouter không báo lỗi auth
        "X-Title": "Laiho SEO Robot"
    }
    # Nếu Dashboard trống, dùng model miễn phí để test
    target_model = model_name.strip() if model_name else "meta-llama/llama-3.2-1b-instruct:free"
    
    payload = {
        "model": target_model,
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

    st.write("🔄 **Đang kiểm tra chìa khóa vạn năng...**")
    
    kw_main = "Dịch vụ lái xe hộ chuyên nghiệp" # Demo bốc từ khóa
    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"

    api_key = v('OPENROUTER_API_KEY')
    model_name = v('MODEL_VERSION')

    st.info(f"🤖 Đang gọi não bộ: `{model_name if model_name else 'Model Free'}`")
    
    with st.spinner("Đang sản xuất nội dung..."):
        content = call_openrouter(api_key, model_name, prompt_final)
        
        if "❌" in content:
            st.error(content)
            st.warning("👉 Nếu lỗi 'No endpoints', bồ hãy đổi MODEL_VERSION thành model miễn phí (xem bên dưới).")
        else:
            st.success("✅ THÀNH CÔNG!")
            st.text_area("Bản thảo AI", content, height=400)
            # Sau đó bồ thêm logic ghi Sheet vào đây là xong bài.

# --- 4. GIAO DIỆN TRANG CHỦ ---
data, sh = load_all_tabs()
if data:
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            run_ai_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
