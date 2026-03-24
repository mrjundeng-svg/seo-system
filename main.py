import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import requests, random, time
from datetime import datetime

st.set_page_config(page_title="LÁI HỘ MASTER", layout="wide", page_icon="🚕")

# --- HÀM CHẨN ĐOÁN VÀ KẾT NỐI ---
@st.cache_data(ttl=10) # Giảm cache để test cho nhanh
def load_data():
    try:
        if "service_account" not in st.secrets:
            return None, "Chưa tìm thấy mục [service_account] trong Secrets!"
        
        info = dict(st.secrets["service_account"])
        # Tự động sửa lỗi xuống dòng phổ biến
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        client = gspread.authorize(creds)
        
        sheet_id = st.secrets["GOOGLE_SHEET_ID"].strip()
        sh = client.open_by_key(sheet_id)
        
        data = {}
        for t in ["Dashboard", "Website", "Backlink", "Report", "Image", "Spin", "Local"]:
            try: data[t] = pd.DataFrame(sh.worksheet(t).get_all_records())
            except: data[t] = pd.DataFrame()
        return data, "✅ Kết nối thành công"
    except Exception as e:
        # Hiện chi tiết lỗi để sếp dễ bắt bệnh
        return None, f"Lỗi chi tiết: {type(e).__name__} - {str(e)}"

# --- UI & ROBOT (GIỮ NGUYÊN LOGIC v13.5) ---
st.markdown("<h1 style='color:#ffd700;'>🚕 LÁI HỘ MASTER v13.6</h1>", unsafe_allow_html=True)
data, msg = load_data()

if data:
    st.toast(msg)
    tabs = st.tabs(list(data.keys()))
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 START ROBOT", type="primary", use_container_width=True):
                    st.write("Robot đang chuẩn bị...") # Ní có thể dán hàm run_robot vào đây
            st.dataframe(data[name], use_container_width=True, height=450, hide_index=True)
else:
    st.error(f"❌ {msg}")
    st.info("Kiểm tra: 1. Đã bật Google Sheets/Drive API chưa? 2. Đã dán Secrets đúng định dạng chưa?")
