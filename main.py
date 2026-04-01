import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time
import datetime
import random
import statistics
import re
import requests
import html
import pytz
import concurrent.futures
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==========================================
# ⚙️ CẤU HÌNH HỆ THỐNG & MÚI GIỜ CHUẨN VN
# ==========================================
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
def get_vn_now(): return datetime.datetime.now(VN_TZ)

st.set_page_config(page_title="Auto SEO Pipeline | Lái Hộ", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .log-box {
        background-color: #0f172a; color: #10b981; font-family: 'Courier New', monospace; font-size: 14px;
        padding: 15px; border-radius: 8px; height: 800px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6;
        word-wrap: break-word;
    }
    .log-error { color: #ef4444; font-weight: bold; }
    .log-warn { color: #f59e0b; }
    .log-success { color: #3b82f6; font-weight: bold; }
    .log-quota { color: #a855f7; font-weight: bold; }
    .log-detail { color: #94a3b8; font-size: 13px; font-style: italic; }
    </style>
    """, unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

# ==========================================
# 🔐 TẦNG BẢO MẬT & ĐĂNG NHẬP
# ==========================================
def check_password():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("## 🔐 System Gateway Authentication")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        if st.button("Access Pipeline"):
            if username == st.secrets.get("admin_user", "admin") and password == st.secrets.get("admin_pass", "admin123"):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("❌ Sai thông tin đăng nhập!")
        return False
    return True

if not check_password(): st.stop()

# ==========================================
# 🛠 HÀM KẾT NỐI GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=60)
def load_data_from_gsheets():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        db = {}
        for tab in ['DASHBOARD', 'WEBSITE', 'KEYWORD', 'IMAGE', 'SPIN', 'REPORT']:
            try:
                ws = spreadsheet.worksheet(tab)
                data = ws.get_all_values()
                if data:
                    headers = data[0]
                    clean_headers, seen = [], set()
                    for i, h in enumerate(headers):
                        val = str(h).strip() or f"COL_{i}"
                        if val in seen: val = f"{val}_{i}"
                        seen.add(val)
                        clean_headers.append(val)
                    db[tab] = pd.DataFrame(data[1:], columns=clean_headers)
                else: db[tab] = pd.DataFrame()
            except: db[tab] = pd.DataFrame()
        return db
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        return None

# ==========================================
# 🚀 HÀM BẮN BÀI LÊN CMS
# ==========================================
def post_to_cms(website_row, title, html_content, dash_config):
    blog_receiver_email = str(website_row.get('WS_BLOG_CONTENT', '')).strip()
    ws_user = str(website_row.get('WS_LOGIN_USER', '')).strip()
    ws_pass = str(website_row.get('WS_LOGIN_PASS', '')).strip()
    
    if "@blogger.com" in blog_receiver_email.lower():
        smtp_email = dash_config.get('EMAIL_SENDER', '').strip()
        smtp_pass = dash_config.get('EMAIL_SENDER_PASSWORD', '').strip()
        if not smtp_email or not smtp_pass:
            return False, f"Thiếu EMAIL_SENDER hoặc EMAIL_SENDER_PASSWORD trong tab DASHBOARD."
        try:
            msg = MIMEMultipart()
            msg['From'] = smtp_email
            msg['To'] = blog_receiver_email
            msg['Subject'] = title
            msg.attach(MIMEText(html_content, 'html'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_pass) 
            server.send_message(msg)
            server.quit()
            return True, f"Đã bắn bài lên Blogspot thành công (Từ: {smtp_email} -> Tới: {blog_receiver_email})"
        except Exception as e:
            return False, f"Lỗi gửi Mail tới Blogger: {e}"
            
    else:
        domain = str(website_row.get('WS_LINK_IN_BACKLINK', '')).split(',')[0].strip()
        if not domain: return False, "Không tìm thấy domain trong cột WS_LINK_IN_BACKLINK để cấu hình API WordPress."
        if not domain.endswith('/'): domain += '/'
        api_url = f"{domain}wp-json/wp/v2/posts"
        data = {'title': title, 'content': html_content, 'status': 'publish'}
        try:
            res = requests.post(api_url, auth=(ws_user, ws_pass), json=data, timeout=30)
            if res.status_code in [200, 201]: return True, f"Đăng WordPress thành công (Post ID: {res.json().get('id')})"
            else: return False, f"Lỗi WP API ({res.status_code}): {res.text[:100]}"
        except Exception as e: return False, f"Lỗi kết nối WP: {e}"

# ==========================================
# 🤖 LÕI ĐỘNG CƠ: AUTO SEO PIPELINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, data_frames, master_log_list):
        self.db = data_frames
        self.dashboard = {str(k).strip(): str(v).strip() for k, v in zip(self.db.get('DASHBOARD', pd.DataFrame())['DATA_KEY'], self.db.get('DASHBOARD', pd.DataFrame())['DATA_CONTENT'])}
        self.now_vn = get_vn_now()
        self.history_log = master_log_list
        
        self.target_web = None
        self.publish_time = None
        self.main_kw_row = None
        self.all_kws = []
        self.target_length = 0
        self.is_short_form = False
        self.serp_style = "Văn phong chuyên gia sâu sắc, logic và thuyết phục."
        self.raw_html = ""
        self.final_title = ""
        self.kcs_metrics = {}
        self.used_imgs = []
        self.used_spins = []
        self.out_lim, self.in_lim = 0, 0
        self.injected_ext, self.injected_int = 0, 0
        
        if 'evolution_cache' not in st.session_state: st.session_state.evolution_cache = ""

    def add_log(self, ui_placeholder, message, level="info"):
        t_str = get_vn_now().strftime('%H:%M:%S')
        fmt_msg = message
        if level == "error": fmt_msg = f'<span class="log-error">{message}</span>'
        elif level == "warn": fmt_msg = f'<span class="log-warn">{message}</span>'
        elif level == "success": fmt_msg = f'<span class="log-success">{message}</span>'
        elif level == "quota": fmt_msg = f'<span class="log-quota">{message}</span>'
        elif level == "detail": fmt_msg = f'<span class="log-detail">{message}</span>'
        
        self.history_log.append(f"[{t_str}] {fmt_msg}")
        if ui_placeholder: 
            log_html = f'<div class="log-box" id="logbox">{"<br>".join(self.history_log)}</div><script>var objDiv = document.getElementById("logbox"); objDiv.scrollTop = objDiv.scrollHeight;</script>'
            ui_placeholder.markdown(log_html, unsafe_allow_html=True)

    def safe_int(self, value, default=0):
        try: return int(str(value).strip())
        except: return default

    def get_min_max(self, val_str, default_min, default_max):
        try:
            s = str(val_str).strip()
            if '-' in s:
                parts = s.split('-')
                val1, val2 = int(parts[0].strip()), int(parts[1].strip())
                return min(val1, val2), max(val1, val2)
            val = int(s)
            return val, val
        except: return default_min, default_max

    def parse_random_range(self, val_str, default=0):
        min_v, max_v = self.get_min_max(val_str, default, default)
        return random.randint(min_v, max_v)

    def pick_random_prompt_variant(self, text):
        parts = [p.strip() for p in re.split(r'\|\|\|', str(text)) if p.strip()]
        return random.choice(parts) if parts else str(text).strip()

    # --- BƯỚC 1: SLOT ---
    def step1_allocate_slot(self, ui_log) -> bool:
        df_rep = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        batch_size = self.parse_random_range(self.dashboard.get('BATCH_SIZE', 10), 10)
        max_days = self.parse_random_range(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        
        try:
            trange = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
            start_h, start_m = map(int, trange[0].strip().split(':'))
            end_h, end_m = map(int, trange[1].strip().split(':'))
            min_s, max_s = self.get_min_max(self.dashboard.get('POST_SPACING_MINUTES', '30-90'), 30, 90)
        except:
            self.add_log(ui_log, "🛑 [LỖI CONFIG] Khung giờ sai format.", "error")
            return False

        today_str = self.now_vn.strftime('%Y-%m-%d')
        posts_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else 0
        if posts_today >= batch_size: return False

        avail_webs = df_web.sample(frac=1).reset_index(drop=True)
        for d_off in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=d_off)
            day_x_str = day_x.strftime('%Y-%m-%d')
            for _, web in avail_webs.iterrows():
                ws_name = str(web.get('WS_NAME', '')).strip()
                ws_limit = self.parse_random_range(web.get('WS_POST_LIMIT', 1), 1)
                posts_day_x = df_rep[(df_rep['REP_WS_NAME'].astype(str).str.strip() == ws_name) & (df_rep['REP_PUBLISH_DATE'].astype(str).str.strip().str.startswith(day_x_str))] if not df_rep.empty and 'REP_PUBLISH_DATE' in df_rep.columns else pd.DataFrame()
                
                self.add_log(ui_log, f"🔍 [QUOTA] Global: {posts_today}/{batch_size} | Local '{ws_name}' ({day_x_str}): {len(posts_day_x)}/{ws_limit}", "quota")
                if len(posts_day_x) < ws_limit:
                    st_vn = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(start_h, start_m)))
                    ed_vn = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(end_h, end_m)))
                    if d_off == 0 and self.now_vn > ed_vn: continue 
                    base_t = max(self.now_vn, st_vn) if d_off == 0 else st_vn
                    
                    if posts_day_x.empty: pub_t = base_t + datetime.timedelta(minutes=random.randint(0, 30))
                    else:
                        try:
                            max_t = VN_TZ.localize(datetime.datetime.strptime(str(posts_day_x['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M'))
                            pub_t = max(max_t, base_t) + datetime.timedelta(minutes=random.randint(min_s, max_s))
                        except: pub_t = base_t + datetime.timedelta(minutes=random.randint(min_s, max_s))
                    
                    if pub_t < self.now_vn: pub_t = self.now_vn + datetime.timedelta(minutes=5)
                    if pub_t > ed_vn: continue 
                    
                    self.target_web = web
                    self.publish_time = pub_t
                    self.add_log(ui_log, f"✅ [CHỐT SLOT] {ws_name} | Lên lịch: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
        self.add_log(ui_log, "🛑 Đã full lịch.", "error")
        return False

    # --- BƯỚC 2 & 3: TỪ KHÓA & SERP ---
    def step2_3_keyword_and_serp(self, ui_log) -> bool:
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        df_sorted = df_kw.sample(frac=1).sort_values('KW_STATUS')
        self.main_kw_row = df_sorted.iloc[0]
        main_kw = str(self.main_kw_row['KW_TEXT']).strip()
        main_cat = str(self.main_kw_row.get('KW_CONTENT', '')).strip()
        main_grp = str(self.main_kw_row.get('KW_GROUP', '')).strip()
        
        self.out_lim = self.parse_random_range(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        self.in_lim = self.parse_random_range(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        total_links = self.out_lim + self.in_lim
        
        kws_needed = max(1, total_links)
        subs_needed = max(0, kws_needed - 1)
        
        self.add_log(ui_log, f"📐 [QUOTA TỪ KHÓA] Cần nhét {self.out_lim} Ngoại + {self.in_lim} Nội = {total_links} Links. (Bốc 1 Chính + {subs_needed} Phụ).", "quota")
        
        sub_df = df_sorted[(df_sorted['KW_TEXT'] != main_kw) & (df_sorted['KW_CONTENT'].astype(str).str.strip() == main_cat) & (df_sorted['KW_GROUP'].astype(str).str.strip() != main_grp)]
        subs = sub_df.head(subs_needed)['KW_TEXT'].tolist() if not sub_df.empty else []
        self.all_kws = [main_kw] + subs
        self.add_log(ui_log, f"📦 [TỪ KHÓA ĐÃ GOM] {len(self.all_kws)} KWs: {', '.join(self.all_kws)}")

        min_w, max_w = self.get_min_max(self.dashboard.get('WORD_COUNT_RANGE', '900-1200'), 900, 1200)
        if len(self.all_kws) < 3: self.is_short_form, self.target_length = True, random.randint(min_w, max_w) // 2
        else: self.target_length = random.randint(min_w, max_w)
        
        self.add_log(ui_log, f"📏 [RULE BÀI] Cần viết: ~{self.target_length} chữ.")

        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        comp_list = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        
        serp_success = False
        if serp_key:
            try:
                res = requests.get("https://serpapi.com/search", params={"q": main_kw, "hl": "vi", "gl": "vn", "api_key": serp_key}, timeout=15).json()
                org_results = res.get("organic_results", [])
                
                comp_links = [r["link"] for r in org_results[:10] if comp_list and any(c in r.get("link","") for c in comp_list)]
                target_link = comp_links[0] if comp_links else (org_results[0]["link"] if org_results else None)
                
                if target_link:
                    r_html = requests.get(target_link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    if r_html.status_code == 200:
                        soup = BeautifulSoup(r_html.text, 'html.parser')
                        for tag in soup(["script", "style", "nav", "footer"]): tag.decompose()
                        self.serp_style = "\n\n".join([tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'p'])])[:3000]
                        self.add_log(ui_log, f"✅ [SERP] Trích xuất văn phong thành công từ: {target_link}")
                        serp_success = True
            except: pass
        if not serp_success: self.add_log(ui_log, f"🕵️ [SERP] Dùng Internal Cache.")
        return True

    # --- BƯỚC 4: GỌI AI & HIỂN THỊ LOG PROMPT CHI TIẾT ---
    def step4_llm_generation(self, ui_log) -> bool:
        req_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        prompts = {k: self.pick_random_prompt_variant(self.dashboard.get(k, '')) for k in req_keys}
        if any(not v for v in prompts.values()):
            self.add_log(ui_log, "🛑 Tab DASHBOARD trống ô PROMPT.", "error")
            return False

        ws_per = str(self.target_web.get('WS_PERSONA', ''))
        kw_int = str(self.main_kw_row.get('KW_INTENT', ''))
        main_kw = self.all_kws[0]
        subs = ", ".join(self.all_kws[1:])
        dist = self.target_length // max(len(self.all_kws), 1)

        # BUNG LẠI LOG PROMPT THEO YÊU CẦU SẾP
        self.add_log(ui_log, f"🧠 [PROMPT BUILDER] Đang rắp ráp lệnh từ 6 Keys trong DASHBOARD:", "detail")
        self.add_log(ui_log, f"   + PROMPT_TEMPLATE: Sườn bài viết cơ bản.", "detail")
        self.add_log(ui_log, f"   + PROMPT_CONTENT_STRATEGY: Định hướng nội dung.", "detail")
        self.add_log(ui_log, f"   + PROMPT_KEYWORD_SEARCH: Quy tắc rải từ khóa.", "detail")
        self.add_log(ui_log, f"   + PROMPT_SERP_STYLE: Giả lập văn phong.", "detail")
        self.add_log(ui_log, f"   + PROMPT_SEO_GLOBAL_RULE: Luật SEO chống Spam (Ép H1, Đánh số H3).", "detail")
        self.add_log(ui_log, f"   + PROMPT_AI_HUMANIZER: Khử văn phong máy móc.", "detail")

        force_kw = f"""
        \n[LỆNH ÉP TỐI THƯỢNG - BẮT BUỘC TUÂN THỦ 100%]:
        1. CẤM TUYỆT ĐỐI các từ ngữ chào hỏi ở đầu bài: "Kính thưa các Sếp", "Chào quý vị", "Thân gửi", "Tuyệt vời". VÀO THẲNG VẤN ĐỀ BẰNG Sapo.
        2. TIÊU ĐỀ (THẺ H1): Bắt buộc chứa cụm từ "{main_kw}". Nằm NGẪU NHIÊN ở GIỮA hoặc CUỐI tiêu đề.
        3. TỪ KHÓA TRONG BÀI:
        - Từ khóa chính: "{main_kw}" (rải tự nhiên 2-3 lần)
        - Từ khóa phụ: "{subs}" (Mỗi từ xuất hiện đúng 1 lần, rải đều). Tuyệt đối không dùng dấu in đậm `**` cho các từ khóa này.
        4. CẤU TRÚC SEO H3: Nếu có chia các đề mục nhỏ (thẻ <h3>) nằm dưới thẻ <h2>, BẮT BUỘC phải đánh số thứ tự (ví dụ: 1., 2., 3.,...) cho các thẻ <h3> đó.
        5. ĐA DẠNG ĐOẠN VĂN: Cấm viết các đoạn dài bằng nhau. Phải đan xen đoạn rất ngắn và đoạn phân tích dài.
        6. TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>.
        """
        
        master_prompt_raw = f"{prompts['PROMPT_TEMPLATE']}\n{prompts['PROMPT_CONTENT_STRATEGY']}\n{prompts['PROMPT_KEYWORD_SEARCH']}\n{prompts['PROMPT_SERP_STYLE']}\n[Dữ liệu SERP]:\n{self.serp_style}\n{prompts['PROMPT_SEO_GLOBAL_RULE']}\n{prompts['PROMPT_AI_HUMANIZER']}"
        master_prompt_raw = master_prompt_raw.replace('{{ws_persona}}', ws_per).replace('{{kw_intent}}', kw_int).replace('{{keyword}}', main_kw).replace('{{word_count}}', str(self.target_length))
        
        for i, kw in enumerate(self.all_kws):
            master_prompt_raw = re.sub(rf'\[?REP_KW_{i+1}\]?', kw, master_prompt_raw, flags=re.IGNORECASE)
        
        mut = f"\n[Tiến Hóa]: Cấm lặp cấu trúc: {st.session_state.evolution_cache}." if st.session_state.evolution_cache else ""
        master_prompt = f"{master_prompt_raw}{mut}\n{force_kw}"

        gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        or_keys = [k.strip() for k in str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',') if k.strip()]
        gem_models = [m.strip() for m in str(self.dashboard.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        or_models = [m.strip() for m in str(self.dashboard.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini')).split(',') if m.strip()]

        response = None
        for gk in gem_keys:
            genai.configure(api_key=gk)
            for gm in gem_models:
                if response: break
                self.add_log(ui_log, f"🌐 [API CALL] Gemini ({gm})...")
                try:
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        response = ex.submit(lambda: genai.GenerativeModel(gm).generate_content(master_prompt).text).result(timeout=90)
                # ĐÃ FIX LOG API FALLBACK CHUẨN XÁC
                except Exception as e: self.add_log(ui_log, f"⚠️ Gemini sập (429/503). Hệ thống tự động chuyển sang API Key/Model dự phòng để thử lại...", "warn")

        if not response:
            for ok in or_keys:
                for om in or_models:
                    if response: break
                    self.add_log(ui_log, f"🌐 [API CALL] OpenRouter ({om})...")
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            def call_or():
                                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {ok}"}, json={"model": om, "messages": [{"role": "user", "content": master_prompt}]}, timeout=90)
                                res.raise_for_status()
                                return res.json()["choices"][0]["message"]["content"]
                            response = ex.submit(call_or).result(timeout=90)
                    except Exception as e: self.add_log(ui_log, f"🛑 OpenRouter sập: {str(e)[:80]}", "error")

        if not response:
            self.add_log(ui_log, "🛑 [FATAL] Toàn bộ API sập.", "error")
            return False
            
        self.raw_html = response.replace('```html', '').replace('```', '').strip()
        
        # Tẩy sạch dấu in đậm Markdown do AI đẻ ra để không làm nhiễu lúc cắm Link
        self.raw_html = re.sub(r'\*\*(.*?)\*\*', r'\1', self.raw_html)
        
        # Dịch ngược mã thành chữ thật
        for i, kw in enumerate(self.all_kws):
            self.raw_html = re.sub(rf'\[?REP_KW_{i+1}\]?', kw, self.raw_html, flags=re.IGNORECASE)
            if i == 0: self.raw_html = re.sub(r'\{\{keyword\}\}', kw, self.raw_html, flags=re.IGNORECASE)

        # XÓA TẬN GỐC TẤT CẢ MÃ REP_KW RÁC CÒN SÓT LẠI DO AI BỊ ẢO GIÁC
        self.raw_html = re.sub(r'\[?REP_KW_\d+\]?', '', self.raw_html, flags=re.IGNORECASE
