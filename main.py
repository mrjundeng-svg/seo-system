import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH ---
st.set_page_config(page_title="SEO MASTER PRO", layout="wide", page_icon="📈")

def get_vn_time():
    return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=60)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Đồng bộ dữ liệu thành công."
    except Exception as e: return None, str(e)

# --- ENGINE ---
@st.dialog("📋 BÁO CÁO VẬN HÀNH CHI TIẾT", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    # CSS Ép Log xuống dòng, không cho hiện thanh cuộn ngang
    st.markdown("""
        <style>
            [data-testid="stExpander"] div, .stMarkdown div {
                word-break: break-all;
                white-space: pre-wrap;
            }
        </style>
    """, unsafe_allow_html=True)

    log_area = st.empty()
    log_h = [f"### NHẬT KÝ VẬN HÀNH - {get_vn_time().strftime('%H:%M:%S')}"]
    
    def add_log(msg, color="white"):
        log_h.append(f"<div style='color:{color}; font-family: monospace; border-bottom: 1px dashed #444; padding: 5px 0;'>{msg}</div>")
        log_area.markdown("\n".join(log_h), unsafe_allow_html=True)

    # 1. Khởi tạo AI
    add_log("⚙️ Đang thiết lập kết nối Google AI Studio...")
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        chosen = "models/gemini-1.5-flash" if "models/gemini-1.5-flash" in models else models[0]
        model_ai = genai.GenerativeModel(chosen.replace("models/", ""))
        add_log(f"✅ Đã thông kết nối. Sử dụng: {chosen}", "#00ff00")
    except Exception as e:
        add_log(f"❌ Lỗi API: {str(e)}", "red"); return

    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    backlinks = data['Backlink']
    num_to_run = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_to_run):
        add_log(f"<b>[BÀI {i+1}/{num_to_run}] ĐANG XỬ LÝ...</b>", "#ffd700")
        site = active_sites.sample(n=1).iloc[0]
        kw_list = v('Danh sách Keyword bài viết')
        main_kw = kw_list.split('|')[0].strip()
        link_url, anchor = "N/A", "N/A"
        if not backlinks.empty:
            bl_row = backlinks.sample(n=1).iloc[0]
            link_url, anchor = bl_row.get('Link trỏ về', 'N/A'), bl_row.get('Từ khoá chèn', 'N/A')

        add_log(f"📍 Website: {site['Tên web']} | Từ khóa: {main_kw}")
        add_log(f"🔗 Link: {link_url} | Anchor: {anchor}")

        success = False
        retries = 0
        while not success and retries < 3: # Thử lại tối đa 3 lần nếu gặp 429
            try:
                add_log("... AI đang biên tập nội dung chuyên sâu ...")
                response = model_ai.generate_content(f"{v('PROMPT_TEMPLATE')}\nTừ khóa: {kw_list}\nChèn link {link_url} vào {anchor}")
                content = response.text
                
                add_log("... Đang cập nhật báo cáo vào Google Sheet ...")
                now_vn = get_vn_time()
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                    site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/p-{random.randint(100,999)}", 
                    now_vn.strftime("%Y-%m-%d"), kw_list, anchor, "✅", "1.2%", "85/100", 
                    link_url, "Tiêu đề", "Sapo", now_vn.strftime("%H:%M:%S"), "Thành công", "Active"
                ])
                add_log(f"✅ Hoàn tất lúc: {now_vn.strftime('%H:%M:%S')}", "#00ffff")
                success = True
            except Exception as e:
                if "429" in str(e):
                    retries += 1
                    add_log(f"⚠️ Hết lượt dùng (429). Đang đợi 30 giây để thử lại (Lần {retries})...", "orange")
                    time.sleep(32) # Đợi 32 giây cho chắc
                else:
                    add_log(f"❌ Lỗi phát sinh: {str(e)}", "red")
                    break
        time.sleep(2)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- UI ---
st.markdown("<h2 style='text-align: center; color: #ffd700;'>HỆ THỐNG SEO MASTER v31.0</h2>", unsafe_allow_html=True)

data, msg = load_data()
if data:
    tabs = st.tabs([f"📂 {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
                    st.cache_data.clear(); st.rerun()
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=550, hide_index=True)
else: st.error(f"Lỗi: {msg}")
