import streamlit as st
import pandas as pd
import re
import time

st.set_page_config(page_title="LÁI HỘ SEO", layout="wide")

# ==========================================
# HÀM POPUP TERMINAL HACKER (CHẠY THỜI GIAN THỰC)
# ==========================================
@st.dialog("💀 HỆ THỐNG ROBOT SEO ĐANG THỰC THI...")
def hacker_terminal():
    terminal_box = st.empty()
    log_text = ""
    
    # Kịch bản log giả lập chạy AI
    logs = [
        "root@laiho-server:~# ./start_robot.sh",
        "[+] Khởi tạo lõi hệ thống SEO Automation...",
        "[+] Đang kiểm tra API Keys...",
        "    -> Gemini API: Hợp lệ.",
        "    -> SERP API: Hợp lệ.",
        "[+] Kích hoạt module phân tích từ khóa đối thủ...",
        "    -> Target: lmd.vn, butl.vn...",
        "    -> Đang quét cấu trúc silô...",
        "[!] CẢNH BÁO: Phát hiện Rate Limit từ đối thủ. Đang đổi Proxy...",
        "    -> Bypass thành công!",
        "[+] Bắt đầu luồng viết bài (Target: 10 bài, 900-1200 chữ)...",
        "[+] Đang gọi AI xử lý nội dung...",
        "    -> Bài 1: Xong.",
        "    -> Bài 2: Xong.",
        "    -> Đang chèn 3-4 backlink/bài...",
        "[+] Kết nối Google Drive ID: 1STdk4mpDP2...",
        "[+] Đang đồng bộ file lên Cloud...",
        "=========================================",
        "🚀 HOÀN TẤT! HỆ THỐNG CHỜ LỆNH TIẾP THEO."
    ]
    
    # Hiệu ứng chữ chạy từ từ
    for line in logs:
        log_text += line + "\n"
        # In ra màn hình đen chữ xanh/trắng kiểu bash
        terminal_box.code(log_text, language="bash")
        time.sleep(0.4) # Chạy chậm chậm cho giống thật
        
    if st.button("ĐÓNG TERMINAL"):
        st.rerun()

# ==========================================
# CẤU HÌNH DỮ LIỆU & GIAO DIỆN CHÍNH
# ==========================================
TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

if 'db' not in st.session_state:
    st.session_state['db'] = {k: pd.DataFrame(columns=v) for k, v in TABS_CONFIG.items()}
    st.session_state['db']['Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SERPAPI_KEY", "380c97c05d054e..."],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["Số lượng bài cần tạo", "10"],
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)

tabs = st.tabs(list(TABS_CONFIG.keys()))

for i, (name, cols) in enumerate(TABS_CONFIG.items()):
    with tabs[i]:
        # Expander nhập liệu siêu tốc
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

        # Toolbar
        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 3])
        with c1: st.button("☁️ LƯU CLOUD", key=f"up_{name}", use_container_width=True)
        with c2: st.button("🔄 RESTORE", key=f"res_{name}", use_container_width=True)
        with c3:
            if name == "Dashboard":
                # NÚT KHỞI ĐỘNG GỌI POPUP HACKER
                if st.button("🔥 START ROBOT", key="run_robot", type="primary", use_container_width=True):
                    hacker_terminal()

        # Bảng dữ liệu
        st.session_state['db'][name] = st.data_editor(
            st.session_state['db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            hide_index=True,
            key=f"edit_{name}"
        )
