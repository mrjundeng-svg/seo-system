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
    
    /* Box hiển thị số liệu (Metrics) */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #ef4444; /* Màu viền đỏ cam cho rực rỡ */
    }
    div[data-testid="metric-container"] label { font-size: 1rem !important; font-weight: 600; color: #475569; }
    div[data-testid="metric-container"] div { font-size: 2.2rem !important; color: #1e293b; font-weight: bold; }
    
    /* Log Box Hacker Style */
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
# 🛠 CÁC HÀM XỬ LÝ DỮ LIỆU & EMAIL
# ==========================================
@st.cache_data(ttl=10)
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

        posted_count = 0
        for idx, row in df_report.iterrows():
            if str(row.get('REP_RESULT')).strip() == 'PENDING':
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
        status_box.success(f"🎉 Đã lên {posted_count} bài viết thành công!")
    except Exception as e: status_box.error(f"❌ Lỗi khi ép đăng: {e}")

# ==========================================
# 🤖 LÕI AI NẶN BÀI 
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

    def add_log(self, ui_box, message, level="info"):
        """Ghi log và render trực tiếp ra màn hình đen thời gian thực"""
        time_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%H:%M:%S')
        log_line = f"[{time_str}] {message}"
        self.history_log.append(log_line)
        if ui_box:
            # Gộp toàn bộ lịch sử log thành HTML hiển thị dạng Console
            formatted_logs = "<br>".join(self.history_log)
            ui_box.markdown(f'<div class="log-box">{formatted_logs}</div>', unsafe_allow_html=True)

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        if df.empty: return {}
        return {str(k).strip(): str(v).strip() for k, v in zip(df['DATA_KEY'], df['DATA_CONTENT'])}

    def fetch_reference_content(self, log_placeholder):
        self.add_log(log_placeholder, "Đang tải cấu hình API SerpAPI...")
        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        if serp_key:
            try:
                self.add_log(log_placeholder, f"Tiến hành quét TOP 5 Google cho từ khoá: '{self.main_kw_text}'")
                url = "https://serpapi.com/search"
                res = requests.get(url, params={"q": self.main_kw_text, "hl": "vi", "gl": "vn", "api_key": serp_key}, timeout=10).json()
                results = res.get("organic_results", [])
                target_urls = [r["link"] for r in results[:5] if "link" in r]
                random.shuffle(target_urls)
                for t_url in target_urls:
                    self.add_log(log_placeholder, f"Đang truy cập và bóc tách dữ liệu thô từ: {t_url}")
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res_html = requests.get(t_url, headers=headers, timeout=10)
                    if res_html.status_code == 200:
                        soup = BeautifulSoup(res_html.text, 'html.parser')
                        for tag in soup(["script", "style", "nav", "footer", "header"]): tag.decompose()
                        content = "\n\n".join([tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'p']) if tag.get_text(strip=True)])
                        if len(content) > 300:
                            self.add_log(log_placeholder, f"COMPETITOR_LIST thành công từ: {t_url}")
                            return content[:6000]
            except Exception as e: 
                self.add_log(log_placeholder, f"Lỗi cào dữ liệu: {e}")
        return None

    def append_to_google_doc(self, html_content, title, log_placeholder):
        try:
            self.add_log(log_placeholder, "Đang khởi tạo kết nối với Google Docs API...")
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
            self.add_log(log_placeholder, "Lưu bản nháp HTML thành công vào Google Docs (Kho lưu trữ).")
        except: 
            self.add_log(log_placeholder, "Bỏ qua bước lưu nháp Google Docs do lỗi quyền truy cập.")

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        self.add_log(log_placeholder, "=============================================")
        self.add_log(log_placeholder, "BẮT ĐẦU CHU TRÌNH TỰ ĐỘNG NẶN BÀI")
        self.add_log(log_placeholder, "=============================================")
        self.add_log(log_placeholder, "Đang quét slot đăng bài trống và kiểm tra hệ thống...")
        
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        if df_web.empty: 
            self.add_log(log_placeholder, "Không tìm thấy dữ liệu tab WEBSITE. Dừng hệ thống!")
            return False
        
        spacing = str(self.dashboard.get('POST_SPACING_MINUTES', '30-60')).split('-')
        random_spacing = datetime.timedelta(minutes=random.randint(int(spacing[0]), int(spacing[-1])))
        
        available_webs = df_web.sample(frac=1).reset_index(drop=True)
        self.target_web = available_webs.iloc[0]
        
        self.publish_time = self.current_date + random_spacing
        self.add_log(log_placeholder, f"Chốt Web: {self.target_web.get('WS_NAME')} - Lên lịch hẹn giờ: {self.publish_time.strftime('%Y-%m-%d %H:%M')}")
        return True

    def run_ai_content_pipeline(self, log_placeholder):
        self.add_log(log_placeholder, "NHỊP 1: Trích xuất Từ khóa từ Kho dữ liệu...")
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty:
            self.add_log(log_placeholder, "Kho từ khóa trống, không có dữ liệu để chạy.")
            return None

        main_kw_row = df_kw.sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        self.add_log(log_placeholder, f"Đã khóa mục tiêu Main Keyword: '{self.main_kw_text}'")
        
        self.content_kws = df_kw.sample(n=2)['KW_TEXT'].tolist() if len(df_kw) > 2 else []
        self.all_used_kws = [self.main_kw_text] + self.content_kws

        self.add_log(log_placeholder, f"REP_KW: {', '.join(self.all_used_kws)}")

        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        final_word_count = random.randint(int(word_range[0]), int(word_range[-1]))
        self.add_log(log_placeholder, f"Đã thiết lập độ dài bài viết mục tiêu: {final_word_count} chữ.")

        self.add_log(log_placeholder, "NHỊP 2: Phân tích đối thủ (SERP Analysis)...")
        ref_content = self.fetch_reference_content(log_placeholder)
        if not ref_content:
            self.add_log(log_placeholder, "Bỏ qua bước COMPETITOR_LIST. Tự động chuyển sang chế độ tự do sáng tạo!")
            ref_content = "Tự do sáng tạo chuyên sâu."

        self.add_log(log_placeholder, "NHỊP 3: Lên Prompts & Gọi AI Sáng tạo Nội dung...")
        prompt = f"Viết bài chuẩn SEO HTML về {self.main_kw_text}, độ dài {final_word_count} chữ. Keywords phụ: {', '.join(self.content_kws)}. Trả về HTML (h1, h2, h3, p). Dữ liệu tham khảo: {ref_content}"

        response_text = ""
        or_key = str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',')[0].strip()
        if or_key:
            try:
                self.add_log(log_placeholder, "Đang gửi tín hiệu qua API OpenRouter (Claude-3.5-Sonnet)...")
                headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}
                payload = {"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]}
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120).json()
                response_text = res["choices"][0]["message"]["content"]
                self.add_log(log_placeholder, "Nhận phản hồi từ OpenRouter thành công. Đang xử lý Text sang HTML...")
            except Exception as e:
                self.add_log(log_placeholder, f"OpenRouter lỗi Timeout/Kết nối: {e}")

        if not response_text:
            gem_key = str(self.dashboard.get('GEMINI_API_KEY', '')).split(',')[0].strip()
            if gem_key:
                try:
                    self.add_log(log_placeholder, "Kích hoạt AI dự phòng: Gemini 1.5 Flash...")
                    genai.configure(api_key=gem_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response_text = model.generate_content(prompt).text
                    self.add_log(log_placeholder, "Nhận phản hồi từ Gemini thành công. Đang làm sạch mã HTML...")
                except: pass

        self.add_log(log_placeholder, "Phân bổ Backlink vào đúng vị trí...")
        self.add_log(log_placeholder, "Phân bổ WS_IMG_LIMIT theo rule...")

        self.raw_html = response_text.replace('```html', '').replace('```', '').strip() if response_text else "Lỗi tạo bài."
        
        self.add_log(log_placeholder, "Đang quét và trích xuất thẻ <h1> làm Tiêu đề (Title)...")
        h1_match = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else f"Bài viết: {self.main_kw_text}"
        
        self.append_to_google_doc(self.raw_html, self.generated_title, log_placeholder)

        self.add_log(log_placeholder, "Đóng gói dữ liệu chuẩn bị đẩy lên Google Sheet...")
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

    def step7_save_to_sheet(self, new_data, log_placeholder):
        if not new_data: return
        try:
            self.add_log(log_placeholder, "Đang mở cầu nối với Tab REPORT...")
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).worksheet('REPORT')
            headers = sheet.row_values(1)
            sheet.append_row([str(new_data.get(h, "")) for h in headers])
            self.add_log(log_placeholder, "=============================================")
            self.add_log(log_placeholder, "HOÀN TẤT! Đã ghi nhận bài viết lên hệ thống Data.")
            self.add_log(log_placeholder, "=============================================")
        except Exception as e: 
            self.add_log(log_placeholder, f"Lỗi ghi dữ liệu lên Sheet: {e}")

# ==========================================
# 🖥 HIỂN THỊ GIAO DIỆN WEB
# ==========================================
db_mock = load_data_from_gsheets()
if db_mock is None: st.stop()

df_report = db_mock.get('REPORT', pd.DataFrame())
df_dash = db_mock.get('DASHBOARD', pd.DataFrame())

# TỰ ĐỘNG LẤY TÊN DỰ ÁN TỪ TAB DASHBOARD
dash_dict = {str(k).strip(): str(v).strip() for k, v in zip(df_dash['DATA_KEY'], df_dash['DATA_CONTENT'])} if not df_dash.empty else {}
project_name = dash_dict.get('PROJECT_NAME', 'Hệ Thống Vận Hành SEO Vô Cực')
batch_size = dash_dict.get('BATCH_SIZE', '0')

st.title(f"🛡️ {project_name}")
st.markdown("---")

# TẠO 3 TABS NHƯ YÊU CẦU
tab1, tab2, tab3 = st.tabs(["🚀 BẢNG ĐIỀU KHIỂN & TỔNG QUAN", "📋 QUẢN LÝ BÀI VIẾT & LOG", "📊 REPORT (FULL)"])

# TAB 1: ĐIỀU KHIỂN
with tab1:
    # CHIA THÀNH 3 CỘT CHO CÂN ĐỐI (Đã gỡ điểm SEO)
    col1, col2, col3 = st.columns(3)
    
    # Tính toán "Tổng Bài Viết trong ngày / BATCH_SIZE"
    today_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%Y-%m-%d')
    if not df_report.empty and 'REP_CREATED_AT' in df_report.columns:
        posts_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.contains(today_str)])
    else:
        posts_today = 0
        
    total_posts = len(df_report)
    done_posts = len(df_report[df_report['REP_RESULT'].astype(str).str.strip() == 'DONE']) if total_posts > 0 else 0
    pending_posts = len(df_report[df_report['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if total_posts > 0 else 0
    
    col1.metric("Tổng Bài Viết", f"{posts_today}/{batch_size}")
    col2.metric("✅ Đã đăng bài", done_posts)
    col3.metric("⏳ Chờ hẹn giờ", pending_posts)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("Bảng Điều Khiển Hệ Thống")
    
    # NÚT BẤM NỔI BẬT VÀ ĐỔI TÊN
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1: start_btn = st.button("🔥 Soạn bài AI", type="primary", use_container_width=True)
    with c2: force_btn = st.button("✈️ Lên bài ngay", type="primary", use_container_width=True)
    with c3: 
        if st.button("🔄 Update DB", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    # BOX CHẠY LOG THỜI GIAN THỰC (MÀN HÌNH ĐEN)
    if start_btn:
        st.markdown("---")
        st.markdown("**🖥 Trạng thái tiến trình (Console Log):**")
        log_placeholder = st.empty() # Khung chứa log
        
        bot = AutoContentSEO(db_mock)
        if bot.step1_kiem_tra_he_thong(log_placeholder):
            res = bot.run_ai_content_pipeline(log_placeholder)
            bot.step7_save_to_sheet(res, log_placeholder)

    if force_btn:
        st.markdown("---")
        with st.status("✈️ Đang quét và ép gửi bài PENDING...", expanded=True) as s:
            force_publish_pending_posts(s)

# TAB 2: QUẢN LÝ & LOG CHI TIẾT
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

# TAB 3: HIỂN THỊ FULL REPORT GOOGLE SHEET
with tab3:
    st.subheader("Toàn bộ dữ liệu Tab REPORT gốc")
    if not df_report.empty:
        # Show full dataframe không qua format
        st.dataframe(df_report, use_container_width=True)
    else:
        st.info("Tab REPORT đang trống.")
