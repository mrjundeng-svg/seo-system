import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG & KẾT NỐI ---
st.set_page_config(page_title="LAIHO.VN - ULTIMATE COMMAND CENTER", layout="wide")

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def clean_str(s):
    return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except Exception as e:
        st.error(f"Lỗi cấu hình Secrets: {e}"); return None

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        creds = get_creds()
        if not creds: return None, None
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        tabs = ["Dashboard", "Keyword", "Report"]
        data = {}
        for t in tabs:
            ws = sh.worksheet(t.strip())
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame()
            else:
                headers = [clean_str(h).upper() for h in vals[0]]
                rows = [[clean_str(cell) for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}"); return None, None

# --- 2. CÁC HÀM TIỆN ÍCH (AI & TELEGRAM) ---

def send_telegram_noti(token, chat_id, message):
    """Gửi tin nhắn báo cáo về điện thoại"""
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def call_ai(api_key, model_name, prompt, provider="groq"):
    url = "https://api.groq.com/openai/v1/chat/completions" if provider == "groq" else "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    if provider != "groq": headers["HTTP-Referer"] = "https://laiho.vn"
    payload = {"model": model_name.strip(), "messages": [{"role": "user", "content": prompt}], "temperature": 0.7}
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60).json()
        return resp['choices'][0]['message']['content']
    except: return "❌ Lỗi"

# --- 3. TIẾN TRÌNH CHẠY CÔNG NGHIỆP (BATCH POPUP) ---
@st.dialog("🚀 CHIẾN DỊCH VIẾT BÀI TỰ ĐỘNG", width="large")
def run_batch_popup(all_data, sh, num_posts):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip().str.upper() == k.strip().upper()].iloc[:, 1]
        return clean_str(res.values[0]) if not res.empty else ""

    df_kw = all_data['Keyword']
    cols = df_kw.columns.tolist()
    name_col = next((c for c in ['KW_TEXT', 'KW_NAME', 'NAME'] if c in cols), None)
    status_col = next((c for c in ['KW_STATUS', 'STATUS'] if c in cols), None)
    
    todo_list = df_kw[(df_kw[status_col] == '0') | (df_kw[status_col] == '')].head(num_posts)
    if todo_list.empty:
        st.warning("Không còn từ khóa nào để viết!"); return

    tg_token = v('TELEGRAM_BOT_TOKEN')
    tg_id = v('TELEGRAM_CHAT_ID')
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, (idx, row) in enumerate(todo_list.iterrows()):
        kw_main = row[name_col]
        status_text.write(f"⏳ **Đang xử lý {i+1}/{len(todo_list)}:** {kw_main}")
        
        prompt_final = f"Viết bài SEO về {kw_main}. Quy tắc: {v('SEO_GLOBAL_RULE')}"
        content = ""
        models = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
        
        for m_name in models:
            provider = "openrouter" if '/' in m_name else "groq"
            api_key = v('OPENROUTER_API_KEY') if provider == "openrouter" else v('GROQ_API_KEY')
            content = call_ai(api_key, m_name, prompt_final, provider)
            if "❌" not in content: break
        
        if "❌" not in content:
            try:
                # 1. Ghi Report
                ws_rep = sh.worksheet("Report")
                ws_rep.append_row([get_vn_time().strftime("%Y-%m-%d %H:%M"), kw_main, content[:100], "SUCCESS"])
                
                # 2. Cập nhật Status Keyword
                ws_kw = sh.worksheet("Keyword")
                cell = ws_kw.find(kw_main)
                ws_kw.update_cell(cell.row, 3, "SUCCESS")
                
                # 3. Bắn Telegram
                msg = f"✅ *Robot Laiho:* Đã lên bài thành công!\n\n🔑 *Từ khóa:* {kw_main}\n⏰ *Thời gian:* {get_vn_time().strftime('%H:%M:%S')}"
                if tg_token and tg_id:
                    send_telegram_noti(tg_token, tg_id, msg)
                
                st.success(f"Đã xong: {kw_main}")
                time.sleep(2)
            except Exception as e:
                st.error(f"Lỗi ghi dữ liệu: {e}")
        
        progress_bar.progress((i + 1) / len(todo_list))
    
    st.balloons()
    st.write("🏁 **CHIẾN DỊCH HOÀN TẤT!**")

# --- 4. GIAO DIỆN HOME ---
data, sh = load_all_tabs()
if data:
    st.sidebar.header("⚙️ Cấu hình Batch")
    num_to_write = st.sidebar.number_input("Số bài mỗi lần chạy", min_value=1, max_value=20, value=3)
    
    col1, col2, _ = st.columns([1.5, 1, 4])
    with col1:
        if st.button("Viết bài AI", type="primary", use_container_width=True):
            if sh: run_batch_popup(data, sh, num_to_write)
            else: st.error("Mất kết nối Sheet!")
    with col2:
        if st.button("🔄 Reload Data", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()
    st.subheader("📂 Danh sách từ khóa")
    st.dataframe(data['Keyword'], use_container_width=True, hide_index=True)
