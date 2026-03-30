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
from googleapiclient.http import MediaIoBaseUpload

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
        'REP_POST_URL': 'Đường dẫn',
        'REP_HTML': 'Link File (Drive)'
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
            headers = {'User-Agent': 'Mozilla/5.0'}
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

    def upload_to_drive(self, html_content, title, log_placeholder):
        try:
            # TỰ ĐỘNG BỐC ID TỪ SHEET DASHBOARD
            folder_id = self.dashboard.get('EMAIL_FOLDER_DRIVE_ID', '').strip()
            if not folder_id:
                log_placeholder.error("❌ Thiếu EMAIL_FOLDER_DRIVE_ID trong tab DASHBOARD.")
                return ""

            scopes = ['https://www.googleapis.com/auth/drive']
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
            drive_service = build('drive', 'v3', credentials=creds)
            
            file_metadata = {'name': f"{title}.html", 'parents': [folder_id]}
            media = MediaIoBaseUpload(io.BytesIO(html_content.encode('utf-8')), mimetype='text/html', resumable=True)
            file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            return file.get('webViewLink')
        except Exception as e:
            log_placeholder.error(f"❌ Lỗi Drive API: {e}")
            return ""

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        log_placeholder.write("🔍 Đang quét slot đăng bài...")
        today_str = self.current_date.strftime('%Y-%m-%d')
        df_report = self.db.get('REPORT', pd.DataFrame())
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        
        created_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.startswith(today_str, na=False)]) if not df_report.empty and 'REP_CREATED_AT' in df_report.columns else 0
        self.metrics.update({'created_today': created_today, 'batch_total': batch_size})

        if created_today >= batch_size: return False

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
                    break
            if self.target_web is not None: break 
        
        if self.target_web:
            log_placeholder.write(f"📅 Chốt: **{self.target_web.get('WS_NAME')}**")
            return True
        return False

    def run_ai_content_pipeline(self, log_placeholder):
        log_placeholder.write("🔑 Đang trích xuất từ khoá theo logic Nhịp 1...")
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return {"Lỗi": "Tab KEYWORD trống!"}
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        
        kw_web_content = self.actual_limits.get('post', 1) + self.actual_limits.get('link_out', 1)
        main_kw_row = df_kw[df_kw['KW_STATUS'] == df_kw['KW_STATUS'].min()].sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        kw_topic = str(main_kw_row.get('KW_CONTENT', ''))
        kw_group = str(main_kw_row.get('KW_GROUP', ''))
        
        valid_kws = df_kw[df_kw['KW_GROUP'].astype(str) != kw_group]
        if kw_topic:
            same_topic = valid_kws[valid_kws['KW_CONTENT'].astype(str) == kw_topic]
            if not same_topic.empty: valid_kws = same_topic
                
        valid_kws = valid_kws.sort_values(by='KW_STATUS')
        needed = min(4, kw_web_content)
        self.content_kws = valid_kws.head(needed)['KW_TEXT'].tolist()
        self.all_used_kws = [self.main_kw_text] + self.content_kws

        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        base_word = random.randint(int(word_range[0]), int(word_range[-1]))
        self.final_word_count = base_word // 2 if kw_web_content < 3 else base_word

        log_placeholder.write("🧠 Gọi AI Gemini viết bài...")
        final_prompt = f"Viết bài SEO {self.final_word_count} chữ về '{self.main_kw_text}'. Từ khoá: {', '.join(self.all_used_kws)}. Trả về HTML thô."
        
        gemini_key = self.dashboard.get('GEMINI_API_KEY', '')
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(final_prompt)
        self.raw_html = response.text.replace('```html', '').replace('```', '').strip()

        log_placeholder.write("☁️ Đang tải lên Drive...")
        drive_link = self.upload_to_drive(self.raw_html, self.main_kw_text, log_placeholder)

        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_CREATED_AT': self.current_date.strftime('%Y-%m-%d %H:%M'),
            'REP_TITLE': self.main_kw_text.title(),
            'REP_KW_1': self.all_used_kws[0],
            'REP_KW_2': self.all_used_kws[1] if len(self.all_used_kws) > 1 else "",
            'REP_PUBLISH_DATE': (self.current_date + datetime.timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'),
            'REP_RESULT': "PENDING",
            'REP_HTML': drive_link if drive_link else "Lỗi Upload Drive"
        }

    def step7_save_to_sheet(self, new_data, log_placeholder):
        try:
            scopes = ['https://www.googleapis.com/auth/spreadsheets']
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID)
            report_tab = sheet.worksheet('REPORT')
            headers = report_tab.row_values(1)
            report_tab.append_row([str(new_data.get(str(h).strip(), "")) for h in headers])
            log_placeholder.write("✅ Ghi Sheet xong.")
        except Exception as e: log_placeholder.error(f"Lỗi Sheet: {e}")

# ==========================================
# GIAO DIỆN WEB
# ==========================================
db_mock = load_data_from_gsheets()
dash_dict = {}
if db_mock is not None:
    dash_dict = dict(zip(db_mock['DASHBOARD']['DATA_KEY'], db_mock['DASHBOARD']['DATA_CONTENT']))

st.title(f"🚀 {dash_dict.get('PROJECT_NAME', 'SEO SYSTEM')}")

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "⚙️ CONTROL", "📝 REPORT"])

with tab2:
    if st.button("🚀 BẮT ĐẦU CHẠY AUTO"):
        with st.status("Đang vận hành...") as status:
            bot = AutoContentSEO(db_mock)
            if bot.step1_kiem_tra_he_thong(status):
                new_data = bot.run_ai_content_pipeline(status)
                bot.step7_save_to_sheet(new_data, status)
                status.update(label="🎉 Hoàn thành!", state="complete")
                st.balloons()
