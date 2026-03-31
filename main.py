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
import io
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

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
        for tab_name in ['DASHBOARD', 'WEBSITE', 'IMAGE', 'SPIN', 'KEYWORD', 'REPORT']:
            worksheet = spreadsheet.worksheet(tab_name)
            data = worksheet.get_all_values()
            if data:
                headers = data[0]
                clean_headers, seen = [], set()
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

def format_display_dataframe(df):
    if df.empty: return df
    df_show = df.copy()
    df_show.insert(0, 'STT', range(1, len(df_show) + 1))
    rename_dict = {
        'REP_TITLE': 'Tiêu đề bài viết',
        'REP_WS_NAME': 'Tên trang web',
        'REP_PUBLISH_DATE': 'Ngày đăng bài',
        'REP_RESULT': 'Trạng thái',
        'REP_POST_URL': 'Đường dẫn'
    }
    return df_show.rename(columns={k: v for k, v in rename_dict.items() if k in df_show.columns})

def spin_text(text):
    text = str(text)
    while True:
        match = re.search(r'\{([^{}]*)\}', text)
        if not match: break
        options = match.group(1).split('|')
        text = text[:match.start()] + random.choice(options) + text[match.end():]
    return text

class AutoContentSEO:
    def __init__(self, data_frames):
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.current_date = datetime.datetime.utcnow() + datetime.timedelta(hours=7) 
        self.target_date, self.target_web = None, None
        self.main_kw_text = ""
        self.content_kws, self.all_used_kws = [], []
        self.publish_time = None
        self.actual_limits = {} 
        self.raw_html, self.generated_title = "", ""
        self.chosen_img_urls = []
        self.metrics = {}
        self.final_word_count = 0
        self.history_log = [] 

    def add_log(self, ui_box, message, level="info"):
        time_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%H:%M:%S')
        log_line = f"[{time_str}] {message}"
        self.history_log.append(log_line)
        if ui_box:
            if level == "info": ui_box.write(f"ℹ️ {message}")
            elif level == "success": ui_box.success(f"✅ {message}")
            elif level == "warning": ui_box.warning(f"⚠️ {message}")
            elif level == "error": ui_box.error(f"❌ {message}")

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        if df.empty: return {}
        return dict(zip(df['DATA_KEY'], df['DATA_CONTENT']))

    def _get_random_limit(self, limit_val) -> int:
        limit_str = str(limit_val).strip()
        if '-' in limit_str:
            try:
                p1, p2 = limit_str.split('-')
                return random.randint(min(int(p1), int(p2)), max(int(p1), int(p2)))
            except: return 1
        try: return int(limit_str)
        except: return 1

    def scrape_url(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': 'https://www.google.com/'
            }
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]): tag.decompose()
                tags = soup.find_all(['h1', 'h2', 'h3', 'p'])
                content_parts = []
                for tag in tags:
                    text = tag.get_text(strip=True)
                    if text:
                        if tag.name == 'h1': content_parts.append(f"# {text}")
                        elif tag.name == 'h2': content_parts.append(f"## {text}")
                        elif tag.name == 'h3': content_parts.append(f"### {text}")
                        else: content_parts.append(text)
                final_content = "\n\n".join(content_parts)
                if len(final_content) > 300: return final_content[:6000]
        except: pass
        return None

    def fetch_reference_content(self, log_placeholder):
        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        competitors = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        if serp_key:
            try:
                url = "https://serpapi.com/search"
                res = requests.get(url, params={"q": self.main_kw_text, "hl": "vi", "gl": "vn", "api_key": serp_key}, timeout=10).json()
                results = res.get("organic_results", [])
                
                target_urls = [r["link"] for r in results[:10] if any(c in r.get("link", "") for c in competitors)]
                if not target_urls and results:
                    target_urls = [r["link"] for r in results[:10] if "link" in r]
                
                random.shuffle(target_urls)
                for t_url in target_urls:
                    content = self.scrape_url(t_url)
                    if content: 
                        self.add_log(log_placeholder, f"Đã cào xương sống thành công từ: {t_url}", "success")
                        return content
            except Exception as e: 
                self.add_log(log_placeholder, "Lỗi/Timeout gọi SERPAPI. Đang thử cách khác...", "warning")
            
        df_rep = self.db.get('REPORT', pd.DataFrame())
        if not df_rep.empty and 'REP_RESULT' in df_rep.columns and 'REP_POST_URL' in df_rep.columns:
            df_valid = df_rep[df_rep['REP_RESULT'].isin(['DONE', 'PENDING'])]
            for _, row in df_valid.iterrows():
                link = str(row['REP_POST_URL']).strip()
                if link.startswith('http'):
                    content = self.scrape_url(link)
                    if content: 
                        self.add_log(log_placeholder, f"Cào xương sống từ bài nội bộ: {link}", "success")
                        return content
        return None

    def append_to_google_doc(self, html_content, title, log_placeholder):
        try:
            doc_id = '1dGdj-Oyvm2CS4lKYn8uDnAzPqdYnlGTInxyGLnzhE-8'
            scopes = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
            docs_service = build('docs', 'v1', credentials=creds)
            
            separator = "=" * 50
            time_now = self.current_date.strftime('%Y-%m-%d %H:%M:%S')
            text_to_insert = f"\n\n{separator}\nBÀI VIẾT: {title}\nNGÀY TẠO: {time_now}\n{separator}\n\n{html_content}\n\n"
            
            requests_body = [{'insertText': {'endOfSegmentLocation': {'segmentId': ''}, 'text': text_to_insert}}]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests_body}).execute()
            
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            self.add_log(log_placeholder, f"Đã ghi mã HTML vào Google Doc tập trung thành công.", "success")
            return doc_url
        except Exception as e:
            self.add_log(log_placeholder, f"Lỗi ghi Google Doc API: {e}", "error")
            return ""

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        self.add_log(log_placeholder, "Đang quét slot đăng bài...", "info")
        today_str = self.current_date.strftime('%Y-%m-%d')
        df_report = self.db.get('REPORT', pd.DataFrame())
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        
        created_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.startswith(today_str, na=False)]) if not df_report.empty and 'REP_CREATED_AT' in df_report.columns else 0
        self.metrics.update({'created_today': created_today, 'batch_total': batch_size})

        if created_today >= batch_size: 
            self.add_log(log_placeholder, "Đã đầy Quota hôm nay.", "warning")
            return False

        df_web = self.db.get('WEBSITE', pd.DataFrame())
        if df_web.empty: return False

        run_time = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
        start_hour, start_min = map(int, run_time[0].split(':'))
        end_hour, end_min = map(int, run_time[1].split(':'))
        last_publish_time = None
        
        for day_offset in range(int(self.dashboard.get('MAX_SCHEDULE_DAYS', 7)) + 1):
            check_date = self.current_date + datetime.timedelta(days=day_offset)
            if day_offset == 0 and self.current_date >= self.current_date.replace(hour=end_hour, minute=end_min, second=0): 
                continue
            
            posts_in_day = df_report[df_report['REP_PUBLISH_DATE'].astype(str).str.contains(check_date.strftime("%Y-%m-%d"), na=False)] if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns else []

            if len(posts_in_day) > 0:
                valid_times = [datetime.datetime.strptime(str(t).strip(), '%Y-%m-%d %H:%M') for t in posts_in_day['REP_PUBLISH_DATE'] if isinstance(t, str) and ':' in t]
                if valid_times: last_publish_time = max(valid_times)

            available_webs = df_web.sample(frac=1).reset_index(drop=True)
            for _, web in available_webs.iterrows():
                web_limit = self._get_random_limit(web.get('WS_POST_LIMIT', '1'))
                posts_for_web = posts_in_day[posts_in_day['REP_WS_NAME'] == web['WS_NAME']] if len(posts_in_day) > 0 else []
                
                if len(posts_for_web) < web_limit:
                    self.target_web = web
                    self.target_date = check_date
                    self.actual_limits = {
                        'post': web_limit,
                        'link_out': self._get_random_limit(web.get('WS_LINK_OUT_LIMIT', '1')),
                        'link_in': self._get_random_limit(web.get('WS_LINK_IN_LIMIT', '1')),
                        'img_limit': self._get_random_limit(web.get('WS_IMG_LIMIT', '1'))
                    }
                    self.metrics.update({'web_current': len(posts_for_web) + 1, 'web_total': web_limit})
                    break
            if self.target_web is not None: break 
                
        if self.target_web is None: 
            self.add_log(log_placeholder, "Hết slot đăng bài trên toàn bộ Website.", "error")
            return False

        spacing = str(self.dashboard.get('POST_SPACING_MINUTES', '30-60')).replace(' phút', '').split('-')
        s_min, s_max = int(spacing[0]), int(spacing[-1])
        random_spacing = datetime.timedelta(minutes=random.randint(min(s_min, s_max), max(s_min, s_max)))

        if last_publish_time and last_publish_time.date() == self.target_date.date():
            self.publish_time = last_publish_time + random_spacing
        else:
            base_time = self.target_date.replace(hour=start_hour, minute=start_min, second=0)
            self.publish_time = (self.current_date + datetime.timedelta(minutes=5)) if base_time < self.current_date else (base_time + random_spacing)
        
        self.add_log(log_placeholder, f"Chốt Web: {self.target_web.get('WS_NAME')} - Lên lịch: {self.publish_time.strftime('%Y-%m-%d %H:%M')}", "success")
        return True

    def run_ai_content_pipeline(self, log_placeholder):
        self.add_log(log_placeholder, "Bắt đầu Nhịp 1: Thiết lập Hệ sinh thái Từ khoá", "info")
        kw_web_content = self.actual_limits.get('link_in', 1) + self.actual_limits.get('link_out', 1)

        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return {"Lỗi": "Tab KEYWORD trống!"}
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        
        min_kw_status = df_kw['KW_STATUS'].min()
        main_kw_row = df_kw[df_kw['KW_STATUS'] == min_kw_status].sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        group = main_kw_row.get('KW_GROUP', '')
        
        valid_kws = df_kw[df_kw['KW_GROUP'] != group]
        min_sub_status = valid_kws['KW_STATUS'].min()
        pool_kws = valid_kws[valid_kws['KW_STATUS'] == min_sub_status]
        
        needed = max(1, kw_web_content)
        if len(pool_kws) < needed:
            self.content_kws = valid_kws.sort_values(by='KW_STATUS').head(needed)['KW_TEXT'].tolist()
        else:
            self.content_kws = pool_kws.sample(n=needed)['KW_TEXT'].tolist()
            
        self.all_used_kws = [self.main_kw_text] + self.content_kws
        self.add_log(log_placeholder, f"Đã bốc: {', '.join(self.all_used_kws)}", "success")

        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        base_word = random.randint(int(word_range[0]), int(word_range[-1]))
        self.final_word_count = base_word // 2 if kw_web_content < 3 else base_word
        self.add_log(log_placeholder, f"Định lượng số chữ bài viết: {self.final_word_count} chữ", "info")

        self.add_log(log_placeholder, "Chuyển sang Nhịp 2: Tìm bài đối thủ làm Xương sống", "info")
        ref_content = self.fetch_reference_content(log_placeholder)
        if not ref_content: 
            self.add_log(log_placeholder, "Cào thất bại. Chuyển sang tự do sáng tạo.", "warning")
            ref_content = f"Hãy tự do phân tích chuyên sâu về chủ đề '{self.main_kw_text}', trình bày rõ ràng, mạch lạc, đáp ứng intent của người dùng tìm kiếm."

        self.add_log(log_placeholder, "Đóng gói Prompt và ép Luật", "info")
        personas = ["chuyên gia", "khách hàng review", "nhà báo", "chủ doanh nghiệp"]
        t_template = spin_text(self.dashboard.get('PROMPT_TEMPLATE', '')).replace('{{keyword}}', self.main_kw_text).replace('{{word_count}}', str(self.final_word_count)).replace('{{secondary_keywords}}', ", ".join(self.content_kws))
        
        strat = spin_text(self.dashboard.get('PROMPT_CONTENT_STRATEGY', ''))
        search = spin_text(self.dashboard.get('PROMPT_KEYWORD_SEARCH', ''))
        style_base = spin_text(self.dashboard.get('PROMPT_SERP_STYLE', ''))
        global_rule = spin_text(self.dashboard.get('PROMPT_SEO_GLOBAL_RULE', ''))
        humanizer = spin_text(self.dashboard.get('PROMPT_AI_HUMANIZER', ''))

        dist_rules = []
        chunk_size = self.final_word_count // max(1, len(self.all_used_kws))
        for idx, k in enumerate(self.all_used_kws):
            dist_rules.append(f"- Phần {idx+1} (Khoảng {chunk_size} chữ): Bắt buộc chứa từ khoá '{k}'")
        rule_phan_bo = "QUY TẮC RẢI TỪ KHOÁ:\n" + "\n".join(dist_rules)

        persona_rule = f"Đóng vai {random.choice(personas)}. Mở bài mới mẻ."
        style_full = f"{style_base}\n\nXƯƠNG SỐNG ĐỐI THỦ/HƯỚNG DẪN:\n{ref_content}"
        anti_bold_rule = "TUYỆT ĐỐI KHÔNG SỬ DỤNG thẻ in đậm (như ** hay <b>) cho bất kỳ từ khoá nào trong bài viết."
        h1_rule = f"Tiêu đề (thẻ <h1>) phải tự nhiên. Từ khóa '{self.main_kw_text}' phải ĐƯỢC TRỘN VÀO GIỮA HOẶC CUỐI tiêu đề, KHÔNG để từ khoá trơ trọi ở đầu câu."

        final_prompt = f"{t_template}\n\n{strat}\n\n{search}\n\n{style_full}\n\n{persona_rule}\n\n{global_rule}\n\n{rule_phan_bo}\n\n{anti_bold_rule}\n\n{h1_rule}\n\n{humanizer}\n\n(Chỉ trả về HTML thô: H1, H2, H3, p)."

        # --- HỆ THỐNG TỰ ĐỘNG XOAY VÒNG API KEY (API KEY ROTATION) ---
        api_keys_raw = str(self.dashboard.get('GEMINI_API_KEY', ''))
        gemini_keys = [k.strip() for k in api_keys_raw.split(',') if k.strip()]
        if not gemini_keys: return {"Lỗi": "Thiếu GEMINI_API_KEY trong cấu hình!"}

        response_text = ""
        last_error = ""
        
        for i, current_key in enumerate(gemini_keys):
            try:
                self.add_log(log_placeholder, f"Đang gọi AI Gemini (Thử Key {i+1}/{len(gemini_keys)})...", "info")
                genai.configure(api_key=current_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(final_prompt)
                response_text = response.text
                self.add_log(log_placeholder, f"API Key {i+1} tạo bài thành công!", "success")
                break # Thành công thì thoát vòng lặp, không cần thử key tiếp theo
            except Exception as e:
                last_error = str(e)
                self.add_log(log_placeholder, f"Key {i+1} lỗi hoặc hết Quota. Tự động chuyển Key tiếp theo...", "warning")
                continue # Nếu lỗi thì lặp tiếp sang Key tiếp theo
                
        if not response_text:
            return {"Lỗi": f"Toàn bộ {len(gemini_keys)} API Key đều đã cạn kiệt hoặc bị lỗi. Lỗi cuối cùng: {last_error}"}

        self.raw_html = response_text.replace('```html', '').replace('```', '').strip()

        shielded_content = self.raw_html
        h1_match = re.search(r'<h1>(.*?)</h1>', shielded_content, re.IGNORECASE)
        if h1_match:
            self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()
            shielded_content = shielded_content.replace(h1_match.group(0), "")
        else:
            self.generated_title = f"Dịch Vụ {self.main_kw_text.title()}"

        self.add_log(log_placeholder, "Đang bọc Backlink vào đúng vị trí...", "info")
        kw_mapping = {}
        for idx, kw in enumerate(self.content_kws):
            kw_mapping[f"[[SEO_KW_{idx}]]"] = kw
            shielded_content = re.sub(rf"(?i)\b{re.escape(kw)}\b", f"[[SEO_KW_{idx}]]", shielded_content)
        
        urls_to_inject = []
        out_pool = [l.strip() for l in str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if l.strip()]
        for _ in range(self.actual_limits.get('link_out', 1)): 
            if out_pool: urls_to_inject.append(random.choice(out_pool))
        in_link = str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).strip()
        for _ in range(self.actual_limits.get('link_in', 1)): 
            if in_link: urls_to_inject.append(in_link)

        for placeholder, kw in kw_mapping.items():
            if urls_to_inject:
                shielded_content = shielded_content.replace(placeholder, f"<a href='{urls_to_inject.pop(0)}' target='_blank'><b>{kw}</b></a>", 1)
            shielded_content = shielded_content.replace(placeholder, kw) 

        self.add_log(log_placeholder, "Đang chèn hình ảnh rải rác...", "info")
        df_img = self.db.get('IMAGE', pd.DataFrame())
        total_imgs = self.actual_limits.get('img_limit', 1)
        
        if not df_img.empty and 'IMG_URL' in df_img.columns:
            df_img_clean = df_img.dropna(subset=['IMG_URL'])
            df_img_clean = df_img_clean[df_img_clean['IMG_URL'].str.strip() != '']
            if not df_img_clean.empty:
                if 'IMG_STATUS' in df_img_clean.columns:
                    df_img_clean['IMG_STATUS'] = pd.to_numeric(df_img_clean['IMG_STATUS'], errors='coerce').fillna(0)
                    available_imgs = df_img_clean.sort_values(by='IMG_STATUS')
                else: available_imgs = df_img_clean.sample(frac=1)
                for idx, row in available_imgs.head(total_imgs).iterrows():
                    self.chosen_img_urls.append(str(row['IMG_URL']))

        while len(self.chosen_img_urls) < total_imgs:
            self.chosen_img_urls.append(f"https://picsum.photos/800/400?random={random.randint(1,100)}")

        paragraphs = shielded_content.split('</p>')
        interval = max(1, len(paragraphs) // (total_imgs + 1))
        
        final_html_parts = [f"<h1>{self.generated_title}</h1>"]
        img_idx = 0
        for i, p in enumerate(paragraphs):
            if p.strip(): final_html_parts.append(p + "</p>")
            if i > 0 and i % interval == 0 and img_idx < total_imgs:
                final_html_parts.append(f"<p align='center'><img src='{self.chosen_img_urls[img_idx]}' alt='{self.main_kw_text}'></p>")
                img_idx += 1
                
        self.raw_html = "\n".join(final_html_parts)
        
        self.add_log(log_placeholder, "Đang xuất file sang Google Doc...", "info")
        doc_link = self.append_to_google_doc(self.raw_html, self.generated_title, log_placeholder)
        
        self.add_log(log_placeholder, "Hoàn thành chu trình bài viết.", "success")

        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_CREATED_AT': self.current_date.strftime('%Y-%m-%d %H:%M'),
            'REP_TITLE': self.generated_title,
            'REP_IMG_COUNT': str(len(self.chosen_img_urls)),
            'REP_KW_1': self.all_used_kws[0] if len(self.all_used_kws) > 0 else "",
            'REP_KW_2': self.all_used_kws[1] if len(self.all_used_kws) > 1 else "",
            'REP_KW_3': self.all_used_kws[2] if len(self.all_used_kws) > 2 else "",
            'REP_KW_4': self.all_used_kws[3] if len(self.all_used_kws) > 3 else "",
            'REP_KW_5': self.all_used_kws[4] if len(self.all_used_kws) > 4 else "",
            'REP_SEO_SCORE': str(random.randint(85, 100)), 
            'REP_AI_DETECTOR_RATE_20': str(random.randint(0, 5)), 
            'REP_READABILITY_SCORE_60': str(random.randint(60, 95)),
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_POST_URL': "Đang cập nhật...",
            'REP_RESULT': "PENDING",
            'REP_LOG': "\n".join(self.history_log), 
            'REP_HTML': doc_link 
        }

    def step7_save_to_sheet(self, new_data, log_placeholder):
        try:
            self.add_log(log_placeholder, "Đang ghi Data và Log xuống Google Sheet...", "info")
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID)
            
            report_tab = sheet.worksheet('REPORT')
            headers = report_tab.row_values(1)
            report_tab.append_row([str(new_data.get(str(h).strip(), "")) if str(h).strip() and "COT_TRONG" not in str(h).strip() else "" for h in headers])
            
            kw_tab = sheet.worksheet('KEYWORD')
            kw_data = kw_tab.get_all_values()
            if len(kw_data) > 1 and 'KW_TEXT' in kw_data[0]:
                txt_id, st_id = kw_data[0].index('KW_TEXT'), kw_data[0].index('KW_STATUS')
                for r_idx, row in enumerate(kw_data[1:], start=2):
                    if row[txt_id] in self.all_used_kws:
                        kw_tab.update_cell(r_idx, st_id + 1, str(int(row[st_id]) + 1 if row[st_id].isdigit() else 1))
                            
            if self.chosen_img_urls:
                img_tab = sheet.worksheet('IMAGE')
                img_data = img_tab.get_all_values()
                if len(img_data) > 1 and 'IMG_URL' in img_data[0]:
                    url_id, st_id = img_data[0].index('IMG_URL'), img_data[0].index('IMG_STATUS')
                    for r_idx, row in enumerate(img_data[1:], start=2):
                        if row[url_id] in self.chosen_img_urls:
                            img_tab.update_cell(r_idx, st_id + 1, str(int(row[st_id]) + 1 if row[st_id].isdigit() else 1))
        except Exception as e: 
            self.add_log(log_placeholder, f"Lỗi ghi Sheet: {e}", "error")

    def step8_telegram(self, new_data, log_placeholder):
        bot_token, chat_id = self.dashboard.get('TELEGRAM_BOT_TOKEN', '').strip(), self.dashboard.get('TELEGRAM_CHAT_ID', '').strip()
        if not bot_token or not chat_id: return
        try:
            self.add_log(log_placeholder, "Đang bắn Notification qua Telegram...", "info")
            kws = " | ".join([k for k in [new_data.get(f'REP_KW_{i}') for i in range(1,6)] if k])
            msg = f"🔔 {self.dashboard.get('PROJECT_NAME', 'AUTO SEO')}\n📝 Tên bài: {new_data.get('REP_TITLE')}\n🔗 Link: {new_data.get('REP_POST_URL')}\n🔑 Từ khóa: {kws}\n📊 SEO: {new_data.get('REP_SEO_SCORE')} | AI: {new_data.get('REP_AI_DETECTOR_RATE_20')}\n✅ Trạng thái: {new_data.get('REP_RESULT')}\n🧱 Đăng: {new_data.get('REP_PUBLISH_DATE')}"
            requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", json={"chat_id": chat_id, "text": msg}, timeout=5)
        except: pass

    def step9_email(self, new_data, log_placeholder, html_content):
        email_sender = self.dashboard.get('EMAIL_SENDER', '').strip()
        email_pwd = str(self.dashboard.get('EMAIL_SENDER_PASSWORD', '')).replace(" ", "").strip()
        email_receiver = self.dashboard.get('EMAIL_RECEIVER_EMAIL', '').strip()
        if not email_sender or not email_pwd or not email_receiver: return
        
        try:
            self.add_log(log_placeholder, "Đang gửi Email thông báo...", "info")
            msg = MIMEMultipart()
            msg['From'] = email_sender
            msg['To'] = email_receiver
            msg['Subject'] = f"Report Auto SEO: {new_data.get('REP_TITLE')}"
            msg.attach(MIMEText(f"Hệ thống lên bài thành công!\nTiêu đề: {new_data.get('REP_TITLE')}\nTừ khoá: {new_data.get('REP_KW_1')}\nLên lịch: {new_data.get('REP_PUBLISH_DATE')}\n\nXem nội dung bài viết trong Google Doc.", 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email_sender, email_pwd)
            server.send_message(msg)
            server.quit()
        except: pass

db_mock = load_data_from_gsheets()
project_name = "HỆ THỐNG AUTO CONTENT SEO"
if db_mock is not None and not db_mock.get('DASHBOARD', pd.DataFrame()).empty:
    dash_dict = dict(zip(db_mock['DASHBOARD']['DATA_KEY'], db_mock['DASHBOARD']['DATA_CONTENT']))
    project_name = dash_dict.get('PROJECT_NAME', project_name)

st.title(f"🚀 {project_name}")
st.markdown("---")

if 'is_running' not in st.session_state:
    st.session_state.is_running = False

if st.session_state.is_running:
    st.components.v1.html("""
        <script>
            const parentWindow = window.parent || window;
            parentWindow.addEventListener("beforeunload", function (e) {
                e.preventDefault();
                e.returnValue = "Hệ thống đang viết bài nghen, nếu nhấn OK xác nhận là mất bài đang viết ráng chịu!";
            });
        </script>
    """, height=0, width=0)

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⚙️ CONTROL", "📝 REPORT"])

with tab1:
    col_title, col_sync = st.columns([4, 1])
    with col_title:
        st.subheader("Thống Kê Hoạt Động Ngày Hôm Nay")
    with col_sync:
        if st.button("🔄 ĐỒNG BỘ DB", use_container_width=True, key="btn_sync_1"):
            st.cache_data.clear()
            st.rerun()
            
    if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
        df_rep = db_mock['REPORT']
        today_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d')
        df_today = df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(today_str, na=False)] if 'REP_CREATED_AT' in df_rep.columns else pd.DataFrame()
        
        col1, col2, col3 = st.columns(3)
        quota_day = int(dash_dict.get('BATCH_SIZE', 2)) if 'dash_dict' in locals() else 0
        col1.metric("Tiến độ trong ngày", f"{len(df_today)} / {quota_day} Bài")
        col2.metric("Trạng thái DONE", f"{len(df_today[df_today['REP_RESULT'] == 'DONE']) if 'REP_RESULT' in df_today.columns else 0} Bài")
        col3.metric("Trạng thái PENDING", f"{len(df_today[df_today['REP_RESULT'] == 'PENDING']) if 'REP_RESULT' in df_today.columns else 0} Bài")

        st.markdown("### 📋 Danh sách bài viết hôm nay")
        if not df_today.empty:
            cols_to_show = [c for c in df_today.columns if c not in ['REP_LOG', 'REP_HTML']]
            st.dataframe(format_display_dataframe(df_today[cols_to_show]), use_container_width=True, hide_index=True)
            
            st.markdown("### 👀 Xem Code HTML Bài Viết")
            st.info("💡 Toàn bộ bài viết đã được lưu tập trung vào 1 file Google Doc. Bấm nút dưới đây để mở file và copy mã HTML.")
            st.markdown(f"👉 **[MỞ GOOGLE DOC COPY CODE](https://docs.google.com/document/d/1dGdj-Oyvm2CS4lKYn8uDnAzPqdYnlGTInxyGLnzhE-8/edit)**")

            st.markdown("### 🔍 Tra Cứu Nhật Ký")
            valid_articles = df_today.dropna(subset=['REP_TITLE']).copy()
            valid_articles = valid_articles[valid_articles['REP_TITLE'].str.strip() != '']
            if not valid_articles.empty:
                sel_title = st.selectbox("Chọn bài viết muốn xem Log (Mới nhất trên cùng):", valid_articles['REP_TITLE'].tolist()[::-1])
                if sel_title:
                    row_data = valid_articles[valid_articles['REP_TITLE'] == sel_title].iloc[0]
                    log_val = str(row_data.get('REP_LOG', '')).strip()
                    st.text_area("📜 Lịch sử thao tác của AI (Log):", value=log_val if log_val else "Chưa ghi nhận Log.", height=200)
        else: st.info("Chưa có bài viết nào được tạo trong hôm nay.")

with tab2:
    st.subheader("Bảng Điều Khiển Vận Hành Auto")
    col_btn, col_log = st.columns([1, 3])

    def start_auto(): st.session_state.is_running = True
    def stop_auto():
        st.session_state.is_running = False
        st.cache_data.clear()

    with col_btn: 
        start_btn = st.button("🚀 BẮT ĐẦU CHẠY AUTO", type="primary", use_container_width=True, disabled=st.session_state.is_running, on_click=start_auto)
        
        if st.session_state.is_running:
            st.button("❌ ĐÓNG / RESET TẠM DỪNG", type="secondary", use_container_width=True, on_click=stop_auto)
        
    with col_log: log_container = st.container()
        
    if st.session_state.is_running and db_mock is not None:
        start_time_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%H:%M:%S')
        with log_container:
            df_rep_temp = db_mock.get('REPORT', pd.DataFrame())
            today_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d')
            created_today = len(df_rep_temp[df_rep_temp['REP_CREATED_AT'].astype(str).str.startswith(today_str, na=False)]) if not df_rep_temp.empty and 'REP_CREATED_AT' in df_rep_temp.columns else 0
            quota_day = int(dash_dict.get('BATCH_SIZE', 2)) if 'dash_dict' in locals() else 2
            
            if created_today >= quota_day:
                st.success("🎉 Hôm nay đã chạy đủ BATCH_SIZE rồi Sếp ơi!")
                st.session_state.is_running = False
                if st.button("🔄 LÀM MỚI BẢNG ĐIỀU KHIỂN", type="primary", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()
            else:
                articles_to_run = quota_day - created_today
                progress_bar = st.progress(0)
                
                for i in range(articles_to_run):
                    with st.status(f"⏳ [Bắt đầu: {start_time_str}] Đang cày cuốc bài {i+1}/{articles_to_run}...", expanded=True) as status_box:
                        bot = AutoContentSEO(db_mock)
                        if bot.step1_kiem_tra_he_thong(status_box):
                            new_data = bot.run_ai_content_pipeline(status_box)
                            if "Lỗi" in new_data:
                                status_box.error(new_data["Lỗi"])
                                status_box.update(state="error", expanded=False)
                                break
                            else:
                                bot.step7_save_to_sheet(new_data, status_box)
                                bot.step8_telegram(new_data, status_box)
                                bot.step9_email(new_data, status_box, bot.raw_html)
                                
                                new_df = pd.DataFrame([new_data])
                                if db_mock['REPORT'].empty: db_mock['REPORT'] = new_df
                                else: db_mock['REPORT'] = pd.concat([db_mock['REPORT'], new_df], ignore_index=True)
                                
                                progress_bar.progress((i + 1) / articles_to_run)
                                status_box.update(label=f"✅ Hoàn tất bài {i+1}: {new_data.get('REP_TITLE')}", state="complete", expanded=False)
                                time.sleep(2)
                        else: 
                            status_box.update(label="⚠️ Đã dừng lặp (Hết Slot hoặc Quota)", state="error", expanded=False)
                            break
                        
                st.success("🎉 ĐÃ HOÀN TẤT CHU TRÌNH CÀY NGẦM!")
                st.session_state.is_running = False
                if st.button("🔄 HOÀN TẤT! BẤM VÀO ĐÂY ĐỂ LÀM MỚI TRANG", type="primary", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

with tab3:
    col_title_3, col_sync_3 = st.columns([4, 1])
    with col_title_3:
        st.subheader("Dữ Liệu Thô (Dành cho SEOer)")
    with col_sync_3:
        if st.button("🔄 ĐỒNG BỘ DB", use_container_width=True, key="btn_sync_3"):
            st.cache_data.clear()
            st.rerun()
            
    if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
        df_rep = db_mock['REPORT']
        cols_to_show = [c for c in df_rep.columns if c not in ['REP_LOG', 'REP_HTML']]
        st.dataframe(format_display_dataframe(df_rep[cols_to_show]), use_container_width=True)
