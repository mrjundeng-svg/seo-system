import streamlit as st
import pandas as pd
import time
import random
import datetime

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU "BẤT TỬ"
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]

def init_v4200():
    SCHEMAS = {
        "Dashboard": ["Hạng mục", "Giá trị thực tế"],
        "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
        "Data_Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
        "Data_Report": REPORT_COLS
    }
    
    INIT_DATA = {
        "Dashboard": [
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["Số lượng bài cần tạo", "5"],
            ["Tỉ lệ bài Local (%)", "30"], # Chỉ 30% bài dùng Local để né spam
            ["Khung giờ vàng", "09:30-19:30"],
            ["Giãn cách (phút)", "30-90"]
        ],
        "Data_Website": [
            ["Blog Lái Hộ 1", "blogger", "admin@blogger.com", "Bật", "3-5"]
        ],
        "Data_Local": [["Hà Nội", "Hoàn Kiếm", "Phố Tạ Hiện"], ["TP.HCM", "Quận 1", "Bùi Viện"]]
    }

    for key, cols in SCHEMAS.items():
        s_key = f"df_{key}"
        if s_key not in st.session_state:
            st.session_state[s_key] = pd.DataFrame(INIT_DATA.get(key, []), columns=cols) if key in INIT_DATA or key == "Data_Report" else pd.DataFrame([[""] * len(cols)], columns=cols)

init_v4200()

# =================================================================
# 2. 🧠 LOGIC NÉ SPAM & XÍ NGẦU LOCAL
# =================================================================
def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

def get_natural_title(kw, use_local=False):
    """Rule: Tạo tiêu đề tự nhiên, nếu không dùng local thì dùng văn phong chia sẻ"""
    if use_local:
        df = st.session_state['df_Data_Local']
        if df.empty or str(df.iloc[0,0]) == "": return f"Dịch vụ {kw} uy tín"
        row = df.sample(n=1).iloc[0]
        t, q, d = str(row[0]), str(row[1]), str(row[2])
        dice = random.randint(1, 4)
        if dice == 1: loc = f"tại {t}"
        elif dice == 2: loc = f"khu vực {q}, {t}"
        elif dice == 3: loc = f"gần {d}, {q}"
        else: loc = f"tại {d} ({q}, {t})"
        return f"Dịch vụ {kw} chuyên nghiệp {loc}"
    else:
        # Danh sách mẫu tiêu đề General để né spam
        templates = [
            f"Bí quyết chọn {kw} an toàn cho chuyến đi dài",
            f"Tại sao bạn nên sử dụng {kw} khi đã uống rượu bia?",
            f"Top 5 lưu ý quan trọng khi thuê {kw} hiện nay",
            f"Trải nghiệm dịch vụ {kw} chất lượng cao giá rẻ",
            f"Hướng dẫn cách đặt {kw} nhanh chóng chỉ trong 5 phút"
        ]
        return random.choice(templates)

# =================================================================
# 3. 🤖 CONSOLE ROBOT (CHECK QUOTA & NÉ SPAM LOGIC)
# =================================================================
@st.dialog("🎬 COLAB CONSOLE v55.0 ANTI-SPAM", width="large")
def run_robot_v4200():
    st.markdown("""<style> .term { font-family: 'Courier New', monospace; color: #00FF00; background-color: #111; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; border: 1px solid #333; line-height: 1.5; } .err { color: #FF4B4B; } .warn { color: #FFD700; } .blue { color: #00AAFF; } </style>""", unsafe_allow_html=True)
    logs = [f"<b>[SYSTEM]</b> Khởi động Robot Lái Hộ v55.0..."]
    log_area = st.empty()
    
    def log(msg, type="info"):
        timestamp = get_vn_now().strftime('%H:%M:%S')
        color = "class='err'" if type == "error" else "class='warn'" if type == "warn" else "class='blue'" if type == "blue" else ""
        logs.append(f"<span style='color:#777'>[{timestamp}]</span> <span {color}>{msg}</span>")
        log_area.markdown(f"<div class='term'>{'<br>'.join(logs[-25:])}</div>", unsafe_allow_html=True)

    dash_df = st.session_state['df_Dashboard']
    num_posts = int(dash_df[dash_df.iloc[:,0].str.contains("Số lượng bài", na=False)].iloc[0,1])
    try: local_pct = int(dash_df[dash_df.iloc[:,0].str.contains("Tỉ lệ bài Local")].iloc[0,1])
    except: local_pct = 30 # Mặc định 30%

    active_sites = st.session_state['df_Data_Website'][st.session_state['df_Data_Website']['Trạng thái'].str.lower() == 'bật'].to_dict('records')
    
    current_time_marker = get_vn_now()
    pb = st.progress(0)

    for i in range(num_posts):
        success = False
        while not success:
            date_key = current_time_marker.strftime('%Y-%m-%d')
            random.shuffle(active_sites)
            target_site = None
            
            # 1. Check Quota Web
            for site in active_sites:
                limit = 3 # Giả sử limit cố định để test
                count_today = len(st.session_state['df_Data_Report'][(st.session_state['df_Data_Report']['Website'] == site['Tên web']) & (st.session_state['df_Data_Report']['Ngày đăng bài'] == date_key)])
                if count_today < limit:
                    target_site = site; break
            
            if target_site:
                log(f"🔥 <b>TIẾN TRÌNH BÀI #{i+1}</b>")
                
                # 2. QUY QUYẾT: DÙNG LOCAL HAY GENERAL?
                use_local = random.randint(1, 100) <= local_pct
                style_name = "LOCAL" if use_local else "GENERAL"
                log(f"🎭 Phong cách bài viết: <b style='color:#00FF00'>{style_name}</b> (Né pattern spam)", type="blue")
                
                title = get_natural_title("lái xe hộ", use_local)
                log(f"📝 Tiêu đề: {title}")
                
                # Tính giờ gap
                current_time_marker += datetime.timedelta(minutes=random.randint(30, 90))
                if current_time_marker.hour >= 20:
                    current_time_marker = (current_time_marker + datetime.timedelta(days=1)).replace(hour=9, minute=30)
                
                # 3. Ghi Report
                new_entry = [target_site['Tên web'], target_site['Nền tảng'], target_site['URL / ID'], date_key, "lái xe hộ", "", "", "", "", "Chờ đăng", title, "DRIVE_ID", current_time_marker.strftime('%Y-%m-%d %H:%M:%S'), "PENDING"]
                st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_entry], columns=REPORT_COLS), st.session_state['df_Data_Report']], ignore_index=True)
                
                log(f"✅ Đã xếp lịch lên {target_site['Tên web']} ({current_time_marker.strftime('%H:%M')})")
                success = True
            else:
                log(f"⚠️ Hết hạn mức ngày {date_key}, nhảy sang ngày mai...", type="warn")
                current_time_marker = (current_time_marker + datetime.timedelta(days=1)).replace(hour=9, minute=30)

        pb.progress(int((i+1)/num_posts * 100))
        log("--------------------------------------------------")
        time.sleep(0.3)

    st.success("🏁 XONG! BLOG CỦA NÍ GIỜ NHÌN RẤT 'THẬT'.")
    if st.button("XEM REPORT"): st.rerun()

# =================================================================
# 4. 🎨 UI/UX SIDEBAR KHÍT RỊT
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v4200", page_icon=" taxi", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"] { display: none !important; }
    div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        width: 100% !important; height: 50px !important; border-radius: 0px !important;
        margin: 0px !important; background-color: #111 !important; border: 1px solid #222 !important;
        color: #888 !important; text-align: left !important; padding-left: 20px !important;
    }
    .active-btn div[data-testid="stButton"] button {
        background-color: #ffd700 !important; color: #000 !important; font-weight: 700 !important; border-left: 8px solid #fff !important;
    }
    .main-toolbar div[data-testid="stButton"] button { height: 45px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; }
    .btn-blue button { background-color: #0055ff !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")
with nav_col:
    st.markdown("<h3 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ SEO</h3>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"): st.session_state['active_tab'] = key; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"#### 📍 Tab: {tab}")
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT"): run_robot_v4200()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
            if st.button("☁️ UPDATE DB"): st.toast("Lưu bản nháp!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2: st.markdown('<div class="btn-blue">', unsafe_allow_html=True); st.button("🔄 RESTORE"); st.markdown('</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL"); st.markdown('</div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL"); st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("</div><br>", unsafe_allow_html=True)

    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=700, hide_index=True)

st.caption("🚀 v4200.0 | Anti-Spam Logic (30/70 Local) | Quota Check | v55.0 Stable Engine")
