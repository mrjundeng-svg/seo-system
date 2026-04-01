import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import time, datetime, random, statistics, re, requests, html, pytz
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import concurrent.futures

# ==========================================
# ⚙️ CẤU HÌNH HỆ THỐNG
# ==========================================
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
def get_vn_now(): return datetime.datetime.now(VN_TZ)

st.set_page_config(page_title="Auto SEO Pipeline | Lái Hộ", layout="wide", page_icon="🛡️")
st.markdown("""<style>.log-box {background-color: #0f172a; color: #10b981; font-family: monospace; font-size: 14px; padding: 15px; border-radius: 8px; height: 800px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6; word-wrap: break-word;} .log-error {color: #ef4444; font-weight: bold;} .log-warn {color: #f59e0b;} .log-success {color: #3b82f6; font-weight: bold;} .log-quota {color: #a855f7; font-weight: bold;} .log-detail {color: #94a3b8; font-size: 13px; font-style: italic;}</style>""", unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

def check_password():
    if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
    if not st.session_state["logged_in"]:
        st.markdown("## 🔐 Hack em làm gì?")
        u = st.text_input("Username", key="username")
        p = st.text_input("Password", type="password", key="password")
        if st.button("Zô mần ziệc"):
            if u == st.secrets.get("admin_user", "admin") and p == st.secrets.get("admin_pass", "admin123"):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("❌ Sai thông tin đăng nhập!")
        return False
    return True

if not check_password(): st.stop()

@st.cache_data(ttl=60)
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

# ==========================================
# 🤖 CORE ENGINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, data_frames, master_log_list):
        self.db = data_frames
        self.dashboard = {str(k).strip(): str(v).strip() for k, v in zip(self.db['DASHBOARD']['DATA_KEY'], self.db['DASHBOARD']['DATA_CONTENT'])}
        self.now_vn, self.history_log = get_vn_now(), master_log_list
        self.target_web, self.publish_time, self.main_kw_row = None, None, None
        self.all_kws, self.target_length, self.raw_html, self.final_title = [], 0, "", ""
        self.kcs_metrics, self.used_imgs, self.used_spins, self.failed_imgs = {}, [], [], []
        self.out_lim, self.in_lim, self.injected_ext, self.injected_int = 0, 0, 0, 0
        self.is_short_form, self.serp_style, self.prompt_content = False, "", ""
        self.min_w, self.max_w = 0, 0
        if 'evolution_cache' not in st.session_state: st.session_state.evolution_cache = ""

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
        parts = [p.strip() for p in re.split(r'\|\|\|', str(text)) if p.strip()]
        return random.choice(parts) if parts else str(text).strip()

    def step1_allocate_slot(self, ui_log) -> bool:
        df_rep, df_web = self.db.get('REPORT', pd.DataFrame()), self.db.get('WEBSITE', pd.DataFrame())
        batch, max_days = self.parse_rng(self.dashboard.get('BATCH_SIZE', 10), 10), self.parse_rng(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        today_str = self.now_vn.strftime('%Y-%m-%d')
        posts_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(today_str)]) if not df_rep.empty else 0
        
        self.add_log(ui_log, f"🔍 [CHECK QUOTA] Global hôm nay: {posts_today}/{batch}", "quota")
        if posts_today >= batch: return False

        avail_webs = df_web.sample(frac=1).reset_index(drop=True)
        for d_off in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=d_off)
            day_x_str = day_x.strftime('%Y-%m-%d')
            for _, web in avail_webs.iterrows():
                ws_name, ws_limit = str(web.get('WS_NAME', '')).strip(), self.parse_rng(web.get('WS_POST_LIMIT', 1), 1)
                day_posts = df_rep[(df_rep['REP_WS_NAME'] == ws_name) & (df_rep['REP_PUBLISH_DATE'].astype(str).str.startswith(day_x_str))] if not df_rep.empty else pd.DataFrame()
                
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
        total_links = self.out_lim + self.in_lim
        self.add_log(ui_log, f"📐 [QUOTA LINK] Out Limit: {self.out_lim} + In Limit: {self.in_lim} => Tổng: {total_links} Links.", "quota")
        
        kws_needed = max(1, total_links)
        subs = df_kw[(df_kw['KW_TEXT'] != m_kw) & (df_kw['KW_CONTENT'] == str(self.main_kw_row.get('KW_CONTENT', '')))].head(max(0, kws_needed - 1))['KW_TEXT'].tolist()
        self.all_kws = [m_kw] + subs
        self.add_log(ui_log, f"📦 [KWs ĐÃ GOM] Cần {len(self.all_kws)} KWs: {', '.join(self.all_kws)}", "detail")
        
        try:
            wrng = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
            mn, mx = int(wrng[0]), int(wrng[1])
        except: mn, mx = 900, 1200
        
        self.is_short_form = len(self.all_kws) < 3
        if self.is_short_form:
            self.target_length = random.randint(mn // 2, mx // 2)
        else:
            self.target_length = random.randint(mn, mx)
            
        self.min_w = self.target_length
        self.max_w = int(self.min_w * 1.3)
        self.add_log(ui_log, f"📏 [RULE BÀI] Khóa cứng Word Count: Tối thiểu {self.min_w} chữ, Tối đa {self.max_w} chữ (+30%).", "detail")
        
        s_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        c_list = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        serp_chunks, scraped_urls = [], []

        if s_key:
            self.add_log(ui_log, f"🕵️ [SERP] Bắt đầu quét cào data đa từ khóa...", "detail")
            for kw in self.all_kws:
                try:
                    res = requests.get("https://serpapi.com/search", params={"q": kw, "hl": "vi", "gl": "vn", "api_key": s_key}, timeout=10).json()
                    orgs = res.get("organic_results", [])
                    clinks = [r["link"] for r in orgs[:10] if c_list and any(c in r.get("link","") for c in c_list)]
                    t_link = clinks[0] if clinks else (orgs[0]["link"] if orgs else None)
                    if t_link:
                        rh = requests.get(t_link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                        if rh.status_code == 200:
                            soup = BeautifulSoup(rh.text, 'html.parser')
                            for t in soup(["script", "style", "nav", "footer", "header"]): t.decompose()
                            ext = "\n".join([t.get_text(strip=True) for t in soup.find_all(['h2', 'h3', 'p'])])[:1000]
                            if ext: 
                                serp_chunks.append(f"--- Data cho '{kw}' ---\n{ext}")
                                scraped_urls.append(t_link)
                except: pass
            
            if serp_chunks:
                raw_serp_text = "\n\n".join(serp_chunks)[:4000]
                url_list_str = "\n".join([f"   + {u}" for u in scraped_urls])
                self.add_log(ui_log, f"✅ [SERP] Đã trộn data từ {len(serp_chunks)} đối thủ:\n{url_list_str}", "success")
                
                gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
                if gem_keys:
                    try:
                        genai.configure(api_key=gem_keys[0])
                        prompt_style = f"Đọc nội dung cào từ đối thủ sau và tóm tắt thành 3 gạch đầu dòng: Văn phong cách viết bài, Nhịp điệu của bài viết, Thể loại bài viết hướng tới.\n\nData:\n{raw_serp_text}"
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            self.serp_style = ex.submit(lambda: genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt_style).text).result(timeout=15)
                    except: self.serp_style = "Văn phong chuyên gia, nhịp điệu logic, thể loại chia sẻ kiến thức."
                else: self.serp_style = "Văn phong chuyên gia, nhịp điệu logic, thể loại chia sẻ kiến thức."
                self.add_log(ui_log, f"🎯 [SERP_STYLE_AI_EXTRACT]:\n{self.serp_style}", "detail")
            else:
                self.serp_style = "Văn phong chuyên gia, logic."
                self.add_log(ui_log, f"⚠️ [SERP] Cào thất bại, dùng Internal Cache.", "warn")
        else: self.serp_style = "Văn phong chuyên gia."
        return True

    def step4_llm_generation(self, ui_log) -> bool:
        keys_to_pull = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        pmts = {k: self.pick_random_prompt_variant(self.dashboard.get(k, '')) for k in keys_to_pull}
        
        self.prompt_content = f"{pmts['PROMPT_TEMPLATE']}\n{pmts['PROMPT_CONTENT_STRATEGY']}\n{pmts['PROMPT_KEYWORD_SEARCH']}\n[SERP_STYLE_AI_EXTRACT]: {self.serp_style}"
        self.add_log(ui_log, f"🧠 [PROMPT_CONTENT TỔNG HỢP (Chuẩn bị gửi AI)]:\n{self.prompt_content[:300]}...", "detail")

        dist = self.min_w // max(len(self.all_kws), 1)
        seed_sang_tao = random.randint(10000, 99999)
        
        # SỬA LẠI PROMPT: CẤP SỐ MIN & MAX THỰC TẾ ĐỂ BẢO TOÀN KEYWORD DENSITY
        force = f"""\n[YÊU CẦU SINH TỬ - BẮT BUỘC TUÂN THỦ]:
        1. CẤM CHÀO HỎI (Cấm 'Kính thưa', 'Chào các Sếp'). Vào thẳng Sapo.
        2. H1: Chứa "{self.all_kws[0]}" ở GIỮA/CUỐI. Cấm đặt đầu câu.
        3. RẢI TỪ KHÓA: Từ khóa chính "{self.all_kws[0]}" (x3). Các từ "{', '.join(self.all_kws[1:])}" mỗi từ x1.
        Rải đều từ khóa tuần tự từ trên xuống. Khoảng cách xấp xỉ {dist} chữ. Đặt tự nhiên lọt thỏm giữa câu. Cấm nhồi nhét 1 chỗ.
        4. ĐỊNH DẠNG HTML (QUAN TRỌNG):
        - BẮT BUỘC dùng thẻ <ul> và <li> nếu có liệt kê danh sách.
        - TUYỆT ĐỐI KHÔNG DÙNG ký tự Markdown như `*` hay `-` để gạch đầu dòng. KHÔNG in đậm `**` từ khóa.
        - H3 phải đánh số 1., 2..
        5. SỐ LƯỢNG CHỮ (QUAN TRỌNG NHẤT):
        - BẮT BUỘC BÀI VIẾT PHẢI CÓ TỔNG SỐ CHỮ NẰM TRONG KHOẢNG TỪ {self.min_w} ĐẾN TỐI ĐA {self.max_w} CHỮ. Bạn hãy phân tích thật sâu, chia làm nhiều luận điểm nhỏ để đạt TỐI THIỂU {self.min_w} chữ. BỊ PHẠT NẾU VIẾT NGẮN HƠN HOẶC DÀI HƠN MỨC NÀY.
        - Ngắn dài đan xen (3-4 câu/đoạn). Mỗi đoạn bọc trong 1 thẻ <p> riêng biệt. Xóa cấu trúc cũ: {st.session_state.evolution_cache}.
        6. GÓC NHÌN (Seed: {seed_sang_tao}): Lập luận theo một góc độ hoàn toàn khác so với bài trước.
        7. TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>."""
        
        m_prompt = f"{self.prompt_content}\n{pmts['PROMPT_SEO_GLOBAL_RULE']}\n{pmts['PROMPT_AI_HUMANIZER']}\n{force}"
        m_prompt = m_prompt.replace('{{ws_persona}}', str(self.target_web.get('WS_PERSONA', ''))).replace('{{kw_intent}}', str(self.main_kw_row.get('KW_INTENT', ''))).replace('{{keyword}}', self.all_kws[0])
        for i, k in enumerate(self.all_kws): m_prompt = re.sub(rf'\[?REP_KW_{i+1}\]?', k, m_prompt, flags=re.IGNORECASE)

        gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        gem_mods = [m.strip() for m in str(self.dashboard.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        or_keys = [k.strip() for k in str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',') if k.strip()]
        or_mods = [m.strip() for m in str(self.dashboard.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini')).split(',') if m.strip()]

        response_text = None
        for gm in gem_mods:
            for gk in gem_keys:
                if response_text: break
                genai.configure(api_key=gk)
                self.add_log(ui_log, f"🌐 [API CALL] Gemini ({gm}) [Timeout 90s]...", "detail")
                try:
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        response_text = ex.submit(lambda: genai.GenerativeModel(gm).generate_content(m_prompt).text).result(timeout=90)
                except Exception as e:
                    self.add_log(ui_log, f"⚠️ Gemini sập (429/Timeout). Đang chuyển dự phòng...", "warn")
            if response_text: break

        if not response_text:
            for om in or_mods:
                for ok in or_keys:
                    if response_text: break
                    self.add_log(ui_log, f"🌐 [API CALL] OpenRouter ({om}) [Timeout 90s]...", "detail")
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            def call_or():
                                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {ok}"}, json={"model": om, "messages": [{"role": "user", "content": m_prompt}]}, timeout=90)
                                res.raise_for_status()
                                return res.json()["choices"][0]["message"]["content"]
                            response_text = ex.submit(call_or).result(timeout=90)
                    except Exception as e:
                        self.add_log(ui_log, f"🛑 OpenRouter sập: {str(e)[:80]}", "error")
                if response_text: break

        if not response_text:
            self.add_log(ui_log, "🛑 [FATAL] LLM Gateway Timeout: Toàn bộ API đều sập hoặc không phản hồi. Xin kiểm tra lại Quota!", "error")
            return False

        self.raw_html = response_text
        self.raw_html = re.sub(r'```html|```', '', self.raw_html).strip()
        self.raw_html = re.sub(r'\*\*(.*?)\*\*', r'\1', self.raw_html) 
        
        self.raw_html = re.sub(r'(?<!^)\s+\*\s+([A-ZĐÁÀẢÃẠĂÂẤẦẨẪẬÊẾỀỂỄỆÔỐỒỔỖỘƠỚỜỞỠỢƯỨỪỬỮỰÍÌỈĨỊÝỲỶỸỴ])', r'</p><p>• \1', self.raw_html)
        if '<p>' not in self.raw_html.lower():
            paras = [p.strip() for p in re.split(r'\n+', self.raw_html) if p.strip()]
            self.raw_html = "".join([f"<p>{p}</p>" for p in paras])
            
        for i, k in enumerate(self.all_kws):
            self.raw_html = re.sub(rf'\[?REP_KW_{i+1}\]?', k, self.raw_html, flags=re.IGNORECASE)
            if i == 0: self.raw_html = self.raw_html.replace('{{keyword}}', k)
        self.raw_html = re.sub(r'\[?REP_KW_\d+\]?', '', self.raw_html, flags=re.IGNORECASE)

        soup = BeautifulSoup(self.raw_html, 'html.parser')
        st.session_state.evolution_cache = f"{len(soup.find_all('h2'))} H2, {len(soup.find_all('p'))} P"
        
        h1 = soup.find('h1')
        self.final_title = h1.get_text(strip=True) if h1 else f"Bài: {self.all_kws[0]}"
        self.add_log(ui_log, f"🏷️ [THÔNG TIN BÀI VIẾT] Tiêu đề: {self.final_title}", "success")
        return True

    def step5_6_spin_and_dom(self, ui_log):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        for i, k in enumerate(self.all_kws): self.raw_html = re.sub(r'(?i)' + re.escape(k), f'__IRON_{i}__', self.raw_html, count=1)
        if not df_spin.empty:
            for _, r in df_spin.iterrows():
                o, v_str = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_VARIANTS', '')).strip()
                if o and v_str:
                    vars = [v.strip() for v in v_str.replace(';', ',').split(',') if v.strip()]
                    if vars and re.search(r'(?i)\b' + re.escape(o) + r'\b', self.raw_html):
                        self.raw_html = re.sub(r'(?i)\b' + re.escape(o) + r'\b', random.choice(vars), self.raw_html)
                        self.used_spins.append(o)
        for i, k in enumerate(self.all_kws): self.raw_html = self.raw_html.replace(f'__IRON_{i}__', k)

        soup = BeautifulSoup(self.raw_html, 'html.parser')
        ou, iu = [u.strip() for u in str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if u.strip()], [u.strip() for u in str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).split(',') if u.strip()]
        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        missed = []
        for k in self.all_kws:
            injected = False
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)' + re.escape(k), p.get_text()):
                    url, is_e = "", False
                    if self.injected_ext < self.out_lim and ou: url, is_e = random.choice(ou), True
                    elif self.injected_int < self.in_lim and iu: url, is_e = random.choice(iu), False
                    
                    if url:
                        p.replace_with(BeautifulSoup(re.sub(r'(?i)' + re.escape(k), lambda m: f"<a href='{url}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                        injected = True
                        if is_e: self.injected_ext += 1
                        else: self.injected_int += 1
                    break
            
            if not injected: missed.append(k)

        pfx_list = [
            "Bên cạnh đó, kinh nghiệm cho thấy việc hiểu rõ về {kw} mang lại góc nhìn toàn diện hơn.",
            "Nhiều người đi trước chia sẻ rằng, tối ưu hóa yếu tố {kw} thường giải quyết được vấn đề lõi.",
            "Trong quá trình triển khai, nếu áp dụng chuẩn xác {kw} sẽ thấy sự khác biệt rõ rệt.",
            "Thực tế, một chiến lược khôn ngoan không thể bỏ qua việc ứng dụng {kw} đúng lúc.",
            "Ngoài ra, Sếp hoàn toàn có thể cân nhắc giải pháp {kw} để tối ưu chi phí.",
            "Nếu Sếp đang cần thêm thông tin, chủ đề về {kw} này rất đáng để xem qua.",
            "Nhiều chuyên gia trong ngành cũng thường xuyên nhắc đến vai trò của {kw} trong hệ thống.",
            "Một yếu tố bổ trợ không kém phần quan trọng chính là {kw}.",
            "Đôi khi, nút thắt của vấn đề lại nằm ở việc chúng ta áp dụng {kw} như thế nào.",
            "Để có quyết định chính xác nhất, việc tham khảo thêm góc nhìn về {kw} là cần thiết."
        ]
        
        gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        gem_mods = [m.strip() for m in str(self.dashboard.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        
        if missed:
            for k in missed:
                url, is_e = "", False
                if self.injected_ext < self.out_lim and ou: url, is_e = random.choice(ou), True
                elif self.injected_int < self.in_lim and iu: url, is_e = random.choice(iu), False
                
                if not url: continue 
                
                gen_txt = ""
                if gem_keys:
                    try:
                        genai.configure(api_key=gem_keys[0])
                        fb_pmt = f"Chủ đề bài viết: '{self.final_title}'. Viết 1-2 câu tiếp nối tự nhiên (TỐI ĐA 30 CHỮ) để bổ sung ý cho một đoạn văn. BẮT BUỘC chứa chính xác cụm từ '{k}' tự nhiên trong câu. TRẢ VỀ VĂN BẢN TRƠN, KHÔNG DÙNG MARKDOWN."
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            gen_txt = ex.submit(lambda: genai.GenerativeModel(gem_mods[0]).generate_content(fb_pmt).text).result(timeout=15).strip()
                            gen_txt = gen_txt.replace('**', '')
                    except: pass
                
                if not gen_txt or len(gen_txt.split()) > 40 or k.lower() not in gen_txt.lower():
                    gen_txt = random.choice(pfx_list).replace('{kw}', k)
                
                pattern = re.compile(re.escape(k), re.IGNORECASE)
                gen_txt = pattern.sub(f"<a href='{url}'>{k}</a>", gen_txt, count=1)
                
                avail_p = [p for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20 and not p.find('a') and not p.find('img')]
                if avail_p:
                    target_p = random.choice(avail_p)
                    target_p.append(BeautifulSoup(f" {gen_txt}", 'html.parser'))
                else:
                    all_p = soup.find_all('p')
                    if len(all_p) > 1:
                        all_p[random.randint(1, len(all_p) - 1)].append(BeautifulSoup(f" {gen_txt}", 'html.parser'))
                    elif all_p:
                        all_p[0].append(BeautifulSoup(f" {gen_txt}", 'html.parser'))
                    
                self.add_log(ui_log, f"⚠️ AI sót '{k}', đã gắn bù liền mạch vào 1 đoạn văn đang có.", "warn")
                if is_e: self.injected_ext += 1
                else: self.injected_int += 1

        self.add_log(ui_log, f"🛠️ [GẮN LINK] {self.injected_ext}/{self.out_lim} Ext | {self.injected_int}/{self.in_lim} Int.", "success")

        mx_img = self.parse_rng(self.target_web.get('WS_IMG_LIMIT', 1), 1)
        req_img = min(len(self.all_kws), mx_img)
        self.add_log(ui_log, f"🖼️ [QUOTA ẢNH] Cần {req_img} ảnh. Bắt đầu Ping (Timeout 5s)...", "detail")
        df_img = self.db.get('IMAGE', pd.DataFrame())
        self.failed_imgs = []
        if not df_img.empty and 'IMG_URL' in df_img.columns and req_img > 0:
            df_img['IMG_STATUS'] = pd.to_numeric(df_img['IMG_STATUS'], errors='coerce').fillna(0)
            for _, r in df_img.sample(frac=1).sort_values('IMG_STATUS').iterrows():
                if len(self.used_imgs) >= req_img: break
                u_img = str(r['IMG_URL']).strip()
                try:
                    if requests.head(u_img, timeout=5).status_code == 200: self.used_imgs.append(u_img)
                    else: self.failed_imgs.append(u_img)
                except: self.failed_imgs.append(u_img)

        if self.used_imgs:
            if self.is_short_form or len(self.used_imgs) == 1:
                img_html = f"<br><p align='center'><img src='{self.used_imgs[0]}' alt='{self.all_kws[0]}'></p><br>"
                inserted = False
                for tag in soup.find_all(['p', 'li', 'h3']):
                    if re.search(r'(?i)' + re.escape(self.all_kws[0]), tag.get_text()):
                        tag.insert_after(BeautifulSoup(img_html, 'html.parser'))
                        inserted = True
                        break
                if not inserted and len(soup.find_all('p')) > 1: 
                    soup.find_all('p')[1].insert_after(BeautifulSoup(img_html, 'html.parser'))
            else:
                for idx, img_u in enumerate(self.used_imgs):
                    kw_t = self.all_kws[idx] if idx < len(self.all_kws) else self.all_kws[-1]
                    img_html = f"<br><p align='center'><img src='{img_u}' alt='{kw_t}'></p><br>"
                    inserted = False
                    for tag in soup.find_all(['p', 'li', 'h3']):
                        if re.search(r'(?i)' + re.escape(kw_t), tag.get_text()) and not tag.find_next_sibling('p', align='center'):
                            tag.insert_after(BeautifulSoup(img_html, 'html.parser'))
                            inserted = True
                            break
                    if not inserted and len(soup.find_all('p')) > idx * 2:
                        soup.find_all('p')[idx * 2].insert_after(BeautifulSoup(img_html, 'html.parser'))

        if self.failed_imgs: self.add_log(ui_log, f"⚠️ Đã loại {len(self.failed_imgs)} ảnh lỗi (Sẽ mark 999).", "warn")
        self.add_log(ui_log, f"🖼️ [GẮN ẢNH] DOM Inject thành công {len(self.used_imgs)} ảnh.")
        self.raw_html = str(soup); return True

    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "⚖️ [KCS] Máy quét AI bắt đầu chấm điểm...")
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        txt, k0 = soup.get_text(' ', strip=True), self.all_kws[0].lower()
        
        wc = len(txt.split())
        self.add_log(ui_log, f"📏 [ĐỘ DÀI] Bài viết đạt {wc} chữ (Target gốc: {self.min_w} - {self.max_w} chữ).", "detail")
        
        h1 = soup.find('h1')
        s_h1 = 30 if h1 and k0 in h1.get_text().lower() else 0
        s_h2 = 20 if any(k0 in h.get_text().lower() for h in soup.find_all('h2')) else 0
        s_bd = 10 if k0 in txt.lower() else 0
        s_alt = 10 if soup.find('img', alt=re.compile(r'(?i)' + re.escape(k0))) else 0
        den = (txt.lower().count(k0) * len(k0.split())) / max(len(txt.split()), 1) * 100
        s_den = 30 if 0.5 <= den <= 4.0 else 0
        
        seo = s_h1 + s_h2 + s_bd + s_alt + s_den
        lens = [len(s.split()) for s in re.split(r'[.!?\n]+', txt) if len(s.split()) > 3]
        ai = min(max(round(max(5, 50 - ((statistics.stdev(lens) if len(lens)>3 else 0) * 4)), 1), 2.0), 99.0)
        read = round(max(10, min(206.835 - (1.015 * (sum(lens) / max(len(lens), 1))) - 84.6 * 1.2, 100)), 1)
        
        self.kcs_metrics = {'SEO': min(seo, 100), 'AI': ai, 'READ': read}
        self.add_log(ui_log, f"   > KCS Tổng kết: Điểm SEO {seo}/100 | AI {ai}% | READ {read}/100", "detail")
        
        req = 35 if self.is_short_form else 70
        fails = []
        if seo < req: fails.append(f"SEO ({seo}/{req})")
        if ai > 20: fails.append(f"AI ({ai}%)")
        if read < 60: fails.append(f"Read ({read})")
        
        # CHẤM ĐIỂM NGHIÊM KHẮC: KHÔNG NỚI LỎNG
        if wc < self.min_w: fails.append(f"Viết Quá ngắn ({wc} < {self.min_w})")
        if wc > self.max_w: fails.append(f"Viết Quá dài ({wc} > {self.max_w})")
        
        if h1: h1.decompose()
        self.raw_html = str(soup)
        
        if fails:
            self.add_log(ui_log, f"❌ [KCS FAIL] Bị loại do: {', '.join(fails)}", "error")
            return "FAIL"
            
        self.add_log(ui_log, f"✅ [KCS PASSED] Đạt chuẩn.", "success")
        return "PENDING"

    def step8_sync_db(self, ui_log, final_result):
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            rep_ws = ss.worksheet('REPORT')
            hdrs = [str(h).strip() for h in rep_ws.row_values(1)]
            def gc(pfx): return next((h for h in hdrs if h.startswith(pfx)), pfx)
            
            row_d = {
                'REP_WS_NAME': str(self.target_web.get('WS_NAME', '')), 'REP_CREATED_AT': self.now_vn.strftime('%Y-%m-%d %H:%M'),
                'REP_TITLE': self.final_title, 'REP_IMG_COUNT': str(len(self.used_imgs)),
                'REP_KW_1': self.all_kws[0] if len(self.all_kws)>0 else "", 'REP_KW_2': self.all_kws[1] if len(self.all_kws)>1 else "",
                'REP_KW_3': self.all_kws[2] if len(self.all_kws)>2 else "", 'REP_KW_4': self.all_kws[3] if len(self.all_kws)>3 else "",
                'REP_KW_5': self.all_kws[4] if len(self.all_kws)>4 else "", 
                gc('REP_SEO_'): str(self.kcs_metrics.get('SEO', 0)), gc('REP_AI_'): f"{self.kcs_metrics.get('AI', 100)}%", gc('REP_READ'): str(self.kcs_metrics.get('READ', 0)),
                'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'), 'REP_POST_URL': "", 
                'REP_RESULT': final_result, 'REP_LOG': "\n".join(self.history_log), 'REP_HTML': self.raw_html if final_result == 'PENDING' else ""
            }
            rep_ws.append_row([row_d.get(h, "") for h in hdrs])
            
            if final_result == 'PENDING':
                ts = self.now_vn.strftime('%Y-%m-%d %H:%M')
                def batch_upd(ws, col_match, val_list, col_st, col_dt):
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

                batch_upd(ss.worksheet('KEYWORD'), 'KW_TEXT', self.all_kws, 'KW_STATUS', 'KW_DATE')
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
            
            self.add_log(ui_log, f"🎉 [HOÀN TẤT] Lưu DB xong. Trạng thái bài viết: {final_result}", "success")
                
        except Exception as e: self.add_log(ui_log, f"🛑 Lỗi ghi Database: {str(e)[:100]}", "error")

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
    p_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else 0
    
    b_val = dash_dict.get('BATCH_SIZE', '10')
    try:
        if '-' in str(b_val): batch = random.randint(int(str(b_val).split('-')[0]), int(str(b_val).split('-')[1]))
        else: batch = int(b_val)
    except: batch = 10
    
    c1.metric("Generated (Hôm nay)", f"{p_today} / {batch}")
    c2.metric("✅ Published (DONE)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'DONE']) if not df_rep.empty and 'REP_RESULT' in df_rep.columns else 0)
    c3.metric("⏳ Scheduled (PENDING)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if not df_rep.empty and 'REP_RESULT' in df_rep.columns else 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    btn_start = btn_col1.button("🔥 Bắt đầu Soạn bài AI", use_container_width=True, type="primary")
    btn_force = btn_col2.button("⚡ Ép Lên bài ngay", use_container_width=True)
    btn_refresh = btn_col3.button("🔄 Làm mới dữ liệu", use_container_width=True)
    
    if btn_refresh:
        load_data_from_gsheets.clear()
        st.rerun()
        
    if btn_force:
        st.markdown("---")
        info_msg = st.empty()
        info_msg.info("⏳ ĐANG KIỂM TRA BÀI QUÁ HẠN...")
        ui_log = st.empty()
        bot = AutoSEOPipeline(db_mock, [])
        
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            ws = ss.worksheet('REPORT')
            data = ws.get_all_values()
            ws_df = db_mock.get('WEBSITE', pd.DataFrame())
            
            if len(data) > 1:
                headers = [str(h).strip() for h in data[0]]
                idx_res = headers.index('REP_RESULT') if 'REP_RESULT' in headers else -1
                idx_pub = headers.index('REP_PUBLISH_DATE') if 'REP_PUBLISH_DATE' in headers else -1
                idx_html = headers.index('REP_HTML') if 'REP_HTML' in headers else -1
                idx_ws = headers.index('REP_WS_NAME') if 'REP_WS_NAME' in headers else -1
                idx_title = headers.index('REP_TITLE') if 'REP_TITLE' in headers else -1

                if idx_res != -1 and idx_pub != -1:
                    upd, count = [], 0
                    now = get_vn_now()
                    for i, row in enumerate(data[1:], 2):
                        if len(row) > max(idx_res, idx_pub) and row[idx_res].strip() == 'PENDING':
                            try:
                                pub_dt = VN_TZ.localize(datetime.datetime.strptime(str(row[idx_pub]).strip(), '%Y-%m-%d %H:%M'))
                                is_due = pub_dt <= now
                            except: is_due = False
                            
                            if is_due:
                                ws_name = row[idx_ws] if idx_ws != -1 else ""
                                title = row[idx_title] if idx_title != -1 else "No Title"
                                html_content = row[idx_html] if idx_html != -1 else ""
                                
                                bot.add_log(ui_log, f"➤ Xử lý bài: '{title}' -> Web: {ws_name}")
                                
                                web_info = ws_df[ws_df['WS_NAME'].astype(str).str.strip() == ws_name.strip()]
                                if not web_info.empty:
                                    w_row = web_info.iloc[0]
                                    success, msg = post_to_cms(w_row, title, html_content, dash_dict)
                                    if success:
                                        bot.add_log(ui_log, f"✅ {msg}", "success")
                                        upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_res+1)}', 'values': [['DONE']]})
                                        count += 1
                                    else:
                                        bot.add_log(ui_log, f"🛑 {msg}", "error")
                                else:
                                    bot.add_log(ui_log, f"⚠️ Không tìm thấy cấu hình tài khoản cho Web '{ws_name}'", "warn")
                                    
                    info_msg.empty()
                    if upd:
                        ws.batch_update(upd)
                        st.success(f"🎉 Đã chốt sổ và bắn thành công {count} bài quá hạn!")
                        time.sleep(2)
                        st.rerun()
                    else: 
                        auto_time = dash_dict.get('AUTO_RUN_TIME', '')
                        bot.add_log(ui_log, f"ℹ️ Không có bài viết ở trạng thái PENDING hoặc đang ngoài giờ lên bài lúc ({auto_time}). Kiểm tra lại nhé Ní ^^!", "warn")
                else: bot.add_log(ui_log, "🛑 Không tìm thấy cột trạng thái trong Sheet REPORT.", "error")
        except Exception as e: bot.add_log(ui_log, f"🛑 Lỗi hệ thống Đăng bài: {str(e)[:150]}", "error")

    if btn_start:
        st.markdown("---")
        st.info("⏳ HỆ THỐNG ĐANG SOẠN BÀI TỰ ĐỘNG... BẠN CỨ ĐỂ YÊN MÀN HÌNH NÀY CHO TỚI KHI BÁO XONG NHA!")
        load_data_from_gsheets.clear()
        
        ui_log = st.empty()
        needed = batch - p_today
        if needed <= 0: ui_log.markdown('<div class="log-box"><span class="log-error">🛑 Đã đạt BATCH_SIZE hôm nay. Không chạy thêm.</span></div>', unsafe_allow_html=True)
        else:
            master_logs = []
            for i in range(needed):
                bot = AutoSEOPipeline(db_mock, master_logs)
                bot.add_log(ui_log, f"<br>🚀 --- BẮT ĐẦU CHẠY BÀI {i+1}/{needed} ---", "success")
                st_t = time.time()
                try:
                    if bot.step1_allocate_slot(ui_log):
                        if bot.step2_3_keyword_and_serp(ui_log):
                            if bot.step4_llm_generation(ui_log):
                                bot.step5_6_spin_and_dom(ui_log)
                                res = bot.step7_qa_validation(ui_log)
                                bot.step8_sync_db(ui_log, res)
                                db_mock = load_data_from_gsheets()
                except Exception as e: bot.add_log(ui_log, f"🛑 Lỗi chí mạng: {str(e)[:150]}", "error")
                if time.time() - st_t > 300:
                    bot.add_log(ui_log, "🛑 Quá 5 phút, tự ngắt để cứu hệ thống.", "error")
                    break
            bot.add_log(ui_log, "<br>✅ TOÀN BỘ TIẾN TRÌNH HOÀN TẤT.", "success")
            st.success("🎉 TẠO BÀI XONG! BẤM LÀM MỚI Ở TRÊN ĐỂ CẬP NHẬT KẾT QUẢ NHA SẾP!")

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
