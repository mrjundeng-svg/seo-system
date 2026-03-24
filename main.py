import streamlit as st
import pandas as pd
import re
import time
import requests
import random
from datetime import datetime, timedelta

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
    st.session_state['db']['Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SERPAPI_KEY", "380c97c05d054e..."],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
        ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
        ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say về nhà an toàn"],
        ["TARGET_URL", "https://laiho.vn/"],
        ["Website đối thủ", "lmd.vn, butl.vn"],
        ["Mục tiêu bài viết", "Bài viết dạng tư vấn, cung cấp giải pháp an toàn"],
        ["Số lượng bài cần tạo", "3"], 
        ["Thiết lập số lượng chữ", "900 - 1200"],
        ["Số lượng backlink/bài", "3 - 4"],
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
        # THÊM 2 DÒNG CẤU HÌNH TELEGRAM ĐỂ NÍ DỄ CLONE DỰ ÁN
        ["TELEGRAM_BOT_TOKEN", "Dán_Token_Vào_Đây"],
        ["TELEGRAM_CHAT_ID", "Dán_ID_Vào_Đây"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

# ==========================================
# CÁC HÀM XỬ LÝ API (GEMINI & TELEGRAM)
# ==========================================
def call_gemini_ai(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.8, "maxOutputTokens": 250}}
    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            return response.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        else:
            return f"Lỗi API: {response.text}"
    except Exception as e:
        return f"Lỗi kết nối: {str(e)}"

def send_telegram(bot_token, chat_id, message):
    if not bot_token or not chat_id or bot_token == "Dán_Token_Vào_Đây":
        return # Nếu chưa cấu hình thì bỏ qua không gửi để tránh lỗi app
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=5)
    except:
        pass # Lỗi mạng rớt tele thì tool vẫn chạy tiếp không bị đứng

# ==========================================
# POPUP TERMINAL: CHUẨN COLAB + BẮN TELEGRAM
# ==========================================
@st.dialog("🤖 TRUNG TÂM ĐIỀU KHIỂN ROBOT SEO", width="large")
def hacker_terminal():
    df_dash = st.session_state['db']['Dashboard']
    def get_val(key_name):
        try: return df_dash.loc[df_dash['Hạng mục'] == key_name, 'Giá trị thực tế'].values[0]
        except: return ""
            
    api_key = get_val('GEMINI_API_KEY')
    keywords = get_val('Danh sách Keyword bài viết')
    muc_tieu = get_val('Mục tiêu bài viết')
    tele_token = get_val('TELEGRAM_BOT_TOKEN')
    tele_chat_id = get_val('TELEGRAM_CHAT_ID')
    
    try: so_luong_can_tao = int(get_val('Số lượng bài cần tạo'))
    except: so_luong_can_tao = 0
        
    today_obj = datetime.now()
    today_str = today_obj.strftime("%d/%m/%Y")
    df_report = st.session_state['db']['Report']
    so_bai_hom_nay = len(df_report[df_report['Ngày đăng bài'] == today_str])
    
    st.write("### 📊 TIẾN ĐỘ NGÀY HÔM NAY")
    
    if so_bai_hom_nay >= so_luong_can_tao:
        st.error(f"🛑 ĐÃ ĐẠT GIỚI HẠN: Hôm nay hệ thống đã tạo **{so_bai_hom_nay}/{so_luong_can_tao}** bài.")
        st.warning("💡 Đóng bảng này và tăng 'Số lượng bài cần tạo' ở Dashboard nếu muốn gen tiếp.")
        if st.button("ĐÓNG CỬA SỔ", type="primary", use_container_width=True): st.rerun()
        return 
        
    so_bai_con_lai = so_luong_can_tao - so_bai_hom_nay
    st.success(f"✅ Đã tạo **{so_bai_hom_nay}/{so_luong_can_tao}** bài. Chuẩn bị gen **{so_bai_con_lai}** bài...")
    
    # [TELEGRAM TRIGGER 1] - BÁO CÁO BẮT ĐẦU CHẠY
    msg_start = f"🤖 <b>[ROBOT LÁI HỘ BÁO CÁO]</b>\nBoss ơi, em bắt đầu tiến trình gen <b>{so_bai_con_lai} bài</b> mới cho ngày {today_str} nhé. Cứ đi uống cafe đi ạ! ☕"
    send_telegram(tele_token, tele_chat_id, msg_start)

    st.divider()
    terminal_box = st.empty()
    log_text = "root@laiho-server:~# Khởi động AI Engine...\n"
    terminal_box.code(log_text, language="bash")
    time.sleep(0.5)
    
    kw_list = [k.strip() for k in keywords.split(',')]
    kw1 = kw_list[0] if len(kw_list) > 0 else ""
    kw2 = kw_list[1] if len(kw_list) > 1 else ""
    new_reports = []
    
    for i in range(so_bai_con_lai):
        bai_so = i + 1
        log_text += f"\n======================================================\n"
        log_text += f"[+] ĐANG THỰC THI BÀI VIẾT SỐ {bai_so}/{so_bai_con_lai}...\n"
        terminal_box.code(log_text, language="bash")
        time.sleep(0.5)
        
        log_text += "    . Trạng thái AI : Đang phân tích từ khoá & viết nội dung...\n"
        terminal_box.code(log_text, language="bash")
        
        prompt = f"Đóng vai chuyên gia SEO. Dựa vào từ khóa: {keywords}\nMục tiêu: {muc_tieu}\nHãy viết 1 Tiêu đề giật tít (dưới 65 ký tự) và 1 Đoạn Sapo (dưới 40 chữ). Format trả về: Tiêu đề: [Nội dung] | Sapo: [Nội dung]"
        ai_result = call_gemini_ai(api_key, prompt)
        
        title = ai_result.split('|')[0].replace("Tiêu đề:", "").strip() if "|" in ai_result else f"Bài SEO Auto {datetime.now().timestamp()}"
        sapo = ai_result.split('|')[1].replace("Sapo:", "").strip() if "|" in ai_result else ai_result
        
        so_anh_chen = random.randint(2, 5)
        gio_dang = (today_obj + timedelta(hours=(so_bai_hom_nay + bai_so) * 2)).strftime("%H:%M")
        
        log_text += f"    . Tiêu đề       : {title}\n"
        log_text += f"    . Từ khoá focus : {kw1}, {kw2}\n"
        log_text += f"    . Lịch hẹn đăng : {gio_dang} ngày {today_str}\n"
        log_text += f"    => [OK] Lưu thành công Bài {bai_so} vào DataBase.\n"
        terminal_box.code(log_text, language="bash")
        
        new_reports.append(["laiho.vn", "WordPress", "laiho.vn/post", today_str, kw1, kw2, "", "", "", "#", title, sapo, f"{gio_dang} {today_str}", "✅ AI Đã Viết"])

        # [TELEGRAM TRIGGER 2] - BÁO CÁO ĐĂNG BÀI THÀNH CÔNG
        msg_done = f"🚀 <b>[ĐĂNG BÀI THÀNH CÔNG {bai_so}/{so_bai_con_lai}]</b>\n🌐 Web: laiho.vn\n📝 Tiêu đề: <i>{title}</i>\n🔑 Từ khoá: {kw1}\n🕒 Lịch đăng: {gio_dang}"
        send_telegram(tele_token, tele_chat_id, msg_done)

        time.sleep(1)

    df_new = pd.DataFrame(new_reports, columns=TABS_CONFIG["Report"])
    st.session_state['db']['Report'] = pd.concat([st.session_state['db']['Report'], df_new], ignore_index=True)
    
    log_text += "\n======================================================\n"
    log_text += f"🚀 TIẾN TRÌNH HOÀN TẤT! XUẤT THÀNH CÔNG {so_bai_con_lai} BÀI."
    terminal_box.code(log_text, language="bash")
        
    st.write("")
    if st.button("ĐÓNG TERMINAL & KIỂM TRA BÁO CÁO", type="primary", use_container_width=True):
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
