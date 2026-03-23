import streamlit as st
import pandas as pd
import re
import time
import requests
from datetime import datetime

st.set_page_config(page_title="LÁI HỘ SEO", layout="wide")

TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "Nội dung tóm tắt", "Thời gian hẹn giờ", "Trạng thái"]
}

if 'db' not in st.session_state:
    st.session_state['db'] = {k: pd.DataFrame(columns=v) for k, v in TABS_CONFIG.items()}
    # TRẢ LẠI BẢNG DASHBOARD CHUẨN 100% THỰC TẾ CỦA NÍ
    st.session_state['db']['Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
        ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
        ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say về nhà an toàn"],
        ["TARGET_URL", "https://laiho.vn/"],
        ["Website đối thủ", "lmd.vn, butl.vn"],
        ["Mục tiêu bài viết", "Bài viết dạng tư vấn, cung cấp giải pháp an toàn"],
        ["Số lượng bài cần tạo", "1"],
        ["Thiết lập số lượng chữ", "900 - 1200"],
        ["Số lượng backlink/bài", "3 - 4"],
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

def call_gemini_ai(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "maxOutputTokens": 250}
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"Lỗi API: {response.text}"
    except Exception as e:
        return f"Lỗi kết nối: {str(e)}"

@st.dialog("💀 HỆ THỐNG AI ĐANG SÁNG TẠO NỘI DUNG...", width="large")
def hacker_terminal():
    terminal_box = st.empty()
    log_text = "root@laiho-server:~# Khởi động AI Engine...\n"
    terminal_box.code(log_text, language="bash")
    
    df_dash = st.session_state['db']['Dashboard']
    
    # HÀM BỐC DỮ LIỆU CHUẨN TỪ BẢNG
    def get_val(key_name):
        try:
            return df_dash.loc[df_dash['Hạng mục'] == key_name, 'Giá trị thực tế'].values[0]
        except:
            return ""
            
    api_key = get_val('GEMINI_API_KEY')
    keywords = get_val('Danh sách Keyword bài viết')
    muc_tieu = get_val('Mục tiêu bài viết')
    
    log_text += f"[+] Keywords nạp vào: {keywords}\n"
    log_text += f"[+] Mục tiêu bài: {muc_tieu}\n"
    log_text += "[+] Đang kết nối máy chủ Google Gemini...\n"
    terminal_box.code(log_text, language="bash")
    time.sleep(1)
    
    # PROMPT AI BÁM SÁT THỰC TẾ
    prompt = f"Đóng vai chuyên gia SEO nội dung. Dựa vào thông tin sau:\n- Từ khóa: {keywords}\n- Mục tiêu: {muc_tieu}\n\nHãy viết 1 Tiêu đề giật tít (dưới 65 ký tự) và 1 Đoạn Sapo mở bài (dưới 40 chữ). Format trả về: Tiêu đề: [Nội dung] | Sapo: [Nội dung]"
    
    log_text += "[!] AI đang phân tích dữ liệu và viết bài...\n"
    terminal_box.code(log_text, language="bash")
    
    ai_result = call_gemini_ai(api_key, prompt)
    
    log_text += f"\n[OK] KẾT QUẢ TỪ AI:\n{ai_result}\n\n"
    log_text += "[+] Đang xuất file vào tab Report...\n"
    terminal_box.code(log_text, language="bash")
    
    title = ai_result.split('|')[0].replace("Tiêu đề:", "").strip() if "|" in ai_result else "Lỗi bóc tách tiêu đề"
    sapo = ai_result.split('|')[1].replace("Sapo:", "").strip() if "|" in ai_result else ai_result
    
    today = datetime.now().strftime("%d/%m/%Y")
    
    # Tách từ khoá 1, 2 từ chuỗi keywords Ní nhập
    kw_list = [k.strip() for k in keywords.split(',')]
    kw1 = kw_list[0] if len(kw_list) > 0 else ""
    kw2 = kw_list[1] if len(kw_list) > 1 else ""
    
    new_report = pd.DataFrame([
        ["laiho.vn", "WordPress", "laiho.vn/post", today, kw1, kw2, "", "", "", "#", title, sapo, "Đăng ngay", "✅ AI Đã Viết"]
    ], columns=TABS_CONFIG["Report"])
    
    st.session_state['db']['Report'] = pd.concat([st.session_state['db']['Report'], new_report], ignore_index=True)
    
    log_text += "=========================================\n"
    log_text += "🚀 HOÀN TẤT LUỒNG AI! XEM BÁO CÁO NHÉ."
    terminal_box.code(log_text, language="bash")
        
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("ĐÓNG TERMINAL & KIỂM TRA BÀI VIẾT", type="primary", use_container_width=True):
            st.rerun()

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
                if st.button("🔥 START ROBOT AI", key="run_robot", type="primary", use_container_width=True):
                    hacker_terminal()

        st.session_state['db'][name] = st.data_editor(
            st.session_state['db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            hide_index=True,
            key=f"edit_{name}"
        )
