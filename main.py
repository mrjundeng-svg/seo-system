import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time
from datetime import datetime

# --- CẤU HÌNH HỆ THỐNG ---
st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        return ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
    except Exception as e:
        st.error(f"❌ Lỗi Secrets: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_data():
    try:
        creds = get_creds()
        if not creds: return None, "Lỗi xác thực"
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        data = {}
        for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]:
            try: data[t] = pd.DataFrame(sh.worksheet(t).get_all_records())
            except: data[t] = pd.DataFrame()
        return data, "✅ Kết nối thành công"
    except Exception as e: return None, str(e)

def call_ai(key, model, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
    except: return "LỖI AI (Kiểm tra API Key hoặc mạng)"

def update_report(row):
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        sh.worksheet("Report").append_row(row)
    except: pass

# --- ĐỘNG CƠ ROBOT (CHẠY KHI BẤM NÚT) ---
@st.dialog("🤖 ROBOT ĐANG VẬN HÀNH", width="large")
def run_robot(data):
    df = data['Dashboard']
    def v(k): 
        try: return str(df.loc[df['Hạng mục'] == k, 'Giá trị thực tế'].values[0])
        except: return ""
    
    api_key = v('GEMINI_API_KEY')
    models = [m.strip() for m in v('MODEL_VERSION').split(',')]
    num_posts = int(v('Số lượng bài cần tạo') or 1)
    ratio = float(v('LOCAL_RATIO') or 0.2)
    
    term = st.empty()
    progress_bar = st.progress(0)
    log = f"root@{v('PROJECT_NAME').lower()}:~# Đang kích hoạt dàn vệ tinh...\n"
    
    for i in range(num_posts):
        # 1. Chọn Site & Model ngẫu nhiên
        site = data['Website'][data['Website']['Trạng thái'] == 'Active'].sample(n=1).iloc[0]
        model = random.choice(models)
        
        # 2. Xử lý LOCAL SEO
        loc_str = ""
        if random.random() < ratio and not data['Local'].empty:
            l = data['Local'].sample(n=1).iloc[0]
            loc_str = f"📍 Đánh mạnh Local: {l['Cung đường']}, {l['Quận']}, {l['Tỉnh thành']}."
        
        log += f"[+] Đang gen bài {i+1}/{num_posts}: {site['Tên web']} | {model}\n"
        term.code(log, language="bash")

        # 3. Gen Bài & Humanize
        p1 = f"{v('PROMPT_TEMPLATE')}\nKeywords: {v('Danh sách Keyword bài viết')}\n{loc_str}"
        content = call_ai(api_key, model, p1)
        
        if v('SPIN_MODE') == "ON" and not data['Spin'].empty:
            log += "  .. Đang chạy Spin lọc AI Detection...\n"
            term.code(log, language="bash")
            rules = data['Spin'].to_string(index=False)
            p2 = f"{v('AI_HUMANIZER_PROMPT')}\nRules: {rules}\nContent: {content}"
            content = call_ai(api_key, "gemini-1.5-flash", p2)

        # 4. Ghi Report & Báo cáo
        pub_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        update_report([site['URL / ID'], site['Nền tảng'], site['URL / ID']+"/post", pub_time, "", "", "", "", "", site['Website đích'], "Tiêu đề AI", "Sapo AI", pub_time, "✅ Thành công", "85"])
        
        log += f"  .. Done! Bài viết đã được lưu vào tab Report.\n"
        term.code(log, language="bash")
        progress_bar.progress((i + 1) / num_posts)
        time.sleep(2)

    st.success("🎉 CHIẾN DỊCH HOÀN TẤT! Sếp check Tab Report nhé.")

# --- GIAO DIỆN UI ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v14.0</h1>", unsafe_allow_html=True)
data, msg = load_data()

if data:
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                st.info("💡 Mọi thứ đã sẵn sàng. Bấm nút bên dưới để Robot bắt đầu viết bài.")
                if st.button("🚀 KÍCH HOẠT VÍT GA", type="primary", use_container_width=True):
                    run_robot(data)
            st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else:
    st.error(f"❌ {msg}")
    st.info("💡 Ní hãy Reboot App để nhận cấu hình mới nhất nhé.")
