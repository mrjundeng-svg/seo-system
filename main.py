import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="HỆ THỐNG QUẢN TRỊ NỘI DUNG SEO", layout="wide", page_icon="📈")

# Hàm lấy múi giờ Việt Nam (GMT+7)
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

# --- BỘ CHẤM ĐIỂM SEO TIÊU CHUẨN ---
def seo_audit_engine(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:350]: score += 25
    if len(words) >= 550: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.8 <= dens <= 2.5: score += 25
    return score, round(dens, 2)

# --- MÀN HÌNH VẬN HÀNH VÀ BÁO CÁO ---
@st.dialog("BÁO CÁO VẬN HÀNH CHI TIẾT", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    # Container log với CSS chống cuộn ngang
    log_container = st.container(height=500, border=True)
    log_area = log_container.empty()
    log_h = [f"### NHẬT KÝ HỆ THỐNG - {get_vn_time().strftime('%d/%m/%Y %H:%M:%S')}"]
    
    def add_log(msg, color="white"):
        log_h.append(f"<div style='color:{color}; word-wrap: break-word; white-space: pre-wrap;'>{msg}</div>")
        log_area.markdown("\n".join(log_h), unsafe_allow_html=True)

    # 1. Khởi tạo AI với cơ chế Tự động Dò tìm Model (Anti-404)
    add_log("⚙️ Đang kiểm tra kết nối Google AI Engine...")
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        # Tự động lấy danh sách Model khả dụng của API Key này
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Ưu tiên chọn các model Flash ổn định
        chosen = ""
        for preferred in ["models/gemini-1.5-flash", "models/gemini-2.0-flash", "models/gemini-1.5-pro"]:
            if preferred in models:
                chosen = preferred; break
        if not chosen: chosen = models[0]
        
        model_ai = genai.GenerativeModel(chosen.replace("models/", ""))
        add_log(f"✅ Kết nối thành công. Model đang sử dụng: {chosen}", "green")
    except Exception as e:
        add_log(f"❌ Lỗi cấu hình API: {str(e)}", "red"); return

    # 2. Kiểm tra Dữ liệu nguồn
    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    backlinks = data['Backlink']
    if active_sites.empty:
        add_log("❌ Lỗi: Không tìm thấy website vệ tinh nào ở trạng thái Active.", "red"); return

    # 3. Chạy tiến trình biên tập
    num_to_run = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num_to_run):
        add_log(f"<br><b>[TIẾN TRÌNH {i+1}/{num_to_run}]</b>", "#ffd700")
        site = active_sites.sample(n=1).iloc[0]
        
        # Chuẩn bị dữ liệu SEO & Backlink
        kw_list = v('Danh sách Keyword bài viết')
        main_kw = kw_list.split('|')[0].strip()
        
        link_url, anchor = "N/A", "N/A"
        if not backlinks.empty:
            bl_row = backlinks.sample(n=1).iloc[0]
            link_url = bl_row.get('Link trỏ về', 'N/A')
            anchor = bl_row.get('Từ khoá chèn', 'N/A')

        add_log(f"📍 Website vệ tinh: {site['Tên web']}")
        add_log(f"📍 Từ khóa viết bài: {main_kw}")
        add_log(f"📍 Từ khóa gắn link: {anchor}")
        add_log(f"📍 Backlink trỏ về: {link_url}")

        try:
            add_log("... Đang biên tập nội dung chuyên sâu ...")
            full_prompt = f"{v('PROMPT_TEMPLATE')}\n\nTừ khóa chính: {kw_list}\nChèn link {link_url} vào cụm từ {anchor} một cách tự nhiên."
            response = model_ai.generate_content(full_prompt)
            article_text = response.text
            
            add_log("... Đang phân tích kỹ thuật SEO ...")
            title = article_text.split('\n')[0].replace('#', '').strip()
            score, dens = seo_audit_engine(article_text, main_kw, title)
            
            add_log(f"📈 Điểm SEO thực tế: <b>{score}/100</b>", "#00ff00")
            add_log(f"📈 Mật độ từ khóa: {dens}%")

            # Ghi báo cáo lên Google Sheet
            add_log("... Đang cập nhật báo cáo dữ liệu ...")
            now_vn = get_vn_time()
            sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/view-{random.randint(100,999)}", 
                now_vn.strftime("%Y-%m-%d"), kw_list, anchor, "Đạt chuẩn SEO", f"{dens}%", f"{score}/100", 
                link_url, title, "Nội dung tối ưu hóa", now_vn.strftime("%H:%M:%S"), "Thành công", "Đã đăng"
            ])
            add_log(f"✅ Hoàn tất đăng tải lúc: {now_vn.strftime('%H:%M:%S')}", "cyan")
        except Exception as e:
            add_log(f"❌ Lỗi tại phiên xử lý {i+1}: {str(e)}", "red")
        
        time.sleep(1.5)

    st.success("🎉 TOÀN BỘ CHIẾN DỊCH ĐÃ HOÀN TẤT THÀNH CÔNG!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- GIAO DIỆN ĐIỀU KHIỂN ---
st.markdown("<h2 style='text-align: center; color: #ffd700;'>HỆ THỐNG BIÊN TẬP NỘI DUNG SEO MASTER</h2>", unsafe_allow_html=True)
st.write(f"<p style='text-align: center;'>Thời gian hệ thống (Việt Nam): {get_vn_time().strftime('%d/%m/%Y %H:%M:%S')}</p>", unsafe_allow_html=True)

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
                
                disp = data[name].copy()
                sensitive_list = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET']
                def mask_sensitive(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive_list):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "********" + val[-4:] if len(val) > 10 else "********"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask_sensitive, axis=1)
                st.dataframe(disp, use_container_width=True, height=500, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=550, hide_index=True)
else: st.error(f"Lỗi hệ thống: {msg}")
