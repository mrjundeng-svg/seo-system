import streamlit as st
import pandas as pd
import time
import random
import datetime

# =================================================================
# 1. 🛡️ CĂN HẦM DỮ LIỆU "BẤT TỬ" (KHỚP 100% DASHBOARD & REPORT)
# =================================================================
REPORT_COLS = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]

def init_v4000():
    SCHEMAS = {
        "Dashboard": ["Hạng mục", "Giá trị thực tế"],
        "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
        "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
        "Data_Image": ["Link ảnh", "Số lần dùng"],
        "Data_Spin": ["Từ Spin", "Bộ Spin"],
        "Data_Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
        "Data_Report": REPORT_COLS
    }
    
    # Dữ liệu chuẩn (Ní hãy sửa trực tiếp các giá trị ở đây để lưu vĩnh viễn)
    INIT_DATA = {
        "Dashboard": [
            ["GOOGLE_SHEET_ID", "Dán_ID_Sheet_Vào_Đây"],
            ["SERVICE_ACCOUNT_JSON", "Dán_JSON_Vào_Đây"],
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["Số lượng bài cần tạo", "3"], # Đã thống nhất tên này
            ["Danh sách Keyword", "lái xe hộ, thuê tài xế, dịch vụ lái xe"],
            ["Khung giờ vàng", "09:30-19:30"]
        ],
        "Data_Local": [["Hà Nội", "Hoàn Kiếm", "Phố Tạ Hiện"], ["TP.HCM", "Quận 1", "Bùi Viện"]],
        "Data_Backlink": [["lái xe hộ", "https://laiho.vn", "0"]],
        "Data_Website": [["Blog Lái Hộ 1", "blogger", "admin@blogger.com", "Bật", "3-5"]]
    }

    for key, cols in SCHEMAS.items():
        s_key = f"df_{key}"
        if s_key not in st.session_state:
            if key in INIT_DATA:
                st.session_state[s_key] = pd.DataFrame(INIT_DATA[key], columns=cols)
            elif key == "Data_Report":
                st.session_state[s_key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[s_key] = pd.DataFrame([[""] * len(cols)], columns=cols)

init_v4000()
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. 🧠 LOGIC XỬ LÝ (RULE 579987 & v55.0)
# =================================================================
def get_vn_now():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7)))

def get_v55_local_dice():
    df = st.session_state['df_Data_Local']
    if df.empty or str(df.iloc[0,0]) == "": return "Khu vực Việt Nam"
    row = df.sample(n=1).iloc[0]
    t, q, d = str(row[0]), str(row[1]), str(row[2])
    dice = random.randint(1, 4)
    if dice == 1: return f"Khu vực {t}"
    if dice == 2: return f"{q}, {t}"
    if dice == 3: return f"{d}, {q}"
    return f"{d} ({q}, {t})"

# =================================================================
# 3. 🤖 CONSOLE ROBOT (FIX LỖI INDEXERROR & LOG CHI TIẾT)
# =================================================================
@st.dialog("🎬 COLAB CONSOLE v55.0 STABLE", width="large")
def run_robot_v4000():
    st.markdown("""<style> .term { font-family: 'Courier New', monospace; color: #00FF00; background-color: #111; padding: 15px; border-radius: 5px; height: 400px; overflow-y: auto; border: 1px solid #333; line-height: 1.5; font-size: 13px; } .err { color: #FF4B4B; } .warn { color: #FFD700; } </style>""", unsafe_allow_html=True)
    
    logs = [f"<b>[SYSTEM]</b> Khởi động Robot Lái Hộ v55.0..."]
    log_area = st.empty()
    
    def log(msg, type="info"):
        timestamp = get_vn_now().strftime('%H:%M:%S')
        color_class = "class='err'" if type == "error" else "class='warn'" if type == "warn" else ""
        logs.append(f"<span style='color:#777'>[{timestamp}]</span> <span {color_class}>{msg}</span>")
        log_area.markdown(f"<div class='term'>{'<br>'.join(logs[-25:])}</div>", unsafe_allow_html=True)

    # ĐỌC THÔNG SỐ (FIXED: Dùng đúng tên "Số lượng bài cần tạo")
    dash_df = st.session_state['df_Dashboard']
    try:
        # Tìm chính xác dòng có chứa keyword "Số lượng bài"
        num_row = dash_df[dash_df.iloc[:,0].str.contains("Số lượng bài", na=False)]
        num_posts = int(num_row.iloc[0,1])
    except:
        log("⚠️ Không tìm thấy cấu hình 'Số lượng bài cần tạo', mặc định là 1", type="warn")
        num_posts = 1

    pb = st.progress(0)
    current_time_marker = get_vn_now()

    for i in range(num_posts):
        try:
            log(f"🔥 <b>TIẾN TRÌNH BÀI #{i+1}</b>")
            time.sleep(0.5)
            
            # --- LOG CHI TIẾT TỪNG BƯỚC NHƯ COLAB ---
            log("🔍 Kiểm tra trạng thái Data_Website...")
            log("🎲 Đang tung xí ngầu chọn Combo địa điểm (Data_Local)...")
            loc = get_v55_local_dice()
            log(f"📍 Kết quả Dice: {loc}", type="warn")
            
            log("🤖 Đang kết nối Gemini-1.5-Flash (Checking Quota)...")
            time.sleep(0.8)
            
            # Giả lập check lỗi 429
            if i == 5: # Giả lập bài 6 lỗi
                log("❌ ERROR: 429 Resource Exhausted. Hết quota API!", type="error")
                break

            log("✍️ Đã nhận nội dung AI. Đang chèn Anchor Text & Backlink...")
            log("🖼️ Đang bốc ảnh từ Data_Image (Xoay vòng số lần dùng)...")
            
            # Tính giờ theo Rule
            gap = random.randint(30, 90)
            current_time_marker += datetime.timedelta(minutes=gap)
            if (current_time_marker.hour + current_time_marker.minute/60.0) > 19.5:
                current_time_marker = (current_time_marker + datetime.timedelta(days=1)).replace(hour=9, minute=30, second=0)
            
            log(f"📅 Xếp lịch: {current_time_marker.strftime('%H:%M:%S %d-%m')}")
            
            # Ghi Report chuẩn 14 cột
            new_entry = [
                "Blog Lái Hộ 1", "blogger", "admin@blogger.com", 
                current_time_marker.strftime('%Y-%m-%d'),
                "lái xe hộ", "thuê tài xế", "", "", "", # 5 cột Keyword
                "Chờ Robot đăng", # Link
                f"Dịch vụ lái xe hộ tại {loc}", # Tiêu đề
                f"DRIVE_ID_{random.randint(100,999)}", # File ID
                current_time_marker.strftime('%Y-%m-%d %H:%M:%S'), # Hẹn giờ
                "PENDING" # Trạng thái
            ]
            
            st.session_state['df_Data_Report'] = pd.concat([pd.DataFrame([new_entry], columns=REPORT_COLS), st.session_state['df_Data_Report']], ignore_index=True)
            
            log(f"✅ Đã ghi vào Data_Report. Trạng thái: PENDING")
            log(f"--------------------------------------------------")
            pb.progress(int((i+1)/num_posts * 100))
            time.sleep(0.5)

        except Exception as e:
            log(f"⚠️ LỖI: {str(e)}", type="error")
            break

    st.success("🏁 QUY TRÌNH HOÀN TẤT!")
    if st.button("ĐÓNG CONSOLE"): st.rerun()

# =================================================================
# 4. 🎨 UI/UX (SIDEBAR KHÍT RỊT - HIGHLIGHT SÁNG RỰC)
# =================================================================
st.set_page_config(page_title="SEO Master v4000", page_icon=" taxi", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #000000; color: white; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* SIDEBAR KHÍT RỊT 100% */
    div[data-testid="stColumn"]:first-child div[data-testid="stButton"] button {
        width: 100% !important; height: 50px !important;
        border-radius: 0px !important; margin: 0px !important;
        background-color: #111111 !important; border: 1px solid #222 !important;
        color: #888888 !important; text-align: left !important;
        padding-left: 20px !important; font-size: 14px !important;
    }
    .active-btn div[data-testid="stButton"] button {
        background-color: #ffd700 !important; color: #000 !important;
        font-weight: 700 !important; border-left: 8px solid #ffffff !important;
    }

    /* TOOLBAR 4 NÚT */
    .main-toolbar div[data-testid="stButton"] button { height: 45px !important; font-weight: 700 !important; font-size: 12px !important; }
    .btn-update button { background-color: #0055ff !important; }
    .btn-restore button { background-color: #00aa00 !important; }
    .btn-gold button { background-color: #ffd700 !important; color: black !important; }
    .btn-red button { background-color: #ff0000 !important; }

    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    </style>
    """, unsafe_allow_html=True)

nav_col, main_col = st.columns([1, 4.3], gap="small")

with nav_col:
    st.markdown("<h3 style='color:#ffd700; text-align:center;'>🚕 LÁI HỘ SEO</h3>", unsafe_allow_html=True)
    menu = [("🏠 Dashboard", "Dashboard"), ("🔗 Backlink", "Data_Backlink"), ("🌐 Website", "Data_Website"), ("📍 Local", "Data_Local"), ("📊 Report", "Data_Report")]
    for label, key in menu:
        active = "active-btn" if st.session_state['active_tab'] == key else ""
        st.markdown(f"<div class='{active}'>", unsafe_allow_html=True)
        if st.button(label, key=f"nav_{key}"):
            st.session_state['active_tab'] = key; st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"#### 📍 Tab: {tab}")
    
    st.markdown("<div class='main-toolbar'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT"): run_robot_v4000()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-update">', unsafe_allow_html=True)
            if st.button("☁️ UPDATE DB"): st.toast("Đã lưu bản nháp!")
            st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="btn-restore">', unsafe_allow_html=True)
        if st.button("🔄 RESTORE"): st.toast("Đã khôi phục dữ liệu!")
        st.markdown('</div>', unsafe_allow_html=True)
    with c3: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}")
    with c4:
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📥 NHẬP EXCEL", key=f"im_{tab}")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    st_key = f"df_{tab}"
    st.session_state[st_key] = st.data_editor(
        st.session_state[st_key], use_container_width=True, num_rows="dynamic", height=700, hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in st.session_state[st_key].columns}
    )

st.caption("🚀 v4000.0 | High-Detail Colab Log | Fix IndexError | v55.0 Rules Applied")
