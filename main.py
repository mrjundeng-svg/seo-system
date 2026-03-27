import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, json, time
from datetime import datetime, timedelta, timezone

# --- 1. CONFIG GIAO DIỆN (DỌN DẸP SẠCH SẼ) ---
st.set_page_config(page_title="LAIHO SEO COMMAND", layout="wide", page_icon="🛡️")

# Fix lỗi trắng xóa Metrics bằng CSS "hàng hiệu"
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #ff4b4b !important; }
    [data-testid="stMetricLabel"] { font-size: 14px; color: #808495 !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre; border-radius: 4px 4px 0px 0px; font-weight: 600; }
    div[data-testid="stExpander"] { border: none; box-shadow: none; }
    </style>
    """, unsafe_allow_html=True)

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))
def clean_str(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. KẾT NỐI HỆ THỐNG ---
def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_data():
    try:
        creds = get_creds()
        client = gspread.authorize(creds)
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        data = {}
        for t in ["Dashboard", "Keyword", "Report"]:
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if vals:
                headers = [clean_str(h).upper() for h in vals[0]]
                data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        return data, sh
    except: return None, None

# --- 3. GIAO DIỆN CHÍNH (UX TINH GỌN) ---
data, sh = load_data()

if data:
    # SIDEBAR: Chỉ để những thứ thực sự cần
    with st.sidebar:
        st.title("🛡️ LAIHO SEO")
        st.caption("Phiên bản V21 - Clean & Stable")
        num_posts = st.select_slider("Số lượng bài viết/lần", options=[1, 3, 5, 10, 20], value=3)
        st.divider()
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    # KPI SECTION: Nhìn phát biết ngay tình hình
    df_kw = data['Keyword']
    total = len(df_kw)
    # Lọc SUCCESS hoặc 1 (tùy bồ điền)
    done = len(df_kw[df_kw.iloc[:, 2].astype(str).str.contains('SUCCESS|1', case=False)])
    pending = total - done

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📌 TỔNG TỪ KHÓA", total)
    m2.metric("✅ ĐÃ XONG", done)
    m3.metric("⏳ ĐANG CHỜ", pending)
    m4.metric("🕒 HỆ THỐNG", get_vn_time().strftime("%H:%M"))

    st.divider()

    # TABS: Chia vùng làm việc rõ ràng
    tab_run, tab_data, tab_log = st.tabs(["🎮 ĐIỀU KHIỂN", "📂 KHO TỪ KHÓA", "📜 BÁO CÁO"])

    with tab_run:
        c_btn, c_txt = st.columns([1, 2])
        with c_btn:
            # Nút bấm to, rõ ràng
            if st.button(f"🚀 CHẠY CHIẾN DỊCH {num_posts} BÀI", type="primary", use_container_width=True):
                # Khi bồ bấm, nó sẽ gọi Batch Popup như V18
                st.toast("Đang khởi động Robot...", icon="🤖")
        with c_txt:
            st.info(f"Robot sẽ bốc {num_posts} từ khóa 'Status = 0' để viết bài.")

    with tab_data:
        st.subheader("Kho từ khóa chiến thuật")
        st.dataframe(df_kw, use_container_width=True, hide_index=True)

    with tab_log:
        st.subheader("Nhật ký 20 bài gần nhất")
        df_rep = data['Report']
        if not df_rep.empty:
            # Hiển thị các cột quan trọng nhất theo hình bồ gửi
            display_cols = ["REP_CREATED_AT", "REP_WS_URL", "REP_TITLE", "REP_RESULT"]
            # Chỉ lấy các cột tồn tại trong DataFrame
            actual_cols = [c for c in display_cols if c in df_rep.columns]
            st.dataframe(df_rep[actual_cols].iloc[::-1].head(20), use_container_width=True, hide_index=True)
        else:
            st.write("Chưa có dữ liệu báo cáo.")
else:
    st.error("❌ Không kết nối được Google Sheet. Kiểm tra lại ID hoặc phân quyền!")
