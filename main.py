import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

# --- CONFIG ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

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
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ OK"
    except Exception as e: return None, str(e)

# --- YOAST SEO ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 25
    if kw in c_low[:300]: score += 25
    if len(words) >= 500: score += 25
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.6 <= dens <= 2.8: score += 25
    return score, round(dens, 2)

# --- AI CALLER v21.0 (CHIÊU THỨC QUÉT 6 CỔNG - DỨT ĐIỂM 404) ---
def call_ai_indestructible(key, model_input, prompt):
    # Chuẩn hóa tên model cơ bản
    m = model_input.strip().lower().replace("models/", "")
    if "flash" in m: base = "gemini-1.5-flash"
    elif "pro" in m: base = "gemini-1.5-pro"
    else: base = "gemini-1.5-flash"

    # Danh sách 6 "địa chỉ" khả thi nhất mà Google có thể dùng
    endpoints = [
        f"https://generativelanguage.googleapis.com/v1beta/models/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1/models/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1beta/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1/{base}:generateContent",
        f"https://generativelanguage.googleapis.com/v1beta/models/{base}-latest:generateContent",
        f"https://generativelanguage.googleapis.com/v1/models/{base}-latest:generateContent"
    ]
    
    last_err = ""
    for url in endpoints:
        try:
            res = requests.post(f"{url}?key={key}", json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            if res.status_code == 200:
                # Trích xuất tên cổng để báo cáo cho sếp
                gate = "v1beta" if "v1beta" in url else "v1"
                return res.json()['candidates'][0]['content']['parts'][0]['text'].strip(), f"{base} ({gate})"
            last_err = f"{url.split('/')[-2]}: {res.status_code}"
        except: continue
        
    return None, f"Cạn kiệt 6 phương án! Lỗi cuối: {last_err}"

# --- ENGINE TERMINAL ---
@st.dialog("🖥️ SYSTEM TERMINAL v21.0", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    df_web = data['Website']
    active_sites = df_web[df_web['Trạng thái'].astype(str).str.strip().str.capitalize() == 'Active']
    
    log_area = st.empty()
    log_history = [f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Kích hoạt bộ quét 6 cổng..."]
    
    def add_log(msg):
        log_history.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.code("\n".join(log_history))

    if active_sites.empty:
        add_log("❌ LỖI: Không tìm thấy Website Active!"); return

    num = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num):
        add_log(f"━━━━ Bài {i+1}/{num} ━━━━")
        site = active_sites.sample(n=1).iloc[0]
        model_name = v('MODEL_VERSION').split(',')[0].strip()
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()

        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        add_log(f"🧠 Robot đang tự tìm cổng kết nối...")

        content, meta = call_ai_indestructible(v('GEMINI_API_KEY'), model_name, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}")
        
        if not content:
            add_log(f"❌ THẤT BẠI: {meta}")
            add_log("👉 Gợi ý: Key của ní có thể bị sai hoặc bị Google khóa vùng rồi.")
            continue
        
        add_log(f"✅ ĐÃ THÔNG! Trả bài qua: {meta}")

        # SEO Audit
        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        add_log(f"📈 Yoast SEO: {score}/100 | Mật độ: {dens}%")
        
        # Ghi Report
        sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
            site['URL / ID'], site['Nền tảng'], f"{site['URL / ID']}/post-{random.randint(100,999)}", 
            datetime.now().strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", f"{dens}%", f"{score}/100", 
            site.get('các website đích',''), title, "Sapo optimized", datetime.now().strftime("%H:%M"), "Thành công", "Active"
        ])
        if sh_ok: add_log("✅ Đã ghi danh vào Report.")
        time.sleep(1)

    st.success("🎉 TẤT CẢ TIẾN TRÌNH HOÀN TẤT!")
    if st.button("❌ ĐÓNG TERMINAL", use_container_width=True): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v21.0</h1>", unsafe_allow_html=True)
if 'last_action' not in st.session_state: st.session_state.last_action = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5: st.warning("⏳ Chậm thôi ní!")
                    else:
                        st.session_state.last_action = time.time(); run_robot(data)
                if c2.button("🔄 Reload DB", use_container_width=True):
                    st.cache_data.clear(); st.rerun()
                
                disp = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask, axis=1)
                st.dataframe(disp, use_container_width=True, height=400, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
