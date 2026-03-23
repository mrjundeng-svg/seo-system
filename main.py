import streamlit as st
import pandas as pd
import re
import time
from datetime import datetime

st.set_page_config(page_title="LÁI HỘ SEO", layout="wide")

# Cấu hình khung sườn
TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

# Khởi tạo bộ nhớ
if 'db' not in st.session_state:
    st.session_state['db'] = {k: pd.DataFrame(columns=v) for k, v in TABS_CONFIG.items()}
    st.session_state['db']['Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SERPAPI_KEY", "380c97c05d054e..."],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["Số lượng bài cần tạo", "2"],
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
    ], columns=["Hạng mục", "Giá trị thực tế"])


# ==========================================
# HÀM POPUP TERMINAL HACKER (BẢN RỘNG - LARGE)
# ==========================================
# Thêm width="large" để bung rộng cái bảng popup
@st.dialog("💀 HỆ THỐNG ROBOT SEO ĐANG THỰC THI...", width="large")
def hacker_terminal():
    terminal_box = st.empty()
    log_text = ""
    
    logs = [
        "root@laiho-server:~# ./start_robot.sh",
        "[+] Kích hoạt module phân tích từ khóa đối thủ...",
        "[+] Bắt đầu luồng viết bài bằng AI...",
        "    -> Đang tạo Bài 1: Dịch vụ lái xe hộ...",
        "    -> Bài 1: Viết xong. Đang chèn backlink...",
        "    -> Đang tạo Bài 2: Đưa người say về nhà an toàn...",
        "    -> Bài 2: Viết xong. Đang chèn backlink...",
        "[+] Đang đồng bộ báo cáo vào hệ thống...",
        "=========================================",
        "🚀 HOÀN TẤT! ĐÃ THÊM 2 BÀI VÀO TAB REPORT."
    ]
    
    for line in logs:
        log_text += line + "\n"
        terminal_box.code(log_text, language="bash")
        time.sleep(0.5)
        
    today = datetime.now().strftime("%d/%m/%Y")
    mock_reports = pd.DataFrame([
        ["laiho.vn", "WordPress", "laiho.vn/wp-admin", today, "thuê tài xế", "lái xe hộ", "an toàn", "", "", "https://laiho.vn/dich-vu-lai-xe-ho", "Dịch vụ thuê tài xế lái xe hộ an toàn số 1", "1A2B3C4D5E", "Đăng ngay", "✅ Thành công"],
        ["laiho.vn", "WordPress", "laiho.vn/wp-admin", today, "đưa người say", "nhậu say", "tài xế", "", "", "https://laiho.vn/dua-nguoi-say", "Giải pháp đưa người say về nhà an toàn", "6F7G8H9J0K", "Đăng ngay", "✅ Thành công"]
    ], columns=TABS_CONFIG["Report"])
    
    st.session_state['db']['Report'] = pd.concat([st.session_state['db']['Report'], mock_reports], ignore_index=True)
        
    # Cho cái nút bự ra giữa luôn cho đẹp
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("ĐÓNG TERMINAL & XEM BÁO CÁO", type="primary", use_container_width=True):
            st.rerun()

# ==========================================
# GIAO DIỆN CHÍNH
# ==========================================
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)

tabs = st.tabs(list(TABS_CONFIG.keys()))

for i, (name, cols) in enumerate(TABS_CONFIG.items()):
    with tabs[i]:
        with st.expander(f"📥 NHẬP LIỆU NHANH {name}"):
            raw_data = st.text_area("Dán nội dung vào đây:", key=f"txt_{name}", height=150)
            if st.button("🔥 ĐỔ VÀO BẢNG", key=f"load_{name}") and raw_data:
                parsed_data = []
                for line in raw_data.strip().split('\n'):
                    if not line.strip(): continue
                    row = [x.strip() for x in re.split(r'\t|\s{2,}', line) if x.strip()]
                    if len(row) > len(cols): row = row[:len(cols)]
                    elif len(row) < len(cols): row.extend([''] * (len(cols) - len(row)))
                    parsed_data.append(row)
                st.session_state['db'][name] = pd.DataFrame(parsed_data, columns=cols)
                st.rerun()

        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 3])
        with c1: st.button("☁️ LƯU CLOUD", key=f"up_{name}", use_container_width=True)
        with c2: st.button("🔄 RESTORE", key=f"res_{name}", use_container_width=True)
        with c3:
            if name == "Dashboard":
                if st.button("🔥 START ROBOT", key="run_robot", type="primary", use_container_width=True):
                    hacker_terminal()

        st.session_state['db'][name] = st.data_editor(
            st.session_state['db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            hide_index=True,
            key=f"edit_{name}"
        )
