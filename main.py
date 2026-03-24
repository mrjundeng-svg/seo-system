import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="LÁI HỘ MASTER v26.0", layout="wide", page_icon="🚕")

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=30)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- ENGINE TERMINAL (DEEP DEBUG) ---
@st.dialog("🖥️ SYSTEM TERMINAL v26.0 (OFFICIAL SDK)", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_area = st.empty()
    log_h = [f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 BẮT ĐẦU RÀ SOÁT TỔNG THỂ..."]
    
    def add_log(msg):
        log_h.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_h))

    # --- BƯỚC 1: KIỂM TRA ĐỘNG CƠ (SDK) ---
    api_key = v('GEMINI_API_KEY')
    add_log(f"🔑 Đang cấu hình API Key...")
    try:
        genai.configure(api_key=api_key)
        # Tự động tìm Model khả dụng
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        add_log(f"✅ Kết nối thành công! Các Model sếp có thể dùng: {', '.join([m.split('/')[-1] for m in available_models[:3]])}")
        
        # Chọn model phù hợp (ưu tiên flash)
        target = "models/gemini-1.5-flash"
        if target not in available_models:
            target = available_models[0] # Bốc đại cái đầu tiên nếu không có flash
        model = genai.GenerativeModel(target.split('/')[-1])
        add_log(f"🎯 Robot đã chọn Model: **{target.split('/')[-1]}**")
    except Exception as e:
        add_log(f"❌ LỖI API: {str(e)}")
        add_log("💡 Gợi ý: Hãy kiểm tra xem API Key có bị thừa dấu cách không, hoặc tạo Key mới tại AI Studio.")
        return

    # --- BƯỚC 2: KIỂM TRA WEBSITE ---
    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.strip().str.capitalize() == 'Active']
    if active_sites.empty:
        add_log("❌ LỖI: Không tìm thấy website nào 'Active' trong Tab Website.")
        return
    add_log(f"🛰️ Đã sẵn sàng {len(active_sites)} vệ tinh.")

    # --- BƯỚC 3: VÍT GA ---
    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━━━━━ Bài {i+1}/{num} ━━━━━━━━")
        site = active_sites.sample(n=1).iloc[0]
        add_log(f"🚀 Vệ tinh: {site['Tên web']}")
        
        try:
            add_log("🧠 AI đang đúc bài...")
            response = model.generate_content(v('PROMPT_TEMPLATE'))
            content = response.text
            
            add_log("✅ AI trả bài thành công. Đang ghi danh vào Report...")
            # Ghi báo cáo
            gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), "Keyword", "", "✅", "1%", "100/100", site.get('các website đích',''), "Tiêu đề AI", "Sapo AI", datetime.now().strftime("%H:%M"), "Thành công", "Active"
            ])
            add_log(f"✨ HOÀN TẤT BÀI {i+1}")
        except Exception as e:
            add_log(f"❌ Lỗi khi đang chạy: {str(e)}")
        
        time.sleep(2)

    st.success("🎉 TẤT CẢ TIẾN TRÌNH ĐÃ KẾT THÚC!")
    if st.button("KẾT THÚC & ĐÓNG"): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v26.0</h1>", unsafe_allow_html=True)
if 'last_act' not in st.session_state: st.session_state.last_act = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_act < 5: st.warning("⏳ Chậm lại ní!")
                    else:
                        st.session_state.last_act = time.time(); run_robot(data)
                if c2.button("🔄 Reload", use_container_width=True):
                    st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, hide_index=True)
else:
    st.error(f"❌ {msg}")
    st.info("💡 Nếu thấy lỗi ModuleNotFoundError: Hãy Reboot App trong Manage App nhé!")
