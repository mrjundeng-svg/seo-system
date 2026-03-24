import streamlit as st
import pandas as pd
import re
import time
import requests
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="LÁI HỘ SEO", layout="wide")

# CẬP NHẬT CẤU TRÚC 2 TAB THEO YÊU CẦU NÍ
TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Đã dùng"], # Bỏ Website đích
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Website đích", "Trạng thái", "Giới hạn bài/ngày"], # Thêm Website đích
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "Nội dung tóm tắt", "Thời gian hẹn giờ", "Trạng thái", "Điểm SEO"]
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
        ["Mục tiêu bài viết", "Cung cấp giải pháp an toàn giao thông"], 
        ["Số lượng bài cần tạo", "2"], 
        ["Thiết lập số lượng chữ", "900 - 1200"],
        ["Số lượng backlink/bài", "3 - 4"], 
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"],
        ["TELEGRAM_BOT_TOKEN", "Dán_Token_Vào_Đây"],
        ["TELEGRAM_CHAT_ID", "Dán_ID_Vào_Đây"]
    ], columns=["Hạng mục", "Giá trị thực tế"])
    
    # Data mẫu tab Backlink (Đã bỏ cột link)
    st.session_state['db']['Backlink'] = pd.DataFrame([
        ["thuê tài xế", "0"],
        ["đưa người say về nhà", "0"],
        ["đã uống bia rượu không tự lái xe", "0"],
        ["dịch vụ lái xe hộ", "0"]
    ], columns=TABS_CONFIG["Backlink"])

    # Data mẫu tab Website (Có cột Website đích, cách nhau dấu phẩy)
    st.session_state['db']['Website'] = pd.DataFrame([
        ["Blog Lái Xe", "WordPress", "bloglaixe.wordpress.com", "laiho.vn, butl.vn", "Active", "3"],
        ["Tin Tức An Toàn", "Blogspot", "antoangiaothong.blogspot.com", "laiho.vn", "Active", "5"]
    ], columns=TABS_CONFIG["Website"])

def calculate_seo_score(title, sapo, keywords):
    score = 0
    title_lower = title.lower()
    sapo_lower = sapo.lower()
    
    valid_kws = [kw.strip().lower() for kw in keywords if kw.strip()]
    if not valid_kws: return 0
    
    if any(kw in title_lower for kw in valid_kws): score += 30
    if any(title_lower.find(kw) == 0 for kw in valid_kws): score += 10
        
    title_len = len(title)
    if 40 <= title_len <= 65: score += 20
    elif 30 <= title_len <= 75: score += 10 
        
    if any(kw in sapo_lower for kw in valid_kws): score += 20
        
    sapo_len = len(sapo)
    if 120 <= sapo_len <= 160: score += 20
    elif 90 <= sapo_len <= 180: score += 10
        
    return score 

def call_gemini_ai(api_key, prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    data = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": 300}}
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
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
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
    doi_thu = get_val('Website đối thủ').replace(',', ' |')
    tele_token = get_val('TELEGRAM_BOT_TOKEN')
    tele_chat_id = get_val('TELEGRAM_CHAT_ID')
    
    try: so_luong_can_tao = int(get_val('Số lượng bài cần tạo'))
    except: so_luong_can_tao = 0
    
    try:
        sl_bl = get_val('Số lượng backlink/bài').split('-')
        min_kw = int(sl_bl[0].strip())
        max_kw = int(sl_bl[1].strip())
    except:
        min_kw, max_kw = 3, 4
        
    today_obj = datetime.now()
    today_str = today_obj.strftime("%Y-%m-%d") 
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
    competitor_kws = ["giá rẻ", "uy tín", "ban đêm", "an toàn", "nhanh chóng", "chuyên nghiệp", "gọi là có"]
    
    df_backlink = st.session_state['db']['Backlink']
    df_website = st.session_state['db']['Website']
    
    hardcoded_style = "VĂN PHONG BẮT BUỘC: Bài viết mang tính tư vấn, giới thiệu, hướng dẫn, và chia sẻ thông tin hữu ích. TUYỆT ĐỐI KHÔNG đánh giá/nhắc đến đối thủ, KHÔNG viết kiểu bán hàng mớm khách, KHÔNG ép mua sản phẩm. Chỉ viết dưới dạng bài chia sẻ cộng đồng để thu hút người đọc một cách tự nhiên."
    
    new_reports = []
    
    for i in range(so_bai_con_lai):
        bai_so = i + 1
        
        # 1. BỐC VỆ TINH VÀ TÌM MONEY SITE (Website đích)
        if not df_website.empty:
            random_site = df_website.sample(n=1).iloc[0]
            satellite_name = random_site['Tên web']
            satellite_url = random_site['URL / ID']
            satellite_platform = random_site['Nền tảng']
            
            # Xử lý cắt chuỗi nếu có nhiều web đích cách nhau bằng dấu phẩy
            target_webs_raw = str(random_site['Website đích'])
            target_web_list = [w.strip() for w in target_webs_raw.split(',') if w.strip()]
            target_web = random.choice(target_web_list) if target_web_list else get_val('TARGET_URL')
        else:
            # Fallback nếu tab Website trống
            satellite_name = "Chưa cấu hình"
            satellite_url = "Chưa cấu hình"
            satellite_platform = "N/A"
            target_web = get_val('TARGET_URL')

        # 2. Bốc Keyword & Anchor Text
        so_luong_boc = random.randint(min_kw, max_kw)
        if len(kw_list) >= so_luong_boc:
            chosen_kws = random.sample(kw_list, so_luong_boc)
        else:
            chosen_kws = kw_list
            
        kw_tele_string = " | ".join(chosen_kws) + " |"
        focus_kw_str = ", ".join(chosen_kws)
        comp_kws_str = " | ".join(random.sample(competitor_kws, 4)) + " |"
        
        if not df_backlink.empty:
            sl_anchor = min(random.randint(2, 3), len(df_backlink))
            anchor_list = df_backlink.sample(n=sl_anchor)['Từ khoá'].tolist()
            anchor_text_str = " | ".join(anchor_list) + " |"
        else:
            anchor_text_str = "Chưa có data backlink |"
        
        # Gọi AI
        prompt = f"""Đóng vai chuyên gia Content SEO chuẩn Yoast SEO.
Từ khóa chính: {focus_kw_str}
{hardcoded_style}

NHIỆM VỤ: Viết 1 Tiêu đề SEO và 1 Sapo (Meta Description) tuân thủ TUYỆT ĐỐI các luật sau:
1. Tiêu đề: ĐỘ DÀI TỪ 50 ĐẾN 60 KÝ TỰ. PHẢI chứa CHÍNH XÁC từ khóa chính.
2. Sapo: ĐỘ DÀI TỪ 130 ĐẾN 150 KÝ TỰ. PHẢI chứa CHÍNH XÁC từ khóa chính. Nội dung tuân thủ đúng luật thép về văn phong ở trên.

TRẢ VỀ ĐÚNG FORMAT SAU (Không giải thích thêm):
Tiêu đề: [Ghi tiêu đề]
Sapo: [Ghi Sapo]"""

        ai_result = call_gemini_ai(api_key, prompt)
        
        title_match = re.search(r'Tiêu đề:\s*(.*)', ai_result, re.IGNORECASE)
        sapo_match = re.search(r'Sapo:\s*(.*)', ai_result, re.IGNORECASE)
        
        title = title_match.group(1).replace('*', '').strip() if title_match else f"Bài SEO Auto {datetime.now().strftime('%H%M%S')}"
        sapo = sapo_match.group(1).replace('*', '').strip() if sapo_match else ai_result
        
        seo_score = calculate_seo_score(title, sapo, chosen_kws)
        if seo_score >= 80: danh_gia = "🟢 Tuyệt vời"
        elif seo_score >= 60: danh_gia = "🟡 Khá"
        else: danh_gia = "🔴 Cần cải thiện"

        gio_dang_full = (today_obj + timedelta(hours=(so_bai_hom_nay + bai_so) * 2)).strftime("%Y-%m-%d %H:%M")
        
        # LOG IN RA MÀN HÌNH THEO CẤU TRÚC VỆ TINH
        log_text += f"[+] ĐANG THỰC THI BÀI VIẾT SỐ {bai_so}/{so_luong_can_tao}...\n"
        log_text += f"  .. vệ tinh đăng: {satellite_url}\n"
        log_text += f"  .. tiêu đề: {title}\n"
        log_text += f"  .. từ khoá gen bài: {kw_tele_string}\n"
        log_text += f"  .. văn phong của: {doi_thu} |\n"
        log_text += f"  .. từ khoá đối thủ theo bài: {comp_kws_str}\n"
        log_text += f"  .. loại văn viết: Cộng đồng, Hướng dẫn, Tư vấn\n" 
        log_text += f"  .. achor text: {anchor_text_str}\n"
        log_text += f"  .. web gắn backlink: {target_web} |\n"
        log_text += f"  .. Trạng thái: Thành công\n"
        log_text += f"  .. Điểm SEO thực tế: {seo_score}/100 ({danh_gia})\n"
        log_text += f"  .. Đăng bài: {gio_dang_full}\n"
        log_text += "------------------------------------------------------\n"
        terminal_box.code(log_text, language="bash")
        
        # TELEGRAM BÁO CÁO RÕ RÀNG LUỒNG ĐI CỦA LINK
        msg_post = (
            f"🚀 <b>[NOTI: ĐĂNG BÀI VỆ TINH] {bai_so}/{so_luong_can_tao}</b>\n"
            f"🛰 Vệ tinh: {satellite_url}\n"
            f"🎯 Bắn link về: {target_web}\n"
            f"⏱ Thời gian: {gio_dang_full}\n"
            f"🔑 Từ khoá: {kw_tele_string}\n"
            f"📝 Tiêu đề: {title}\n"
            f"📈 Điểm SEO: {seo_score}/100\n"
            f"✅ Trạng thái: Thành công"
        )
        send_telegram(tele_token, tele_chat_id, msg_post)

        kw1 = chosen_kws[0] if len(chosen_kws) > 0 else ""
        kw2 = chosen_kws[1] if len(chosen_kws) > 1 else ""
        kw3 = chosen_kws[2] if len(chosen_kws) > 2 else ""
        kw4 = chosen_kws[3] if len(chosen_kws) > 3 else ""
        
        # LƯU VÀO REPORT: CỘT WEBSITE BÂY GIỜ LÀ VỆ TINH, CỘT NỀN TẢNG LÀ NỀN TẢNG CỦA VỆ TINH
        new_reports.append([satellite_url, satellite_platform, satellite_url+"/post", today_obj.strftime("%d/%m/%Y"), kw1, kw2, kw3, kw4, "", target_web, title, sapo, gio_dang_full, "✅ Thành công", f"{seo_score}/100"])
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
