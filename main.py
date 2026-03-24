import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

# --- CONFIG & CONNECTION ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

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
        return {t: pd.DataFrame(sh.worksheet(t).get_all_records()) for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]}, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

# --- YOAST SEO AUDIT ---
def yoast_seo_audit(content, keyword, title):
    score, kw = 0, str(keyword).lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 20
    if kw in c_low[:300]: score += 20
    if len(words) >= 600: score += 20
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.5 <= dens <= 2.5: score += 20
    if "##" in content or "<h3>" in c_low: score += 20
    return score, round(dens, 2)

# --- AI CALLER (ANTI-404 ENGINE) ---
def call_ai_robust(key, model_name, prompt):
    # Tự động thử các biến thể tên model để tránh lỗi 404
    name = model_name.strip()
    # Nếu sếp gõ gemini-1.5-flash, tui sẽ thử cả bản -latest nếu lỗi
    candidates = [name, f"{name}-latest", f"models/{name}"]
    
    last_err = ""
    for cand in candidates:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{cand}:generateContent?key={key}"
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            res_j = res.json()
            if res.status_code == 200:
                return res_j['candidates'][0]['content']['parts'][0]['text'].strip(), "OK"
            last_err = res_j.get('error', {}).get('message', 'Lỗi 404')
        except Exception as e: last_err = str(e)
    
    return None, f"Lỗi: {last_err} (Đã thử {len(candidates)} tên model)"

def update_report(row):
    try:
        sh = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
        return True
    except: return False

# --- ENGINE TERMINAL (LINE-BY-LINE) ---
@st.dialog("🖥️ SYSTEM TERMINAL (DEEP DEBUG)", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    
    # --- LOGGING SETUP ---
    log_placeholder = st.empty()
    log_list = [f"[{datetime.now().strftime('%H:%M:%S')}] root@seo:~# Khởi động hệ thống..."]
    
    def add_log(msg):
        log_list.append(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_placeholder.code("\n".join(log_list)) # Nhả log xuống dòng tăm tắp

    num_to_gen = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num_to_gen):
        add_log(f"━━━━━ BÀI {i+1}/{num_to_gen} ━━━━━")
        site = active_sites.sample(n=1).iloc[0]
        model_list = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
        chosen_model = random.choice(model_list)
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()

        add_log(f"🛰 Vệ tinh: {site['Tên web']}")
        add_log(f"🧠 AI: Đang dùng {chosen_model}...")

        # AI Gen
        content, err = call_ai_robust(v('GEMINI_API_KEY'), chosen_model, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}")
        
        if not content:
            add_log(f"❌ LỖI RỒI! LÝ DO: {err}")
            add_log("👉 Cách sửa: Kiểm tra API Key hoặc gõ đúng 'gemini-1.5-flash' vào Sheet.")
            continue

        # Spin & SEO
        add_log("🔄 Spin: Đang humanize...")
        # (Gọi Spin bằng flash cho nhanh)
        content_spin, _ = call_ai_robust(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string()}\nContent: {content}")
        content = content_spin if content_spin else content

        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        add_log(f"📊 SEO: {score}/100 | Mật độ: {dens}%")
        
        # Ghi Sheet
        add_log("📝 Sheet: Đang ghi báo cáo...")
        sh_res = update_report([
            site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), 
            v('Danh sách Keyword bài viết'), "", "✅", f"{dens}%", f"{score}/100", 
            site.get('các website đích',''), title, "Sapo", datetime.now().strftime("%H:%M"), "Thành công", "Active"
        ])
        
        if sh_res: add_log("✅ Đã lưu vào Tab Report thành công!")
        add_log(f"✨ HOÀN TẤT BÀI {i+1}!")
        time.sleep(1)

    st.success("🎉 TIẾN TRÌNH KẾT THÚC!")
    if st.button("❌ ĐÓNG VÀ QUAY LẠI", use_container_width=True): st.rerun()

# --- UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v17.2</h1>", unsafe_allow_html=True)

if 'last_action' not in st.session_state: st.session_state.last_action = 0

data, msg = load_data()
if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                
                # Nút RUN 5s delay
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5:
                        st.warning("⏳ Chậm lại ní! 5s bấm 1 lần thôi.")
                    else:
                        st.session_state.last_action = time.time()
                        run_robot(data)

                # Nút Reload 5s delay
                if c2.button("🔄 Reload DB", use_container_width=True):
                    if time.time() - st.session_state.last_action < 5:
                        st.toast("⚠️ Đợi 5s hãy Reload tiếp!")
                    else:
                        st.session_state.last_action = time.time()
                        st.cache_data.clear(); st.rerun()
                
                # Masking sensitive data
                disp = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        v_str = str(row['Input dữ liệu'])
                        return v_str[:4] + "****" + v_str[-4:] if len(v_str) > 8 else "****"
                    return row['Input dữ liệu']
                disp['Input dữ liệu'] = disp.apply(mask, axis=1)
                st.dataframe(disp, use_container_width=True, height=400, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else: st.error(f"Lỗi: {msg}")
