import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time
import random
import datetime
import statistics
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
# 🛠 HỆ SINH THÁI DỮ LIỆU
# ==========================================
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
                except: pass
                    
        status_box.success(f"🎉 Đã lên sóng {posted_count} bài viết! (⚠️ Giữ nguyên {skipped_future} bài chưa tới giờ).")
    except Exception as e: status_box.error(f"❌ Lỗi khi lên bài: {e}")

# ==========================================
# 🤖 CORE AI: NHÀ XƯỞNG SẢN XUẤT NỘI DUNG
# ==========================================
class AutoContentSEO:
    def __init__(self, data_frames):
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.current_date = datetime.datetime.utcnow() + datetime.timedelta(hours=7) 
        self.target_date, self.target_web = None, None
        self.main_kw_text = ""
        self.content_kws, self.all_used_kws = [], []
        self.kw_intent, self.ws_persona = "", ""
        self.publish_time = None
        self.raw_html, self.generated_title = "", ""
        self.history_log = [] 
        self.kcs_results = {}
        self.used_img_urls = []
        self.final_word_count = 0

    def add_log(self, ui_box, message):
        time_str = (datetime.datetime.utcnow() + datetime.timedelta(hours=7)).strftime('%H:%M:%S')
        self.history_log.append(f"[{time_str}] {message}")
        if ui_box: ui_box.markdown(f'<div class="log-box">{"<br>".join(self.history_log)}</div>', unsafe_allow_html=True)

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        return {str(k).strip(): str(v).strip() for k, v in zip(df['DATA_KEY'], df['DATA_CONTENT'])} if not df.empty else {}

    def safe_int(self, value, default=1):
        try: return int(str(value).strip())
        except: return default

    # --- NHỊP MEDIA & BACKLINK (THIẾT QUÂN LUẬT 4 BƯỚC) ---
    def process_html_media_and_links(self, html_content, log_placeholder):
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. GẮN BACKLINK (NHỊP 1)
        out_limit = self.safe_int(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        in_limit = self.safe_int(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        out_link = str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).strip()
        in_link = str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).strip()
        
        self.add_log(log_placeholder, f"Nhịp Xử lý: Gắn Backlink chiến lược ({out_limit} Link Ngoại, {in_limit} Link Nội).")
        
        for i, kw in enumerate(self.all_used_kws):
            link_url = out_link if i < out_limit else in_link
            if not link_url: continue
            
            target_p = None
            # Chỉ quét trong thẻ <p> để né Heading (Title)
            for p in soup.find_all('p'):
                if p.find('a'): continue # Tránh bọc link lồng nhau
                if re.search(r'(?i)\b' + re.escape(kw) + r'\b', p.get_text()):
                    target_p = p
                    break
            
            if target_p:
                pattern = re.compile(r'(?i)\b' + re.escape(kw) + r'\b')
                # Replace bảo toàn nguyên trạng ký tự HOA/thường của Keyword
                new_html = pattern.sub(lambda m: f"<a href='{link_url}'>{m.group(0)}</a>", str(target_p), count=1)
                new_p = BeautifulSoup(new_html, 'html.parser')
                target_p.replace_with(new_p)

        # 2. TUYỂN CHỌN & CHÈN ẢNH (NHỊP 2 & 3)
        df_img = self.db.get('IMAGE', pd.DataFrame())
        ws_img_limit = self.safe_int(self.target_web.get('WS_IMG_LIMIT', 3), 3)
        
        word_range_str = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200'))
        max_words = self.safe_int(word_range_str.split('-')[-1], 1200)
        
        # Hạn ngạch bài ngắn (Short-form) hay Standard
        is_short = self.final_word_count <= (max_words / 2)
        actual_img_limit = 1 if is_short else ws_img_limit
        
        if not df_img.empty and 'IMG_URL' in df_img.columns:
            valid_imgs = df_img[df_img['IMG_URL'].astype(str).str.strip() != ''].copy()
            if not valid_imgs.empty:
                if 'IMG_STATUS' not in valid_imgs.columns: valid_imgs['IMG_STATUS'] = 0
                valid_imgs['IMG_STATUS'] = pd.to_numeric(valid_imgs['IMG_STATUS'], errors='coerce').fillna(0)
                
                # Logic: Sắp xếp ưu tiên status thấp nhất, nếu bằng nhau thì random
                valid_imgs = valid_imgs.sample(frac=1).sort_values('IMG_STATUS')
                chosen_imgs = valid_imgs.head(actual_img_limit)
                img_urls = chosen_imgs['IMG_URL'].tolist()
                self.used_img_urls = img_urls
                
                if img_urls:
                    p_tags = soup.find_all('p')
                    if p_tags:
                        idx_first = 0
                        for i, p in enumerate(p_tags):
                            if re.search(r'(?i)\b' + re.escape(self.all_used_kws[0]) + r'\b', p.get_text()):
                                idx_first = i; break
                        
                        idx_last = len(p_tags) - 1
                        if len(self.all_used_kws) > 1:
                            for i, p in enumerate(reversed(p_tags)):
                                if re.search(r'(?i)\b' + re.escape(self.all_used_kws[-1]) + r'\b', p.get_text()):
                                    idx_last = len(p_tags) - 1 - i; break
                                    
                        if idx_last <= idx_first: idx_last = min(idx_first + 2, len(p_tags) - 1)
                        
                        placement_indices = []
                        if len(img_urls) == 1:
                            placement_indices = [idx_first]
                        else:
                            placement_indices.append(idx_first)
                            placement_indices.append(idx_last)
                            remaining = len(img_urls) - 2
                            if remaining > 0:
                                step = max(1, (idx_last - idx_first) // (remaining + 1))
                                for i in range(1, remaining + 1):
                                    placement_indices.insert(i, idx_first + i * step)
                        
                        placement_indices = [min(idx, len(p_tags)-1) for idx in placement_indices]
                        
                        for img_url, p_idx in zip(img_urls, placement_indices):
                            target_p = p_tags[p_idx]
                            # Nhịp 4: Cú pháp bọc HTML căn giữa chuẩn SEO
                            img_html = f"<br><p align='center'><img src='{img_url}'></p><br>"
                            img_soup = BeautifulSoup(img_html, 'html.parser')
                            target_p.insert_after(img_soup)
                            
                    self.add_log(log_placeholder, f"Nhịp Xử lý: Phân bổ vị trí & Chèn {len(img_urls)} Ảnh minh họa (Thuật toán cân bằng).")
        return str(soup)

    # --- NHỊP KIỂM ĐỊNH KCS ---
    def run_kcs_validation(self, log_placeholder, html_content, title):
        self.add_log(log_placeholder, "=============================================")
        self.add_log(log_placeholder, "KÍCH HOẠT KCS: Đánh giá Chất Lượng Đầu Ra")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        words = text_content.split()
        total_words = len(words)
        
        kw_set = set(self.main_kw_text.lower().split())
        def match_flexible(target_str):
            if not kw_set: return False
            target_words = set(target_str.lower().split())
            return (sum(1 for w in kw_set if w in target_words) / len(kw_set)) >= 0.8
        
        seo_score = 0
        if match_flexible(title) and len(title) <= 65: seo_score += 20
        if any(match_flexible(h.get_text()) for h in soup.find_all('h1')): seo_score += 15
        if any(match_flexible(h.get_text()) for h in soup.find_all(['h2', 'h3'])): seo_score += 15
        if match_flexible(" ".join(words[:100])): seo_score += 10
            
        exact_kw_count = text_content.lower().count(self.main_kw_text.lower())
        density = (exact_kw_count * len(kw_set)) / total_words * 100 if total_words > 0 else 0
        if 0.5 <= density <= 3.5: seo_score += 15
        elif density > 3.5: seo_score -= 10
            
        if total_words > 600: seo_score += 15
        elif total_words > 300: seo_score += 10
            
        imgs = soup.find_all('img')
        if imgs: seo_score += 10
            
        seo_score = min(max(seo_score, 0), 100)
        self.add_log(log_placeholder, f"  > 1.1 Chấm điểm SEO (Yoast Engine): {seo_score}/100.")

        sentences = [s.strip() for s in re.split(r'[.!?\n]+', text_content) if len(s.strip().split()) > 3] 
        lengths = [len(s.split()) for s in sentences]
        
        if len(lengths) > 3:
            variance = statistics.stdev(lengths)
            ai_prob = max(5, 50 - (variance * 4)) 
        else: ai_prob = 50
        
        richness = (len(set(text_content.lower().split())) / total_words * 100) if total_words > 0 else 0
        if richness > 40: ai_prob -= 15 
        ai_rate = min(max(round(ai_prob + random.uniform(-3, 3), 1), 2.0), 99.0)
        self.add_log(log_placeholder, f"  > 1.2 Nhận diện AI (Sentence Variance): Tỷ lệ AI = {ai_rate}%.")

        asl = sum(lengths) / len(lengths) if lengths else 0
        readability_score = round(max(10, min(100 - ((asl - 10) * 2.5), 100)), 1)
        self.add_log(log_placeholder, f"  > 1.3 Độ dễ đọc (Vietnamese Formula): Điểm = {readability_score}/100.")

        self.kcs_results = {'SEO': seo_score, 'AI_RATE': ai_rate, 'READABILITY': readability_score, 'WORDS': total_words}
        
        fail_reasons = []
        if seo_score < 40: fail_reasons.append(f"SEO thấp ({seo_score})")
        if ai_rate > 35: fail_reasons.append(f"Văn phong AI lộ ({ai_rate}%)")
        if readability_score < 40: fail_reasons.append(f"Khó đọc ({readability_score})")

        if fail_reasons:
            self.add_log(log_placeholder, f"❌ KCS FAIL: {', '.join(fail_reasons)}. Ghi nhận trạng thái FAIL.")
            return "FAIL: " + " | ".join(fail_reasons)
        else:
            self.add_log(log_placeholder, "✅ KCS PASS: Bài viết đạt chuẩn. Duyệt trạng thái PENDING.")
            return "PENDING"

    def fetch_reference_content(self, log_placeholder):
        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        if not serp_key: return None
        try:
            url = "https://serpapi.com/search"
            res = requests.get(url, params={"q": self.main_kw_text, "hl": "vi", "gl": "vn", "api_key": serp_key}, timeout=10).json()
            target_urls = [r["link"] for r in res.get("organic_results", [])[:5] if "link" in r]
            random.shuffle(target_urls)
            for t_url in target_urls:
                res_html = requests.get(t_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                if res_html.status_code == 200:
                    soup = BeautifulSoup(res_html.text, 'html.parser')
                    for tag in soup(["script", "style", "nav", "footer", "header"]): tag.decompose()
                    content = "\n\n".join([tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'p']) if tag.get_text(strip=True)])
                    if len(content) > 300:
                        self.add_log(log_placeholder, f"COMPETITOR_LIST thành công từ: {t_url}")
                        return content[:6000]
        except: pass
        return None

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
        except: return False

        today_str = self.current_date.strftime('%Y-%m-%d')
        posts_created_today = df_report[df_report['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)] if not df_report.empty and 'REP_CREATED_AT' in df_report.columns else pd.DataFrame()

        if len(posts_created_today) >= batch_size:
            self.add_log(log_placeholder, f"🛑 ĐÃ ĐẠT NGƯỠNG BATCH_SIZE hôm nay ({batch_size} bài). DỪNG!")
            return False
            
        self.add_log(log_placeholder, f"  [✓] Xưởng hôm nay mới tạo {len(posts_created_today)}/{batch_size} bài. Tiến hành bốc Web...")

        available_webs = df_web.sample(frac=1).reset_index(drop=True)
        for _, web in available_webs.iterrows():
            ws_name = str(web.get('WS_NAME', '')).strip()
            ws_limit = self.safe_int(web.get('WS_POST_LIMIT', 1), 1)

            for day_offset in range(max_days + 1):
                day_x = self.current_date.date() + datetime.timedelta(days=day_offset)
                day_x_str = day_x.strftime('%Y-%m-%d')
                
                posts_on_day_x_web = df_report[(df_report['REP_WS_NAME'].astype(str).str.strip() == ws_name) & 
                                               (df_report['REP_PUBLISH_DATE'].astype(str).str.strip().str.startswith(day_x_str))] if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns else pd.DataFrame()

                if len(posts_on_day_x_web) < ws_limit:
                    start_time = datetime.datetime.combine(day_x, datetime.time(start_h, start_m))
                    end_time = datetime.datetime.combine(day_x, datetime.time(end_h, end_m))
                    
                    if day_offset == 0 and self.current_date > end_time: continue 
                    base_time = max(self.current_date, start_time) if day_offset == 0 else start_time
                        
                    if posts_on_day_x_web.empty:
                        pub_time = base_time + datetime.timedelta(minutes=random.randint(0, 30))
                    else:
                        try:
                            max_time = datetime.datetime.strptime(str(posts_on_day_x_web['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M')
                            pub_time = max(max_time, base_time) + datetime.timedelta(minutes=random.randint(min_space, max_space))
                        except: pub_time = base_time + datetime.timedelta(minutes=random.randint(min_space, max_space))
                            
                    if pub_time < self.current_date: pub_time = self.current_date + datetime.timedelta(minutes=random.randint(5, 15))
                    if pub_time > end_time: continue 
                        
                    self.target_web = web
                    self.publish_time = pub_time
                    self.add_log(log_placeholder, f"  [✓] CHỐT SLOT! Khóa mục tiêu Website '{ws_name}' - Lên bài lúc: {pub_time.strftime('%H:%M ngày %d/%m/%Y')}.")
                    return True
        return False

    def run_ai_content_pipeline(self, log_placeholder):
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return None
        
        # Đồng bộ Quota Từ Khóa = Limit Ngoại + Limit Nội
        out_limit = self.safe_int(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        in_limit = self.safe_int(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        total_kws_needed = max(1, out_limit + in_limit)

        main_kw_row = df_kw.sample(n=1).iloc[0]
        self.main_kw_text = str(main_kw_row['KW_TEXT'])
        self.kw_intent = str(main_kw_row.get('KW_INTENT', 'Chia sẻ kiến thức hữu ích, thiết thực.'))
        self.ws_persona = str(self.target_web.get('WS_PERSONA', 'Chuyên gia sâu sắc, hành văn mộc mạc, gần gũi.'))

        content_kws_needed = total_kws_needed - 1
        if content_kws_needed > 0:
            kws_to_sample = min(content_kws_needed, len(df_kw) - 1)
            self.content_kws = df_kw[df_kw['KW_TEXT'] != self.main_kw_text].sample(n=kws_to_sample)['KW_TEXT'].tolist()
        else:
            self.content_kws = []
            
        self.all_used_kws = [self.main_kw_text] + self.content_kws
        self.add_log(log_placeholder, f"REP_KW (Quota = {total_kws_needed}): {', '.join(self.all_used_kws)}")

        word_range_str = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200'))
        self.final_word_count = random.randint(self.safe_int(word_range_str.split('-')[0], 900), self.safe_int(word_range_str.split('-')[-1], 1200))

        ref_content = self.fetch_reference_content(log_placeholder)
        if not ref_content: ref_content = "Không có dữ liệu đối thủ."

        self.add_log(log_placeholder, f"Nạp SUPER PROMPT: Nhập vai '{self.ws_persona}' - Mục tiêu: '{self.kw_intent}'")
        
        prompt = f"""Đóng vai: {self.ws_persona}.
Mục đích bài viết (Intent): {self.kw_intent}.
Chủ đề bài viết: "{self.main_kw_text}". Độ dài tối thiểu: {self.final_word_count} từ.

YÊU CẦU TỐI ƯU SEO (ON-PAGE):
1. Thẻ <h1> (Tiêu đề bài viết): TUYỆT ĐỐI NGẮN GỌN (từ 45 đến tối đa 55 ký tự). Phải chứa từ khóa chính "{self.main_kw_text}". Đánh thẳng vào trọng tâm, không dùng từ thừa.
2. Thẻ <h2>, <h3>: Có ít nhất 1 thẻ <h2> chứa từ khóa chính. Trải đều từ khóa phụ vào H2/H3: {', '.join(self.content_kws)}.
3. Sapo: Chứa từ khóa chính trong 100 từ đầu tiên.

YÊU CẦU VĂN PHONG (HUMAN-TOUCH - Vượt AI Detector):
1. Burstiness (Độ ngắt quãng): Viết đan xen câu cực ngắn (4-6 từ) với câu dài. Tuyệt đối không viết các câu có cấu trúc đều đều nhau.
2. Readability (Dễ đọc): Độ dài trung bình mỗi câu dưới 18 từ. Chia nhỏ đoạn văn (không quá 3-4 câu/đoạn).
3. Đa dạng từ vựng: Tuân thủ tuyệt đối văn phong nhân vật. Không dùng giọng điệu sáo rỗng của AI ("Nhìn chung", "Tóm lại", "Bài viết này sẽ...").

Dữ liệu tham khảo:
{ref_content}

Chỉ trả về mã định dạng HTML (<h1>, <h2>, <p>, <ul>), bắt đầu trực tiếp bằng <h1>."""

        response_text = ""
        or_key = str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',')[0].strip()
        if or_key:
            try:
                self.add_log(log_placeholder, "Đang gọi API OpenRouter...")
                res = requests.post("https://openrouter.ai/api/v1/chat/completions", 
                                    headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                                    json={"model": "anthropic/claude-3.5-sonnet", "messages": [{"role": "user", "content": prompt}]}, 
                                    timeout=120).json()
                response_text = res["choices"][0]["message"]["content"]
            except: pass

        if not response_text:
            gem_key = str(self.dashboard.get('GEMINI_API_KEY', '')).split(',')[0].strip()
            if gem_key:
                try:
                    genai.configure(api_key=gem_key)
                    response_text = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt).text
                except: pass

        raw_html = response_text.replace('```html', '').replace('```', '').strip() if response_text else "<h1>Lỗi tạo bài</h1><p>API Timeout</p>"
        
        # BƯỚC XỬ LÝ MEDIA (CHÈN ẢNH + LINK)
        self.raw_html = self.process_html_media_and_links(raw_html, log_placeholder)
        
        h1_match = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.generated_title = re.sub(r'<[^>]+>', '', h1_match.group(1)).strip() if h1_match else f"Bài viết: {self.main_kw_text}"
        
        final_result = self.run_kcs_validation(log_placeholder, self.raw_html, self.generated_title)
        
        try:
            doc_id = '1dGdj-Oyvm2CS4lKYn8uDnAzPqdYnlGTInxyGLnzhE-8'
            scopes = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
            creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=scopes)
            docs_service = build('docs', 'v1', credentials=creds)
            text_to_insert = f"\n\n{'='*50}\nBÀI VIẾT: {self.generated_title}\nNGÀY TẠO: {self.current_date.strftime('%Y-%m-%d %H:%M:%S')}\n{'='*50}\n\n{self.raw_html}\n\n"
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': [{'insertText': {'endOfSegmentLocation': {'segmentId': ''}, 'text': text_to_insert}}]}).execute()
        except: pass

        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_CREATED_AT': self.current_date.strftime('%Y-%m-%d %H:%M'),
            'REP_TITLE': self.generated_title,
            'REP_IMG_COUNT': str(self.raw_html.count('<img')),
            'REP_KW_1': self.all_used_kws[0],
            'REP_KW_2': self.all_used_kws[1] if len(self.all_used_kws) > 1 else "",
            'REP_KW_3': self.all_used_kws[2] if len(self.all_used_kws) > 2 else "",
            'REP_SEO_SCORE': str(self.kcs_results.get('SEO', 0)),
            'REP_AI_DETECTOR_RATE_20': f"{self.kcs_results.get('AI_RATE', 100)}%",
            'REP_READABILITY_SCORE_60': str(self.kcs_results.get('READABILITY', 0)),
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_RESULT': final_result,
            'REP_LOG': "\n".join(self.history_log),
            'REP_HTML': self.raw_html
        }

    # --- NHỊP 4: LƯU TRỮ VÀ ĐỒNG BỘ ---
    def sync_resources_to_sheet(self, client, log_placeholder):
        try:
            ss = client.open_by_key(SHEET_ID)
            kw_sheet = ss.worksheet('KEYWORD')
            kw_data = kw_sheet.get_all_values()
            time_str = self.current_date.strftime('%Y-%m-%d %H:%M')
            
            if len(kw_data) > 1:
                headers = kw_data[0]
                kw_idx = headers.index('KW_TEXT') if 'KW_TEXT' in headers else -1
                status_idx = headers.index('KW_STATUS') if 'KW_STATUS' in headers else -1
                date_idx = headers.index('KW_DATE') if 'KW_DATE' in headers else -1
                
                updates = []
                for i, row in enumerate(kw_data[1:], start=2): 
                    if kw_idx != -1 and len(row) > kw_idx and str(row[kw_idx]).strip() in self.all_used_kws:
                        if status_idx != -1:
                            curr_status = self.safe_int(row[status_idx] if len(row) > status_idx else 0, 0)
                            updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, status_idx + 1)}', 'values': [[curr_status + 1]]})
                        if date_idx != -1:
                            updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, date_idx + 1)}', 'values': [[time_str]]})
                if updates: kw_sheet.batch_update(updates)
            
            if hasattr(self, 'used_img_urls') and self.used_img_urls:
                img_sheet = ss.worksheet('IMAGE')
                img_data = img_sheet.get_all_values()
                if len(img_data) > 1:
                    headers = img_data[0]
                    url_idx = headers.index('IMG_URL') if 'IMG_URL' in headers else -1
                    status_idx = headers.index('IMG_STATUS') if 'IMG_STATUS' in headers else -1
                    
                    updates = []
                    for i, row in enumerate(img_data[1:], start=2):
                        if url_idx != -1 and len(row) > url_idx and str(row[url_idx]).strip() in self.used_img_urls:
                            if status_idx != -1:
                                curr_status = self.safe_int(row[status_idx] if len(row) > status_idx else 0, 0)
                                updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, status_idx + 1)}', 'values': [[curr_status + 1]]})
                    if updates:
                        img_sheet.batch_update(updates)
                        self.add_log(log_placeholder, f"  > Cập nhật đồng bộ IMG_STATUS thành công cho {len(self.used_img_urls)} ảnh.")
        except: pass

    def step7_save_to_sheet(self, new_data, log_placeholder):
        if not new_data: return
        try:
            creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)
            sheet = client.open_by_key(SHEET_ID).worksheet('REPORT')
            sheet.append_row([str(new_data.get(h, "")) for h in sheet.row_values(1)])
            
            if new_data.get('REP_RESULT') == 'PENDING': self.sync_resources_to_sheet(client, log_placeholder)
            self.add_log(log_placeholder, "HOÀN TẤT - Đã lưu trữ dữ liệu thành công.")
        except Exception as e: self.add_log(log_placeholder, f"Lỗi ghi dữ liệu: {e}")

# ==========================================
# 🖥 GIAO DIỆN WEB ĐIỀU KHIỂN
# ==========================================
if 'is_running' not in st.session_state: st.session_state.is_running = False

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
    posts_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_report.empty and 'REP_CREATED_AT' in df_report.columns else 0
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
            load_data_from_gsheets.clear()
            st.rerun()
    
    if start_btn:
        st.session_state.is_running = True
        st.markdown("---")
        st.markdown("**🖥 Trạng thái tiến trình (Console Log):**")
        log_placeholder = st.empty() 
        
        bot = AutoContentSEO(db_mock)
        if bot.step1_kiem_tra_he_thong(log_placeholder):
            bot.step7_save_to_sheet(bot.run_ai_content_pipeline(log_placeholder), log_placeholder)
        
        st.session_state.is_running = False
        load_data_from_gsheets.clear() 
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
                st.markdown(f'<div class="log-box">{post_data.get("REP_LOG", "").replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            with lc2:
                st.markdown("**🌐 Mã HTML:**")
                st.text_area("Mã HTML", post_data.get('REP_HTML', ''), height=350, label_visibility="collapsed")
    else: st.info("Chưa có bài viết nào.")

with tab3:
    st.subheader("Toàn bộ dữ liệu Tab REPORT gốc")
    if not df_report.empty: st.dataframe(df_report, use_container_width=True)
    else: st.info("Tab REPORT đang trống.")
