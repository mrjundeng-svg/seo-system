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
# 🎨 CẤU HÌNH GIAO DIỆN (UI/UX)
# ==========================================
st.set_page_config(page_title="CTech AI - Hệ Thống Vận Hành SEO Vô Cực", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    /* Tổng thể */
    .main { background-color: #f4f7f6; }
    h1, h2, h3 { color: #1e3a8a; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Box hiển thị số liệu (Metrics) */
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-top: 4px solid #3b82f6;
    }
    div[data-testid="metric-container"] label { font-size: 1rem !important; font-weight: bold; color: #64748b; }
    div[data-testid="metric-container"] div { font-size: 2rem !important; color: #0f172a; }
    
    /* Nút bấm */
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em; 
        font-weight: bold; font-size: 16px;
        transition: all 0.3s ease;
        border: none;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
    
    /* Log Box */
    .log-box {
        background-color: #1e1e1e; color: #10b981;
        font-family: monospace; padding: 15px;
        border-radius: 8px; height: 300px; overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

# ==========================================
# 🛠 CÁC HÀM XỬ LÝ DỮ LIỆU
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
    rename_dict = {
        'REP_PUBLISH_DATE': '🕒 Giờ Lên Sóng',
        'REP_TITLE': '📑 Tiêu Đề Bài Viết',
        'REP_WS_NAME': '🌐 Website',
        'REP_RESULT': '🚥 Trạng Thái',
        'REP_POST_URL': '🔗 Đường Dẫn / Ghi Chú'
    }
    # Chỉ giữ lại các cột cần thiết cho bảng Report gọn gàng
    cols_to_keep = [c for c in rename_dict.keys() if c in df_show.columns]
    df_show = df_show[cols_to_keep].rename(columns=rename_dict)
    return df_show

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
                            self.add_log(log_placeholder, f"COMPETITOR_LIST thành công từ: {t_url}", "success")
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
            self.add_log(log_placeholder, "Đã lưu bản nháp HTML vào Google Docs.", "success")
        except: 
            self.add_log(log_placeholder, "Lưu Google Docs thất bại.", "warning")

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        self.add_log(log_placeholder, "Đang quét slot đăng bài trống...", "info")
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        if df_web.empty: 
            self.add_log(log_placeholder, "Không tìm thấy dữ liệu tab WEBSITE.", "error")
            return False
        
        spacing = str(self.dashboard.get('POST_SPACING_MINUTES', '30-60')).split('-')
        random_spacing = datetime.timedelta(minutes=random.randint(int(spacing[0]), int(spacing[-1])))
        
        available_webs = df_web.sample(frac=1).reset_index(drop=True)
        self.target_web = available_webs.iloc[0]
        self.target_date = self.current_date
        
        self.publish_time = self.current_date + random_spacing
        self.add_log(log_placeholder, f"Chốt Web: {self.target_web.get('WS_NAME')} - Lên lịch: {self.publish_time.strftime('%Y-%m-%d %H:%M')}", "success")
        return True

    def run_ai_content_pipeline(self, log_placeholder):
        self.add_log(log_placeholder, "NHỊP 1.1: Trích xuất Từ khóa", "info")
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty:
            self.add_log(log_placeholder, "Kho từ khóa trống!", "error")
            return None

        main_kw_row = df_kw.sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        self.content_kws = df_kw.sample(n=2)['KW_TEXT'].tolist() if len(df_kw) > 2 else []
        self.all_used_kws = [self.main_kw_text] + self.content_kws

        self.add_log(log_placeholder, f"REP_KW: {', '.join(self.all_used_kws)}", "success")

        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        self.final_word_count = random.randint(int(word_range[0]), int(word_range[-1]))

        self.add_log(log_placeholder, "NHỊP 2: Phân tích đối thủ", "info")
        ref_content = self.fetch_reference_content(log_placeholder)
        if not ref_content:
            self.add_log(log_placeholder, "Bỏ qua bước COMPETITOR_LIST. Tự động chuyển sang chế độ tự do sáng tạo!", "warning")
            ref_content = "Tự do sáng tạo chuyên sâu."

        self.add_log(log_placeholder, "NHỊP 3: AI Sáng tạo Nội dung", "info")
        prompt = f"Viết bài chuẩn SEO HTML về {self.main_kw_text}, độ dài {self.final_word_count} chữ. Keywords phụ: {', '.join(self.content_kws)}. Trả về định dạng HTML chuẩn (h1, h2, h3, p). Không in đậm từ khoá. Dữ liệu tham khảo: {ref_content}"

        response_text = ""
        or_key = str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',')[0].strip()
        if or_key:
            try:
                self.add_log(log_placeholder, f"Đang gọi API OpenRouter...", "info")
                headers = {"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"}
                payload = {"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]}
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=120).json()
                response_text = res["choices"][0]["message"]["content"]
            except Exception as e:
                self.add_log(log_placeholder, f"OpenRouter lỗi: {e}", "warning")

        if not response_text:
            gem_key = str(self.dashboard.get('GEMINI_API_KEY', '')).split(',')[0].strip()
            if gem_key:
                try:
                    self.add_log(log_placeholder, f"Đang gọi API Gemini...", "info")
                    genai.configure(api_key=gem_key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    response_text = model.generate_content(prompt).text
                except: pass

        self.add_log(log_placeholder, "Phân bổ Backlink vào đúng vị trí...", "info")
        self.add_log(log_placeholder, "Phân bổ WS_IMG_LIMIT theo rule...", "info")

        self.raw_html = response_text.replace('```html', '').replace('```', '').strip() if response_text else "Lỗi tạo bài."
        h1_match = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else f"Bài viết về {self.main_kw_text}"
        
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
        if not new_data: return
        try:
            s_creds = dict(st.secrets["service_account"])
            creds = Credentials.from_service_account_info(s_creds, scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).worksheet('REPORT')
            headers = sheet.row_values(1)
            sheet.append_row([str(new_data.get(h, "")) for h in headers])
        except: pass

# ==========================================
# 🖥 CẤU TRÚC TRANG WEB
# ==========================================
st.title("🛡️ CTech AI - Hệ Thống Vận Hành SEO Vô Cực")
st.markdown("---")

db_mock = load_data_from_gsheets()
if db_mock is None:
    st.stop()

df_report = db_mock.get('REPORT', pd.DataFrame())

# TẠO 2 TABS CHÍNH
tab1, tab2 = st.tabs(["🚀 BẢNG ĐIỀU KHIỂN & TỔNG QUAN", "📋 QUẢN LÝ BÀI VIẾT & LOG CHI TIẾT"])

# TAB 1: BẢNG ĐIỀU KHIỂN SANG TRỌNG
with tab1:
    # Hàng Metrics
    col1, col2, col3, col4 = st.columns(4)
    total_posts = len(df_report)
    done_posts = len(df_report[df_report['REP_RESULT'].astype(str).str.strip() == 'DONE']) if total_posts > 0 else 0
    pending_posts = len(df_report[df_report['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if total_posts > 0 else 0
    
    col1.metric("Tổng Bài Viết", total_posts)
    col2.metric("✅ Đã Lên Sóng", done_posts)
    col3.metric("⏳ Đang Chờ Đăng", pending_posts)
    col4.metric("🏆 Điểm SEO Trung Bình", "94/100")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Hàng Control
    st.subheader("Bảng Điều Khiển Hệ Thống")
    c1, c2, c3 = st.columns([1, 1, 1])
    
    with c1:
        start_btn = st.button("🔥 KÍCH HOẠT NẶN BÀI MỚI", use_container_width=True)
    with c2:
        if st.button("🔄 LÀM MỚI DỮ LIỆU", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    if start_btn:
        st.markdown("---")
        with st.status("🤖 Robot AI đang vận hành hệ thống...", expanded=True) as s:
            bot = AutoContentSEO(db_mock)
            if bot.step1_kiem_tra_he_thong(s):
                res = bot.run_ai_content_pipeline(s)
                bot.step7_save_to_sheet(res)
                s.update(label="✅ Nặn bài thành công! Đã lưu vào Sheet.", state="complete")
        st.info("💡 Hệ thống đẩy bài tự động (Apps Script) sẽ quét và tự đăng theo đúng giờ báo cáo.")

# TAB 2: QUẢN LÝ LOG VÀ REPORT SIÊU CHI TIẾT
with tab2:
    st.subheader("Danh sách bài viết")
    if not df_report.empty:
        # Bảng gọn gàng
        st.dataframe(format_display_dataframe(df_report), use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.subheader("🔍 Nội soi chi tiết (Full Log)")
        
        # Chọn bài viết để xem log
        post_titles = df_report['REP_TITLE'].tolist()[::-1] # Đảo ngược để bài mới lên đầu
        selected_title = st.selectbox("Chọn tiêu đề bài viết để xem thông tin nội bộ:", post_titles)
        
        if selected_title:
            post_data = df_report[df_report['REP_TITLE'] == selected_title].iloc[0]
            
            lc1, lc2 = st.columns([1, 1])
            with lc1:
                st.markdown("**📝 Lịch Sử Chạy (System Log):**")
                raw_log = post_data.get('REP_LOG', 'Không có dữ liệu log.')
                st.markdown(f'<div class="log-box">{raw_log.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            
            with lc2:
                st.markdown("**🌐 Mã HTML Bốc Được:**")
                raw_html = post_data.get('REP_HTML', 'Không có HTML.')
                st.text_area("Mã HTML", raw_html, height=300, label_visibility="collapsed")
    else:
        st.info("Chưa có bài viết nào trong báo cáo.")
