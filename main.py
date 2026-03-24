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
    "Backlink": ["Từ khoá", "Đã dùng"], 
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Website đích", "Trạng thái", "Giới hạn bài/ngày"], 
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
        ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say về nhà, dịch vụ lái xe an toàn"],
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
    
    st.session_state['db']['Backlink'] = pd.DataFrame([
        ["thuê tài xế", "0"], ["đưa người say về nhà", "0"]
    ], columns=TABS_CONFIG["Backlink"])

    st.session_state['db']['Website'] = pd.DataFrame([
        ["Blog Lái Xe", "WordPress", "bloglaixe.wordpress.com", "laiho.vn", "Active", "3"]
    ], columns=TABS_CONFIG["Website"])

def calculate_seo_score(title, sapo, keywords):
    score = 0
    title_lower = title.lower()
    sapo_lower = sapo.lower()
    valid_kws = [kw.strip().lower() for kw in keywords if kw.strip()]
    if not valid_kws or "LỖI AI" in title: return 0 
    
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
            return f"Lỗi API ({response.status_code}): Vui lòng check lại API Key"
    except Exception as e:
        return f"Lỗi kết nối mạng: {str(e)}"

def send_telegram(bot_token, chat_id, message):
    bot_token = str(bot_token).strip()
    chat_id = str(chat_id).strip()
    if not bot_token or not chat_id or "Dán_" in bot_token: return
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML", "link_preview_options": {"is_disabled": True}}
    try: requests.post(url, json=payload, timeout=5)
    except: pass

@st.dialog("🤖 TRUNG TÂM ĐIỀU KHIỂN ROBOT SEO", width="large")
def hacker_terminal():
    df_dash = st.session_state['db']['Dashboard']
    def get_val(key_name):
        try: return df_dash.loc[df_dash['Hạng mục'] == key_name, 'Giá trị thực tế'].values[0]
        except: return ""
            
    # HỆ THỐNG VẪN LẤY KEY THẬT TỪ DATABASE NGẦM ĐỂ CHẠY
    api_key = get_val('GEMINI_API_KEY')
    keywords = get_val('Danh sách Keyword bài viết')
    doi_thu = get_val('Website đối thủ').replace(',', ' |')
    tele_token = get_val('TELEGRAM_BOT_TOKEN')
    tele_chat_id = get_val('TELEGRAM_CHAT_ID')
    
    try: so_luong_can_tao = int(get_val('Số lượng bài cần tạo'))
    except: so_luong_can_tao = 0
    try:
        sl_bl = get_val('Số lượng backlink/bài').split('-')
        min_kw, max_kw = int(sl_bl[0].strip()), int(sl_bl[1].strip())
    except: min_kw, max_kw = 3, 4
        
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
    competitor_kws = ["giá rẻ", "uy tín", "ban đêm", "an toàn", "nhanh chóng", "chuyên nghiệp"]
    df_backlink = st.session_state['db']['Backlink']
    df_website = st.session_state['db']['Website']
    hardcoded_style = "VĂN PHONG BẮT BUỘC: Bài viết mang tính tư vấn, giới thiệu, hướng dẫn. TUYỆT ĐỐI KHÔNG đánh giá đối thủ, KHÔNG viết kiểu bán hàng, KHÔNG ép mua sản phẩm."
    
    new_reports = []
    
    for i in range(so_bai_con_lai):
        bai_so = i + 1
        if not df_website.empty:
            random_site = df_website.sample(n=1).iloc[0]
            satellite_url = random_site['URL / ID']
            satellite_platform = random_site['Nền tảng']
            target_webs_raw = str(random_site['Website đích'])
            target_web_list = [w.strip() for w in target_webs_raw.split(',') if w.strip()]
            target_web = random.choice(target_web_list) if target_web_list else get_val('TARGET_URL')
        else:
            satellite_url, satellite_platform, target_web = "Chưa cấu hình", "N/A", get_val('TARGET_URL')

        so_luong_boc = random.randint(min_kw, max_kw)
        chosen_kws = random.sample(kw_list, so_luong_boc) if len(kw_list) >= so_luong_boc else kw_list
        kw_tele_string = " | ".join(chosen_kws) + " |"
        focus_kw_str = ", ".join(chosen_kws)
        comp_kws_str = " | ".join(random.sample(competitor_kws, 4)) + " |"
        
        if not df_backlink.empty:
            sl_anchor = min(random.randint(2, 3), len(df_backlink))
            anchor_list = df_backlink.sample(n=sl_anchor)['Từ khoá'].tolist()
            anchor_text_str = " | ".join(anchor_list) + " |"
        else: anchor_text_str = "Chưa có data backlink |"
        
        prompt = f"""Đóng vai chuyên gia Content SEO chuẩn Yoast SEO.
Từ khóa chính: {focus_kw_str}\n{hardcoded_style}
NHIỆM VỤ: Viết 1 Tiêu đề SEO (50-60 ký tự) và 1 Sapo (130-150 ký tự) chứa CHÍNH XÁC từ khóa.
TRẢ VỀ ĐÚNG FORMAT SAU:
Tiêu đề: [Ghi tiêu đề]
Sapo: [Ghi Sapo]"""

        ai_result = call_gemini_ai(api_key, prompt)
        clean_result = ai_result.replace('*', '')
        title_match = re.search(r'Tiêu đề:\s*([^\n]*)', clean_result, re.IGNORECASE)
        sapo_match = re.search(r'Sapo:\s*([^\n]*)', clean_result, re.IGNORECASE)
        
        if title_match:
            title = title_match.group(1).strip()
            sapo = sapo_match.group(1).strip() if sapo_match else clean_result
        else:
            title = f"LỖI AI/API: {clean_result[:50]}..." 
            sapo = "API không trả về đúng định dạng."
        
        seo_score = calculate_seo_score(title, sapo, chosen_kws)
        if "LỖI AI" in title: danh_gia = "⚫ Lỗi kết nối AI"
        elif seo_score >= 80: danh_gia = "🟢 Tuyệt vời"
        elif seo_score >= 60: danh_gia = "🟡 Khá"
        else: danh_gia = "🔴 Cần cải thiện"

        gio_dang_full = (today_obj + timedelta(hours=(so_bai_hom_nay + bai_so) * 2)).strftime("%Y-%m-%d %H:%M")
        
        log_text += f"[+] ĐANG THỰC THI BÀI VIẾT SỐ {bai_so}/{so_luong_can_tao}...\n"
        log_text += f"  .. vệ tinh đăng: {satellite_url}\n  .. tiêu đề: {title}\n  .. từ khoá gen bài: {kw_tele_string}\n"
        log_text += f"  .. văn phong của: {doi_thu} |\n  .. từ khoá đối thủ theo bài: {comp_kws_str}\n"
        log_text += f"  .. loại văn viết: Cộng đồng, Hướng dẫn, Tư vấn\n  .. achor text: {anchor_text_str}\n"
        log_text += f"  .. web gắn backlink: {target_web} |\n  .. Trạng thái: {'Thất bại' if 'LỖI AI' in title else 'Thành công'}\n"
        log_text += f"  .. Điểm SEO thực tế: {seo_score}/100 ({danh_gia})\n  .. Đăng bài: {gio_dang_full}\n------------------------------------------------------\n"
        terminal_box.code(log_text, language="bash")
        
        msg_post = f"🚀 <b>[NOTI: ĐĂNG BÀI VỆ TINH] {bai_so}/{so_luong_can_tao}</b>\n🛰 Vệ tinh: {satellite_url}\n🎯 Bắn link về: {target_web}\n⏱ Thời gian: {gio_dang_full}\n🔑 Từ khoá: {kw_tele_string}\n📝 Tiêu đề: {title}\n📈 Điểm SEO: {seo_score}/100\n✅ Trạng thái: {'Lỗi AI' if 'LỖI AI' in title else 'Thành công'}"
        send_telegram(tele_token, tele_chat_id, msg_post)

        kw1 = chosen_kws[0] if len(chosen_kws) > 0 else ""
        kw2 = chosen_kws[1] if len(chosen_kws) > 1 else ""
        new_reports.append([satellite_url, satellite_platform, satellite_url+"/post", today_obj.strftime("%d/%m/%Y"), kw1, kw2, "", "", "", target_web, title, sapo, gio_dang_full, "✅ Thành công" if "LỖI" not in title else "❌ Lỗi AI", f"{seo_score}/100"])
        time.sleep(1)

    df_new = pd.DataFrame(new_reports, columns=TABS_CONFIG["Report"])
    st.session_state['db']['Report'] = pd.concat([st.session_state['db']['Report'], df_new], ignore_index=True)
    
    log_text += f"🚀 TIẾN TRÌNH HOÀN TẤT! XUẤT THÀNH CÔNG {so_bai_con_lai} BÀI."
    terminal_box.code(log_text, language="bash")
        
    st.write("")
    if st.button("ĐÓNG TERMINAL & KIỂM TRA BÁO CÁO", type="primary", use_container_width=True): st.rerun()

# ==========================================
# GIAO DIỆN CHÍNH (UI) - ĐÃ BỌC THÉP BẢO MẬT
# ==========================================
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)
tabs = st.tabs(list(TABS_CONFIG.keys()))

for i, (name, cols) in enumerate(TABS_CONFIG.items()):
    with tabs[i]:
        # 1. KHU VỰC FORM NHẬP LIỆU: TỰ ĐỘNG XÓA TRẮNG SAU KHI BẤM THÊM
        with st.expander(f"📥 THÊM DỮ LIỆU MỚI VÀO {name}"):
            with st.form(key=f"form_nhaplieu_{name}", clear_on_submit=True):
                st.info("Mẹo: Copy từ Excel/Google Sheet dán vào đây (Dữ liệu cách nhau bằng nút Tab)")
                raw_data = st.text_area("Dán nội dung vào đây:", height=100)
                submit_button = st.form_submit_button("🔥 THÊM VÀO BẢNG")
                
                if submit_button and raw_data:
                    parsed_data = []
                    for line in raw_data.strip().split('\n'):
                        if not line.strip(): continue
                        row = [x.strip() for x in re.split(r'\t|\s{2,}', line) if x.strip()]
                        if len(row) > len(cols): row = row[:len(cols)]
                        elif len(row) < len(cols): row.extend([''] * (len(cols) - len(row)))
                        parsed_data.append(row)
                    
                    df_new_input = pd.DataFrame(parsed_data, columns=cols)
                    st.session_state['db'][name] = pd.concat([st.session_state['db'][name], df_new_input], ignore_index=True)
                    st.rerun()

        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 3])
        with c1: st.button("☁️ ĐỒNG BỘ GOOGLE SHEET", key=f"up_{name}", use_container_width=True)
        with c2: st.button("🔄 LÀM MỚI (PULL DATA)", key=f"res_{name}", use_container_width=True)
        with c3:
            if name == "Dashboard":
                if st.button("🔥 START ROBOT AI", key="run_robot", type="primary", use_container_width=True): hacker_terminal()

        # 2. XỬ LÝ MẶT NẠ NINJA BẢO MẬT HIỂN THỊ
        display_df = st.session_state['db'][name].copy()
        
        if name == "Dashboard":
            sensitive_keywords = ["API", "TOKEN", "PASSWORD", "ID"]
            for idx, row in display_df.iterrows():
                if any(secret in str(row['Hạng mục']).upper() for secret in sensitive_keywords):
                    display_df.at[idx, 'Giá trị thực tế'] = "****************" # Che khuất tầm nhìn

        # 3. HIỂN THỊ: CHỈ TAB REPORT ĐƯỢC QUYỀN SỬA/XÓA
        if name == "Report":
            st.session_state['db'][name] = st.data_editor(
                st.session_state['db'][name], use_container_width=True, num_rows="dynamic", height=500, hide_index=True, key=f"edit_{name}"
            )
        else:
            # CÁC TAB CÒN LẠI BỊ KHÓA CỨNG (KHÔNG THỂ XÓA CHỮ, KHÔNG THỂ XÓA DÒNG)
            st.dataframe(display_df, use_container_width=True, height=500, hide_index=True)
