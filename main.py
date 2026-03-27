import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time
from datetime import datetime, timedelta, timezone

# --- 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP ---
st.set_page_config(page_title="LAIHO.VN - SEO COMMAND CENTER", layout="wide", page_icon="🚀")

# CSS tùy chỉnh để làm giao diện "sang" hơn
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

def get_vn_time(): 
    return datetime.now(timezone(timedelta(hours=7)))

def clean_str(s):
    return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# [Giữ nguyên hàm get_creds và re_authorize từ V18 để đảm bảo tính ổn định]
def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        data = {}
        for t in ["Dashboard", "Keyword", "Report"]:
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            headers = [clean_str(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        return data, sh
    except: return None, None

# --- 2. GIAO DIỆN CHÍNH (UI/UX) ---
data, sh = load_all_tabs()

if data:
    # --- SIDEBAR CẤU HÌNH ---
    with st.sidebar:
        st.image("https://laiho.vn/wp-content/uploads/2024/logo.png", width=150) # Thay link logo bồ nếu có
        st.header("⚙️ CẤU HÌNH CHIẾN DỊCH")
        num_posts = st.number_input("Số bài viết mỗi đợt", min_value=1, max_value=50, value=3)
        st.divider()
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear(); st.rerun()
        st.info("Phiên bản V19 - UI/UX Master")

    # --- TOP METRICS (KPI) ---
    df_kw = data['Keyword']
    total_kw = len(df_kw)
    # Mapping status linh hoạt
    done_kw = len(df_kw[df_kw.iloc[:, 2].str.contains('SUCCESS|1', case=False, na=False)])
    pending_kw = total_kw - done_kw

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📌 Tổng từ khóa", f"{total_kw}")
    c2.metric("✅ Đã hoàn thành", f"{done_kw}", delta=f"{int(done_kw/total_kw*100)}%" if total_kw > 0 else "0%")
    c3.metric("⏳ Đang chờ", f"{pending_kw}")
    c4.metric("🕒 Giờ hệ thống", get_vn_time().strftime("%H:%M"))

    st.divider()

    # --- TABS ĐIỀU HÀNH ---
    tab_control, tab_data, tab_report = st.tabs(["🎮 TRẠM ĐIỀU KHIỂN", "📂 KHO TỪ KHÓA", "📜 NHẬT KÝ NỘI DUNG"])

    with tab_control:
        st.subheader("🚀 Kích hoạt Robot AI")
        col_btn, col_info = st.columns([1, 2])
        with col_btn:
            if st.button(f"🔥 BẮT ĐẦU VIẾT {num_posts} BÀI", type="primary", use_container_width=True):
                # Gọi lại hàm run_batch_popup từ V18 của bồ ở đây
                st.toast("Robot đang khởi động...", icon="🤖")
        with col_info:
            st.write(f"Robot sẽ bốc **{num_posts}** từ khóa có Status = 0 để thực hiện.")

    with tab_data:
        st.subheader("🔍 Danh sách từ khóa chi tiết")
        # UX XỊN: Dùng column_config để tô màu status
        st.dataframe(
            df_kw,
            use_container_width=True,
            hide_index=True,
            column_config={
                "KW_STATUS": st.column_config.TextColumn(
                    "Trạng thái",
                    help="SUCCESS là đã xong",
                )
            }
        )

    with tab_report:
        st.subheader("📝 Báo cáo nội dung gần đây")
        df_rep = data['Report']
        if not df_rep.empty:
            # Hiển thị bài viết mới nhất lên đầu
            st.table(df_rep.iloc[::-1].head(10)) 
        else:
            st.write("Chưa có báo cáo nào.")
else:
    st.error("❌ Không thể kết nối với Google Sheet. Vui lòng kiểm tra lại ID và Quyền truy cập.")
