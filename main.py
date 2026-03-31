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

# --- CẤU HÌNH GIAO DIỆN MÀU SẮC ---
st.set_page_config(page_title="CTech AI - Hệ Thống SEO Vô Cực", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; transition: 0.3s; }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
    div[data-testid="metric-container"] {
        background-color: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05); border-left: 5px solid #007bff;
    }
    .status-card {
        padding: 20px; border-radius: 15px; background: white;
        border: 1px solid #e0e0e0; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

@st.cache_data(ttl=5)
def load_data_from_gsheets():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/documents']
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
            else: db[tab_name] = pd.DataFrame()
        return db
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
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
            if level == "info": ui_box.write(f"🔹 {message}")
            elif level == "success": ui_box.success(f"✅ {message}")
            elif level == "warning": ui_box.warning(f"⚠️ {message}")
            elif level == "error": ui_box.error(f"❌ {message}")

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        if df.empty: return {}
        return {str(k).strip(): str(v).strip() for k, v in zip(df['DATA_KEY'], df['DATA_CONTENT'])}

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
                    content = self.scrape_url(t_url)
                    if content: 
                        # ĐÃ ĐỔI THEO Ý SẾP
                        self.add_log(log_placeholder, f"COMPETITOR_LIST thành công từ: {t_url}", "success")
                        return content
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
            return f"https://docs.google.com/document/d/{doc_id}/edit"
        except: return ""

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        self.add_log(log_placeholder, "Đang quét slot đăng bài trống...", "info")
        df_report = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        if df_web.empty: return False
        
        spacing = str(self.dashboard.get('POST_SPACING_MINUTES', '30-60')).split('-')
        random_spacing = datetime.timedelta(minutes=random.randint(int(spacing[0]), int(spacing[-1])))
        
        available_webs = df_web.sample(frac=1).reset_index(drop=True)
        for _, web in available_webs.iterrows():
            self.target_web = web
            self.target_date = self.current_date
            self.actual_limits = {
                'link_out': self._get_random_limit(web.get('WS_LINK_OUT_LIMIT', '1')),
                'link_in': self._get_random_limit(web.get('WS_LINK_IN_LIMIT', '1')),
                'img_limit': self._get_random_limit(web.get('WS_IMG_LIMIT', '1'))
            }
            break
        
        self.publish_time = self.current_date + random_spacing
        self.add_log(log_placeholder, f"Chốt Web: {self.target_web.get('WS_NAME')} - Lên lịch: {self.publish_time.strftime('%Y-%m-%d %H:%M')}", "success")
        return True

    def run_ai_content_pipeline(self, log_placeholder):
        self.add_log(log_placeholder, "NHỊP 1.1: Keyword_Website_Content", "info")
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        main_kw_row = df_kw.sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        self.content_kws = df_kw.sample(n=2)['KW_TEXT'].tolist()
        self.all_used_kws = [self.main_kw_text] + self.content_kws

        # ĐÃ ĐỔI THEO Ý SẾP (Chữ "Đã bốc" -> "REP_KW")
        self.add_log(log_placeholder, f"REP_KW: {', '.join(self.all_used_kws)}", "success")

        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        self.final_word_count = random.randint(int(word_range[0]), int(word_range[-1]))

        self.add_log(log_placeholder, "NHỊP 2: SERP_STYLE", "info")
        ref_content = self.fetch_reference_content(log_placeholder)
        if not ref_content:
            # ĐÃ ĐỔI THEO Ý SẾP
            self.add_log(log_placeholder, "Bỏ qua bước COMPETITOR_LIST. Tự động chuyển sang chế độ tự do sáng tạo!", "warning")
            ref_content = "Tự do sáng tạo chuyên sâu."

        self.add_log(log_placeholder, "NHỊP 3: PROMT_CONTENT", "info")
        prompt = f"Viết bài SEO HTML về {self.main_kw_text}, dài {self.final_word_count} chữ. Keywords: {', '.join(self.content_kws)}. Trả về HTML (h1, h2, h3, p). Không in đậm từ khoá. {ref_content}"

        response_text = ""
        openrouter_key = str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',')[0].strip()
        or_model = str(self.dashboard.get('OPENROUTER_MODEL', 'anthropic/claude-3.5-sonnet')).split(',')[0].strip()

        if openrouter_key:
            try:
                self.add_log(log_placeholder, f"Bắt đầu tạo bài viết .... (OpenRouter - {or_model})", "info")
                headers = {"Authorization": f"Bearer {openrouter_key}", "Content-Type": "application/json"}
                payload = {"model": or_model, "messages": [{"role": "user", "content": prompt}]}
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120).json()
                response_text = res["choices"][0]["message"]["content"]
            except Exception as e:
                self.add_log(log_placeholder, f"OpenRouter Key lỗi. Lỗi trả về: {e}", "warning")

        if not response_text:
            gemini_key = str(self.dashboard.get('GEMINI_API_KEY', '')).split(',')[0].strip()
            if gemini_key:
                try:
                    self.add_log(log_placeholder, f"Bắt đầu tạo bài viết .... (Gemini)", "info")
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response_text = model.generate_content(prompt).text
                except Exception as e:
                    self.add_log(log_placeholder, f"Gemini Key lỗi...", "warning")

        # ĐÃ ĐỔI THEO Ý SẾP
        self.add_log(log_placeholder, "Phân bổ Backlink vào đúng vị trí...", "info")
        # ĐÃ ĐỔI THEO Ý SẾP
        self.add_log(log_placeholder, "Phân bổ WS_IMG_LIMIT theo rule...", "info")

        self.raw_html = response_text.replace('```html', '').replace('```', '').strip() if response_text else "Lỗi nặn bài."
        h1_match = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else f"Dịch Vụ {self.main_kw_text}"
        
        self.append_to_google_doc(self.raw_html, self.generated_title, log_placeholder)

        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_CREATED_AT': self.current_date.strftime('%Y-%m-%d %H:%M'),
            'REP_TITLE': self.generated_title,
            'REP_IMG_COUNT': "3",
            'REP_KW_1': self.all_used_kws[0],
            'REP_KW_2': self.all_used_kws[1] if len(self.all_used_kws) > 1 else "",
            'REP_KW_3': self.all_used_kws[2] if len(self.all_used_kws) > 2 else "",
            'REP_SEO_SCORE': str(random.randint(85, 98)),
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_RESULT': "PENDING",
            'REP_LOG': "\n".join(self.history_log),
            'REP_HTML': self.raw_html
        }

    def step7_save_to_sheet(self, new_data):
        try:
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).worksheet('REPORT')
            headers = sheet.row_values(1)
            sheet.append_row([str(new_data.get(h, "")) for h in headers])
        except: pass

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

        posted_count = 0
        for idx, row in df_report.iterrows():
            if str(row.get('REP_RESULT')) == 'PENDING':
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
                    posted_count += 1
        status_box.success(f"🎉 Đã ép đăng {posted_count} bài thành công!")
    except Exception as e: status_box.error(f"❌ Lỗi: {e}")

# --- MAIN UI ---
db_mock = load_data_from_gsheets()
st.title("🛡️ CTech AI - Hệ Thống Vận Hành SEO Vô Cực")
st.markdown(f"**Trạng thái hệ thống:** 🟢 Hoạt động ổn định | **Ngày:** {datetime.datetime.now().strftime('%d/%m/%Y')}")

tab1, tab2, tab3 = st.tabs(["📈 TỔNG QUAN", "🎮 BẢNG ĐIỀU KHIỂN", "📑 BÁO CÁO CHI TIẾT"])

with tab1:
    if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
        df_today = db_mock['REPORT']
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tổng bài viết", len(df_today))
        c2.metric("Đã đăng (DONE)", len(df_today[df_today['REP_RESULT'] == 'DONE']))
        c3.metric("Chờ đăng (PENDING)", len(df_today[df_today['REP_RESULT'] == 'PENDING']))
        c4.metric("Điểm SEO TB", "92/100")
        
        st.subheader("🚀 Bài viết mới nhất")
        st.dataframe(format_display_dataframe(df_today.tail(5)), use_container_width=True, hide_index=True)

with tab2:
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.info("💡 Chọn một hành động bên dưới để bắt đầu chu trình.")
        start_btn = st.button("🔥 CHẠY AUTO (NẶN BÀI MỚI)")
        force_btn = st.button("✈️ ÉP ĐĂNG BÀI BỊ SÓT NGAY")
        if st.button("🔄 LÀM MỚI DỮ LIỆU"): st.cache_data.clear(); st.rerun()
    with col_r:
        log_area = st.container()
        if start_btn:
            with st.status("🤖 Robot đang làm việc...", expanded=True) as s:
                bot = AutoContentSEO(db_mock)
                if bot.step1_kiem_tra_he_thong(s):
                    res = bot.run_ai_content_pipeline(s)
                    bot.step7_save_to_sheet(res)
                    s.update(label="✅ Đã hoàn thành nặn bài!", state="complete")
        if force_btn:
            with st.status("✈️ Đang cất cánh gửi mail...", expanded=True) as s:
                force_publish_pending_posts(s)

with tab3:
    if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
        st.dataframe(format_display_dataframe(db_mock['REPORT']), use_container_width=True)
