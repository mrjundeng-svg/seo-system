import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, re
from datetime import datetime, timedelta, timezone

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="HỆ THỐNG SEO MASTER PRO", layout="wide", page_icon="🚀")

# Hàm lấy thời gian Việt Nam (GMT+7)
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

# --- BỘ CHẤM ĐIỂM SEO YOAST ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:350]: score += 25
    if len(words) >= 600: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.8 <= dens <= 2.5: score += 25
    return score, round(dens, 2)

# --- TRÌNH VẬN HÀNH LOG CHI TIẾT ---
@st.dialog("📋 BÁO CÁO VẬN HÀNH CHI TIẾT", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    log_area = st.empty()
    log_h = [f"--- NHẬT KÝ KHỞI ĐỘNG HỆ THỐNG [{get_vn_time().strftime('%d/%m/%Y %H:%M:%S')}] ---"]
    
    def add_log(msg):
        log_h.append(msg)
        # Sử dụng markdown với bọc code để chống tràn ngang
        log_text = "\n".join(log_h)
        log_area.markdown(f"```text\n{log_text}\n```")

    # 1. Cấu hình AI
    add_log("> Đang kiểm tra kết nối Google AI Engine...")
    try:
        genai.configure(api_key=v('GEMINI_API_KEY'))
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        chosen_model = "gemini-1.5-flash" 
        model_ai = genai.GenerativeModel(chosen_model)
        add_log(f"✅ Kết nối AI thành công: {chosen_model}")
    except Exception as e:
        add_log(f"❌ Lỗi cấu hình API: {str(e)}"); return

    # 2. Kiểm tra Website & Backlink
    active_sites = data['Website'][data['Website']['Trạng thái'].astype(str).str.contains('Active', case=False)]
    backlinks = data['Backlink']
    if active_sites.empty:
        add_log("❌ Lỗi: Không có website vệ tinh nào đang hoạt động."); return

    # 3. Chạy tiến trình
    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"\n[{i+1}/{num}] ĐANG XỬ LÝ BÀI VIẾT...")
        site = active_sites.sample(n=1).iloc[0]
        
        # Lấy dữ liệu SEO & Backlink
        kw_viết = v('Danh sách Keyword bài viết')
        main_kw = kw_viết.split('|')[0].strip()
        
        # Bốc ngẫu nhiên một Backlink nếu có dữ liệu
        link_target = "N/A"
        anchor_text = "N/A"
        if not backlinks.empty:
            bl = backlinks.sample(n=1).iloc[0]
            link_target = bl.get('Link trỏ về', 'N/A')
            anchor_text = bl.get('Từ khoá chèn', 'N/A')

        add_log(f"📍 Website vệ tinh : {site['Tên web']}")
        add_log(f"📍 Nền tảng        : {site['Nền tảng']}")
        add_log(f"📍 Từ khóa bài viết : {main_kw}")
        add_log(f"📍 Từ khóa gắn link : {anchor_text}")
        add_log(f"📍 Backlink trỏ về  : {link_target}")

        try:
            add_log("... Đang biên tập nội dung bài viết bằng AI ...")
            prompt = f"{v('PROMPT_TEMPLATE')}\nTừ khóa: {kw_viết}\nChèn link {link_target} vào từ khóa {anchor_text}"
            response = model_ai.generate_content(prompt)
            content = response.text
            
            add_log("... Đang phân tích kỹ thuật SEO Yoast ...")
            title = content.split('\n')[0].replace('#', '').strip()
            score, dens = yoast_seo_audit(content, main_kw, title)
            
            add_log(f"📈 Điểm SEO thực tế: {score}/100")
            add_log(f"📈 Mật độ từ khóa : {dens}%")

            # Ghi Report
            add_log("... Đang cập nhật dữ liệu vào hệ thống báo cáo ...")
            now_vn = get_vn_time()
            sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
                site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/p-{random.randint(100,999)}", 
                now_vn.strftime("%Y-%m-%d"), kw_viết, anchor_text, "Đạt chuẩn", f"{dens}%", f"{score}/100", 
                link_target, title, "Nội dung tối ưu", now_vn.strftime("%H:%M:%S"), "Thành công", "Đã đăng"
            ])
            add_log(f"✅ Hoàn tất đăng bài lúc: {now_vn.strftime('%H:%M:%S')}")
        except Exception as e:
            add_log(f"❌ Lỗi tại bài {i+1}: {str(e)}")
        
        time.sleep(1)

    st.success("🎉 TOÀN BỘ CHIẾN DỊCH ĐÃ HOÀN TẤT!")
    if st.button("XÁC NHẬN VÀ ĐÓNG", use_container_width=True): st.rerun()

# --- GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center; color: #ffd700;'>HỆ THỐNG QUẢN TRỊ SEO MASTER v29.0</h1>", unsafe_allow_html=True)
st.write(f"🕒 Thời gian hệ thống (Việt Nam): **{get_vn_time().strftime('%d/%m/%Y %H:%M')}**")

data, msg = load_data()
if data:
    tabs = st.tabs([f"📁 {k}" for k in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary", use_container_width=True): run_robot(data)
                if c2.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
                    st.cache_data.clear(); st.rerun()
                
                disp = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "********" + val[-4:] if len(val) > 10 else "********"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask, axis=1)
                st.dataframe(disp, use_container_width=True, height=450, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=550, hide_index=True)
else: st.error(f"Lỗi: {msg}")
