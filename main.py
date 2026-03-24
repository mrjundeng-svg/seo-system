import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time, re
from datetime import datetime

# --- KẾT NỐI HỆ THỐNG ---
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
    score, kw = 0, keyword.lower().strip()
    c_low, t_low, words = content.lower(), title.lower(), content.split()
    if kw in t_low: score += 20
    if kw in c_low[:300]: score += 20
    if len(words) >= 600: score += 20
    dens = (c_low.count(kw) / len(words)) * 100 if words else 0
    if 0.5 <= dens <= 2.5: score += 20
    if "##" in content or "<h3>" in c_low: score += 20
    return score, round(dens, 2)

# --- AI CALLER (TRỊ LỖI 404 & CHI TIẾT LỖI) ---
def call_ai_clean(key, model, prompt):
    model = model.strip() # Xóa sạch khoảng trắng dư thừa gây lỗi 404
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        res_j = res.json()
        if res.status_code == 200:
            return res_j['candidates'][0]['content']['parts'][0]['text'].strip(), "OK"
        else:
            msg = res_j.get('error', {}).get('message', 'Lỗi không xác định')
            if res.status_code == 404: reason = f"Lỗi 404: Tên Model '{model}' không đúng hoặc API chưa cấp quyền."
            elif res.status_code == 429: reason = "Lỗi 429: Hết hạn mức API (Quota Exceeded)."
            else: reason = f"Lỗi {res.status_code}: {msg}"
            return None, reason
    except Exception as e: return None, f"Lỗi kết nối: {str(e)}"

# --- ENGINE TERMINAL (DÒNG NÀO RA DÒNG ĐÓ) ---
@st.dialog("🖥️ SYSTEM TERMINAL (DEEP DEBUG)", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    active_sites = data['Website'][data['Website']['Trạng thái'] == 'Active']
    
    # Khu vực Log sạch sẽ
    full_log = f"[{datetime.now().strftime('%H:%M:%S')}] root@seo:~# Khởi động Robot...\n"
    terminal = st.empty()
    terminal.code(full_log)

    def write_log(msg):
        nonlocal full_log
        full_log += f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n"
        terminal.code(full_log) # In đè Log cũ để tạo hiệu ứng cuộn xuống dòng

    num_to_gen = int(v('Số lượng bài cần tạo') or 1)
    for i in range(num_to_gen):
        write_log(f"━━━━━━━━━━ BÀI {i+1}/{num_to_gen} ━━━━━━━━━━")
        site = active_sites.sample(n=1).iloc[0]
        model_v = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
        chosen_model = random.choice(model_v)
        main_kw = v('Danh sách Keyword bài viết').split('|')[0].strip()

        write_log(f"🛰 Vệ tinh: {site['Tên web']}")
        write_log(f"🧠 AI: Đang dùng {chosen_model}")

        # AI Gen
        write_log(".. Đang tạo nội dung...")
        content, err = call_ai_clean(v('GEMINI_API_KEY'), chosen_model, f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}")
        
        if not content:
            write_log(f"❌ STUCK! LÝ DO: {err}")
            continue

        # Spin & SEO
        if v('SPIN_MODE') == "ON":
            write_log("🔄 Spin: Đang lách AI Detection...")
            content, _ = call_ai_clean(v('GEMINI_API_KEY'), "gemini-1.5-flash", f"{v('AI_HUMANIZER_PROMPT')}\nRules: {data['Spin'].to_string()}\nContent: {content}")

        title = content.split('\n')[0].replace('#', '').strip()
        score, dens = yoast_seo_audit(content, main_kw, title)
        write_log(f"📊 SEO Audit: {score}/100 | Mật độ: {dens}%")
        
        # Ghi Sheet
        write_log("📝 Sheet: Đang ghi vào Tab Report...")
        sh_ok = gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row([
            site['URL / ID'], site['Nền tảng'], "Link", datetime.now().strftime("%Y-%m-%d"), v('Danh sách Keyword bài viết'), "", "✅", f"{dens}%", f"{score}/100", site.get('các website đích',''), title, "Sapo", datetime.now().strftime("%H:%M"), "Thành công", "Active"
        ])
        
        if sh_ok: write_log("✅ Đã lưu bài thành công!")
        write_log(f"✨ HOÀN TẤT BÀI {i+1}!")
        time.sleep(1)

    st.success("🎉 TIẾN TRÌNH KẾT THÚC!")

# --- UI INTERFACE ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v17.0</h1>", unsafe_allow_html=True)

# Khởi tạo bộ đếm thời gian để Anti-Spam
if 'last_action_time' not in st.session_state:
    st.session_state.last_action_time = 0

data, msg = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                c1, c2, _ = st.columns([1, 1, 4])
                
                # Logic Nút RUN với Delay 5s
                if c1.button("🚀 RUN", type="primary", use_container_width=True):
                    curr = time.time()
                    if curr - st.session_state.last_action_time < 5:
                        st.warning(f"⏳ Chậm lại ní ơi! Đợi {int(5 - (curr - st.session_state.last_action_time))}s nữa nhé.")
                    else:
                        st.session_state.last_action_time = curr
                        run_robot(data)

                # Logic Nút Reload với Delay 5s
                if c2.button("🔄 Reload DB", use_container_width=True):
                    curr = time.time()
                    if curr - st.session_state.last_action_time < 5:
                        st.toast(f"⚠️ Reload quá nhanh! Đợi {int(5 - (curr - st.session_state.last_action_time))}s.")
                    else:
                        st.session_state.last_action_time = curr
                        st.cache_data.clear()
                        st.rerun()
                
                disp_df = data[name].copy()
                sensitive = ['KEY', 'API', 'MAIL', 'TOKEN', 'PASSWORD', 'SECRET', 'CHAT_ID']
                def mask(row):
                    if any(w in str(row['Hạng mục']).upper() for w in sensitive):
                        val = str(row['Input dữ liệu'])
                        return val[:4] + "****" + val[-4:] if len(val) > 8 else "****"
                    return row['Input dữ liệu']
                disp_df['Input dữ liệu'] = disp_df.apply(mask, axis=1)
                st.dataframe(disp_df, use_container_width=True, height=400, hide_index=True)
            else: st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else: st.error(f"Lỗi: {msg}")
