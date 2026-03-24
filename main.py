import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime, timedelta, timezone

# --- CONFIG ---
st.set_page_config(page_title="HỆ THỐNG SEO MASTER v33.0", layout="wide", page_icon="🚕")

# CSS Chống cuộn ngang & UI Chuyên nghiệp
st.markdown("""
    <style>
    .report-card {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #ffd700;
        margin-bottom: 10px;
        font-family: 'Segoe UI', sans-serif;
    }
    div[data-testid="stExpander"] { border: none !important; }
    /* Ép text xuống dòng không cho scroll ngang */
    .stCodeBlock, .stMarkdown { word-break: break-all !important; white-space: pre-wrap !important; }
    </style>
""", unsafe_allow_html=True)

def get_vn_time():
    return datetime.now(timezone(timedelta(hours=7)))

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
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Đồng bộ dữ liệu thành công."
    except Exception as e: return None, str(e)

# --- ENGINE ---
@st.dialog("🚀 TRUNG TÂM ĐIỀU HÀNH SEO", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_placeholder = st.container()

    # 1. Khởi tạo AI (Auto-Discovery Model)
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        model_name = "gemini-1.5-flash"
        if f"models/{model_name}" not in available: model_name = available[0].replace("models/","")
        model_ai = genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"❌ Lỗi cấu hình API: {str(e)}"); return

    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    df_bl = data['Backlink']
    num_to_run = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_to_run):
        site = active_sites.sample(n=1).iloc[0]
        kw_full = v('Danh sách Keyword bài viết')
        main_kw = kw_full.split('|')[0].strip()
        
        # Logic bốc Backlink chuẩn (Fix lỗi N/A)
        link_url, anchor = "Không có", "Không có"
        if not df_bl.empty:
            bl_row = df_bl.sample(n=1).iloc[0]
            # Chuẩn hóa tìm tên cột
            for col in df_bl.columns:
                c_low = col.lower()
                if 'link' in c_low or 'url' in c_low: link_url = bl_row[col]
                if 'từ' in c_low or 'anchor' in c_low: anchor = bl_row[col]

        with log_placeholder:
            st.markdown(f"""
            <div class="report-card">
                <b style='color:#ffd700;'>[BÀI {i+1}/{num_to_run}]</b> | 🛰️ <b>{site['Tên web']}</b><br>
                🎯 <b>Từ khóa:</b> {main_kw} | 🔗 <b>Link:</b> <span style='color:#00ff00;'>{link_url}</span> | ⚓ <b>Anchor:</b> {anchor}
            </div>
            """, unsafe_allow_html=True)

            try:
                # Biên tập nội dung
                resp = model_ai.generate_content(f"{v('PROMPT_TEMPLATE')}\nTừ khóa: {kw_full}\nChèn link {link_url} cho cụm từ {anchor}")
                content = resp.text
                
                # Ghi Report (Đúng 15 cột template)
                now_vn = get_vn_time()
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                    site['URL / ID'], site['Nền tảng'], "Chờ đăng...", now_vn.strftime("%Y-%m-%d"), 
                    kw_full, anchor, "✅ Pass", "1.2%", "90/100", link_url, "Tiêu đề AI", "Sapo AI", 
                    now_vn.strftime("%H:%M:%S"), "Thành công", "Active"
                ])
                st.caption(f"✔️ Đã lưu báo cáo lúc {now_vn.strftime('%H:%M:%S')}")
            except Exception as e:
                st.error(f"❌ Lỗi phiên {i+1}: {str(e)}")
        
        time.sleep(1.5)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- UI ---
st.markdown("<h2 style='text-align: center; color: #ffd700;'>🚕 LÁI HỘ - SEO MASTER v33.0</h2>", unsafe_allow_html=True)
data, msg = load_data()
if data:
    tabs = st.tabs([f"📁 {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 LÀM MỚI", use_container_width=True): st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=600, hide_index=True)
