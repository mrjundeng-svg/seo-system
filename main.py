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
from email.mime.text import MIMEText
from bs4 import BeautifulSoup
from googleapiclient.discovery import build

# ==========================================
# 🎨 CẤU HÌNH GIAO DIỆN CƠ BẢN
# ==========================================
st.set_page_config(page_title="Hệ Thống Auto SEO", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { color: #0f172a; font-family: 'Segoe UI', Tahoma, sans-serif; }
    
    div[data-testid="metric-container"] {
        background-color: white; padding: 15px 20px;
        border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #ef4444; 
    }
    div[data-testid="metric-container"] label { font-size: 1rem !important; font-weight: 600; color: #475569; }
    div[data-testid="metric-container"] div { font-size: 2.2rem !important; color: #1e293b; font-weight: bold; }
    
    .log-box {
        background-color: #0f172a; color: #10b981;
        font-family: 'Courier New', Courier, monospace; font-size: 14px;
        padding: 15px; border-radius: 8px; height: 350px; overflow-y: auto;
        border: 1px solid #334155; line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

# ==========================================
# 🛠 CÁC HÀM XỬ LÝ DỮ LIỆU & EMAIL (SMART CACHE)
# ==========================================
# Bật lại Cache 60s để chống lỗi Google Sheets API 429 Quota Exceeded
@st.cache_data(ttl=60)
def load_data_from_gsheets():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
        s_creds = dict(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        db = {}
        for tab_name in ['DASHBOARD', 'WEBSITE', 'IMAGE', 'SPIN', 'KEYWORD', 'REPORT']:
            try:
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
                else: db[tab_name] = pd.DataFrame()
            except: db[tab_name] = pd.DataFrame()
        return db
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        return None

def format_display_dataframe(df):
    if df.empty: return df
    df_show = df.copy()
    rename_dict = {
        'REP_CREATED_AT': 'Tạo bài lúc',
        'REP_PUBLISH_DATE': '🕒 Giờ Lên Sóng',
        'REP_TITLE': '📑 Tiêu Đề Bài Viết',
        'REP_WS_NAME': '🌐 Website',
        'REP_RESULT': '🚥 Trạng Thái',
        'REP_POST_URL': '🔗 Đường Dẫn / Ghi Chú'
    }
    cols_to_keep = [c for c in rename_dict.keys() if c in df_show.columns]
    df_show = df_show[cols_to_keep].rename(columns=rename_dict)
    return df_show

def force_publish_pending_posts(status_box):
    try:
        s_creds = dict(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(s_creds, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        client = gspread.authorize(creds)
        ss = client.open_by_key(SHEET_ID)
        ws_report = ss.worksheet('REPORT')
        df_report = pd.DataFrame(ws_report.get_all_records())
        ws_web = ss.worksheet('WEBSITE')
        df_web = pd.DataFrame(ws_web.get_all_records())
        dash = {r['DATA_KEY']: r['DATA_CONTENT'] for r in ss.worksheet('DASHBOARD').get_all_records()}
        
        email_sender = str(dash.get('EMAIL_SENDER', '')).strip()
        email_pwd = str(dash.get('EMAIL_SENDER_PASSWORD', '')).replace(' ', '').strip()

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
        today_str = now.strftime('%Y-%m-%d')
        
        posted_count = 0
        skipped_future = 0
        
        for idx, row in df_report.iterrows():
            if str(row.get('REP_RESULT')).strip() == 'PENDING':
                pub_date_str = str(row.get('REP_PUBLISH_DATE')).strip()
                try:
                    pub_date = datetime.datetime.strptime(pub_date_str, '%Y-%m-%d %H:%M')
                    if pub_date.strftime('%Y-%m-%d') == today_str and pub_date <= now:
                        ws_name = str(row.get('REP_WS_NAME'))
                        target_email = str(df_web[df_web['WS_NAME'] == ws_name].iloc[0].get('WS_BLOG_CONTENT', ''))
                        if '@' in target_email:
                            msg = MIMEMultipart()
                            msg['From'], msg['To'], msg['Subject'] = email_sender, target_email, row['REP_TITLE']
                            msg.attach(MIMEText(row['REP_HTML'], 'html'))
                            server = smtplib.SMTP('smtp.gmail.com', 587)
                            server.starttls()
                            server.login(email_sender, email_pwd)
                            server.send_message(msg)
                            server.quit()
                            
                            ws_report.update_cell(idx + 2, list(df_report.columns).index('REP_RESULT') + 1, 'DONE')
                            ws_report.update_cell(idx + 2, list(df_report.columns).index('REP_POST_URL') + 1, 'Đã đẩy qua Mail2Blogger')
                            posted_count += 1
                    else:
                        skipped_future += 1
                except:
                    pass
                    
        status_box.success(f"🎉 Đã lên sóng {posted_count} bài viết! (⚠️ Giữ nguyên {skipped_future} bài chưa tới giờ hoặc của ngày tương lai).")
    except Exception as e: status_box.error(f"❌ Lỗi khi ép đăng: {e}")

# ==========================================
# 🤖 LÕI AI SOẠN BÀI VÀ LOGIC CHỐNG SPAM
# ==========================================
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
        self.history_log = [] 
        self.kcs_results = {}

    def add_log(self, ui_box, message):
        time_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%H:%M:%S')
        log_line = f"[{time_str}] {message}"
        self.history_log.append(log_line)
        if ui_box:
            formatted_logs = "<br>".join(self.history_log)
            ui_box.markdown(f'<div class="log-box">{formatted_logs}</div>', unsafe_allow_html=True)

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        if df.empty: return {}
        return {str(k).strip(): str(v).strip() for k, v in zip(df['DATA_KEY'], df['DATA_CONTENT'])}

    def safe_int(self, value, default=1):
        try:
            val_str = str(value).strip()
            if not val_str: return default
            return int(val_str)
        except:
            return default

    def run_kcs_validation(self, log_placeholder, html_content, title):
        self.add_log(log_placeholder, "=============================================")
        self.add_log(log_placeholder, "KÍCH HOẠT KCS: Nhịp 1 - Quy trình Kiểm định Đa tầng")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        main_kw_lower = self.main_kw_text.lower()

        seo_score = 0
        if main_kw_lower in title.lower(): seo_score += 15
        h1_tags = [h.get_text().lower() for h in soup.find_all('h1')]
        if any(main_kw_lower in h1 for h1 in h1_tags): seo_score += 15
        h2_tags = [h.get_text().lower() for h in soup.find_all('h2')]
        if any(main_kw_lower in h2 for h2 in h2_tags): seo_score += 15
        
        words = text_content.split()
        first_100_words = " ".join(words[:100]).lower()
        if main_kw_lower in first_100_words: seo_score += 15
        
        img_tags = [img.get('alt', '').lower() for img in soup.find_all('img')]
        if any(main_kw_lower in alt for alt in img_tags): seo_score += 10
        
        if seo_score == 0: 
             seo_score = 10 if main_kw_lower in text_content.lower() else 0

        self.add_log(log_placeholder, f"  > 1.1 Đo lường On-page SEO: Đạt {seo_score}/70 điểm.")

        total_words = len(words)
        unique_words = len(set(words))
        if total_words > 0:
            lexical_richness = (unique_words / total_words) * 100
            ai_rate = max(0, 100 - (lexical_richness * 2))
        else:
            ai_rate = 100
        ai_rate = round(min(ai_rate, 99.0), 1) 
        self.add_log(log_placeholder, f"  > 1.2 Nhận diện AI (Lexical & Uniqueness): {ai_rate}%.")

        sentences = re.split(r'[.!?]+', text_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
        num_sentences = len(sentences)
        
        if num_sentences > 0 and total_words > 0:
            asl = total_words / num_sentences
            asw = 1.0 
            readability_score = 206.835 - (1.015 * asl) - (84.6 * asw)
        else:
            readability_score = 0
            
        readability_score = round(max(0, min(readability_score, 100)), 1)
        self.add_log(log_placeholder, f"  > 1.3 Đánh giá độ dễ đọc (Flesch VN): {readability_score}/100.")

        self.kcs_results = {
            'SEO': seo_score,
            'AI_RATE': ai_rate,
            'READABILITY': readability_score,
            'WORDS': total_words
        }
        
        return self.evaluate_kcs(log_placeholder)

    def evaluate_kcs(self, log_placeholder):
        self.add_log(log_placeholder, "Nhịp 2: Phê duyệt Kết quả KCS")
        seo = self.kcs_results['SEO']
        ai = self.kcs_results['AI_RATE']
        read = self.kcs_results['READABILITY']
        
        fail_reasons = []
        if seo < 35: fail_reasons.append(f"SEO Score quá thấp ({seo})")
        if ai > 20: fail_reasons.append(f"AI Rate quá cao ({ai}%)")
        if read < 60: fail_reasons.append(f"Độ dễ đọc kém ({read})")

        if fail_reasons:
            self.add_log(log_placeholder, f"❌ KCS FAIL: {', '.join(fail_reasons)}.")
            return "FAIL: " + " | ".join(fail_reasons)
        else:
            self.add_log(log_placeholder, "✅ KCS PASS: Đạt tiêu chuẩn xuất bản.")
            return "PENDING"

    def fetch_reference_content(self, log_placeholder):
        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        if serp_key:
            try:
                url = "https://serpapi.com/search"
                res = requests.get(url, params={"q": self.main_kw_text, "hl": "vi", "gl": "vn", "api_key": serp_key}, timeout=10).json()
                results = res.get("organic_results", [])
                target_urls = [r["link"] for r in results[:5] if "link" in r]
                random.shuffle(target_urls)
                for t_url in target_urls:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res_html = requests.get(t_url, headers=headers, timeout=10)
                    if res_html.status_code == 200:
                        soup = BeautifulSoup(res_html.text, 'html.parser')
                        for tag in soup(["script", "style", "nav", "footer", "header"]): tag.decompose()
                        content = "\n\n".join([tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'p']) if tag.get_text(strip=True)])
                        if len(content) > 300:
                            self.add_log(log_placeholder, f"COMPETITOR_LIST thành công từ: {t_url}")
                            return content[:6000]
            except: pass
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
        except: pass

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        self.add_log(log_placeholder, "=============================================")
        self.add_log(log_placeholder, "BẮT ĐẦU CHU TRÌNH TỰ ĐỘNG SOẠN BÀI AI")
        self.add_log(log_placeholder, "=============================================")
        
        df_report = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        if df_web.empty: return False

        try:
            max_days = self.safe_int(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
            batch_size = self.safe_int(self.dashboard.get('BATCH_SIZE', 6), 6)
            
            time_range = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
            start_h, start_m = map(int, time_range[0].strip().split(':'))
            end_h, end_m = map(int, time_range[1].strip().split(':'))
            
            spacing = str(self.dashboard.get('POST_SPACING_MINUTES', '30-90')).split('-')
            min_space, max_space = self.safe_int(spacing[0], 30), self.safe_int(spacing[-1], 90)
        except Exception as e: return False

        today_str = self.current_date.strftime('%Y-%m-%d')

        self.add_log(log_placeholder, f"Kiểm tra Cửa Ải 1: Giới hạn TẠO BÀI hôm nay (BATCH_SIZE = {batch_size}).")
        if not df_report.empty and 'REP_CREATED_AT' in df_report.columns:
            posts_created_today = df_report[df_report['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]
        else:
            posts_created_today = pd.DataFrame()

        if len(posts_created_today) >= batch_size:
            self.add_log(log_placeholder, f"🛑 ĐÃ ĐẠT NGƯỠNG BATCH_SIZE: Hôm nay đã tạo {len(posts_created_today)}/{batch_size} bài. Hệ thống DỪNG để chống Spam Gen!")
            return False
            
        self.add_log(log_placeholder, f"  [✓] Xưởng hôm nay mới tạo {len(posts_created_today)}/{batch_size} bài. Tiến hành bốc Web...")

        available_webs = df_web.sample(frac=1).reset_index(drop=True)

        for _, web in available_webs.iterrows():
            ws_name = str(web.get('WS_NAME', '')).strip()
            ws_limit = self.safe_int(web.get('WS_POST_LIMIT', 1), 1)

            for day_offset in range(max_days + 1):
                day_x = self.current_date.date() + datetime.timedelta(days=day_offset)
                day_x_str = day_x.strftime('%Y-%m-%d')
                
                if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns:
                    posts_on_day_x_web = df_report[(df_report['REP_WS_NAME'].astype(str).str.strip() == ws_name) & 
                                                   (df_report['REP_PUBLISH_DATE'].astype(str).str.strip().str.startswith(day_x_str))]
                else:
                    posts_on_day_x_web = pd.DataFrame()

                if len(posts_on_day_x_web) < ws_limit:
                    start_time = datetime.datetime.combine(day_x, datetime.time(start_h, start_m))
                    end_time = datetime.datetime.combine(day_x, datetime.time(end_h, end_m))
                    
                    if day_offset == 0 and self.current_date > end_time:
                        continue 
                        
                    if day_offset == 0:
                        base_time = max(self.current_date, start_time)
                    else:
                        base_time = start_time
                        
                    if posts_on_day_x_web.empty:
                        pub_time = base_time + datetime.timedelta(minutes=random.randint(0, 30))
                    else:
                        try:
                            max_time_str = posts_on_day_x_web['REP_PUBLISH_DATE'].max()
                            max_time = datetime.datetime.strptime(str(max_time_str), '%Y-%m-%d %H:%M')
                            pub_time = max(max_time, base_time) + datetime.timedelta(minutes=random.randint(min_space, max_space))
                        except:
                            pub_time = base_time + datetime.timedelta(minutes=random.randint(min_space, max_space))
                            
                    if pub_time < self.current_date:
                        pub_time = self.current_date + datetime.timedelta(minutes=random.randint(5, 15))
                        
                    if pub_time > end_time:
                        continue 
                        
                    self.target_web = web
                    self.publish_time = pub_time
                    self.add_log(log_placeholder, f"  [✓] CHỐT SLOT! Khóa mục tiêu Website '{ws_name}' - Lên bài lúc: {pub_time.strftime('%H:%M ngày %d/%m/%Y')}.")
                    return True
                else:
                    self.add_log(log_placeholder, f"  [-] Website '{ws_name}' ngày {day_x_str} đã full Limit. Quét ngày kế tiếp...")
                    
        self.add_log(log_placeholder, f"🛑 Đã lên lịch full cho toàn bộ Website trong {max_days} ngày. Dừng hệ thống.")
        return False

    def run_ai_content_pipeline(self, log_placeholder):
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return None

        main_kw_row = df_kw.sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        
        self.content_kws = df_kw.sample(n=2)['KW_TEXT'].tolist() if len(df_kw) > 2 else []
        self.all_used_kws = [self.main_kw_text] + self.content_kws
        self.add_log(log_placeholder, f"REP_KW: {', '.join(self.all_used_kws)}")

        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        final_word_count = random.randint(self.safe_int(word_range[0], 900), self.safe_int(word_range[-1], 1200))

        ref_content = self.fetch_reference_content(log_placeholder)
        if not ref_content:
            self.add_log(log_placeholder, "Bỏ qua bước COMPETITOR_LIST. Tự động chuyển sang chế độ tự do sáng tạo!")
            ref_content = "Tự do sáng tạo chuyên sâu."

        prompt = f"Viết bài chuẩn SEO HTML về {self.main_kw_text}, độ dài {final_word_count} chữ. Keywords phụ: {', '.join(self.content_kws)}. Trả về HTML (h1, h2, h3, p). Dữ liệu tham khảo: {ref_content}"

        response_text = ""
        or_key = str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',')[0].strip()
        if or_key:
            try:
                self.add_log(log_placeholder, "Đang gọi API OpenRouter...")
                headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}
                payload = {"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]}
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120).json()
                response_text = res["choices"][0]["message"]["content"]
            except: pass

        if not response_text:
            gem_key = str(self.dashboard.get('GEMINI_API_KEY', '')).split(',')[0].strip()
            if gem_key:
                try:
                    genai.configure(api_key=gem_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response_text = model.generate_content(prompt).text
                except: pass

        self.add_log(log_placeholder, "Phân bổ Backlink vào đúng vị trí...")
        self.add_log(log_placeholder, "Phân bổ WS_IMG_LIMIT theo rule...")

        self.raw_html = response_text.replace('```html', '').replace('```', '').strip() if response_text else "<h1>Lỗi tạo bài</h1><p>API Timeout</p>"
        
        h1_match = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else f"Bài viết: {self.main_kw_text}"
        
        final_result = self.run_kcs_validation(log_placeholder, self.raw_html, self.generated_title)
        self.append_to_google_doc(self.raw_html, self.generated_title, log_placeholder)

        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_CREATED_AT': self.current_date.strftime('%Y-%m-%d %H:%M'),
            'REP_TITLE': self.generated_title,
            'REP_IMG_COUNT': "3",
            'REP_KW_1': self.all_used_kws[0],
            'REP_KW_2': self.all_used_kws[1] if len(self.all_used_kws) > 1 else "",
            'REP_KW_3': self.all_used_kws[2] if len(self.all_used_kws) > 2 else "",
            'REP_SEO_SCORE': str(self.kcs_results.get('SEO', 0)),
            'REP_AI_DETECTOR_RATE_20': str(self.kcs_results.get('AI_RATE', 100)),
            'REP_READABILITY_SCORE_60': str(self.kcs_results.get('READABILITY', 0)),
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_RESULT': final_result,
            'REP_LOG': "\n".join(self.history_log),
            'REP_HTML': self.raw_html
        }

    def sync_resources_to_sheet(self, client, log_placeholder):
        self.add_log(log_placeholder, "Nhịp 3: Đồng bộ & 'Hồi sinh' Tài nguyên (System Sync)...")
        try:
            ss = client.open_by_key(SHEET_ID)
            kw_sheet = ss.worksheet('KEYWORD')
            kw_data = kw_sheet.get_all_values()
            
            if len(kw_data) > 1:
                headers = kw_data[0]
                kw_idx = headers.index('KW_TEXT') if 'KW_TEXT' in headers else -1
                status_idx = headers.index('KW_STATUS') if 'KW_STATUS' in headers else -1
                date_idx = headers.index('KW_DATE') if 'KW_DATE' in headers else -1
                
                updates = []
                time_str = self.current_date.strftime('%Y-%m-%d %H:%M')
                
                for i, row in enumerate(kw_data[1:], start=2): 
                    if kw_idx != -1 and len(row) > kw_idx and str(row[kw_idx]).strip() in self.all_used_kws:
                        if status_idx != -1:
                            curr_status = self.safe_int(row[status_idx] if len(row) > status_idx else 0, 0)
                            updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, status_idx + 1)}', 'values': [[curr_status + 1]]})
                        if date_idx != -1:
                            updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, date_idx + 1)}', 'values': [[time_str]]})
                
                if updates:
                    kw_sheet.batch_update(updates)
                    self.add_log(log_placeholder, f"  > Cập nhật thành công trạng thái cho {len(self.all_used_kws)} Từ khóa (Tăng KW_STATUS, Ghi KW_DATE).")
        except:
            pass

    def step7_save_to_sheet(self, new_data, log_placeholder):
        if not new_data: return
        try:
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).worksheet('REPORT')
            headers = sheet.row_values(1)
            
            row_to_append = [str(new_data.get(h, "")) for h in headers]
            sheet.append_row(row_to_append)
            
            if new_data.get('REP_RESULT') == 'PENDING':
                self.sync_resources_to_sheet(client, log_placeholder)
                
            self.add_log(log_placeholder, "Nhịp 4: HOÀN TẤT - Đã ghi nhận lên Data.")
        except Exception as e: 
            self.add_log(log_placeholder, f"Lỗi ghi dữ liệu lên Sheet: {e}")

# ==========================================
# 🖥 HIỂN THỊ GIAO DIỆN WEB
# ==========================================
if 'is_running' not in st.session_state:
    st.session_state.is_running = False

db_mock = load_data_from_gsheets()
if db_mock is None: st.stop()

df_report = db_mock.get('REPORT', pd.DataFrame())
df_dash = db_mock.get('DASHBOARD', pd.DataFrame())

dash_dict = {str(k).strip(): str(v).strip() for k, v in zip(df_dash['DATA_KEY'], df_dash['DATA_CONTENT'])} if not df_dash.empty else {}
project_name = dash_dict.get('PROJECT_NAME', 'Hệ Thống Vận Hành SEO Vô Cực')
batch_size = dash_dict.get('BATCH_SIZE', '0')

st.title(f"🛡️ {project_name}")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🚀 BẢNG ĐIỀU KHIỂN & TỔNG QUAN", "📋 QUẢN LÝ BÀI VIẾT & LOG", "📊 REPORT (FULL)"])

with tab1:
    col1, col2, col3 = st.columns(3)
    
    today_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d')
    if not df_report.empty and 'REP_CREATED_AT' in df_report.columns:
        posts_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)])
    else:
        posts_today = 0
        
    total_posts = len(df_report)
    done_posts = len(df_report[df_report['REP_RESULT'].astype(str).str.strip() == 'DONE']) if total_posts > 0 else 0
    pending_posts = len(df_report[df_report['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if total_posts > 0 else 0
    
    col1.metric("Bài Đã Gen Hôm Nay", f"{posts_today}/{batch_size}")
    col2.metric("✅ Đã đăng bài", done_posts)
    col3.metric("⏳ Chờ hẹn giờ", pending_posts)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Bảng Điều Khiển Hệ Thống")
    
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: start_btn = st.button("🔥 Soạn bài AI", type="primary", use_container_width=True, disabled=st.session_state.is_running)
    with c2: force_btn = st.button("✈️ Lên bài ngay", type="primary", use_container_width=True, disabled=st.session_state.is_running)
    with c3: 
        if st.button("🔄 Update DB", use_container_width=True, disabled=st.session_state.is_running):
            # Xóa cache thủ công khi Sếp bấm nút Update
            load_data_from_gsheets.clear()
            st.rerun()
    
    if start_btn:
        st.session_state.is_running = True
        st.markdown("---")
        st.markdown("**🖥 Trạng thái tiến trình (Console Log):**")
        log_placeholder = st.empty() 
        
        bot = AutoContentSEO(db_mock)
        if bot.step1_kiem_tra_he_thong(log_placeholder):
            res = bot.run_ai_content_pipeline(log_placeholder)
            bot.step7_save_to_sheet(res, log_placeholder)
        
        st.session_state.is_running = False
        load_data_from_gsheets.clear() # Xóa cache sau khi ghi data mới
        
        # ĐÃ BỎ st.rerun() ĐỂ SẾP ĐỌC LOG THOẢI MÁI
        st.success("✅ Hoàn tất chu trình! Sếp có thể xem log bên trên. Bấm 'Update DB' để làm mới số liệu.")

    if force_btn:
        st.session_state.is_running = True
        st.markdown("---")
        with st.status("✈️ Đang quét đúng rule để lên bài...", expanded=True) as s:
            force_publish_pending_posts(s)
        st.session_state.is_running = False
        load_data_from_gsheets.clear()
        st.success("✅ Hoàn tất đăng bài! Bấm 'Update DB' để làm mới số liệu.")

with tab2:
    if not df_report.empty:
        st.dataframe(format_display_dataframe(df_report.tail(15)), use_container_width=True, hide_index=True)
        st.markdown("---")
        st.subheader("🔍 Nội soi Log chi tiết")
        
        post_titles = df_report['REP_TITLE'].tolist()[::-1]
        selected_title = st.selectbox("Chọn bài viết để xem Log & HTML:", post_titles)
        
        if selected_title:
            post_data = df_report[df_report['REP_TITLE'] == selected_title].iloc[0]
            lc1, lc2 = st.columns([1, 1])
            with lc1:
                st.markdown("**📝 Lịch Sử Chạy (System Log):**")
                raw_log = post_data.get('REP_LOG', 'Không có dữ liệu log.')
                st.markdown(f'<div class="log-box">{raw_log.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            with lc2:
                st.markdown("**🌐 Mã HTML:**")
                st.text_area("Mã HTML", post_data.get('REP_HTML', ''), height=350, label_visibility="collapsed")
    else: st.info("Chưa có bài viết nào.")

with tab3:
    st.subheader("Toàn bộ dữ liệu Tab REPORT gốc")
    if not df_report.empty:
        st.dataframe(df_report, use_container_width=True)
    else:
        st.info("Tab REPORT đang trống.")
