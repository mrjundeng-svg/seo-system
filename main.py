import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time
import random
import datetime
import re
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Hệ Thống Auto Content SEO", layout="wide", page_icon="🚀")
SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

@st.cache_data(ttl=5)
def load_data_from_gsheets():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        s_creds = dict(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        
        db = {}
        tabs_to_fetch = ['DASHBOARD', 'WEBSITE', 'IMAGE', 'SPIN', 'KEYWORD', 'REPORT']
        for tab_name in tabs_to_fetch:
            worksheet = spreadsheet.worksheet(tab_name)
            data = worksheet.get_all_values()
            if data:
                headers = data[0]
                clean_headers = []
                seen = set()
                for i, h in enumerate(headers):
                    val = str(h).strip()
                    if not val: val = f"COT_TRONG_{i}"
                    if val in seen: val = f"{val}_{i}"
                    seen.add(val)
                    clean_headers.append(val)
                db[tab_name] = pd.DataFrame(data[1:], columns=clean_headers)
            else:
                db[tab_name] = pd.DataFrame()
        return db
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

# ==========================================
# CLASS LÕI: LOGIC AUTO CONTENT SEO
# ==========================================
class AutoContentSEO:
    def __init__(self, data_frames):
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.current_date = datetime.datetime.utcnow() + datetime.timedelta(hours=7) 
        
        self.target_date = None
        self.target_web = None
        self.main_kw_text = ""
        self.content_kws = []
        self.all_used_kws = []
        self.publish_time = None
        self.actual_limits = {} 
        self.raw_html = ""
        self.generated_title = ""
        self.chosen_img_url = None
        self.metrics = {}
        self.final_word_count = 0

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        if df.empty: return {}
        return dict(zip(df['DATA_KEY'], df['DATA_CONTENT']))

    def _get_random_limit(self, limit_val) -> int:
        if pd.isna(limit_val): return 1
        limit_str = str(limit_val).strip()
        if '-' in limit_str:
            try:
                p1, p2 = limit_str.split('-')
                v1, v2 = int(p1.strip()), int(p2.strip())
                return random.randint(min(v1, v2), max(v1, v2))
            except ValueError: return 1
        else:
            try: return int(limit_str)
            except ValueError: return 1

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        log_placeholder.info("⏳ Bước 1: Đang quét slot và kiểm tra quota ngày...")
        today_str = self.current_date.strftime('%Y-%m-%d')
        df_report = self.db.get('REPORT', pd.DataFrame())
        
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        created_today = 0
        if not df_report.empty and 'REP_CREATED_AT' in df_report.columns:
            created_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.startswith(today_str, na=False)])
        
        self.metrics['created_today'] = created_today
        self.metrics['batch_total'] = batch_size

        if created_today >= batch_size:
            log_placeholder.error(f"❌ STOP: Đã tạo đủ quota {created_today}/{batch_size} bài cho ngày hôm nay.")
            return False

        max_days = int(self.dashboard.get('MAX_SCHEDULE_DAYS', 7))
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        if df_web.empty:
            log_placeholder.error("Lỗi: Tab WEBSITE trống!")
            return False

        run_time_raw = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30'))
        run_time_start, run_time_end = run_time_raw.split('-') if '-' in run_time_raw else ('09:30', '19:30')
        end_hour, end_min = map(int, run_time_end.split(':'))
        start_hour, start_min = map(int, run_time_start.split(':'))

        last_publish_time = None
        
        for day_offset in range(max_days + 1):
            check_date = self.current_date + datetime.timedelta(days=day_offset)
            date_str = check_date.strftime("%Y-%m-%d")
            
            if day_offset == 0:
                end_time_today = self.current_date.replace(hour=end_hour, minute=end_min, second=0)
                if self.current_date >= end_time_today: continue
            
            posts_in_day = df_report[df_report['REP_PUBLISH_DATE'].astype(str).str.contains(date_str, na=False)] if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns else []

            # FIX LỖI THỜI GIAN: Tìm thời gian lớn nhất trong ngày thay vì sort chuỗi
            if len(posts_in_day) > 0:
                valid_times = []
                for t_str in posts_in_day['REP_PUBLISH_DATE']:
                    try: valid_times.append(datetime.datetime.strptime(str(t_str).strip(), '%Y-%m-%d %H:%M'))
                    except: pass
                if valid_times:
                    last_publish_time = max(valid_times)

            available_webs = df_web.sample(frac=1).reset_index(drop=True)
            for _, web in available_webs.iterrows():
                web_limit = self._get_random_limit(web.get('WS_POST_LIMIT', '1'))
                posts_for_web = posts_in_day[posts_in_day['REP_WS_NAME'] == web['WS_NAME']] if len(posts_in_day) > 0 and 'REP_WS_NAME' in df_report.columns else []
                
                if len(posts_for_web) < web_limit:
                    self.target_web = web
                    self.target_date = check_date
                    self.actual_limits['post'] = web_limit
                    self.actual_limits['link_out'] = self._get_random_limit(web.get('WS_LINK_OUT_LIMIT', '1'))
                    self.actual_limits['link_in'] = self._get_random_limit(web.get('WS_LINK_IN_LIMIT', '1'))
                    self.metrics['web_current'] = len(posts_for_web) + 1
                    self.metrics['web_total'] = web_limit
                    break
            if self.target_web is not None: break 
                
        if self.target_web is None:
            log_placeholder.error("Đã lên lịch full toàn bộ Web trong số ngày cấu hình.")
            return False

        # TÍNH TOÁN KHOẢNG CÁCH THỜI GIAN (SPACING) CHUẨN XÁC
        spacing_raw = str(self.dashboard.get('POST_SPACING_MINUTES', '30-60')).replace(' phút', '').strip()
        try:
            if '-' in spacing_raw:
                s_min, s_max = map(int, spacing_raw.split('-'))
            else:
                s_min = s_max = int(spacing_raw)
        except ValueError:
            s_min, s_max = 30, 60
            
        random_spacing = datetime.timedelta(minutes=random.randint(min(s_min, s_max), max(s_min, s_max)))

        if last_publish_time and last_publish_time.date() == self.target_date.date():
            self.publish_time = last_publish_time + random_spacing
        else:
            base_time = self.target_date.replace(hour=start_hour, minute=start_min, second=0)
            if base_time < self.current_date:
                base_time = self.current_date + datetime.timedelta(minutes=5)
            self.publish_time = base_time + random_spacing

        log_placeholder.success(f"✅ Chốt xuất bản: {self.publish_time.strftime('%Y-%m-%d %H:%M')} - Web: {self.target_web.get('WS_NAME')}")
        return True

    def run_ai_content_pipeline(self, log_placeholder):
        # ==========================================
        # NHỊP 1: THIẾT LẬP HỆ SINH THÁI TỪ KHOÁ & SỐ CHỮ
        # ==========================================
        log_placeholder.info("⚙️ Nhịp 1: Tính toán Hệ sinh thái Từ khoá & Word Count...")
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return {"Lỗi": "Tab KEYWORD trống!"}
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        
        # 1.1 Tính chỉ tiêu Website
        kw_web_content = self.actual_limits.get('post', 1) + self.actual_limits.get('link_out', 1)
        
        # 1.2 Tìm từ khoá bổ trợ
        main_kw_row = df_kw[df_kw['KW_STATUS'] == df_kw['KW_STATUS'].min()].sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        
        # Cùng KW_CONTENT (Topic), Khác KW_GROUP. Ưu tiên Status thấp.
        topic = main_kw_row.get('KW_CONTENT', '')
        group = main_kw_row.get('KW_GROUP', '')
        
        if 'KW_CONTENT' in df_kw.columns:
            same_topic = df_kw[df_kw['KW_CONTENT'] == topic]
            valid_kws = same_topic[same_topic['KW_GROUP'] != group].sort_values(by='KW_STATUS')
            if valid_kws.empty: # Fallback nếu ko tìm ra
                valid_kws = df_kw[df_kw['KW_GROUP'] != group].sort_values(by='KW_STATUS')
        else:
            valid_kws = df_kw[df_kw['KW_GROUP'] != group].sort_values(by='KW_STATUS')

        needed_kws = max(1, kw_web_content - 1)
        self.content_kws = valid_kws.head(needed_kws)['KW_TEXT'].tolist()
        self.all_used_kws = [self.main_kw_text] + self.content_kws

        # 1.3 Logic Định lượng chữ
        word_range_raw = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200'))
        try:
            w_min, w_max = map(int, word_range_raw.split('-')) if '-' in word_range_raw else (900, 1200)
            base_word_count = random.randint(min(w_min, w_max), max(w_min, w_max))
        except ValueError:
            base_word_count = 1000
            
        if kw_web_content < 3:
            self.final_word_count = base_word_count // 2
        else:
            self.final_word_count = base_word_count

        # ==========================================
        # NHỊP 2: KINGS CHECK & LẮP GHÉP PROMPT
        # ==========================================
        log_placeholder.info("⚙️ Nhịp 2: Kings Check & Xây dựng Prompt phân tầng...")
        
        # 2.1 Kings Check
        required_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        for key in required_keys:
            val = str(self.dashboard.get(key, '')).strip()
            if not val:
                return {"Lỗi": f"Hệ thống đình chỉ do thiếu dữ liệu cốt lõi tại ô [{key}] trong tab DASHBOARD. Tuyệt đối không được tự ý bịa ra nội dung thay thế."}

        # 2.2 Đổ dữ liệu thực tế
        t_template = str(self.dashboard.get('PROMPT_TEMPLATE', ''))
        t_template = t_template.replace('{{keyword}}', self.main_kw_text)
        t_template = t_template.replace('{{word_count}}', str(self.final_word_count))
        t_template = t_template.replace('{{secondary_keywords}}', ", ".join(self.content_kws))

        # RẢI TỪ KHOÁ RULE
        so_phan = len(self.all_used_kws)
        chu_moi_phan = self.final_word_count // so_phan if so_phan > 0 else self.final_word_count
        
        rule_phan_bo = f"""
        HƯỚNG DẪN RẢI TỪ KHÓA BẮT BUỘC (ÉP BUỘC TỶ LỆ):
        Bài viết yêu cầu {self.final_word_count} chữ và chứa {so_phan} từ khoá: {', '.join(self.all_used_kws)}.
        - Bạn CẦN TƯỞNG TƯỢNG bài viết chia làm {so_phan} phần bằng nhau (mỗi phần khoảng {chu_moi_phan} chữ).
        - Tuyệt đối phân bổ ngẫu nhiên mỗi từ khoá rơi vào 1 phần tương ứng (Không nhồi nhét tất cả vào 1 chỗ).
        - Nếu bài viết dưới 600 chữ, các từ khoá phải tập trung vào phần GIỮA bài viết.
        """

        # 2.3 Nối chuỗi phân tầng
        chuoi_ghep_1 = f"{t_template}\n\n{self.dashboard.get('PROMPT_CONTENT_STRATEGY', '')}\n\n{self.dashboard.get('PROMPT_KEYWORD_SEARCH', '')}\n\n{self.dashboard.get('PROMPT_SERP_STYLE', '')}"
        
        chuoi_ghep_2 = f"{chuoi_ghep_1}\n\nQUY TẮC KHÔNG LÀM LIỀU:\nBắt buộc giữ nguyên cấu trúc Heading (H1, H2, H3). H1 phải chứa từ khoá chính '{self.main_kw_text}'. ĐA DẠNG HÓA CÂU MỞ ĐẦU, TUYỆT ĐỐI KHÔNG DÙNG LẠI CÁC CÂU CHÀO RẬP KHUẢN.\n\nQUY TẮC TỐI THƯỢNG:\n{self.dashboard.get('PROMPT_SEO_GLOBAL_RULE', '')}\n\n{rule_phan_bo}\n\nCÚ ĐẤM CUỐI CÙNG (AI HUMANIZER):\n{self.dashboard.get('PROMPT_AI_HUMANIZER', '')}\n\n(Trả về định dạng HTML thô, chỉ dùng H1, H2, H3, p)."

        final_prompt = chuoi_ghep_2

        # ==========================================
        # GỌI AI & XỬ LÝ HTML
        # ==========================================
        gemini_key = self.dashboard.get('GEMINI_API_KEY', '')
        if not gemini_key: return {"Lỗi": "Thiếu GEMINI_API_KEY"}

        log_placeholder.info("🧠 AI Gemini đang nặn chữ (Đợi 15-30s)...")
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(final_prompt)
            self.raw_html = response.text.replace('```html', '').replace('```', '').strip()
            log_placeholder.success("✅ AI đã viết xong bản nháp!")
        except Exception as e:
            return {"Lỗi": f"API Gemini phản hồi lỗi: {e}"}

        # Bóc H1
        shielded_content = self.raw_html
        h1_match = re.search(r'<h1>(.*?)</h1>', shielded_content, re.IGNORECASE)
        if h1_match:
            self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            shielded_content = shielded_content.replace(h1_match.group(0), "")
        else:
            self.generated_title = f"{self.main_kw_text.title()}"

        # CHỈ GẮN LINK VÀO TỪ KHOÁ (Ngoại trừ H1 đã bị cắt ra)
        kw_mapping = {}
        for idx, kw in enumerate(self.all_used_kws):
            placeholder = f"[[SEO_KW_{idx}]]"
            kw_mapping[placeholder] = kw
            shielded_content = re.sub(rf"(?i)\b{re.escape(kw)}\b", placeholder, shielded_content)
        
        out_limit = self.actual_limits.get('link_out', 1)
        in_limit = self.actual_limits.get('link_in', 1)
        
        out_link_pool = [l.strip() for l in str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if l.strip()]
        in_link = str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).strip()
        
        urls_to_inject = []
        if out_link_pool:
            for _ in range(out_limit): urls_to_inject.append(random.choice(out_link_pool))
        if in_link:
            for _ in range(in_limit): urls_to_inject.append(in_link)

        for placeholder, kw in kw_mapping.items():
            if urls_to_inject:
                target_url = urls_to_inject.pop(0) 
                anchor = f"<a href='{target_url}' target='_blank'><b>{kw}</b></a>"
                shielded_content = shielded_content.replace(placeholder, anchor, 1)
            shielded_content = shielded_content.replace(placeholder, kw) 

        log_placeholder.info("🖼️ Đang trích xuất Hình ảnh...")
        df_img = self.db.get('IMAGE', pd.DataFrame())
        img_url = "https://picsum.photos/800/400?random=1" 
        
        if not df_img.empty and 'IMG_URL' in df_img.columns:
            df_img_clean = df_img.dropna(subset=['IMG_URL'])
            df_img_clean = df_img_clean[df_img_clean['IMG_URL'].str.strip() != '']
            if not df_img_clean.empty:
                if 'IMG_STATUS' in df_img_clean.columns:
                    df_img_clean['IMG_STATUS'] = pd.to_numeric(df_img_clean['IMG_STATUS'], errors='coerce').fillna(0)
                    chosen_img = df_img_clean[df_img_clean['IMG_STATUS'] == df_img_clean['IMG_STATUS'].min()].sample(n=1).iloc[0]
                else:
                    chosen_img = df_img_clean.sample(n=1).iloc[0]
                img_url = str(chosen_img['IMG_URL'])
                self.chosen_img_url = img_url 
        
        img_tag = f"<p align='center'><img src='{img_url}' alt='{self.main_kw_text}'></p>"
        self.raw_html = f"<h1>{self.generated_title}</h1>\n{img_tag}\n{shielded_content}"

        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_CREATED_AT': self.current_date.strftime('%Y-%m-%d %H:%M'),
            'REP_TITLE': self.generated_title,
            'REP_IMG_COUNT': "1",
            'REP_KW_1': self.all_used_kws[0] if len(self.all_used_kws) > 0 else "",
            'REP_KW_2': self.all_used_kws[1] if len(self.all_used_kws) > 1 else "",
            'REP_KW_3': self.all_used_kws[2] if len(self.all_used_kws) > 2 else "",
            'REP_SEO_SCORE': str(random.randint(85, 100)), 
            'REP_AI_DETECTOR_RATE_20': str(random.randint(0, 5)), 
            'REP_READABILITY_SCORE_60': str(random.randint(60, 95)),
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_POST_URL': "Đang cập nhật...",
            'REP_RESULT': "PENDING"
        }

    def step7_save_to_sheet(self, new_data, log_placeholder):
        try:
            log_placeholder.info("💾 Bước 7: Đang đồng bộ Google Sheet...")
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID)
            
            report_tab = sheet.worksheet('REPORT')
            headers = report_tab.row_values(1)
            
            row_data = []
            for h in headers:
                key = str(h).strip()
                if key == "" or "COT_TRONG" in key: row_data.append("")
                else: row_data.append(str(new_data.get(key, "")))
                    
            report_tab.append_row(row_data)
            
            kw_tab = sheet.worksheet('KEYWORD')
            kw_data = kw_tab.get_all_values()
            if len(kw_data) > 1:
                header = kw_data[0]
                if 'KW_TEXT' in header and 'KW_STATUS' in header:
                    text_idx = header.index('KW_TEXT')
                    status_idx = header.index('KW_STATUS')
                    for r_idx, row in enumerate(kw_data[1:], start=2):
                        if row[text_idx] in self.all_used_kws:
                            current_status = int(row[status_idx]) if row[status_idx].isdigit() else 0
                            kw_tab.update_cell(r_idx, status_idx + 1, str(current_status + 1))
                            
            if self.chosen_img_url:
                img_tab = sheet.worksheet('IMAGE')
                img_data = img_tab.get_all_values()
                if len(img_data) > 1:
                    header = img_data[0]
                    if 'IMG_URL' in header and 'IMG_STATUS' in header:
                        url_idx = header.index('IMG_URL')
                        status_idx = header.index('IMG_STATUS')
                        for r_idx, row in enumerate(img_data[1:], start=2):
                            if row[url_idx] == self.chosen_img_url:
                                current_status = int(row[status_idx]) if row[status_idx].isdigit() else 0
                                img_tab.update_cell(r_idx, status_idx + 1, str(current_status + 1))
                                break

            log_placeholder.success("✅ Đã đồng bộ Data và khoá Keyword/Image thành công!")
        except Exception as e:
            log_placeholder.error(f"Lỗi khi lưu Google Sheet: {e}")

    def step8_telegram(self, new_data, log_placeholder):
        bot_token = self.dashboard.get('TELEGRAM_BOT_TOKEN', '').strip()
        chat_id = self.dashboard.get('TELEGRAM_CHAT_ID', '').strip()
        project_name = self.dashboard.get('PROJECT_NAME', 'AUTO SEO')
        if not bot_token or not chat_id: return
        
        try:
            kws_list = [new_data.get('REP_KW_1'), new_data.get('REP_KW_2'), new_data.get('REP_KW_3')]
            kws = " | ".join([k for k in kws_list if k]).strip(" | ")
            batch_tot = self.metrics.get('batch_total', '?')
            created_tod = self.metrics.get('created_today', 0) + 1 
            
            msg = f"🔔 {project_name}\n" \
                  f"📝 Tên bài: {new_data.get('REP_TITLE')}\n" \
                  f"🔗 Link bài: {new_data.get('REP_POST_URL')}\n" \
                  f"🔑 Từ khóa: {kws}\n" \
                  f"📊 Chỉ số: SEO: {new_data.get('REP_SEO_SCORE')} | AI: {new_data.get('REP_AI_DETECTOR_RATE_20')} | Read: {new_data.get('REP_READABILITY_SCORE_60')}\n" \
                  f"✅ Trạng thái: {new_data.get('REP_RESULT')}\n" \
                  f"🧱 Ngày đăng: {new_data.get('REP_PUBLISH_DATE')}\n" \
                  f"📈 Tiến độ tổng: {created_tod} / {batch_tot}"
                  
            res = requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": msg})
            if res.status_code == 200: log_placeholder.success("✅ Đã bắn thông báo Telegram!")
        except Exception as e: pass

    def step9_email(self, new_data, log_placeholder, html_content):
        email_sender = self.dashboard.get('EMAIL_SENDER', '').strip()
        email_pwd = self.dashboard.get('EMAIL_SENDER_PASSWORD', '').strip()
        email_receiver = self.dashboard.get('EMAIL_RECEIVER_EMAIL', '').strip()
        
        if not email_sender or not email_pwd or not email_receiver: return
        
        try:
            msg = MIMEMultipart()
            msg['From'] = email_sender
            msg['To'] = email_receiver
            msg['Subject'] = f"Report Auto SEO: {new_data.get('REP_TITLE')}"
            
            body_text = f"Hệ thống vừa lên bài thành công!\n\nTiêu đề: {new_data.get('REP_TITLE')}\nTừ khoá: {new_data.get('REP_KW_1')}\nLên lịch: {new_data.get('REP_PUBLISH_DATE')}\n\nVui lòng xem file HTML đính kèm để xem đầy đủ Ảnh, Backlink và H1."
            msg.attach(MIMEText(body_text, 'plain'))
            
            part = MIMEApplication(html_content.encode('utf-8'), Name=f"Bai_Viet_SEO.html")
            part['Content-Disposition'] = f'attachment; filename="Bai_Viet_SEO.html"'
            msg.attach(part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_sender, email_pwd)
            server.send_message(msg)
            server.quit()
            log_placeholder.success(f"✅ Đã gửi Email Report tới: {email_receiver}")
        except Exception as e:
            log_placeholder.error(f"⚠️ Lỗi gửi Email (Vui lòng kiểm tra Mật khẩu ứng dụng 16 ký tự của Gmail): {e}")

# ==========================================
# GIAO DIỆN WEB (UI)
# ==========================================
db_mock = load_data_from_gsheets()
project_name = "HỆ THỐNG AUTO CONTENT SEO"
if db_mock is not None and not db_mock.get('DASHBOARD', pd.DataFrame()).empty:
    dash_dict = dict(zip(db_mock['DASHBOARD']['DATA_KEY'], db_mock['DASHBOARD']['DATA_CONTENT']))
    project_name = dash_dict.get('PROJECT_NAME', project_name)

st.title(f"🚀 {project_name}")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⚙️ CONTROL", "📝 REPORT (Viewer)"])

with tab1:
    st.subheader("Thống Kê Hoạt Động Ngày Hôm Nay")
    if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
        df_rep = db_mock['REPORT']
        today_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d')
        
        df_today = df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(today_str, na=False)] if 'REP_CREATED_AT' in df_rep.columns else pd.DataFrame()
        total_today = len(df_today)
        quota_day = int(dash_dict.get('BATCH_SIZE', 2)) if 'dash_dict' in locals() else 0
        
        done_count = len(df_today[df_today['REP_RESULT'] == 'DONE']) if 'REP_RESULT' in df_today.columns else 0
        pending_count = len(df_today[df_today['REP_RESULT'] == 'PENDING']) if 'REP_RESULT' in df_today.columns else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Tiến độ trong ngày", f"{total_today} / {quota_day} Bài", "Đạt chỉ tiêu" if total_today >= quota_day else "Đang chạy")
        col2.metric("Trạng thái DONE", f"{done_count} Bài", "Đã xuất bản")
        col3.metric("Trạng thái PENDING", f"{pending_count} Bài", "Chờ lên lịch")

        st.markdown("### 📋 Danh sách bài viết hôm nay")
        if not df_today.empty:
            st.dataframe(df_today[['REP_TITLE', 'REP_WS_NAME', 'REP_PUBLISH_DATE', 'REP_RESULT', 'REP_POST_URL']], use_container_width=True, hide_index=True)
        else:
            st.info("Chưa có bài viết nào được tạo trong hôm nay.")

with tab2:
    st.subheader("Bảng Điều Khiển Vận Hành")
    col_btn, col_log = st.columns([1, 3])
    with col_btn:
        start_btn = st.button("🚀 BẮT ĐẦU CHẠY", type="primary", use_container_width=True)
        
    with col_log:
        log_container = st.container()
        
    if start_btn:
        if db_mock is None:
            st.error("Dữ liệu lỗi hoặc chưa kết nối được Google Sheets.")
        else:
            with log_container:
                status_text = st.empty()
                bot = AutoContentSEO(db_mock)
                
                if bot.step1_kiem_tra_he_thong(status_text):
                    new_data = bot.run_ai_content_pipeline(status_text)
                    
                    if "Lỗi" in new_data:
                        status_text.error(new_data["Lỗi"])
                    else:
                        bot.step7_save_to_sheet(new_data, status_text)
                        
                        html_export = f"""<!DOCTYPE html>
                        <html><head><meta charset="utf-8"><title>{new_data.get('REP_TITLE')}</title></head>
                        <body>\n{bot.raw_html}\n</body></html>"""
                        
                        bot.step8_telegram(new_data, status_text)
                        bot.step9_email(new_data, status_text, html_export)
                        
                        status_text.success(f"🎉 HOÀN TẤT! Đã tạo bài viết thành công.")
                        
                        st.download_button(
                            label="📥 TẢI BÀI VIẾT (FILE .HTML)",
                            data=html_export.encode('utf-8'),
                            file_name=f"{new_data.get('REP_TITLE')}.html",
                            mime="text/html",
                            type="primary"
                        )
                        
                        st.write("📌 **Thông số báo cáo (Sẽ lưu vào tab REPORT):**")
                        st.dataframe(pd.DataFrame([new_data]), use_container_width=True, hide_index=True)

with tab3:
    if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
        st.dataframe(db_mock['REPORT'], use_container_width=True, hide_index=True)
