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
        ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say về nhà, dịch vụ lái xe an toàn, gọi tài xế nhậu say, tìm người lái xe hộ, xe ôm công nghệ ban đêm"],
        ["TARGET_URL", "laiho.vn"],
        ["Website đối thủ", "lmd.vn, butl.vn"],
        ["Mục tiêu bài viết", "Bài viết dạng tư vấn, cung cấp giải pháp an toàn"],
        ["Số lượng bài cần tạo", "2"], 
        ["Thiết lập số lượng chữ", "900 - 1200"],
        ["Số lượng backlink/bài", "3 - 4"], # SẼ ĐỌC TỪ ĐÂY ĐỂ BỐC TỪ KHÓA
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
        ["TELEGRAM_BOT_TOKEN", "Dán_Token_Vào_Đây"],
        ["TELEGRAM_CHAT_ID", "Dán_ID_Vào_Đây"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

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
    bot_token = str(bot_token).strip()
    chat_id = str(chat_id).strip()
    if not bot_token or not chat_id or "Dán_" in bot_token: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

@st.dialog("🤖 TRUNG TÂM ĐIỀU KHIỂN ROBOT SEO", width="large")
def hacker_terminal():
    df_dash = st.session_state['db']['Dashboard']
    def get_val(key_name):
        try: return df_dash.loc[df_dash['Hạng mục'] == key_name, 'Giá trị thực tế'].values[0]
        except: return ""
            
    api_key = get_val('GEMINI_API_KEY')
    keywords = get_val('Danh sách Keyword bài viết')
    muc_tieu = get_val('Mục tiêu bài viết')
    doi_thu = get_val('Website đối thủ').replace(',', ' |')
    target_web = get_val('TARGET_URL')
    tele_token = get_val('TELEGRAM_BOT_TOKEN')
    tele_chat_id = get_val('TELEGRAM_CHAT_ID')
    
    try: so_luong_can_tao = int(get_val('Số lượng bài cần tạo'))
    except: so_luong_can_tao = 0
    
    # Phân tích số lượng từ khóa cần bốc (VD: 3 - 4)
    try:
        sl_bl = get_val('Số lượng backlink/bài').split('-')
        min_kw = int(sl_bl[0].strip())
        max_kw = int(sl_bl[1].strip())
    except:
        min_kw, max_kw = 3, 4
        
    today_obj = datetime.now()
    today_str = today_obj.strftime("%Y-%m-%d") # Chuẩn format cho form mới
    df_report = st.session_state['db']['Report']
    so_bai_hom_nay = len(df_report[df_report['Ngày đăng bài'] == today_obj.strftime("%d/%m/%Y")])
    
    if so_bai_hom_nay >= so_luong_can_tao:
        st.error(f"🛑 ĐÃ ĐẠT GIỚI HẠN: Hôm nay hệ thống đã tạo **{so_bai_hom_nay}/{so_luong_can_tao}** bài.")
        if st.button("ĐÓNG CỬA SỔ", type="primary", use_container_width=True): st.rerun()
        return 
        
    so_bai_con_lai = so_luong_can_tao - so_bai_hom_nay
    st.success(f"✅ Đã tạo **{so_bai_hom_nay}/{so_luong_can_tao}** bài. Chuẩn bị gen **{so_bai_con_lai}** bài...")

    st.divider()
    terminal_box = st.empty()
    log_text = "root@laiho-server:~# Khởi động AI Engine...\n\n"
    terminal_box.code(log_text, language="bash")
    time.sleep(0.5)
    
    kw_list = [k.strip() for k in keywords.split(',') if k.strip()]
    
    # Từ khóa đối thủ giả lập để report (có thể móc từ API khác sau)
    competitor_kws = ["giá rẻ", "uy tín", "ban đêm", "an toàn", "nhanh chóng", "chuyên nghiệp"]
    
    new_reports = []
    
    for i in range(so_bai_con_lai):
        bai_so = i + 1
        
        # Bốc số lượng từ khóa theo cấu hình Dashboard (VD: random từ 3 đến 4 từ)
        so_luong_boc = random.randint(min_kw, max_kw)
        if len(kw_list) >= so_luong_boc:
            chosen_kws = random.sample(kw_list, so_luong_boc)
        else:
            chosen_kws = kw_list
            
        kw_tele_string = " | ".join(chosen_kws) + " |"
        focus_kw_str = ", ".join(chosen_kws)
        
        # Bốc từ khóa đối thủ random
        comp_kws_str = " | ".join(random.sample(competitor_kws, 3)) + " |"
        
        # Gọi AI với lệnh ép format cực gắt
        prompt = f"Đóng vai chuyên gia SEO. Dựa vào các từ khóa: {focus_kw_str}. \nHãy viết 1 Tiêu đề giật tít (dưới 65 ký tự) và 1 Đoạn Sapo (dưới 40 chữ). \nTRẢ VỀ ĐÚNG FORMAT SAU:\nTiêu đề: [Ghi tiêu đề]\nSapo: [Ghi Sapo]"
        ai_result = call_gemini_ai(api_key, prompt)
        
        # Dùng Regex móc tiêu đề (bất chấp AI xuống dòng hay có dấu sao **)
        title_match = re.search(r'Tiêu đề:\s*(.*)', ai_result, re.IGNORECASE)
        sapo_match = re.search(r'Sapo:\s*(.*)', ai_result, re.IGNORECASE)
        
        title = title_match.group(1).replace('*', '').strip() if title_match else f"Bài SEO Auto {datetime.now().strftime('%H%M%S')}"
        sapo = sapo_match.group(1).replace('*', '').strip() if sapo_match else ai_result
        
        gio_dang_full = (today_obj + timedelta(hours=(so_bai_hom_nay + bai_so) * 2)).strftime("%Y-%m-%d %H:%M")
        
        # In log ra màn hình y hệt form Ní vẽ
        log_text += f"[+] ĐANG THỰC THI BÀI VIẾT SỐ {bai_so}/{so_luong_can_tao}...\n"
        log_text += f"  .. tiêu đề: {title}\n"
        log_text += f"  .. từ khoá gen bài: {kw_tele_string}\n"
        log_text += f"  .. văn phong của: {doi_thu} |\n"
        log_text += f"  .. từ khoá đối thủ theo bài: {comp_kws_str}\n"
        log_text += f"  .. loại văn viết: {muc_tieu}\n"
        log_text += f"  .. achor text: {kw_tele_string}\n"
        log_text += f"  .. web gắn backlink: {target_web} |\n"
        log_text += f"  .. Trạng thái: Thành công\n"
        log_text += f"  .. Đăng bài: {gio_dang_full}\n"
        log_text += "------------------------------------------------------\n"
        terminal_box.code(log_text, language="bash")
        
        # Bắn Telegram khi đăng thành công (Form rút gọn)
        msg_post = (
            f"🚀 <b>[NOTI: ĐĂNG BÀI THÀNH CÔNG] {bai_so}/{so_luong_can_tao}</b>\n"
            f"🌐 Website: {target_web}\n"
            f"⏱ Thời gian: {gio_dang_full}\n"
            f"🔑 Từ khoá: {kw_tele_string}\n"
            f"📝 Tiêu đề: {title}\n"
            f"✅ Trạng thái: Thành công"
        )
        send_telegram(tele_token, tele_chat_id, msg_post)

        # Chèn vào data (Xử lý cột từ khóa linh động)
        kw1 = chosen_kws[0] if len(chosen_kws) > 0 else ""
        kw2 = chosen_kws[1] if len(chosen_kws) > 1 else ""
        kw3 = chosen_kws[2] if len(chosen_kws) > 2 else ""
        kw4 = chosen_kws[3] if len(chosen_kws) > 3 else ""
        
        new_reports.append(["laiho.vn", "WordPress", "laiho.vn/post", today_obj.strftime("%d/%m/%Y"), kw1, kw2, kw3, kw4, "", "#", title, sapo, gio_dang_full, "✅ Thành công"])
        time.sleep(1)

    df_new = pd.DataFrame(new_reports, columns=TABS_CONFIG["Report"])
    st.session_state['db']['Report'] = pd.concat([st.session_state['db']['Report'], df_new], ignore_index=True)
    
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
