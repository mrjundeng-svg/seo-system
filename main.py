import streamlit as st
import pandas as pd
import time
import random
import datetime

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU & TIỆN ÍCH DỌN DẸP
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]

def init_v4300():
    SCHEMAS = {
        "Dashboard": ["Hạng mục", "Giá trị thực tế"],
        "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
        "Data_Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
        "Data_Report": REPORT_COLS
    }
    if 'df_Data_Report' not in st.session_state:
        st.session_state['df_Data_Report'] = pd.DataFrame(columns=REPORT_COLS)
    
    for key, cols in SCHEMAS.items():
        s_key = f"df_{key}"
        if s_key not in st.session_state:
            st.session_state[s_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

init_v4300()

# =================================================================
# 2. 🧠 BỘ NÃO ĐIỀU KHIỂN (FIX LỖI NHẢY NGÀY)
# =================================================================
def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

def parse_limit_v55(val):
    s = str(val).strip()
    if '-' in s:
        try: low, high = map(int, s.split('-')); return random.randint(low, high)
        except: return 3
    return int(s) if s.isdigit() else 3

def get_natural_title(kw, use_local):
    if use_local:
        df = st.session_state['df_Data_Local']
        if df.empty or str(df.iloc[0,0]) == "": return f"Dịch vụ {kw} chất lượng"
        r = df.sample(n=1).iloc[0]
        t, q, d = str(r[0]), str(r[1]), str(r[2])
        loc = [f"tại {t}", f"khu vực {q}, {t}", f"gần {d}, {q}", f"ở {d} ({q})"][random.randint(0,3)]
        return f"Dịch vụ {kw} chuyên nghiệp {loc}"
    return random.choice([f"Bí quyết thuê {kw} an toàn", f"Tại sao nên chọn {kw}?", f"Top lưu ý khi dùng {kw}"])

# =================================================================
# 3. 🤖 CONSOLE ROBOT (FIX RUNAWAY LOOP)
# =================================================================
@st.dialog("🎬 COLAB CONSOLE v55.0 STABLE", width="large")
def run_robot_v4300():
    st.markdown("""<style> .term { font-family: 'Courier New', monospace; color: #00FF00; background-color: #111; padding: 15px; height: 400px; overflow-y: auto; border: 1px solid #333; line-height: 1.5; } .err { color: #FF4B4B; } .warn { color: #FFD700; } </style>""", unsafe_allow_html=True)
    logs = [f"<b>[SYSTEM]</b> Khởi động Robot Lái Hộ v55.0..."]
    log_area = st.empty()
    
    def log(msg, type="info"):
        c = "class='err'" if type == "error" else "class='warn'" if type == "warn" else ""
        logs.append(f"<span style='color:#777'>[{get_vn_now().strftime('%H:%M:%S')}]</span> <span {c}>{msg}</span>")
        log_area.markdown(f"<div class='term'>{'<br>'.join(logs[-25:])}</div>", unsafe_allow_html=True)

    # Đọc Dashboard
    dash = st.session_state['df_Dashboard']
    try: num_posts = int(dash[dash.iloc[:,0].str.contains("Số lượng bài", na=False)].iloc[0,1])
    except: num_posts = 1
    try: local_pct = int(dash[dash.iloc[:,0].str.contains("Tỉ lệ", na=False)].iloc[0,1])
    except: local_pct = 30

    active_sites = st.session_state['df_Data_Website'][st.session_state['df_Data_Website']['Trạng thái'].str.lower() == 'bật'].to_dict('records')
    if not active_sites: log("❌ Không có web nào BẬT!", type="error"); return

    current_time_marker = get_vn_now()
    pb = st.progress(0)

    for i in range(num_posts):
        found_slot = False
        safety_counter = 0 # PHANH KHẨN CẤP
        
        while not found_slot and safety_counter < 60:
            date_str = current_time_marker.strftime('%Y-%m-%d')
            random.shuffle(active_sites)
            
            for site in active_sites:
                limit = parse_limit_v55(site['Giới hạn bài/ngày'])
                # Đếm số bài thực tế đã có trong Report
                rep_df = st.session_state['df_Data_Report']
                count_today = len(rep_df[(rep_df['Website'] == site['Tên web']) & (rep_df['Ngày đăng bài'] == date_str)])
                
                if count_today < limit:
                    log(f"🔥 BÀI #{i+1} -> Chọn: {site['Tên web']} (Quota: {count_today}/{limit})")
                    use_local = random.randint(1, 100) <= local_pct
                    title = get_natural_title("lái xe hộ", use_local)
                    log(f"🎭 Style: {'LOCAL' if use_local else 'GENERAL'} | Tiêu đề: {title}")
                    
                    # Gap time
                    current_time_marker += datetime.timedelta(minutes=random.randint(30, 90))
                    if current_time_marker.hour >= 20: current_time_marker = (current_time_marker + datetime.timedelta(days=1)).replace(hour=9, minute=30)
                    
                    # Ghi Report
                    new_row = [site['Tên web'], site['Nền tảng'], site['URL / ID'], date_str, "lái xe hộ", "", "", "", "", "Chờ đăng", title, "ID_DRIVE", current_time_marker.strftime('%Y-%m-%d %H:%M:%S'), "PENDING"]
                    st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_row], columns=REPORT_COLS), st.session_state['df_Data_Report']], ignore_index=True)
                    found_slot = True
                    break
            
            if not found_slot:
                safety_counter += 1
                current_time_marker = (current_time_marker + datetime.timedelta(days=1)).replace(hour=9, minute=30)
                if safety_counter % 5 == 0: log(f"⚠️ Đang tìm slot trống... (Đã nhảy {safety_counter} ngày)", type="warn")

        if safety_counter >= 60:
            log("❌ ĐÃ NHẢY 60 NGÀY VẪN KHÔNG CÓ SLOT! Hãy kiểm tra 'Giới hạn bài/ngày' hoặc xóa Report cũ.", type="error")
            break
        
        pb.progress(int((i+1)/num_posts * 100))
        time.sleep(0.2)

    st.success("🏁 Hoàn tất!")
    if st.button("ĐÓNG"): st.rerun()

# =================================================================
# 4. 🎨 UI/UX SIDEBAR KHÍT RỊT
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v4300", page_icon=" taxi", layout="wide")
st.markdown("""<style> .stApp { background-color: #000; color: white; } header { visibility: hidden; } [data-testid="stSidebar"] { display: none !important; } div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button { width: 100% !important; height: 50px !important; border-radius: 0px !important; margin: 0px !important; background-color: #111 !important; border: 1px solid #222 !important; color: #888 !important; text-align: left !important; padding-left: 20px !important; } .active-btn div[data-testid="stButton"] button { background-color: #ffd700 !important; color: #000 !important; font-weight: 700 !important; border-left: 8px solid #fff !important; } .btn-red button { background-color: #ff0000 !important; } .btn-blue button { background-color: #0055ff !important; } .btn-gold button { background-color: #ffd700 !important; color: #000 !important; } </style>""", unsafe_allow_html=True)

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
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT"): run_robot_v4300()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-blue">', unsafe_allow_html=True); st.button("☁️ UPDATE DB"); st.markdown('</div>', unsafe_allow_html=True)
    with c2: 
        st.markdown('<div class="btn-blue">', unsafe_allow_html=True)
        if st.button("🗑️ CLEAR REPORT"): st.session_state['df_Data_Report'] = pd.DataFrame(columns=REPORT_COLS); st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with c3: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📤 XUẤT EXCEL"); st.markdown('</div>', unsafe_allow_html=True)
    with c4: st.markdown('<div class="btn-gold">', unsafe_allow_html=True); st.button("📥 NHẬP EXCEL"); st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=700, hide_index=True)

st.caption("🚀 v4300.0 | Anti-Runaway Brake (60 Days Max) | Reset Report Feature | v55.0 Stable Engine")
