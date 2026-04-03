import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time, datetime, random, statistics, re, requests, html, pytz, gc, unicodedata
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import concurrent.futures

# ==========================================
# ⚙️ CẤU HÌNH HỆ THỐNG & CSS NÂNG CAO
# ==========================================
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
def get_vn_now(): return datetime.datetime.now(VN_TZ)

st.set_page_config(page_title="Auto SEO Pipeline | Lái Hộ Master", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    .log-box {background-color: #0f172a; color: #10b981; font-family: monospace; font-size: 14px; padding: 15px; border-radius: 8px; height: 800px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6; word-wrap: break-word;} 
    .log-error {color: #ef4444; font-weight: bold;} 
    .log-warn {color: #f59e0b;} 
    .log-success {color: #3b82f6; font-weight: bold;} 
    .log-quota {color: #a855f7; font-weight: bold;} 
    .log-detail {color: #94a3b8; font-size: 13px; font-style: italic;}
    
    .alert-processing {
        animation: blinker 1.5s linear infinite;
        color: #b91c1c; font-weight: bold; font-size: 18px; 
        padding: 12px 15px; background: #fee2e2; border-radius: 8px; border: 2px solid #ef4444;
        text-align: center; margin-bottom: 0px; height: 100%; display: flex; align-items: center; justify-content: center;
    }
    @keyframes blinker { 50% { opacity: 0.4; } }
    
    .alert-done {
        color: #15803d; font-weight: bold; font-size: 20px; 
        padding: 12px 15px; background: #dcfce7; border-radius: 8px; border: 2px solid #22c55e;
        text-align: center; margin-bottom: 0px; height: 100%; display: flex; align-items: center; justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

def check_password():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("## 🔐 Hệ thống Tự động hóa SEO Lái Hộ")
        u = st.text_input("Username", key="username")
        p = st.text_input("Password", type="password", key="password")
        if st.button("Đăng Nhập"):
            if u == st.secrets.get("admin_user", "admin") and p == st.secrets.get("admin_pass", "admin123"):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("❌ Sai thông tin đăng nhập!")
        return False
    return True

if not check_password(): st.stop()

@st.cache_data(ttl=60, show_spinner="Đang nạp dữ liệu lõi...")
def load_data_from_gsheets():
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        ss = gspread.authorize(creds).open_by_key(SHEET_ID)
        db = {}
        for tab in ['DASHBOARD', 'WEBSITE', 'KEYWORD', 'IMAGE', 'SPIN', 'REPORT']:
            ws = ss.worksheet(tab)
            data = ws.get_all_values()
            if data: db[tab] = pd.DataFrame(data[1:], columns=[str(h).strip() for h in data[0]])
            else: db[tab] = pd.DataFrame()
        return db
    except: return None

def post_to_cms(website_row, title, html_content, dash_config):
    blog_receiver = str(website_row.get('WS_BLOG_CONTENT', '')).strip()
    u, p = str(website_row.get('WS_LOGIN_USER', '')).strip(), str(website_row.get('WS_LOGIN_PASS', '')).strip()
    if "@blogger.com" in blog_receiver.lower():
        s_mail, s_pass = dash_config.get('EMAIL_SENDER', '').strip(), dash_config.get('EMAIL_SENDER_PASSWORD', '').strip()
        if not s_mail or not s_pass: return False, "Thiếu EMAIL_SENDER/PASS."
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = s_mail, blog_receiver, title
            msg.attach(MIMEText(html_content, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(s_mail, s_pass); server.send_message(msg); server.quit()
            return True, f"Bắn Blogspot OK: {blog_receiver}"
        except Exception as e: return False, f"Lỗi Mail: {e}"
    else:
        domain = str(website_row.get('WS_LINK_IN_BACKLINK', '')).split(',')[0].strip()
        if not domain: return False, "Thiếu domain WP."
        try:
            res = requests.post(f"{domain.rstrip('/')}/wp-json/wp/v2/posts", auth=(u, p), json={'title': title, 'content': html_content, 'status': 'publish'}, timeout=30)
            if res.status_code in [200, 201]: return True, f"Đăng WP OK (ID: {res.json().get('id')})"
            return False, f"Lỗi WP API: {res.text[:100]}"
        except Exception as e: return False, f"Lỗi WP: {e}"

def send_telegram_noti(dash_config, msg_text):
    token = dash_config.get('TELEGRAM_BOT_TOKEN', '').strip()
    chat_id = dash_config.get('TELEGRAM_CHAT_ID', '').strip()
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": msg_text, "parse_mode": "HTML"}, timeout=5)
        except: pass

def remove_vn_accents(input_str):
    s1 = unicodedata.normalize('NFD', str(input_str))
    return re.sub(r'[\u0300-\u036f]', '', s1).replace('đ', 'd').replace('Đ', 'D')

# ==========================================
# 🤖 CORE ENGINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, data_frames, master_log_list):
        self.db = data_frames
        self.dashboard = {str(k).strip(): str(v).strip() for k, v in zip(self.db['DASHBOARD']['DATA_KEY'], self.db['DASHBOARD']['DATA_CONTENT'])}
        self.now_vn, self.history_log = get_vn_now(), master_log_list
        self.target_web, self.publish_time, self.main_kw_row = None, None, None
        self.raw_html, self.final_title = "", ""
        self.previous_draft = "" 
        self.kcs_metrics, self.used_imgs, self.used_spins, self.failed_imgs = {}, [], [], []
        self.out_lim, self.in_lim, self.injected_ext, self.injected_int = 0, 0, 0, 0
        self.serp_style, self.prompt_content = "", ""
        
        self.min_w, self.mid_w, self.max_w = 0, 0, 0
        self.target_wc = 0
        
        self.retry_count = 0
        self.last_word_count = 0
        self.all_topic_kws = []
        self.injected_kws_list = []
        
        self.copyscape_user = self.dashboard.get('COPYSCAPE_USERNAME', '').strip()
        self.copyscape_key = self.dashboard.get('COPYSCAPE_API_KEY', '').strip()

    def reset_state_for_retry(self):
        self.previous_draft = self.raw_html 
        self.raw_html, self.final_title = "", ""
        self.used_imgs, self.used_spins, self.failed_imgs = [], [], []
        self.injected_ext, self.injected_int = 0, 0
        self.injected_kws_list = []
        self.kcs_metrics = {}

    def safe_int(self, value, default=0):
        try: return int(str(value).strip())
        except: return default

    def add_log(self, ui_placeholder, message, level="info"):
        t_str = get_vn_now().strftime('%H:%M:%S')
        fmt_msg = f'<span class="log-{level}">{message}</span>' if level != "info" else message
        self.history_log.append(f"[{t_str}] {fmt_msg}")
        if ui_placeholder: 
            ui_placeholder.markdown(f'<div class="log-box" id="logbox">{"<br>".join(self.history_log)}</div><script>var objDiv = document.getElementById("logbox"); objDiv.scrollTop = objDiv.scrollHeight;</script>', unsafe_allow_html=True)

    def parse_rng(self, val_str, d=0):
        try:
            s = str(val_str).strip()
            if '-' in s: return random.randint(min(int(s.split('-')[0]), int(s.split('-')[1])), max(int(s.split('-')[0]), int(s.split('-')[1])))
            return int(s)
        except: return d

    def pick_random_prompt_variant(self, text):
        """
        Hàm cốt lõi đọc Ma Trận Prompt.
        Nếu nhận diện được danh sách đánh số (1. 2. 3.), sẽ cắt và bốc random 1 lựa chọn.
        Nếu không, trả về nguyên khối (Luật thép tĩnh).
        """
        raw_text = str(text).strip()
        if not raw_text: return ""
        
        # Nếu có dấu ||| (Cấu trúc cũ)
        if '|||' in raw_text:
            parts = [p.strip() for p in raw_text.split('|||') if p.strip()]
            return random.choice(parts)
            
        # Nếu có dạng danh sách đánh số (Ma trận mới của Sếp)
        if re.search(r'(?m)^\d+[\.\-\)]\s+', raw_text):
            variants = []
            for line in raw_text.split('\n'):
                line = line.strip()
                if line and re.match(r'^\d+[\.\-\)]\s+', line):
                    cleaned_line = re.sub(r'^\d+[\.\-\)]\s+', '', line).strip()
                    variants.append(cleaned_line)
            if variants:
                return random.choice(variants)
                
        # Trả về nguyên khối nếu không có cấu trúc random
        return raw_text

    def step1_allocate_slot(self, ui_log) -> bool:
        df_rep, df_web = self.db.get('REPORT', pd.DataFrame()), self.db.get('WEBSITE', pd.DataFrame())
        batch, max_days = self.parse_rng(self.dashboard.get('BATCH_SIZE', 10), 10), self.parse_rng(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        today_str = self.now_vn.strftime('%Y-%m-%d')
        
        today_all_posts = df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(today_str)] if not df_rep.empty else pd.DataFrame()
        posts_today = len(today_all_posts[today_all_posts['REP_RESULT'].astype(str).str.strip() != 'FAIL']) if not today_all_posts.empty else 0
        
        self.add_log(ui_log, f"🔍 [CHECK QUOTA] Global hôm nay: {posts_today}/{batch} (Không tính bài FAIL)", "quota")
        if posts_today >= batch: return False

        avail_webs = df_web.sample(frac=1).reset_index(drop=True)
        for d_off in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=d_off)
            day_x_str = day_x.strftime('%Y-%m-%d')
            for _, web in avail_webs.iterrows():
                ws_name, ws_limit = str(web.get('WS_NAME', '')).strip(), self.parse_rng(web.get('WS_POST_LIMIT', 1), 1)
                
                day_posts = df_rep[(df_rep['REP_WS_NAME'] == ws_name) & (df_rep['REP_PUBLISH_DATE'].astype(str).str.startswith(day_x_str)) & (df_rep['REP_RESULT'].astype(str).str.strip() != 'FAIL')] if not df_rep.empty else pd.DataFrame()
                
                self.add_log(ui_log, f"🔍 [CHECK QUOTA] Local '{ws_name}' ({day_x_str}): {len(day_posts)}/{ws_limit}", "quota")
                if len(day_posts) < ws_limit:
                    try:
                        trange = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
                        st_v = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(int(trange[0].split(':')[0]), int(trange[0].split(':')[1]))))
                        ed_v = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(int(trange[1].split(':')[0]), int(trange[1].split(':')[1]))))
                    except: return self.add_log(ui_log, "🛑 Lỗi AUTO_RUN_TIME format.", "error") or False
                    
                    if d_off == 0 and self.now_vn > ed_v: continue 
                    base = max(self.now_vn, st_v)
                    try: last_t = VN_TZ.localize(datetime.datetime.strptime(str(day_posts['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M'))
                    except: last_t = base
                    
                    pub_t = max(last_t, base) + datetime.timedelta(minutes=self.parse_rng(self.dashboard.get('POST_SPACING_MINUTES', '30-90'), 30))
                    if pub_t > ed_v: continue 
                    self.target_web, self.publish_time = web, pub_t
                    self.add_log(ui_log, f"✅ [CHỐT SLOT] {ws_name} | Lịch: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
        return False

    def step2_3_keyword_and_serp(self, ui_log) -> bool:
        df_kw = self.db['KEYWORD'].dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(0)
        self.main_kw_row = df_kw.sample(frac=1).sort_values('KW_STATUS').iloc[0]
        m_kw = str(self.main_kw_row['KW_TEXT']).strip()
        
        self.out_lim, self.in_lim = self.parse_rng(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0), self.parse_rng(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        
        # Bốc ngẫu nhiên thêm 3-5 keyword phụ cùng nhóm
        pool_subs = df_kw[(df_kw['KW_TEXT'] != m_kw) & (df_kw['KW_CONTENT'] == str(self.main_kw_row.get('KW_CONTENT', '')))].copy()
        if not pool_subs.empty:
            pool_subs = pool_subs.sample(frac=1).sort_values('KW_STATUS')
            subs = pool_subs['KW_TEXT'].tolist()
        else:
            subs = []
            
        kws_needed = max(3, self.out_lim + self.in_lim + 1)
        self.all_topic_kws = [m_kw] + subs[:kws_needed]
        
        self.add_log(ui_log, f"📦 [KWs ĐIỀU HƯỚNG AI] Tập hợp {len(self.all_topic_kws)} Keywords: {', '.join(self.all_topic_kws)}", "detail")
        
        try:
            wrng_str = str(self.dashboard.get('WORD_COUNT_RANGE', '1000-1200|1500')).strip()
            if '|' in wrng_str:
                base_rng, max_val = wrng_str.split('|')
                base_min = int(base_rng.split('-')[0])
                base_max = int(base_rng.split('-')[1])
                self.min_w = random.randint(base_min, base_max)
                self.mid_w = base_max
                self.max_w = int(max_val)
            else:
                base_min = int(wrng_str.split('-')[0])
                base_max = int(wrng_str.split('-')[1])
                self.min_w = random.randint(base_min, base_max)
                self.mid_w = base_max
                self.max_w = int(self.mid_w * 1.3)
        except:
            self.min_w = random.randint(1000, 1200)
            self.mid_w, self.max_w = 1200, 1500
            
        self.target_wc = random.randint(self.min_w, self.mid_w)
        self.add_log(ui_log, f"📏 [RULE TOÁN HỌC] Khóa mục tiêu độ dài: {self.target_wc} chữ. (Min: {self.min_w}, Max: {self.max_w})", "detail")
        
        s_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        c_list = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        serp_chunks, scraped_urls = [], []

        if s_key:
            self.add_log(ui_log, f"🕵️ [SERP] Quét data qua Serper.dev...", "detail")
            # Quét Top 2 Keywords
            for kw in self.all_topic_kws[:2]:
                try:
                    headers = {'X-API-KEY': s_key, 'Content-Type': 'application/json'}
                    payload = {"q": kw, "gl": "vn", "hl": "vi"}
                    res = requests.post("https://google.serper.dev/search", headers=headers, json=payload, timeout=15)
                    if res.status_code == 200:
                        orgs = res.json().get('organic', [])
                        urls = [item['link'] for item in orgs if 'link' in item]
                        
                        t_link = None
                        if c_list:
                            clinks = [u for u in urls if any(c in u for c in c_list)]
                            if clinks: t_link = clinks[0]
                        if not t_link and urls: t_link = random.choice(urls[:3])
                            
                        if t_link:
                            rh = requests.get(t_link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                            if rh.status_code == 200:
                                soup = BeautifulSoup(rh.text, 'html.parser')
                                for t in soup(["script", "style", "nav", "footer", "header"]): t.decompose()
                                ext = "\n".join([t.get_text(strip=True) for t in soup.find_all(['h2', 'h3', 'p'])])[:1000]
                                if ext: 
                                    serp_chunks.append(f"--- Data cho '{kw}' ---\n{ext}")
                                    scraped_urls.append(t_link)
                    else:
                        self.add_log(ui_log, f"⚠️ Lỗi Serper API: {res.text[:100]}", "warn")
                except Exception as e:
                    self.add_log(ui_log, f"⚠️ Lỗi kết nối Serper: {e}", "warn")
            
            if serp_chunks:
                raw_serp_text = "\n\n".join(serp_chunks)[:3000]
                unique_urls = list(set(scraped_urls))
                url_list_str = "\n".join([f"   + {u}" for u in unique_urls])
                self.add_log(ui_log, f"✅ [SERP] Cào data từ {len(unique_urls)} URL:\n{url_list_str}", "success")
                
                gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
                if gem_keys:
                    try:
                        genai.configure(api_key=gem_keys[0])
                        prompt_style = f"Phân tích ngắn gọn thuật ngữ ngành, góc nhìn và nhịp điệu của các đối thủ sau:\n\nData:\n{raw_serp_text}"
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            self.serp_style = ex.submit(lambda: genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt_style).text).result(timeout=15)
                    except: self.serp_style = "Văn phong chuyên gia, logic, chia sẻ kiến thức."
                else: self.serp_style = "Văn phong chuyên gia, logic, chia sẻ kiến thức."
                self.add_log(ui_log, f"🎯 [SERP_STYLE_AI_EXTRACT]:\n{self.serp_style}", "detail")
            else:
                self.serp_style = "Văn phong chuyên gia, logic."
                self.add_log(ui_log, f"⚠️ [SERP] Cào thất bại, dùng Internal Cache.", "warn")
        else: self.serp_style = "Văn phong chuyên gia."
        return True

    def step4_llm_generation(self, ui_log) -> bool:
        # Lấy các biến từ Dashboard và Lọc qua Ma trận Xổ Số
        p_template = self.pick_random_prompt_variant(self.dashboard.get('PROMPT_TEMPLATE', ''))
        p_strategy = self.pick_random_prompt_variant(self.dashboard.get('PROMPT_CONTENT_STRATEGY', ''))
        p_humanizer = self.pick_random_prompt_variant(self.dashboard.get('PROMPT_AI_HUMANIZER', ''))
        p_end = self.pick_random_prompt_variant(self.dashboard.get('PROMPT_END', ''))
        
        # Các biến Luật Thép (Lấy full)
        p_serp_rule = str(self.dashboard.get('PROMPT_SERP_STYLE', '')).strip()
        p_kw_rule = str(self.dashboard.get('PROMPT_KEYWORD_SEARCH', '')).strip()
        p_seo_global = str(self.dashboard.get('PROMPT_SEO_GLOBAL_RULE', '')).strip()

        # Log Ma Trận để Sếp theo dõi
        self.add_log(ui_log, f"🎲 [MA TRẬN XỔ SỐ TẦNG 1] Persona: {p_template[:60]}...", "detail")
        self.add_log(ui_log, f"🎲 [MA TRẬN XỔ SỐ TẦNG 2] Strategy: {p_strategy[:60]}...", "detail")
        self.add_log(ui_log, f"🎲 [MA TRẬN XỔ SỐ TẦNG 3] Humanizer: {p_humanizer[:60]}...", "detail")
        self.add_log(ui_log, f"🎲 [MA TRẬN XỔ SỐ TẦNG 4] End-Module: {p_end[:60]}...", "detail")
        
        m_kw_str = self.all_topic_kws[0]
        kws_injection_str = ", ".join([f"'{k}'" for k in self.all_topic_kws])

        # -------------------------------------------------------------
        # THUẬT TOÁN ĐẾM CHỮ & PHÂN BỔ CẤU TRÚC (KHUNG XƯƠNG THÉP PYTHON)
        # -------------------------------------------------------------
        # 1. Tính toán số thẻ H2 dựa trên Target Word Count
        num_h2 = max(3, self.target_wc // 300) # Trung bình 300 chữ / 1 H2
        if num_h2 > 7: num_h2 = 7 # Tránh bài quá loãng
        
        # 2. Tính toán lượng Text đổ vào mỗi H2
        words_per_h2 = max(200, (self.target_wc - 200) // num_h2) # Trừ 200 chữ cho Mở/Kết bài
        
        # 3. Yêu cầu H3 ngẫu nhiên (chỉ ép ở một số H2 để cấu trúc lồi lõm tự nhiên)
        h3_instruction = f"TẠI ĐÚNG 2 THẺ H2 BẤT KỲ TRONG BÀI, bạn bắt buộc phải chia nhỏ nội dung xuống thành 2-3 thẻ <h3>. Các thẻ H2 còn lại chỉ dùng thẻ <p> hoặc <ul>."
        
        math_skeleton = f"""
        [BỘ LỆNH TOÁN HỌC ĐIỀU KHIỂN CẤU TRÚC - BẮT BUỘC TUÂN THỦ 100%]:
        1. TARGET WORD COUNT: Toàn bộ bài viết của bạn phải dài từ {self.target_wc} đến {self.max_w} chữ. Bất cứ bài viết nào ngắn hơn sẽ bị hệ thống từ chối.
        2. QUY LẬT HEADING 2: Xây dựng chính xác {num_h2} thẻ <h2> (Không tính H1).
        3. QUY LUẬT ĐỔ TEXT: Dưới MỖI một thẻ <h2>, BẮT BUỘC phải xả một lượng kiến thức sâu sắc, chi tiết, đảm bảo độ dài phần chữ dao động từ {words_per_h2} đến {words_per_h2 + 50} chữ. KHÔNG ĐƯỢC VIẾT NGẮN HƠN MỨC NÀY cho mỗi H2.
        4. QUY LUẬT HEADING 3: {h3_instruction}
        """

        retry_cmd = ""
        draft_injection = ""
        if self.retry_count > 0:
            if self.last_word_count < self.min_w:
                retry_cmd = f"\n[LỆNH BƠM OXY TỐI QUAN TRỌNG]: Bản nháp trước của bạn QUÁ NGẮN (Chỉ có {self.last_word_count} chữ, thấp hơn mức tối thiểu {self.min_w}). BẠN PHẢI GIỮ NGUYÊN CÁC Ý CHÍNH CỦA BẢN NHÁP CŨ, NHƯNG BẮT BUỘC PHẢI BỊA THÊM VÍ DỤ THỰC TẾ, ĐẮP THÊM CHI TIẾT PHÂN TÍCH VÀO TỪNG CÁI H2 ĐỂ BÀI VIẾT PHÌNH RA THÀNH {self.target_wc} CHỮ."
                if self.previous_draft:
                    draft_injection = f"\n\n--- BẢN NHÁP CŨ CỦA BẠN (HÃY LẤY LÀM NỀN MÓNG VÀ KÉO DÀI NÓ RA) ---\n{self.previous_draft[:5000]}\n--- KẾT THÚC BẢN NHÁP CŨ ---"
            elif self.last_word_count > self.max_w:
                retry_cmd = f"\n[LỆNH TỐI QUAN TRỌNG]: Bản nháp trước của bạn QUÁ DÀI ({self.last_word_count} chữ). Rút gọn lại tối đa {self.max_w} chữ nhưng giữ cấu trúc H2."
            
        force = f"""\n[TỔNG HỢP YÊU CẦU SINH TỬ]:{retry_cmd}
        {math_skeleton}
        - Chủ đề chính: "{m_kw_str}".
        - TỪ KHÓA BẮT BUỘC PHẢI RẢI ĐỀU: {kws_injection_str}. 
        - MODULE ĐẶC BIỆT Ở CUỐI BÀI: Để kết thúc mã HTML của bài viết, BẮT BUỘC phải tạo nội dung sau: {p_end.upper()}.
        - TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>, KẾT THÚC LÀ MÃ ĐÓNG MODULE ĐẶC BIỆT ĐÃ NÊU TRÊN.{draft_injection}"""
        
        m_prompt = f"{p_template}\n\n{p_strategy}\n\n{p_serp_rule}\n[SERP_DATA]: {self.serp_style}\n\n{p_kw_rule}\n\n{p_seo_global}\n\n{p_humanizer}\n\n{force}"

        gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        gem_mods = [m.strip() for m in str(self.dashboard.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        or_keys = [k.strip() for k in str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',') if k.strip()]
        or_mods = [m.strip() for m in str(self.dashboard.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini')).split(',') if m.strip()]

        response_text = None
        for gm in gem_mods:
            for gk in gem_keys:
                if response_text: break
                genai.configure(api_key=gk)
                self.add_log(ui_log, f"🌐 [API CALL] Gemini ({gm}) [Max: 8192 Tokens]...", "detail")
                try:
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        response_text = ex.submit(lambda: genai.GenerativeModel(gm).generate_content(m_prompt, generation_config=genai.types.GenerationConfig(max_output_tokens=8192)).text).result(timeout=120)
                except Exception as e:
                    self.add_log(ui_log, f"⚠️ Gemini sập (429/Timeout). Đang chuyển...", "warn")
            if response_text: break

        if not response_text:
            for om in or_mods:
                for ok in or_keys:
                    if response_text: break
                    self.add_log(ui_log, f"🌐 [API CALL] OpenRouter ({om}) [Max: 8192 Tokens]...", "detail")
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            def call_or():
                                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {ok}"}, json={"model": om, "messages": [{"role": "user", "content": m_prompt}], "max_tokens": 8192}, timeout=120)
                                res.raise_for_status()
                                return res.json()["choices"][0]["message"]["content"]
                            response_text = ex.submit(call_or).result(timeout=120)
                    except Exception as e:
                        self.add_log(ui_log, f"🛑 OpenRouter sập: {str(e)[:80]}", "error")
                if response_text: break

        if not response_text:
            self.add_log(ui_log, "🛑 [FATAL] Toàn bộ API đều sập hoặc không phản hồi.", "error")
            return False

        self.raw_html = response_text
        self.raw_html = re.sub(r'```html|```', '', self.raw_html).strip()
        
        # Dọn dẹp Markdown in đậm (**) vì đã có lệnh Anti-Stuffing cấm in đậm keyword
        self.raw_html = re.sub(r'\*\*(.*?)\*\*', r'\1', self.raw_html) 
        
        # Cởi trói dấu ngoặc kép cho Keyword nếu AI lỡ bọc vào
        for k in self.all_topic_kws:
            self.raw_html = re.sub(rf"[`'‘’\"“”]\s*({re.escape(k)})\s*[`'‘’\"“”]", r"\1", self.raw_html, flags=re.IGNORECASE)
        
        # Fix Bullet point rác AI sinh ra
        self.raw_html = re.sub(r'(?<!^)\s+\*\s+([A-ZĐÁÀẢÃẠĂÂẤẦẨẪẬÊẾỀỂỄỆÔỐỒỔỖỘƠỚỜỞỠỢƯỨỪỬỮỰÍÌỈĨỊÝỲỶỸỴ])', r'</p><p>• \1', self.raw_html)
        if '<p>' not in self.raw_html.lower():
            paras = [p.strip() for p in re.split(r'\n+', self.raw_html) if p.strip()]
            self.raw_html = "".join([f"<p>{p}</p>" for p in paras])
            
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        
        # Máy Hút Bụi: Hủy diệt ảnh rác AI tự chèn để chừa slot cho ảnh xịn của mình
        for img in soup.find_all('img'):
            img_parent = img.parent
            img.decompose()
            if img_parent and not img_parent.get_text(strip=True) and img_parent.name != 'body':
                img_parent.decompose()
            
        # Máy X-Ray: Xử lý số tự động H3
        h2_list = soup.find_all('h2')
        for h2 in h2_list:
            h3_count = 1
            curr = h2.find_next()
            while curr and curr.name != 'h2':
                if curr.name == 'h3':
                    text = curr.get_text(strip=True)
                    if not re.match(r'^\d+[\.\-\)]', text):
                        curr.string = f"{h3_count}. {text}"
                    h3_count += 1
                curr = curr.find_next()

        # Upper Case chữ cái đầu cho thẩm mỹ
        for tag in soup.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4']):
            for text_node in tag.find_all(string=True):
                if text_node.strip(): 
                    stripped = text_node.lstrip()
                    new_text = stripped[0].upper() + stripped[1:]
                    space_prefix = text_node[:len(text_node)-len(stripped)]
                    text_node.replace_with(space_prefix + new_text)
                    break
                    
        h1 = soup.find('h1')
        if h1: h1.string = h1.get_text(strip=True).upper()
            
        self.raw_html = str(soup)
        st.session_state.evolution_cache = f"{len(soup.find_all('h2'))} H2, {len(soup.find_all('h3'))} H3"
        
        self.final_title = h1.get_text(strip=True) if h1 else f"Bài: {self.all_topic_kws[0].upper()}"
        if self.retry_count == 0:
            self.add_log(ui_log, f"🏷️ [THÔNG TIN BÀI VIẾT] Tiêu đề: {self.final_title}", "success")
        return True

    def step5_6_spin_and_dom(self, ui_log):
        temp_soup = BeautifulSoup(self.raw_html, 'html.parser')
        current_wc = len(temp_soup.get_text(' ', strip=True).split())
        bonus_inject = 0
        
        if current_wc > self.mid_w:
            bonus_inject = 1
            if self.out_lim > 0: self.out_lim += 1
            else: self.in_lim += 1
            self.add_log(ui_log, f"📈 [BONUS KPI] Đạt mốc {current_wc} chữ (Vượt chuẩn {self.mid_w}). Thưởng thêm quota: +1 Link & +1 Ảnh!", "success")
            
        df_spin = self.db.get('SPIN', pd.DataFrame())
        for i, k in enumerate(self.all_topic_kws): 
            self.raw_html = re.sub(re.escape(k), f'__IRON_{i}__', self.raw_html, count=1, flags=re.IGNORECASE)
        if not df_spin.empty:
            for _, r in df_spin.iterrows():
                o, v_str = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_VARIANTS', '')).strip()
                if o and v_str:
                    vars = [v.strip() for v in v_str.replace(';', ',').split(',') if v.strip()]
                    if vars and re.search(re.escape(o), self.raw_html, flags=re.IGNORECASE):
                        self.raw_html = re.sub(re.escape(o), random.choice(vars), self.raw_html, flags=re.IGNORECASE)
                        self.used_spins.append(o)
        for i, k in enumerate(self.all_topic_kws): self.raw_html = self.raw_html.replace(f'__IRON_{i}__', k)

        soup = BeautifulSoup(self.raw_html, 'html.parser')
        ou, iu = [u.strip() for u in str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if u.strip()], [u.strip() for u in str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).split(',') if u.strip()]
        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        self.injected_kws_list = []
        total_links_needed = min(self.out_lim + self.in_lim, len(self.all_topic_kws))
        kws_to_inject = self.all_topic_kws[:total_links_needed]
        
        avail_p = [p for p in soup.find_all(['p', 'li']) if len(p.get_text(strip=True)) > 20 and not p.find('a') and not p.find('img')]

        if avail_p and kws_to_inject:
            n_chunks = len(kws_to_inject)
            chunk_size = max(1, len(avail_p) // n_chunks)

            for i, k in enumerate(kws_to_inject):
                start_idx = min(i * chunk_size, len(avail_p) - 1)
                end_idx = min((i + 1) * chunk_size, len(avail_p)) if i < n_chunks - 1 else len(avail_p)
                chunk_p = avail_p[start_idx:end_idx]
                if not chunk_p: chunk_p = avail_p

                url, is_e = "", False
                if self.injected_ext < self.out_lim and ou: url, is_e = random.choice(ou), True
                elif self.injected_int < self.in_lim and iu: url, is_e = random.choice(iu), False
                if not url: continue

                injected = False
                for p in chunk_p:
                    # KẾT NỐI KHÔNG DẤU - X-Ray Scanner
                    if re.search(re.escape(k), p.get_text(), flags=re.IGNORECASE):
                        p.replace_with(BeautifulSoup(re.sub(re.escape(k), lambda m: f"<a href='{url}'>{m.group(0)}</a>", str(p), count=1, flags=re.IGNORECASE), 'html.parser'))
                        injected = True
                        break

                if not injected:
                    target_p = random.choice(chunk_p)
                    fallback_sentences = [
                        f" Song song đó, yếu tố cốt lõi liên quan đến {k} luôn được các chuyên gia đánh giá cao.",
                        f" Đồng thời, các khía cạnh liên quan đến {k} cũng cần được phân tích kỹ lưỡng.",
                        f" Khảo sát thực tế cũng cho thấy {k} đóng vai trò như một điểm mấu chốt."
                    ]
                    gen_txt = random.choice(fallback_sentences)
                    pattern = re.compile(re.escape(k), re.IGNORECASE)
                    final_html = pattern.sub(f"<a href='{url}'>{k}</a>", gen_txt, count=1)
                    target_p.append(BeautifulSoup(final_html, 'html.parser'))
                    self.add_log(ui_log, f"⚠️ Dùng câu nối cho từ '{k}' ở Khúc {i+1}.", "warn")

                self.injected_kws_list.append(k)
                if is_e: self.injected_ext += 1
                else: self.injected_int += 1

        self.add_log(ui_log, f"🛠️ [GẮN LINK] Chốt: {self.injected_ext}/{self.out_lim} Ext | {self.injected_int}/{self.in_lim} Int. Tổng dùng {len(self.injected_kws_list)} từ khóa.", "success")

        mx_img = self.parse_rng(self.target_web.get('WS_IMG_LIMIT', 1), 1) + bonus_inject
        req_img = min(len(self.injected_kws_list) if self.injected_kws_list else 1, mx_img)
        self.add_log(ui_log, f"🖼️ [QUOTA ẢNH] Cần {req_img} ảnh. Bắt đầu Ping (Timeout 5s)...", "detail")
        df_img = self.db.get('IMAGE', pd.DataFrame())
        self.failed_imgs = []
        
        if not df_img.empty and 'IMG_URL' in df_img.columns and req_img > 0:
            df_img['IMG_STATUS'] = pd.to_numeric(df_img['IMG_STATUS'], errors='coerce').fillna(0)
            for _, r in df_img.sample(frac=1).sort_values('IMG_STATUS').iterrows():
                if len(self.used_imgs) >= req_img: break
                u_img = str(r['IMG_URL']).strip()
                try:
                    res = requests.get(u_img, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, stream=True, timeout=5)
                    if res.status_code == 200 and 'image' in res.headers.get('Content-Type', '').lower(): 
                        self.used_imgs.append(u_img)
                    else: self.failed_imgs.append(u_img)
                except: self.failed_imgs.append(u_img)

        ws_banner = str(self.target_web.get('WS_BANNER', '')).strip()
        if not ws_banner:
            img_max_w = '100%'
            self.add_log(ui_log, f"⚠️ Web chưa cấu hình WS_BANNER, tự động dùng size mặc định 100%.", "warn")
        else:
            img_max_w = ws_banner

        # ==========================================
        # PYTHON LOGIC: RẢI ẢNH CHỐNG DÍNH CHÙM TỐI ƯU
        # ==========================================
        if self.used_imgs:
            n_imgs = len(self.used_imgs)
            n_kws = len(self.injected_kws_list)
            target_kw_idx = []
            
            if n_imgs == 1:
                target_kw_idx = [0] if n_kws > 0 else []
            elif n_imgs == 2:
                if n_kws >= 3: target_kw_idx = [0, 2] 
                else: target_kw_idx = [0, 1] if n_kws >= 2 else ([0] if n_kws > 0 else [])
            else: 
                target_kw_idx = list(range(min(n_imgs, n_kws))) 

            all_tags = soup.find_all(['p', 'h2', 'h3'])
            inserted_tag_indices = []
            
            for i, img_u in enumerate(self.used_imgs):
                kw_img_alt = self.injected_kws_list[target_kw_idx[i]] if i < len(target_kw_idx) else self.all_topic_kws[0]
                img_html = f"<div style='margin: 20px auto; text-align: center;'><img src='{img_u}' alt='{kw_img_alt}' loading='lazy' style='max-width: {img_max_w}; height: auto; width: 100%; display: inline-block;'></div>"
                inserted = False

                if i < len(target_kw_idx):
                    target_kw_text = self.injected_kws_list[target_kw_idx[i]]
                    for t_idx, tag in enumerate(all_tags):
                        if not any(abs(t_idx - ins_idx) < 3 for ins_idx in inserted_tag_indices):
                            if tag.name in ['p', 'h2', 'h3'] and re.search(re.escape(target_kw_text), tag.get_text(), flags=re.IGNORECASE):
                                tag.insert_after(BeautifulSoup(img_html, 'html.parser'))
                                inserted_tag_indices.append(t_idx)
                                inserted = True
                                break
                                
                if not inserted:
                    for t_idx, tag in enumerate(all_tags):
                        if tag.name == 'p' and not any(abs(t_idx - ins_idx) < 4 for ins_idx in inserted_tag_indices):
                            tag.insert_after(BeautifulSoup(img_html, 'html.parser'))
                            inserted_tag_indices.append(t_idx)
                            inserted = True
                            break
                            
                    if not inserted and all_tags:
                        all_tags[-1].insert_after(BeautifulSoup(img_html, 'html.parser'))

        if self.failed_imgs: self.add_log(ui_log, f"⚠️ Đã loại {len(self.failed_imgs)} ảnh lỗi hoặc không cho phép load.", "warn")
        self.add_log(ui_log, f"🖼️ [GẮN ẢNH] DOM Inject thành công {len(self.used_imgs)} ảnh (Max-width: {img_max_w} | Anti-Clump Bật).")
        self.raw_html = str(soup); return True

    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "⚖️ [KCS Bước 1] Chấm điểm cơ bản (Miễn phí)...")
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        txt, k0 = soup.get_text(' ', strip=True), self.all_topic_kws[0].lower()
        
        wc = len(txt.split())
        self.last_word_count = wc
        
        self.add_log(ui_log, f"📏 [ĐỘ DÀI THỰC TẾ] Đạt {wc} chữ (Luật: MIN {self.min_w} | Chuẩn {self.target_wc} | MAX {self.max_w} chữ).", "detail")
        
        h1 = soup.find('h1')
        h1_text = h1.get_text().lower() if h1 else ""
        
        match_h1 = k0 in h1_text or remove_vn_accents(k0) in remove_vn_accents(h1_text)
        
        s_h1 = 30 if h1 and match_h1 else 0
        s_h2 = 20 if any(k0 in h.get_text().lower() or remove_vn_accents(k0) in remove_vn_accents(h.get_text().lower()) for h in soup.find_all('h2')) else 0
        s_bd = 10 if k0 in txt.lower() or remove_vn_accents(k0) in remove_vn_accents(txt.lower()) else 0
        s_alt = 10 if soup.find('img', alt=re.compile(r'(?i)' + re.escape(k0))) else 0
        
        den = (remove_vn_accents(txt.lower()).count(remove_vn_accents(k0)) * len(k0.split())) / max(len(txt.split()), 1) * 100
        s_den = 30 if 0.5 <= den <= 4.0 else 0
        
        seo = s_h1 + s_h2 + s_bd + s_alt + s_den
        lens = [len(s.split()) for s in re.split(r'[.!?\n]+', txt) if len(s.split()) > 3]
        ai = min(max(round(max(5, 50 - ((statistics.stdev(lens) if len(lens)>3 else 0) * 4)), 1), 2.0), 99.0)
        read = round(max(10, min(206.835 - (1.015 * (sum(lens) / max(len(lens), 1))) - 84.6 * 1.2, 100)), 1)
        
        self.kcs_metrics = {'SEO': min(seo, 100), 'AI': ai, 'READ': read}
        
        req = 35 if (self.out_lim + self.in_lim) < 3 else 70
        fails = []
        if seo < req: fails.append(f"SEO ({seo}/{req})")
        if ai > 20: fails.append(f"AI ({ai}%)")
        if read < 60: fails.append(f"Read ({read})")
        if wc < self.min_w: fails.append(f"Viết Quá ngắn ({wc} < {self.min_w})")
        if wc > self.max_w: fails.append(f"Viết Quá dài ({wc} > {self.max_w})")
        
        if fails:
            self.kcs_metrics['PLAGIARISM'] = "Skipped"
            self.kcs_metrics['JUDGE'] = "Skipped"
            self.add_log(ui_log, f"❌ [KCS FAIL] Trượt tiêu chuẩn cơ bản do: {', '.join(fails)}", "error")
            if h1: h1.decompose()
            self.raw_html = str(soup)
            return "FAIL"

        if self.copyscape_user and self.copyscape_key:
            self.add_log(ui_log, "🕵️ [KCS Bước 2] Gọi Copyscape check đạo văn...", "detail")
            try:
                cs_data = {
                    'u': self.copyscape_user, 'k': self.copyscape_key,
                    'o': 'csearch', 'e': 'UTF-8', 't': txt, 'f': 'json'
                }
                res = requests.post('https://www.copyscape.com/api/', data=cs_data, timeout=30)
                if res.status_code == 200:
                    cs_json = res.json()
                    if 'error' in cs_json:
                        self.add_log(ui_log, f"⚠️ Copyscape báo lỗi: {cs_json['error']}", "warn")
                        self.kcs_metrics['PLAGIARISM'] = "Error"
                    else:
                        all_matched = int(cs_json.get('allwordsmatched', 0))
                        plag_score = round((all_matched / max(wc, 1)) * 100, 2)
                        self.kcs_metrics['PLAGIARISM'] = plag_score
                        self.add_log(ui_log, f"📊 [PLAGIARISM] Tỷ lệ trùng lặp: {plag_score}%", "detail")
                        if plag_score > 10: fails.append(f"Đạo văn cao ({plag_score}% > 10%)")
            except Exception as e:
                self.add_log(ui_log, f"⚠️ Không kết nối được Copyscape: {e}", "warn")
                self.kcs_metrics['PLAGIARISM'] = "Error"
                
        if fails:
            self.kcs_metrics['JUDGE'] = "Skipped"
            self.add_log(ui_log, f"❌ [KCS FAIL] Bị loại ở vòng Copyscape: {', '.join(fails)}", "error")
            if h1: h1.decompose()
            self.raw_html = str(soup)
            return "FAIL"
                
        ws_judge_flag = str(self.target_web.get('WS_LLM_JUDGE', '')).strip()
        or_keys = [k.strip() for k in str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',') if k.strip()]
        or_mods = [m.strip() for m in str(self.dashboard.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini')).split(',') if m.strip()]
        
        if ws_judge_flag == '1' and or_keys and or_mods:
            judge_key = or_keys[0]
            judge_model = or_mods[0]
            self.add_log(ui_log, f"⚖️ [KCS Bước 3] Nhờ {judge_model} chấm điểm...", "detail")
            judge_prompt = f"Chấm điểm bài viết HTML sau dựa trên từ khóa chính: '{k0}'. Trả về DUY NHẤT một con số từ 0 đến 100, không kèm chữ nào khác.\n\nBài viết:\n{self.raw_html[:4000]}"
            try:
                res = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {judge_key}"},
                    json={"model": judge_model, "messages": [{"role": "user", "content": judge_prompt}], "max_tokens": 10},
                    timeout=30
                )
                if res.status_code == 200:
                    judge_resp = res.json()["choices"][0]["message"]["content"].strip()
                    match = re.search(r'\d+', judge_resp)
                    if match:
                        judge_score = int(match.group())
                        self.kcs_metrics['JUDGE'] = judge_score
                        self.add_log(ui_log, f"🎯 [AI JUDGE] Điểm đánh giá: {judge_score}/100", "detail")
                        if judge_score < 70: fails.append(f"AI Judge chấm trượt ({judge_score} < 70)")
                    else: self.kcs_metrics['JUDGE'] = "Error"
                else: self.kcs_metrics['JUDGE'] = "Error"
            except Exception as e: self.kcs_metrics['JUDGE'] = "Error"
        else: self.kcs_metrics['JUDGE'] = "N/A"

        plag_disp = self.kcs_metrics.get('PLAGIARISM', 'N/A')
        if isinstance(plag_disp, (int, float)): plag_disp = f"{plag_disp}%"
        judge_disp = self.kcs_metrics.get('JUDGE', 'N/A')
        
        self.add_log(ui_log, f"   > KCS Tổng kết: Điểm SEO {seo}/100 | AI {ai}% | READ {read}/100 | COPYSCAPE: {plag_disp} | JUDGE: {judge_disp}", "detail")

        if h1: h1.decompose()
        self.raw_html = str(soup)
        
        if fails:
            self.add_log(ui_log, f"❌ [KCS FAIL] Bị loại ở vòng AI Judge do: {', '.join(fails)}", "error")
            return "FAIL"
            
        self.add_log(ui_log, f"✅ [KCS PASSED] Vượt qua mọi bài test!", "success")
        return "PENDING"

    def step8_sync_db(self, ui_log, final_result):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
                ss = gspread.authorize(creds).open_by_key(SHEET_ID)
                rep_ws = ss.worksheet('REPORT')
                hdrs = [str(h).strip() for h in rep_ws.row_values(1)]
                def gc(pfx): return next((h for h in hdrs if h.startswith(pfx)), pfx)
                
                log_kws = self.injected_kws_list + [""] * 5
                
                plag_val = self.kcs_metrics.get('PLAGIARISM', '')
                if isinstance(plag_val, (int, float)): plag_val = f"{plag_val}%"
                elif not plag_val: plag_val = "N/A"
                
                judge_val = str(self.kcs_metrics.get('JUDGE', 'N/A'))
                
                row_d = {
                    'REP_WS_NAME': str(self.target_web.get('WS_NAME', '')), 'REP_CREATED_AT': self.now_vn.strftime('%Y-%m-%d %H:%M'),
                    'REP_TITLE': self.final_title, 'REP_IMG_COUNT': str(len(self.used_imgs)),
                    'REP_KW_1': log_kws[0], 'REP_KW_2': log_kws[1],
                    'REP_KW_3': log_kws[2], 'REP_KW_4': log_kws[3],
                    'REP_KW_5': log_kws[4], 
                    gc('REP_SEO_'): str(self.kcs_metrics.get('SEO', 0)), 
                    gc('REP_AI_'): f"{self.kcs_metrics.get('AI', 100)}%", 
                    gc('REP_READ'): str(self.kcs_metrics.get('READ', 0)),
                    gc('REP_PLAG'): str(plag_val),
                    gc('REP_JUDGE_'): judge_val,
                    'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'), 'REP_POST_URL': "", 
                    'REP_RESULT': final_result, 'REP_LOG': "\n".join(self.history_log), 'REP_HTML': self.raw_html if final_result == 'PENDING' else ""
                }
                rep_ws.append_row([row_d.get(h, "") for h in hdrs])
                
                if final_result == 'PENDING':
                    ts = self.now_vn.strftime('%Y-%m-%d %H:%M')
                    def batch_upd(ws, col_match, val_list, col_st, col_dt):
                        if not val_list: return
                        data = ws.get_all_values()
                        upds = []
                        if len(data) > 1:
                            h = [str(col).strip() for col in data[0]]
                            i_m = h.index(col_match) if col_match in h else -1
                            i_s = h.index(col_st) if col_st and col_st in h else -1
                            i_d = h.index(col_dt) if col_dt in h else -1
                            for i, r in enumerate(data[1:], 2):
                                if i_m != -1 and len(r) > i_m and str(r[i_m]).strip() in val_list:
                                    if i_s != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_s+1)}', 'values': [[self.safe_int(r[i_s] if len(r)>i_s else 0) + 1]]})
                                    if i_d != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_d+1)}', 'values': [[ts]]})
                        if upds: ws.batch_update(upds)

                    batch_upd(ss.worksheet('KEYWORD'), 'KW_TEXT', self.injected_kws_list, 'KW_STATUS', 'KW_DATE')
                    batch_upd(ss.worksheet('IMAGE'), 'IMG_URL', self.used_imgs, 'IMG_STATUS', 'IMG_DATE')
                    if self.used_spins: batch_upd(ss.worksheet('SPIN'), 'SPIN_ORIGINAL', self.used_spins, None, 'SPIN_DATE')
                    
                    if hasattr(self, 'failed_imgs') and self.failed_imgs:
                        s_img, d_img = ss.worksheet('IMAGE'), ss.worksheet('IMAGE').get_all_values()
                        if len(d_img) > 1:
                            h_img = [str(x).strip() for x in d_img[0]]
                            im_img, is_img = h_img.index('IMG_URL'), h_img.index('IMG_STATUS') if 'IMG_STATUS' in h_img else -1
                            u_img = []
                            for i, r in enumerate(d_img[1:], 2):
                                if r[im_img].strip() in self.failed_imgs and is_img != -1:
                                    u_img.append({'range': f'{gspread.utils.rowcol_to_a1(i, is_img+1)}', 'values': [[999]]})
                            if u_img: s_img.batch_update(u_img)
                
                telegram_msg = f"""🚀 {self.dashboard.get('PROJECT_NAME', 'Auto SEO Pipeline')}

🌐 Target Domain: {self.target_web.get('WS_NAME', '')}
📑 Title: {self.final_title}
🔑 Keywords: {" | ".join(self.injected_kws_list)}
📊 SEO: {self.kcs_metrics.get('SEO', 0)} | AI: {self.kcs_metrics.get('AI', 100)}%
🚥 Status: {final_result}
🧱 Schedule: {self.publish_time.strftime('%Y-%m-%d %H:%M')}"""
                send_telegram_noti(self.dashboard, telegram_msg)
                
                self.add_log(ui_log, f"🎉 [HOÀN TẤT] Lưu DB xong. Trạng thái bài viết: {final_result}", "success")
                break 
            except Exception as e: 
                if attempt == max_retries - 1:
                    self.add_log(ui_log, f"🛑 Lỗi ghi Database sau 3 lần thử: {str(e)[:100]}", "error")
                else:
                    self.add_log(ui_log, f"⚠️ Mất kết nối Google Sheets. Đang thử lại ({attempt+1}/{max_retries})...", "warn")
                    time.sleep(3)

# ==========================================
# 🖥 UI CHUẨN CLASSIC CỦA SẾP
# ==========================================
db_mock = load_data_from_gsheets()
if db_mock is None: st.stop()

df_rep = db_mock.get('REPORT', pd.DataFrame())
df_dash = db_mock.get('DASHBOARD', pd.DataFrame())
dash_dict = {str(k).strip(): str(v).strip() for k, v in zip(df_dash['DATA_KEY'], df_dash['DATA_CONTENT'])} if not df_dash.empty else {}

st.title(f"🛡️ {dash_dict.get('PROJECT_NAME', 'Hệ Thống Lái Hộ Auto SEO')}")
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD", "📋 CONTENT", "🗄️ DATABASE"])

with tab1:
    c1, c2, c3 = st.columns(3)
    today_str = get_vn_now().strftime('%Y-%m-%d')
    
    df_today = df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)] if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else pd.DataFrame()
    p_today = len(df_today[df_today['REP_RESULT'].astype(str).str.strip() != 'FAIL']) if not df_today.empty and 'REP_RESULT' in df_today.columns else 0
    
    b_val = dash_dict.get('BATCH_SIZE', '10')
    try:
        if '-' in str(b_val): batch = random.randint(int(str(b_val).split('-')[0]), int(str(b_val).split('-')[1]))
        else: batch = int(b_val)
    except: batch = 10
    
    c1.metric("Generated (Hôm nay)", f"{p_today} / {batch}")
    c2.metric("✅ Published (DONE)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'DONE']) if not df_rep.empty and 'REP_RESULT' in df_rep.columns else 0)
    c3.metric("⏳ Scheduled (PENDING)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if not df_rep.empty and 'REP_RESULT' in df_rep.columns else 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    if "run_mode" not in st.session_state: st.session_state.run_mode = None
    if "cancel_run" not in st.session_state: st.session_state.cancel_run = False

    def cb_start_auto():
        st.session_state.run_mode = "auto"
        st.session_state.cancel_run = False

    def cb_start_force():
        st.session_state.run_mode = "force"
        st.session_state.cancel_run = False

    def cb_cancel():
        st.session_state.cancel_run = True

    def cb_done():
        st.session_state.run_mode = None
        st.session_state.cancel_run = False

    action_col = st.empty()
    is_proc = st.session_state.run_mode is not None
    with action_col.container():
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        btn_col1.button("🔥 Bắt đầu Soạn bài AI", use_container_width=True, type="primary", disabled=is_proc, on_click=cb_start_auto)
        btn_col2.button("⚡ Ép Lên bài ngay", use_container_width=True, disabled=is_proc, on_click=cb_start_force)
        btn_refresh = btn_col3.button("🔄 Làm mới dữ liệu", use_container_width=True, disabled=is_proc)
        
    if btn_refresh:
        load_data_from_gsheets.clear()
        st.rerun()

    if st.session_state.run_mode == "force":
        action_col.empty()
        st.markdown("---")
        
        top_control_area = st.empty()
        with top_control_area.container():
            status_col, btn_c_col = st.columns([4, 1])
            with status_col:
                st.markdown('<div class="alert-processing">⏳ ĐANG KIỂM TRA VÀ ĐĂNG BÀI QUÁ HẠN... VUI LÒNG KHÔNG TẮT TRÌNH DUYỆT!</div>', unsafe_allow_html=True)
            with btn_c_col:
                st.button("❌ Hủy chạy (Cancel)", use_container_width=True, key="cancel_force", on_click=cb_cancel)
                
        ui_log = st.empty()
        bot = AutoSEOPipeline(db_mock, [])
        upd, count, cleanup_count = [], 0, 0
        
        if not st.session_state.cancel_run:
            try:
                ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
                ws = ss.worksheet('REPORT')
                data = ws.get_all_values()
                ws_df = db_mock.get('WEBSITE', pd.DataFrame())
                
                if len(data) > 1:
                    headers = [str(h).strip() for h in data[0]]
                    idx_res, idx_pub = headers.index('REP_RESULT') if 'REP_RESULT' in headers else -1, headers.index('REP_PUBLISH_DATE') if 'REP_PUBLISH_DATE' in headers else -1
                    idx_html, idx_ws, idx_title = headers.index('REP_HTML') if 'REP_HTML' in headers else -1, headers.index('REP_WS_NAME') if 'REP_WS_NAME' in headers else -1, headers.index('REP_TITLE') if 'REP_TITLE' in headers else -1
                    idx_log = headers.index('REP_LOG') if 'REP_LOG' in headers else -1 
                    idx_created = headers.index('REP_CREATED_AT') if 'REP_CREATED_AT' in headers else -1

                    if idx_res != -1 and idx_pub != -1:
                        now = get_vn_now()
                        bot.add_log(ui_log, "🔍 [SYSTEM] Quét tìm bài PENDING quá hạn và dọn rác Data cũ...", "detail")
                        for i, row in enumerate(data[1:], 2):
                            if st.session_state.cancel_run: break
                            
                            res_val = str(row[idx_res]).strip() if len(row) > idx_res else ""
                            created_val = str(row[idx_created]).strip() if idx_created != -1 and len(row) > idx_created else ""
                            
                            if res_val == 'PENDING':
                                try: pub_dt = VN_TZ.localize(datetime.datetime.strptime(str(row[idx_pub]).strip(), '%Y-%m-%d %H:%M'))
                                except: pub_dt = None
                                
                                if pub_dt and pub_dt <= now:
                                    ws_name, title, html_content = row[idx_ws] if idx_ws != -1 else "", row[idx_title] if idx_title != -1 else "No Title", row[idx_html] if idx_html != -1 else ""
                                    bot.add_log(ui_log, f"➤ Xử lý bài: '{title}' -> Web: {ws_name}")
                                    web_info = ws_df[ws_df['WS_NAME'].astype(str).str.strip() == ws_name.strip()]
                                    if not web_info.empty:
                                        success, msg = post_to_cms(web_info.iloc[0], title, html_content, dash_dict)
                                        if success:
                                            bot.add_log(ui_log, f"✅ {msg} (Xóa HTML)", "success")
                                            upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_res+1)}', 'values': [['DONE']]})
                                            if idx_html != -1: upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_html+1)}', 'values': [['']]})
                                            count += 1
                                            res_val = 'DONE'
                                        else: bot.add_log(ui_log, f"🛑 {msg}", "error")
                                    else: bot.add_log(ui_log, f"⚠️ Không tìm thấy cấu hình Web '{ws_name}'", "warn")
                            
                            if res_val in ['DONE', 'FAIL'] and idx_log != -1 and len(row) > idx_log and str(row[idx_log]).strip() != '':
                                try:
                                    c_date = VN_TZ.localize(datetime.datetime.strptime(created_val, '%Y-%m-%d %H:%M')).date()
                                    if (now.date() - c_date).days >= 2:
                                        upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_log+1)}', 'values': [['']]})
                                        cleanup_count += 1
                                except: pass
                                        
                        if upd: ws.batch_update(upd)
                        if cleanup_count > 0: bot.add_log(ui_log, f"🧹 [AUTO-CLEAN] Đã dọn sạch REP_LOG cũ của {cleanup_count} bài viết.", "success")
                    else: bot.add_log(ui_log, "🛑 Không tìm thấy cột trạng thái trong Sheet.", "error")
            except Exception as e: bot.add_log(ui_log, f"🛑 Lỗi Đăng bài: {str(e)[:150]}", "error")

        top_control_area.empty()
        with top_control_area.container():
            c1, c2 = st.columns([4, 1])
            if st.session_state.cancel_run:
                with c1: st.markdown('<div class="alert-done" style="color:#b91c1c; border-color:#ef4444; background:#fee2e2;">🛑 ĐÃ HỦY TIẾN TRÌNH ÉP LÊN BÀI!</div>', unsafe_allow_html=True)
            elif count > 0 or cleanup_count > 0:
                with c1: st.markdown(f'<div class="alert-done">🎉 ĐÃ CHỐT SỔ: BẮN THÀNH CÔNG {count} BÀI VÀ XÓA {cleanup_count} DÒNG RÁC!</div>', unsafe_allow_html=True)
            else:
                with c1: st.markdown(f'<div class="alert-done">✅ Đã kiểm tra xong. Không có bài mới.</div>', unsafe_allow_html=True)
            with c2: st.button("✅ Quay lại", type="primary", use_container_width=True, key="done_force", on_click=cb_done)

    if st.session_state.run_mode == "auto":
        action_col.empty()
        st.markdown("---")
        
        top_control_area = st.empty()
        with top_control_area.container():
            status_col, btn_c_col = st.columns([4, 1])
            with status_col:
                st.markdown('<div class="alert-processing">⏳ HỆ THỐNG ĐANG SOẠN BÀI TỰ ĐỘNG... VUI LÒNG KHÔNG TẮT TRÌNH DUYỆT!</div>', unsafe_allow_html=True)
            with btn_c_col:
                st.button("❌ Hủy chạy (Cancel)", use_container_width=True, key="cancel_start", on_click=cb_cancel)
                
        load_data_from_gsheets.clear()
        db_mock = load_data_from_gsheets()
        df_rep = db_mock.get('REPORT', pd.DataFrame())
        df_today = df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)] if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else pd.DataFrame()
        p_today = len(df_today[df_today['REP_RESULT'].astype(str).str.strip() != 'FAIL']) if not df_today.empty and 'REP_RESULT' in df_today.columns else 0
        
        ui_log = st.empty()
        needed = batch - p_today
        if needed <= 0: 
            ui_log.markdown('<div class="log-box"><span class="log-error">🛑 Đã đạt BATCH_SIZE hôm nay. Không chạy thêm.</span></div>', unsafe_allow_html=True)
            top_control_area.empty()
            with top_control_area.container():
                c1, c2 = st.columns([4, 1])
                with c1: st.markdown(f'<div class="alert-done">✅ Hôm nay đã đủ bài (Đạt BATCH_SIZE).</div>', unsafe_allow_html=True)
                with c2: st.button("✅ Quay lại", type="primary", use_container_width=True, key="done_start_0", on_click=cb_done)
        else:
            master_logs = []
            success_count = 0
            fail_count = 0
            
            for i in range(needed):
                if st.session_state.cancel_run:
                    bot = AutoSEOPipeline(db_mock, master_logs)
                    bot.add_log(ui_log, "🛑 ĐÃ BỊ HỦY BỞI NGƯỜI DÙNG...", "error")
                    break
                    
                if i > 0 and i % 3 == 0:
                    bot = AutoSEOPipeline(db_mock, master_logs)
                    sleep_time = random.randint(7, 10)
                    bot.add_log(ui_log, f"♻️ [SYSTEM] Xả hơi {sleep_time}s chống sập API...", "warn")
                    time.sleep(sleep_time)
                    gc.collect()
                    
                bot = AutoSEOPipeline(db_mock, master_logs)
                bot.add_log(ui_log, f"<br>🚀 --- BẮT ĐẦU CHẠY BÀI {i+1}/{needed} ---", "success")
                st_t = time.time()
                try:
                    if bot.step1_allocate_slot(ui_log):
                        if st.session_state.cancel_run: break
                        if bot.step2_3_keyword_and_serp(ui_log):
                            
                            final_res = "FAIL"
                            for attempt in range(3):  
                                if st.session_state.cancel_run: break
                                bot.retry_count = attempt
                                if attempt > 0:
                                    bot.reset_state_for_retry()
                                    bot.add_log(ui_log, f"🔄 [AUTO-RETRY] Bài fail KCS. Bơm Oxy hiệp {attempt+1}...", "warn")
                                
                                if bot.step4_llm_generation(ui_log):
                                    if st.session_state.cancel_run: break
                                    bot.step5_6_spin_and_dom(ui_log)
                                    final_res = bot.step7_qa_validation(ui_log)
                                    if final_res == "PENDING": break 
                                else: break 
                            
                            if not st.session_state.cancel_run:      
                                bot.step8_sync_db(ui_log, final_res)
                                db_mock = load_data_from_gsheets()
                                if final_res == "PENDING": success_count += 1
                                else: fail_count += 1
                except Exception as e: bot.add_log(ui_log, f"🛑 Lỗi: {str(e)[:150]}", "error")
                
                if time.time() - st_t > 300:
                    bot.add_log(ui_log, "🛑 Quá 5 phút, tự ngắt để cứu hệ thống.", "error")
                    break
            
            if not st.session_state.cancel_run: bot.add_log(ui_log, "<br>✅ TOÀN BỘ TIẾN TRÌNH HOÀN TẤT.", "success")
                
            top_control_area.empty()
            with top_control_area.container():
                c1, c2 = st.columns([4, 1])
                if st.session_state.cancel_run:
                    with c1: st.markdown(f'<div class="alert-done" style="color:#b91c1c; border-color:#ef4444; background:#fee2e2;">🛑 ĐÃ HỦY TIẾN TRÌNH! <span style="font-size:16px; font-weight:normal; color:#475569; margin-left: 10px;"> Đã lưu: {success_count} OK | {fail_count} FAIL</span></div>', unsafe_allow_html=True)
                else:
                    with c1: st.markdown(f'<div class="alert-done">🎉 ĐÃ HOÀN TẤT TẠO BÀI VIẾT! <span style="font-size:16px; font-weight:normal; color:#475569; margin-left: 10px;"> OK: {success_count} | FAIL: {fail_count}</span></div>', unsafe_allow_html=True)
                with c2: st.button("✅ Quay lại Dashboard", type="primary", use_container_width=True, key="done_start_1", on_click=cb_done)

with tab2:
    if not df_rep.empty:
        df_vn = df_rep[['REP_CREATED_AT', 'REP_PUBLISH_DATE', 'REP_TITLE', 'REP_WS_NAME', 'REP_RESULT']].copy()
        df_vn.columns = ['Ngày tạo bài', 'Ngày đăng bài', 'Tiêu đề', 'Trang web', 'Trạng thái']
        st.dataframe(df_vn.tail(15), use_container_width=True, hide_index=True)
        st.markdown("---")
        titles = df_rep['REP_TITLE'].tolist()[::-1]
        sel = st.selectbox("🔍 Nội soi chi tiết bài viết (Log & HTML):", titles)
        if sel:
            row = df_rep[df_rep['REP_TITLE'] == sel].iloc[0]
            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown("**📝 Nhật ký chạy (System Log):**")
                st.markdown(f'<div class="log-box">{str(row.get("REP_LOG", "")).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            with lc2:
                st.markdown("**🌐 Mã nguồn (Raw HTML):**")
                st.text_area("", str(row.get('REP_HTML', '')), height=800, label_visibility="collapsed")

with tab3:
    st.dataframe(df_rep, use_container_width=True)
