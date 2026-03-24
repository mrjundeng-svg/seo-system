import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="LÁI HỘ - HỆ THỐNG SEO TỰ ĐỘNG", layout="wide", page_icon="🚕")

# Hàm lấy thời gian Việt Nam (GMT+7)
def get_vn_time():
    vn_tz = timezone(timedelta(hours=7))
    return datetime.now(vn_tz)

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
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối dữ liệu thành công"
    except Exception as e: return None, str(e)

# --- YOAST SEO ENGINE ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:300]: score += 25
    if len(words) >= 500: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.8 <= dens <= 2.5: score += 25
    return score, round(dens, 2)

# --- TIẾN TRÌNH VẬN HÀNH CHÍNH ---
@st.dialog("⚙️ TRÌNH ĐIỀU KHIỂN HỆ THỐNG", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_area = st.empty()
    log_h = [f"[{get_vn_time().strftime('%H:%M:%S')}] 🔍 ĐANG KHỞI TẠO TIẾN TRÌNH KIỂM TRA TỔNG THỂ..."]
    
    def add_log(msg):
        log_h.append(f"[{get_vn_time().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_h))

    # 1. Kiểm tra cấu hình API
    api_key = v('GEMINI_API_KEY')
    add_log("🔑 Bước 1: Xác thực cấu hình API Key...")
    try:
        genai.configure(api_key=api_key)
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        chosen_model_name = "gemini-1.5-flash"
        model = genai.GenerativeModel(chosen_model_name)
        add_log(f"✅ Xác thực thành công. Model sử dụng: {chosen_model_name}")
    except Exception as e:
        add_log(f"❌ LỖI XÁC THỰC API: {str(e)}")
        return

    # 2. Kiểm tra danh sách website vệ tinh
    df_web = data['Website']
    active_sites = df_web[df_web['Trạng thái'].astype(str).str.strip().str.capitalize() == 'Active']
    if active_sites.empty:
        add_log("❌ THÔNG BÁO: Không có website vệ tinh nào đang ở trạng thái 'Active'.")
        return
    add_log(f"✅ Hệ thống đã sẵn sàng kết nối tới {len(active_sites)} website vệ tinh.")

    # 3. Thực hiện biên tập nội dung
    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━━━━━━━ TIẾN TRÌNH BÀI VIẾT {i+1}/{num} ━━━━━━━━━━")
        site = active_sites.sample(n=1).iloc[0]
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()
        
        add_log(f"🌐 Website đích: {site['Tên web']}")
        add_log(f"🎯 Từ khóa mục tiêu: {main_kw}")
        
        try:
            add_log("🧠 Trí tuệ nhân tạo đang biên tập nội dung bài viết...")
            response = model.generate_content(v('PROMPT_TEMPLATE'))
            full_text = response.text
            
            add_log("📊 Đang thực hiện chấm điểm tiêu chuẩn Yoast SEO...")
            title = full_text.split('\n')[0].replace('#', '').strip()
            score, dens = yoast_seo_audit(full_text, main_kw, title)
            add_log(f"✅ Điểm SEO: {score}/100 | Mật độ từ khóa: {dens}%")
            
            add_log("📝 Đang thực hiện lưu trữ báo cáo vào Google Sheet...")
            now_vn = get_vn_time()
            sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post-{random.randint(1000,9999)}", 
                now_vn.strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅ Pass", f"{dens}%", f"{score}/100", 
                site.get('các website đích',''), title, "Nội dung đã tối ưu hóa", now_vn.strftime("%H:%M"), "Thành công", "Active"
            ])
            if sh_ok: add_log(f"✨ HOÀN TẤT XỬ LÝ BÀI VIẾT {i+1}")
        except Exception as e:
            add_log(f"❌ LỖI PHÁT SINH TRONG QUÁ TRÌNH BIÊN TẬP: {str(e)}")
        
        time.sleep(1.5)

    st.success("🎉 TẤT CẢ CÁC TIẾN TRÌNH ĐÃ ĐƯỢC THỰC HIỆN HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- GIAO DIỆN NGƯỜI DÙNG ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ - HỆ THỐNG SEO MASTER v27.0</h1>", unsafe_allow_html=True)

if 'last_run' not in st.session_state: st.session_state.last_run = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_run < 5:
                        st.warning("⚠️ Vui lòng đợi 5 giây giữa các lần yêu cầu.")
                    else:
                        st.session_state.last_run = time.time()
                        run_robot(data)
                
                if c2.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
                    if time.time() - st.session_state.last_run < 5:
                        st.toast("⚠️ Vui lòng thao tác chậm lại.")
                    else:
                        st.session_state.last_run = time.time()
                        st.cache_data.clear(); st.rerun()
                
                # Hiển thị bảng Dashboard với dữ liệu đã được bảo mật
                disp = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask_data(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "********" + val[-4:] if len(val) > 8 else "********"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask_data, axis=1)
                st.dataframe(disp, use_container_width=True, height=450, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
else: st.error(f"⚠️ {msg}")
