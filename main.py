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
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
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
    except Exception as e: return None

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
        self.is_short_form, self.serp_style = False, ""
        if 'evolution_cache' not in st.session_state: st.session_state.evolution_cache = ""

    # FIX LỖI #6: Khôi phục hàm safe_int bị thiếu
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
        self.target_length = random.randint(mn, mx) if not self.is_short_form else random.randint(mn, mx)//2
        
        s_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        c_list = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        serp_chunks = []
        scraped_urls = []

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
                self.serp_style = "\n\n".join(serp_chunks)[:5000]
                # FIX LỖI #4: Sắp xếp Link SERP đẹp đẽ xuống dòng
                url_list_str = "\n".join([f"   + {u}" for u in scraped_urls])
                self.add_log(ui_log, f"✅ [SERP] Đã trộn data từ {len(serp_chunks)} đối thủ:\n{url_list_str}", "success")
            else:
                self.serp_style = "Văn phong chuyên gia, logic."
                self.add_log(ui_log, f"⚠️ [SERP] Cào thất bại, dùng Internal Cache.", "warn")
        else: self.serp_style = "Văn phong chuyên gia."
        return True

    def step4_llm_generation(self, ui_log) -> bool:
        keys_to_pull = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        pmts = {k: self.pick_random_prompt_variant(self.dashboard.get(k, '')) for k in keys_to_pull}
        
        # FIX LỖI #5: In chi tiết nội dung Prompt để Sếp theo dõi
        self.add_log(ui_log, f"🧠 [PROMPT BUILDER] Nội dung bốc ngẫu nhiên từ Dashboard:", "detail")
        for k, v in pmts.items():
            snippet = (v[:150] + '...') if len(v) > 150 else v
            self.add_log(ui_log, f"   ➤ **{k}**: {snippet}", "detail")

        dist = self.target_length // max(len(self.all_kws), 1)
        force = f"""\n[ÉP LUẬT TỐI THƯỢNG - SOP MẶC ĐỊNH]:
        1. CẤM CHÀO HỎI (Cấm 'Kính thưa', 'Chào các Sếp'). Vào thẳng Sapo.
        2. H1: Chứa "{self.all_kws[0]}" ở GIỮA/CUỐI. Cấm đặt đầu câu.
        3. THUẬT TOÁN RẢI TỪ KHÓA:
        - Từ khóa chính "{self.all_kws[0]}" (x3). Các từ "{', '.join(self.all_kws[1:])}" mỗi từ x1.
        - Bắt buộc rải đều từ khóa tuần tự từ trên xuống. Khoảng cách xấp xỉ {dist} chữ. Đặt tự nhiên lọt thỏm giữa câu, KHÔNG mặc định đầu/cuối câu. Cấm nhồi nhét 1 chỗ.
        4. ĐỊNH DẠNG HTML (QUAN TRỌNG):
        - BẮT BUỘC dùng thẻ <ul> và <li> nếu có liệt kê danh sách.
        - TUYỆT ĐỐI KHÔNG DÙNG ký tự Markdown như `*` hay `-` để gạch đầu dòng hay liệt kê trên 1 dòng.
        - KHÔNG in đậm `**` từ khóa.
        5. CẤU TRÚC ĐOẠN VĂN: Cấm viết dài thoòng. Ngắn dài đan xen (3-4 câu/đoạn). Mỗi đoạn bọc trong 1 thẻ <p> riêng biệt.
        6. TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>."""
        
        m_prompt = f"{pmts['PROMPT_TEMPLATE']}\n{pmts['PROMPT_CONTENT_STRATEGY']}\n{pmts['PROMPT_KEYWORD_SEARCH']}\n{pmts['PROMPT_SERP_STYLE']}\n[SERP Data Hỗn Hợp]:\n{self.serp_style}\n{pmts['PROMPT_SEO_GLOBAL_RULE']}\n{pmts['PROMPT_AI_HUMANIZER']}\n{force}"
        m_prompt = m_prompt.replace('{{ws_persona}}', str(self.target_web.get('WS_PERSONA', ''))).replace('{{kw_intent}}', str(self.main_kw_row.get('KW_INTENT', ''))).replace('{{keyword}}', self.all_kws[0]).replace('{{word_count}}', str(self.target_length))
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
                self.add_log(ui_log, f"🌐 [API CALL] Gemini ({gm})...", "detail")
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
                    self.add_log(ui_log, f"🌐 [API CALL] OpenRouter ({om})...", "detail")
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
            self.add_log(ui_log, "🛑 [FATAL] Toàn bộ API đều sập hoặc không phản hồi. Xin kiểm tra lại Quota!", "error")
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
        
        # FIX LỖI #1: Khôi phục Log in Tiêu đề bài viết
        h1 = soup.find('h1')
        self.final_title = h1.get_text(strip=True) if h1 else f"Bài: {self.all_kws[0]}"
        self.add_log(ui_log, f"🏷️ [THÔNG TIN BÀI VIẾT] Web: {self.target_web.get('WS_NAME','')} | Tiêu đề: {self.final_title}", "success")
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

        # FIX LỖI #2: CHỐNG SPAM VÀ ĐẾM ĐÚP
        missed = []
        for k in self.all_kws:
            url, is_e = ("", False)
            if self.injected_ext < self.out_lim and ou: url, is_e = random.choice(ou), True
            elif self.injected_int < self.in_lim and iu: url, is_e = random.choice(iu), False
            if not url: continue 
            
            injected = False
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)' + re.escape(k), p.get_text()):
                    p.replace_with(BeautifulSoup(re.sub(r'(?i)' + re.escape(k), lambda m: f"<a href='{url}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                    injected = True
                    if is_e: self.injected_ext += 1
                    else: self.injected_int += 1
                    break
            
            # Ghi nhận từ khóa bị sót nhưng CHƯA cộng Quota
            if not injected: missed.append((k, url, is_e))

        # RẢI LINK SÓT BẰNG CÁCH TẠO THẺ P MỚI HOÀN TOÀN Ở GIỮA BÀI (Chống nối đuôi rác)
        if missed:
            pfxs = ["Sếp có thể tham khảo thêm dịch vụ", "Gợi ý thêm một lựa chọn an toàn là", "Tìm hiểu thêm thông tin về"]
            all_p_tags = soup.find_all('p')
            
            for k, u, is_e in missed:
                new_p = BeautifulSoup(f"<p>{random.choice(pfxs)} <a href='{u}'>{k}</a>.</p>", 'html.parser')
                # Chèn thẻ P mới vào các vị trí ngẫu nhiên ở giữa bài viết (tránh đầu và cuối)
                if len(all_p_tags) > 4:
                    idx = random.randint(2, len(all_p_tags) - 2)
                    all_p_tags[idx].insert_after(new_p)
                elif all_p_tags:
                    all_p_tags[0].insert_after(new_p)
                else:
                    soup.append(new_p)
                    
                self.add_log(ui_log, f"⚠️ AI sót '{k}', đã tạo 1 đoạn văn mới rải rác vào GIỮA bài.", "warn")
                
                # Cộng Quota sau khi đã chèn thành công
                if is_e: self.injected_ext += 1
                else: self.injected_int += 1

        self.add_log(ui_log, f"🛠️ [GẮN LINK] Đã ép đủ Quota: {self.injected_ext}/{self.out_lim} Ext | {self.injected_int}/{self.in_lim} Int.", "success")

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
                for p in soup.find_all('p'):
                    if re.search(r'(?i)' + re.escape(self.all_kws[0]), p.get_text()):
                        p.insert_after(BeautifulSoup(img_html, 'html.parser')); inserted = True; break
                if not inserted and soup.find_all('p'): soup.find_all('p')[0].insert_after(BeautifulSoup(img_html, 'html.parser'))
            else:
                for idx, img_u in enumerate(self.used_imgs):
                    kw_t = self.all_kws[idx] if idx < len(self.all_kws) else self.all_kws[-1]
                    img_html = f"<br><p align='center'><img src='{img_u}' alt='{kw_t}'></p><br>"
                    inserted = False
                    for p in soup.find_all('p'):
                        if re.search(r'(?i)' + re.escape(kw_t), p.get_text()) and not p.find_next_sibling('p', align='center'):
                            p.insert_after(BeautifulSoup(img_html, 'html.parser')); inserted = True; break
                    if not inserted and len(soup.find_all('p')) > idx:
                        soup.find_all('p')[idx].insert_after(BeautifulSoup(img_html, 'html.parser'))

        if self.failed_imgs: self.add_log(ui_log, f"⚠️ Đã loại {len(self.failed_imgs)} ảnh lỗi (Sẽ mark 999).", "warn")
        self.add_log(ui_log, f"🖼️ [GẮN ẢNH] DOM Inject thành công {len(self.used_imgs)} ảnh.")
        self.raw_html = str(soup); return True

    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "⚖️ [KCS] Chấm điểm và xóa H1 lặp...")
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        txt, k0 = soup.get_text(' ', strip=True), self.all_kws[0].lower()
        h1 = soup.find('h1')
        s_h1 = 30 if h1 and k0 in h1.get_text().lower() else 0
        s_h2 = 20 if any(k0 in h.get_text().lower() for h in soup.find_all('h2')) else 0
        s_bd = 10 if k0 in txt.lower() else 0
        s_alt = 10 if soup.find('img', alt=re.compile(r'(?i)' + re.escape(k0))) else 0
        den = (txt.lower().count(k0) * len(k0.split())) / max(len(txt.split()), 1) * 100
        s_den = 30 if 0.5 <= den <= 4.0 else 0
        seo = s_h1 + s_h2 + s_bd + s_alt + s_den
        lens = [len(s.split()) for s in re.split(r'[.!?\n]+', txt) if len(s.split()) > 3]
        ai, rd = min(max(round(max(5, 50-((statistics.stdev(lens) if len(lens)>3 else 0)*4)),1), 2.0), 99.0), round(max(10, min(206.835-(1.015*(sum(lens)/max(len(lens),1)))-84.6*1.2, 100)), 1)
        self.kcs_metrics = {'SEO': seo, 'AI': ai, 'READ': rd}
        self.add_log(ui_log, f"   > SEO {seo}/100 | AI {ai}% | READ {rd}/100", "detail")
        if h1: h1.decompose()
        self.raw_html = str(soup).strip()
        req = 35 if self.is_short_form else 70
        if seo < req or ai > 20 or rd < 60: return "FAIL"
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
                'REP_KW_1': self.all_kws[0], 'REP_KW_2': self.all_kws[1] if len(self.all_kws)>1 else "",
                'REP_KW_3': self.all_kws[2] if len(self.all_kws)>2 else "", 'REP_KW_4': self.all_kws[3] if len(self.all_kws)>3 else "",
                'REP_KW_5': self.all_kws[4] if len(self.all_kws)>4 else "", 
                gc('REP_SEO_'): str(self.kcs_metrics.get('SEO', 0)), gc('REP_AI_'): f"{self.kcs_metrics.get('AI', 100)}%", gc('REP_READ'): str(self.kcs_metrics.get('READ', 0)),
                'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'), 'REP_POST_URL': "", 
                'REP_RESULT': final_result, 'REP_LOG': "\n".join(self.history_log), 'REP_HTML': self.raw_html if final_result == 'PENDING' else ""
            }
            rep_ws.append_row([row_d.get(h, "") for h in hdrs])
            
            # FIX LỖI #3: Phục hồi Báo cáo kết quả
            self.add_log(ui_log, f"🎉 [HOÀN TẤT] Lưu DB xong. Trạng thái bài viết: {final_result}", "success")
            
            if final_result == 'PENDING':
                ts = self.now_vn.strftime('%Y-%m-%d %H:%M')
                def batch(w, k_col, vals, col_s, col_d):
                    s, d = ss.worksheet(w), ss.worksheet(w).get_all_values()
                    if len(d) > 1:
                        h = [str(x).strip() for x in d[0]]
                        im, is_, idt = h.index(k_col), h.index(col_s) if col_s in h else -1, h.index(col_d) if col_d in h else -1
                        u = []
                        for i, r in enumerate(d[1:], 2):
                            if r[im].strip() in vals:
                                if is_ != -1: u.append({'range': f'{gspread.utils.rowcol_to_a1(i, is_+1)}', 'values': [[self.safe_int(r[is_] or 0)+1]]})
                                if idt != -1: u.append({'range': f'{gspread.utils.rowcol_to_a1(i, idt+1)}', 'values': [[ts]]})
                        if u: s.batch_update(u)
                batch('KEYWORD', 'KW_TEXT', self.all_kws, 'KW_STATUS', 'KW_DATE')
                batch('IMAGE', 'IMG_URL', self.used_imgs, 'IMG_STATUS', 'IMG_DATE')
                if self.used_spins: batch('SPIN', 'SPIN_ORIGINAL', self.used_spins, None, 'SPIN_DATE')
                
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
                        
        except Exception as e: self.add_log(ui_log, f"🛑 Lỗi DB: {e}", "error")

# ==========================================
# 🖥 UI
# ==========================================
db = load_data_from_gsheets()
if not db: st.stop()
d_rep, dash = db['REPORT'], {str(k).strip(): str(v).strip() for k, v in zip(db['DASHBOARD']['DATA_KEY'], db['DASHBOARD']['DATA_CONTENT'])}

st.title(f"🛡️ {dash.get('PROJECT_NAME', 'Auto SEO Pipeline')}")
st.markdown("---")
t1, t2, t3 = st.tabs(["📊 DASHBOARD", "📋 CONTENT", "🗄️ DATABASE"])

with t1:
    tdy = get_vn_now().strftime('%Y-%m-%d')
    p_tdy = len(d_rep[d_rep['REP_CREATED_AT'].astype(str).str.startswith(tdy)]) if not d_rep.empty else 0
    try: b_val = int(str(dash.get('BATCH_SIZE', '10')).split('-')[0])
    except: b_val = 10
    c1, c2, c3 = st.columns(3)
    c1.metric("Generated Today", f"{p_tdy}/{b_val}")
    c2.metric("DONE", len(d_rep[d_rep['REP_RESULT'] == 'DONE']) if not d_rep.empty else 0)
    c3.metric("PENDING", len(d_rep[d_rep['REP_RESULT'] == 'PENDING']) if not d_rep.empty else 0)
    st.markdown("<br>", unsafe_allow_html=True)
    bc1, bc2, bc3 = st.columns(3)
    b_run, b_frc, b_ref = bc1.button("🔥 Soạn bài AI", use_container_width=True, type="primary"), bc2.button("⚡ Ép Lên bài ngay", use_container_width=True), bc3.button("🔄 Làm mới", use_container_width=True)
    
    if b_ref: load_data_from_gsheets.clear(); st.rerun()
    if b_frc:
        st.info("⏳ ĐANG POST BÀI..."); ui = st.empty(); bot = AutoSEOPipeline(db, [])
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            ws, data = ss.worksheet('REPORT'), ss.worksheet('REPORT').get_all_values()
            df_w = db['WEBSITE']
            if len(data) > 1:
                h = [str(x).strip() for x in data[0]]
                ir, ip, ih, iw, it = h.index('REP_RESULT'), h.index('REP_PUBLISH_DATE'), h.index('REP_HTML'), h.index('REP_WS_NAME'), h.index('REP_TITLE')
                upds, cnt = [], 0
                for i, r in enumerate(data[1:], 2):
                    if r[ir].strip() == 'PENDING' and str(r[ip]).startswith(tdy):
                        bot.add_log(ui, f"➤ Đăng: '{r[it]}' -> {r[iw]}")
                        w_row = df_w[df_w['WS_NAME'].astype(str).str.strip() == r[iw].strip()]
                        if not w_row.empty:
                            ok, msg = post_to_cms(w_row.iloc[0], r[it], r[ih], dash)
                            if ok:
                                bot.add_log(ui, f"✅ {msg}", "success")
                                upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, ir+1)}', 'values': [['DONE']]})
                                cnt += 1
                            else: bot.add_log(ui, f"🛑 {msg}", "error")
                if upds: ws.batch_update(upds); st.success(f"🎉 Xong {cnt} bài!"); time.sleep(1); st.rerun()
        except Exception as e: st.error(f"Lỗi: {e}")

    if b_run:
        load_data_from_gsheets.clear(); ui = st.empty(); need = b_val - p_tdy
        if need > 0:
            m_logs = []
            for i in range(need):
                bot = AutoSEOPipeline(db, m_logs)
                bot.add_log(ui, f"<br>🚀 --- BÀI {i+1}/{need} ---", "success")
                st_t = time.time()
                try:
                    if bot.step1_allocate_slot(ui) and bot.step2_3_keyword_and_serp(ui) and bot.step4_llm_generation(ui):
                        bot.step5_6_spin_and_dom(ui); bot.step8_sync_db(ui, bot.step7_qa_validation(ui))
                        db = load_data_from_gsheets()
                except Exception as e: bot.add_log(ui, f"🛑 Lỗi: {e}", "error")
                if time.time() - st_t > 300: break
            st.success("🎉 HOÀN TẤT!")

with t2:
    if not d_rep.empty:
        df_vn = d_rep[['REP_CREATED_AT', 'REP_PUBLISH_DATE', 'REP_TITLE', 'REP_WS_NAME', 'REP_RESULT']].copy()
        df_vn.columns = ['Ngày tạo bài', 'Ngày đăng bài', 'Tiêu đề', 'Trang web', 'Trạng thái']
        st.dataframe(df_vn.tail(15), use_container_width=True, hide_index=True)
        sel = st.selectbox("🔍 Soi Log:", d_rep['REP_TITLE'].tolist()[::-1])
        if sel:
            r = d_rep[d_rep['REP_TITLE'] == sel].iloc[0]
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="log-box">{str(r["REP_LOG"]).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            c2.text_area("HTML:", str(r["REP_HTML"]), height=800)

with t3:
    st.dataframe(d_rep, use_container_width=True)
