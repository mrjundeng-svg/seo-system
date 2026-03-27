import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & LÀM SẠCH DỮ LIỆU ---
st.set_page_config(page_title="LAIHO.VN - SEO MASTER V14", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def clean_str(s):
    return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        
        tabs = ["Dashboard", "Website", "Keyword", "Image", "Report"]
        data = {}
        for t in tabs:
            ws = sh.worksheet(t.strip())
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame()
            else:
                # 🛡️ VIẾT HOA + TRIM TOÀN BỘ TIÊU ĐỀ
                headers = [clean_str(h).upper() for h in vals[0]]
                rows = [[clean_str(cell) for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. HÀM GỌI AI (GIỮ NGUYÊN PHƯƠNG ÁN SONG KIẾM) ---
def call_ai(api_key, model_name, prompt, provider="groq"):
    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "groq" else "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    if provider != "groq": headers["HTTP-Referer"] = "https://laiho.vn"
    
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60).json()
        return resp['choices'][0]['message']['content']
    except: return "❌ Lỗi API"

# --- 3. TRUNG TÂM VIẾT BÀI AI (POPUP) ---
@st.dialog("⚙️ HỆ THỐNG VIẾT BÀI AI (AUTO-MAPPING)", width="large")
def run_hybrid_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().str.upper() == k.strip().upper()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    st.write("🔄 **Đang dò tìm cột dữ liệu...**")
    
    # 🔍 MẮT THẦN: TỰ ĐỘNG KHỚP TÊN CỘT THEO SHEET CỦA BỒ
    df_kw = all_data['Keyword']
    cols = df_kw.columns.tolist()
    
    # Tìm cột chứa từ khóa: Ưu tiên KW_TEXT (như trong ảnh bồ gửi) rồi đến KW_NAME
    name_col = next((c for c in ['KW_TEXT', 'KW_NAME', 'NAME'] if c in cols), None)
    # Tìm cột chứa trạng thái: Ưu tiên KW_STATUS rồi đến STATUS
    status_col = next((c for c in ['KW_STATUS', 'STATUS'] if c in cols), None)
    
    if not name_col or not status_col:
        st.error(f"❌ Không tìm thấy cột từ khóa hoặc trạng thái! Cột hiện có: {cols}")
        return

    # 📋 LỌC TỪ KHÓA: Dựa trên ảnh bồ gửi, trạng thái đang là số (0, 1, 2...)
    # Tui sẽ viết cho những từ khóa có STATUS = '0' hoặc trống
    available_kw = df_kw[(df_kw[status_col] == '0') | (df_kw[status_col] == '')]
    
    if available_kw.empty:
        st.warning("Đã hết từ khóa cần xử lý (Status = 0)!"); return
    
    target_row = available_kw.iloc[0]
    kw_main = target_row[name_col]
    st.info(f"🔑 Đang 'múa phím' cho từ khóa: **{kw_main}**")

    prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"
    content_raw = ""
    models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
    
    for m_name in models_to_try:
        provider = "openrouter" if '/' in m_name else "groq"
        api_key = v('OPENROUTER_API_KEY') if provider == "openrouter" else v('GROQ_API_KEY')
        
        st.write(f"⏳ Thử {provider}: `{m_name}`")
        res = call_ai(api_key, m_name, prompt_final, provider)
        if "❌" not in res: content_raw = res; break
            
    if content_raw:
        st.success("✅ **VIẾT XONG!** Đang lưu báo cáo...")
        
        # 📝 GHI REPORT
        ws_rep = sh.worksheet("Report")
        ws_rep.append_row([get_vn_time().strftime("%Y-%m-%d %H:%M"), kw_main, content_raw[:150], "SUCCESS"])
        
        # ✅ CẬP NHẬT TRẠNG THÁI (Đổi từ 0 thành 1 hoặc SUCCESS)
        ws_kw = sh.worksheet("Keyword")
        cell = ws_kw.find(kw_main)
        # Ghi 'SUCCESS' hoặc '1' vào cột Status (cột C theo ảnh bồ gửi)
        ws_kw.update_cell(cell.row, 3, "SUCCESS") 
        
        st.balloons()
        st.markdown(content_raw)
    else:
        st.error("💀 Không súng nào nổ. Kiểm tra lại Key/Tiền ví.")

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    if st.button("Viết bài AI", type="primary", use_container_width=True):
        run_hybrid_popup(data, sh)
    st.divider()
    # Hiển thị Keyword để bồ xem Robot đã bốc đúng chưa
    st.subheader("📂 Dữ liệu từ khóa hiện tại")
    st.dataframe(data['Keyword'], use_container_width=True, hide_index=True)
