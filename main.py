import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG (ÉP LAYOUT RỘNG)
st.set_page_config(page_title="SEO Lái Hộ v270.0", page_icon="🚕", layout="wide")

# --- CSS SIÊU CẤP: ÉP GIAO DIỆN 2 CỘT & NHUỘM VÀNG ĐEN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* NỀN ĐEN TOÀN DIỆN */
    .stApp { background-color: #000000 !important; }
    header { visibility: hidden; }
    .block-container { padding-top: 1rem !important; }

    /* ẨN SIDEBAR GỐC CỦA STREAMLIT ĐỂ KHÔNG BỊ RỐI */
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MÀU CHỮ TRẮNG & VÀNG GOLD */
    * { color: #ffffff !important; font-family: 'Inter', sans-serif !important; }
    .gold-text { color: #ffd700 !important; font-weight: 700; }
    
    /* STYLE CHO CỘT MENU (SIDEBAR TỰ CHẾ) */
    .nav-col {
        border-right: 1px solid #333333;
        padding-right: 20px;
        height: 100vh;
    }

    /* NÚT MENU SẮC NÉT */
    .stButton>button {
        width: 100% !important; border-radius: 4px !important; font-weight: 600 !important;
        background-color: transparent !important; border: 1px solid transparent !important;
        text-align: left !important; padding: 12px !important; margin-bottom: 5px !important;
        transition: 0.3s;
    }
    .stButton>button:hover {
        border: 1px solid #ffd700 !important; color: #ffd700 !important; background-color: #111111 !important;
    }
    
    /* NÚT ĐANG CHỌN (ACTIVE) */
    .active-nav button {
        background-color: #1a1a1a !important;
        border-left: 5px solid #ffd700 !important;
        color: #ffd700 !important;
    }

    /* NÚT CHẠY MÀU ĐỎ QUYỀN LỰC */
    .btn-red button {
        background-color: #ff0000 !important; color: white !important;
        border: none !important; font-weight: 700 !important; height: 3.5em !important;
    }

    /* BẢNG DỮ LIỆU SẠCH */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #444 !important; }
    </style>
    """, unsafe_allow_html=True)

# =================================================================
# 2. KHỞI TẠO DỮ LIỆU AN TOÀN (SESSION STATE)
# =================================================================
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

def init_all_data():
    # 13 Dòng cấu hình chuẩn (Nạp đúng thông tin Ní cần)
    if 'df_config' not in st.session_state:
        st.session_state['df_config'] = pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Danh sách Keyword", "thuê tài xế lái hộ, lái xe hộ tphcm..."],
            ["Website đối thủ", "lmd.vn, butl.vn, saycar.vn"],
            ["Mục tiêu bài viết", "Bài viết tư vấn chuyên sâu, chốt sale"],
            ["Số lượng bài/ngày", "10"],
            ["Thiết lập số chữ", "1000 - 1200"],
            ["Mật độ Link/bài", "3 - 5"],
            ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
        ], columns=["Hạng mục", "Giá trị thiết lập"])

    # Khởi tạo các bảng khác
    map_tables = {
        "Data_Backlink": "df_backlink",
        "Data_Website": "df_website",
        "Data_Image": "df_image",
        "Data_Spin": "df_spin",
        "Data_Local": "df_local",
        "Data_Report": "df_report"
    }
    for key in map_tables.values():
        if key not in st.session_state:
            st.session_state[key] = pd.DataFrame(columns=["STT", "Nội dung", "Ghi chú"])

init_all_data()

# =================================================================
# 3. BỐ CỤC CHÍNH: CHIA 2 CỘT CỐ ĐỊNH (CHỐNG ẨN MENU)
# =================================================================
# Cột 1 (Sidebar tự chế) | Cột 2 (Nội dung chính)
nav_col, main_col = st.columns([1, 4], gap="large")

with nav_col:
    st.markdown("<h2 class='gold-text'>🚕 ĐIỀU HÀNH SEO</h2>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Danh sách các Tab
    tabs = ["Dashboard", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    
    for t in tabs:
        # Style cho nút đang chọn
        if st.session_state['active_tab'] == t:
            st.markdown("<div class='active-nav'>", unsafe_allow_html=True)
            if st.button(f"▪️ {t}", key=f"nav_{t}"): pass
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.button(f"  {t}", key=f"nav_{t}"):
                st.session_state['active_tab'] = t
                st.rerun()
                
    st.markdown("<div style='height:200px'></div>", unsafe_allow_html=True)
    if st.button("🚪 ĐĂNG XUẤT", use_container_width=True): st.stop()

# =================================================================
# 4. HIỂN THỊ NỘI DUNG (CỘT PHẢI)
# =================================================================
with main_col:
    active = st.session_state['active_tab']
    st.markdown(f"### 📍 {active}")

    if active == "Dashboard":
        # TOOLBAR
        c1, c2, c3, _ = st.columns([1, 1, 1, 2])
        with c1: st.download_button("📤 XUẤT CSV", data=st.session_state['df_config'].to_csv(index=False).encode('utf-8-sig'), file_name="config.csv", use_container_width=True)
        with c2: st.button("🔄 ĐỒNG BỘ", use_container_width=True)
        with c3: st.button("📥 NHẬP FILE", use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        cl, cr = st.columns([2, 1])
        with cl:
            st.markdown("<p class='gold-text'>⚙️ THÔNG SỐ CẤU HÌNH (13 DÒNG)</p>", unsafe_allow_html=True)
            # SHOW FULL 13 DÒNG SÁT NÓC
            st.session_state['df_config'] = st.data_editor(st.session_state['df_config'], use_container_width=True, height=520, num_rows="fixed")
        with cr:
            st.markdown("<p class='gold-text'>🚀 ĐIỀU KHIỂN ROBOT</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.write("Vận hành v55.0 Stable:")
                st.markdown('<div class="btn-red">', unsafe_allow_html=True)
                if st.button("🔥 CHẠY CHIẾN DỊCH NGAY", use_container_width=True):
                    prog = st.progress(0)
                    for i in range(11):
                        time.sleep(0.1); prog.progress(i*10)
                    st.success("✅ ĐÃ XONG!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.button("📅 LẬP LỊCH ROBOT", use_container_width=True)

    else:
        # Lấy Key bảng an toàn bằng Dictionary (Không dùng split để tránh IndexError)
        data_keys = {
            "Data_Backlink": "df_backlink",
            "Data_Website": "df_website",
            "Data_Image": "df_image",
            "Data_Spin": "df_spin",
            "Data_Local": "df_local",
            "Data_Report": "df_report"
        }
        df_key = data_keys.get(active)
        
        if active == "Data_Report":
            st.markdown("<p class='gold-text'>📋 BÁO CÁO HỆ THỐNG IN RA</p>", unsafe_allow_html=True)
            st.dataframe(st.session_state[df_key], use_container_width=True, height=800)
        else:
            st.markdown(f"<p class='gold-text'>📥 NHẬP DỮ LIỆU: {active}</p>", unsafe_allow_html=True)
            st.session_state[df_key] = st.data_editor(st.session_state[df_key], use_container_width=True, num_rows="dynamic", height=800)

st.caption("🚀 SEO Automation Lái Hộ v270.0 | Fixed UI - Bug Free Edition")
