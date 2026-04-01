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
# 🔐 BẢO MẬT
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
# 🛠 DATA CONNECT
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
# 🚀 POST CMS
# ==========================================
def post_to_cms(website_row, title, html_content, dash_config):
    blog_receiver_email = str(website_row.get('WS_BLOG_CONTENT', '')).strip()
    ws_user = str(website_row.get('WS_LOGIN_USER', '')).strip()
    ws_pass = str(website_row.get('WS_LOGIN_PASS', '')).strip()
    
    if "@blogger.com" in blog_receiver_email.lower():
        smtp_email = dash_config.get('EMAIL_SENDER', '').strip()
        smtp_pass = dash_config.get('EMAIL_SENDER_PASSWORD', '').strip()
        if not smtp_email or not smtp_pass: return False, f"Thiếu EMAIL_SENDER / PASSWORD."
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = smtp_email, blog_receiver_email, title
            msg.attach(MIMEText(html_content, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(smtp_email, smtp_pass) 
            server.send_message(msg)
            server.quit()
            return True, f"Bắn bài lên Blogspot thành công: {blog_receiver_email}"
        except Exception as e: return False, f"Lỗi gửi Mail: {e}"
    else:
        domain = str(website_row.get('WS_LINK_IN_BACKLINK', '')).split(',')[0].strip()
        if not domain: return False, "Thiếu domain WP."
        api_url = f"{domain.rstrip('/')}/wp-json/wp/v2/posts"
        try:
            res = requests.post(api_url, auth=(ws_user, ws_pass), json={'title': title, 'content': html_content, 'status': 'publish'}, timeout=30)
            if res.status_code in [200, 201]: return True, f"Đăng WordPress thành công (ID: {res.json().get('id')})"
            return False, f"Lỗi WP API: {res.text[:100]}"
        except Exception as e: return False, f"Lỗi WP: {e}"

# ==========================================
# 🤖 CORE ENGINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, data_frames, master_log_list):
        self.db = data_frames
        self.dashboard = {str(k).strip(): str(v).strip() for k, v in zip(self.db.get('DASHBOARD', pd.DataFrame())['DATA_KEY'], self.db.get('DASHBOARD', pd.DataFrame())['DATA_CONTENT'])}
        self.now_vn = get_vn_now()
        self.history_log = master_log_list
        self.target_web, self.publish_time, self.main_kw_row = None, None, None
        self.all_kws, self.target_length, self.raw_html, self.final_title = [], 0, "", ""
        self.kcs_metrics, self.used_imgs, self.used_spins = {}, [], []
        self.out_lim, self.in_lim, self.injected_ext, self.injected_int = 0, 0, 0, 0
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

    def get_min_max(self, val_str, d_min, d_max):
        try:
            s = str(val_str).strip()
            if '-' in s:
                p = s.split('-')
                return min(int(p[0]), int(p[1])), max(int(p[0]), int(p[1]))
            return int(s), int(s)
        except: return d_min, d_max

    def parse_random_range(self, val_str, default=0):
        mn, mx = self.get_min_max(val_str, default, default)
        return random.randint(mn, mx)

    def pick_random_prompt_variant(self, text):
        parts = [p.strip() for p in re.split(r'\|\|\|', str(text)) if p.strip()]
        return random.choice(parts) if parts else str(text).strip()

    def step1_allocate_slot(self, ui_log) -> bool:
        df_rep, df_web = self.db.get('REPORT', pd.DataFrame()), self.db.get('WEBSITE', pd.DataFrame())
        batch_size = self.parse_random_range(self.dashboard.get('BATCH_SIZE', 10), 10)
        max_days = self.parse_random_range(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        try:
            trange = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
            h1, m1 = map(int, trange[0].strip().split(':'))
            h2, m2 = map(int, trange[1].strip().split(':'))
            min_s, max_s = self.get_min_max(self.dashboard.get('POST_SPACING_MINUTES', '30-90'), 30, 90)
        except: return self.add_log(ui_log, "🛑 Lỗi giờ.", "error") or False

        today_str = self.now_vn.strftime('%Y-%m-%d')
        if len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(today_str)]) >= batch_size: return False

        avail_webs = df_web.sample(frac=1).reset_index(drop=True)
        for d_off in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=d_off)
            day_x_str = day_x.strftime('%Y-%m-%d')
            for _, web in avail_webs.iterrows():
                ws_name, ws_limit = str(web.get('WS_NAME', '')).strip(), self.parse_random_range(web.get('WS_POST_LIMIT', 1), 1)
                day_posts = df_rep[(df_rep['REP_WS_NAME'] == ws_name) & (df_rep['REP_PUBLISH_DATE'].astype(str).str.startswith(day_x_str))] if not df_rep.empty else pd.DataFrame()
                
                self.add_log(ui_log, f"🔍 [QUOTA] Local '{ws_name}' ({day_x_str}): {len(day_posts)}/{ws_limit}", "quota")
                if len(day_posts) < ws_limit:
                    st_v, ed_v = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(h1, m1))), VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(h2, m2)))
                    if d_off == 0 and self.now_vn > ed_v: continue 
                    base = max(self.now_vn, st_v) if d_off == 0 else st_v
                    try: last_t = VN_TZ.localize(datetime.datetime.strptime(str(day_posts['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M'))
                    except: last_t = base
                    
                    pub_t = max(last_t, base) + datetime.timedelta(minutes=random.randint(min_s, max_s)) if not day_posts.empty else base + datetime.timedelta(minutes=random.randint(0, 30))
                    pub_t = max(pub_t, self.now_vn + datetime.timedelta(minutes=5))
                    if pub_t > ed_v: continue 
                    self.target_web, self.publish_time = web, pub_t
                    self.add_log(ui_log, f"✅ [CHỐT SLOT] {ws_name} | Lên lịch: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
        return False

    def step2_3_keyword_and_serp(self, ui_log) -> bool:
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        self.main_kw_row = df_kw.sample(frac=1).sort_values('KW_STATUS').iloc[0]
        main_kw = str(self.main_kw_row['KW_TEXT']).strip()
        
        self.out_lim, self.in_lim = self.parse_random_range(self.target_web.get('WS_LINK_OUT_LIMIT', 0)), self.parse_random_range(self.target_web.get('WS_LINK_IN_LIMIT', 0))
        total_needed = max(1, self.out_lim + self.in_lim)
        
        subs = df_kw[(df_kw['KW_TEXT'] != main_kw) & (df_kw['KW_CONTENT'] == str(self.main_kw_row.get('KW_CONTENT', '')))].head(max(0, total_needed - 1))['KW_TEXT'].tolist()
        self.all_kws = [main_kw] + subs
        self.add_log(ui_log, f"📐 [KWs] Cần {total_needed} KWs -> Gom: {', '.join(self.all_kws)}", "quota")

        min_w, max_w = self.get_min_max(self.dashboard.get('WORD_COUNT_RANGE', '900-1200'), 900, 1200)
        self.target_length = random.randint(min_w, max_w) if len(self.all_kws) >= 3 else random.randint(min_w, max_w)//2
        
        s_key, c_list = self.dashboard.get('SERPAPI_KEY', '').strip(), [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        self.serp_style = "Văn phong chuyên gia."
        if s_key:
            try:
                res = requests.get("https://serpapi.com/search", params={"q": main_kw, "hl": "vi", "gl": "vn", "api_key": s_key}, timeout=15).json().get("organic_results", [])
                links = [r["link"] for r in res[:10] if c_list and any(c in r.get("link","") for c in c_list)] or [r["link"] for r in res[:3]]
                if links:
                    rh = requests.get(links[0], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    if rh.status_code == 200:
                        soup = BeautifulSoup(rh.text, 'html.parser')
                        self.serp_style = "\n".join([t.get_text(strip=True) for t in soup.find_all(['h2', 'h3', 'p'])])[:3000]
                        self.add_log(ui_log, f"✅ [SERP] Trích văn phong từ: {links[0]}")
            except: pass
        return True

    def step4_llm_generation(self, ui_log) -> bool:
        req_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        pmts = {k: self.pick_random_prompt_variant(self.dashboard.get(k, '')) for k in req_keys}
        if any(not v for v in pmts.values()): return self.add_log(ui_log, "🛑 Thiếu Prompt.", "error") or False

        self.add_log(ui_log, f"🧠 [PROMPT BUILDER] Đang rắp ráp lệnh từ 6 Keys:", "detail")
        for k in req_keys: self.add_log(ui_log, f"   + {k} (Spin variant)", "detail")

        dist = self.target_length // max(len(self.all_kws), 1)
        force_kw = f"""
        \n[LỆNH ÉP TUÂN THỦ]:
        1. CẤM CHÀO HỎI "Kính thưa", "Chào các Sếp". VÀO THẲNG VẤN ĐỀ.
        2. H1: Chứa "{self.all_kws[0]}" NGẪU NHIÊN ở GIỮA hoặc CUỐI (CẤM ĐỂ Ở ĐẦU).
        3. TỪ KHÓA: "{self.all_kws[0]}" rải 2-3 lần. Các từ "{', '.join(self.all_kws[1:])}" xuất hiện đúng 1 lần. Tuyệt đối ko dùng ** cho từ khóa.
        4. H3: Phải đánh số thứ tự (1., 2.,...). ĐOẠN VĂN: Cấm dài bằng nhau, đan xen ngắn dài.
        5. ĐỘ DÀI: ~{self.target_length} chữ. TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>.
        """
        
        m_prompt = f"{pmts['PROMPT_TEMPLATE']}\n{pmts['PROMPT_CONTENT_STRATEGY']}\n{pmts['PROMPT_KEYWORD_SEARCH']}\n{pmts['PROMPT_SERP_STYLE']}\n[Data]:\n{self.serp_style}\n{pmts['PROMPT_SEO_GLOBAL_RULE']}\n{pmts['PROMPT_AI_HUMANIZER']}\n{force_kw}"
        m_prompt = m_prompt.replace('{{ws_persona}}', str(self.target_web.get('WS_PERSONA', ''))).replace('{{kw_intent}}', str(self.main_kw_row.get('KW_INTENT', ''))).replace('{{keyword}}', self.all_kws[0]).replace('{{word_count}}', str(self.target_length))
        for i, k in enumerate(self.all_kws): m_prompt = re.sub(rf'\[?REP_KW_{i+1}\]?', k, m_prompt, flags=re.IGNORECASE)

        mods = [m.strip() for m in str(self.dashboard.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        
        for m in mods:
            for k in keys:
                genai.configure(api_key=k)
                self.add_log(ui_log, f"🌐 [API CALL] Gemini ({m})...", "detail")
                try: 
                    self.raw_html = genai.GenerativeModel(m).generate_content(m_prompt).text
                    break
                except Exception as e: self.add_log(ui_log, f"⚠️ API sập (429/503) -> Chuyển Key/Model dự phòng...", "warn")
            if self.raw_html: break

        if not self.raw_html: return self.add_log(ui_log, "🛑 Toàn bộ API chết.", "error") or False
            
        self.raw_html = re.sub(r'```html|```', '', self.raw_html).strip()
        self.raw_html = re.sub(r'\*\*(.*?)\*\*', r'\1', self.raw_html) # Xóa sạch in đậm
        
        for i, k in enumerate(self.all_kws):
            self.raw_html = re.sub(rf'\[?REP_KW_{i+1}\]?', k, self.raw_html, flags=re.IGNORECASE)
            if i==0: self.raw_html = self.raw_html.replace('{{keyword}}', k)
        self.raw_html = re.sub(r'\[?REP_KW_\d+\]?', '', self.raw_html, flags=re.IGNORECASE) # Xóa mã dư

        soup = BeautifulSoup(self.raw_html, 'html.parser')
        st.session_state.evolution_cache = f"{len(soup.find_all('h2'))}H2,{len(soup.find_all('p'))}P"
        h1_m = soup.find('h1')
        self.final_title = h1_m.get_text(strip=True) if h1_m else f"Bài: {self.all_kws[0]}"
        self.add_log(ui_log, f"🏷️ [THÔNG TIN BÀI VIẾT] Web: {self.target_web.get('WS_NAME','')} | Tiêu đề: {self.final_title}", "success")
        return True

    def step5_6_dom(self, ui_log):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        for i, k in enumerate(self.all_kws): self.raw_html = re.sub(r'(?i)' + re.escape(k), f'__IRON_{i}__', self.raw_html, count=1)
        if not df_spin.empty:
            for _, r in df_spin.iterrows():
                o, v_str = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_VARIANTS', r.get('SPIN_REPLACE', ''))).strip()
                if o and v_str:
                    vars = [v.strip() for v in v_str.replace(';', ',').split(',') if v.strip()]
                    if vars and re.search(r'(?i)\b' + re.escape(o) + r'\b', self.raw_html):
                        self.raw_html = re.sub(r'(?i)\b' + re.escape(o) + r'\b', random.choice(vars), self.raw_html)
                        self.used_spins.append(o)
        for i, k in enumerate(self.all_kws): self.raw_html = self.raw_html.replace(f'__IRON_{i}__', k)

        soup = BeautifulSoup(self.raw_html, 'html.parser')
        ou = [u.strip() for u in str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if u.strip()]
        iu = [u.strip() for u in str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).split(',') if u.strip()]
        
        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        # GẮN LINK THÔNG MINH - FIX LỖI 4/3
        missed = []
        for k in self.all_kws:
            url, is_e = ("", False)
            if self.injected_ext < self.out_lim and ou: url, is_e = random.choice(ou), True
            elif self.injected_int < self.in_lim and iu: url, is_e = random.choice(iu), False
            
            if not url: continue # Hết Quota
            
            # TRỪ QUOTA NGAY KHI CHỌN URL
            if is_e: self.injected_ext += 1
            else: self.injected_int += 1

            injected = False
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)' + re.escape(k), p.get_text()):
                    p.replace_with(BeautifulSoup(re.sub(r'(?i)' + re.escape(k), lambda m: f"<a href='{url}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                    injected = True; break
            if not injected: missed.append((k, url))

        # ÉP LINK RẢI RÁC (ANTI-SPAM)
        if missed:
            pfxs = ["Hơn nữa, Sếp có thể xem thêm về", "Một gợi ý là", "Thông tin về"]
            avail_p = [p for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20 and not p.find('a')]
            for k, u in missed:
                if avail_p:
                    target = random.choice(avail_p); avail_p.remove(target)
                    target.append(BeautifulSoup(f" {random.choice(pfxs)} <a href='{u}'>{k}</a>.", 'html.parser'))
                    self.add_log(ui_log, f"⚠️ AI sót '{k}', đã rải vào 1 đoạn văn.", "warn")
                else: soup.append(BeautifulSoup(f"<p>{random.choice(pfxs)} <a href='{u}'>{k}</a>.</p>", 'html.parser'))

        self.add_log(ui_log, f"🛠️ [GẮN LINK] {self.injected_ext}/{self.out_lim} Ext | {self.injected_int}/{self.in_lim} Int.", "success")

        # LOG QUÉT ẢNH THEO RULE SẾP
        mx_img = self.parse_random_range(self.target_web.get('WS_IMG_LIMIT', 1), 1)
        self.add_log(ui_log, f"🖼️ [QUOTA ẢNH] Web cho phép tối đa {mx_img} ảnh.", "detail")
        df_img = self.db.get('IMAGE', pd.DataFrame())
        if not df_img.empty and 'IMG_URL' in df_img.columns and mx_img > 0:
            df_img['IMG_STATUS'] = pd.to_numeric(df_img.get('IMG_STATUS', 0), errors='coerce').fillna(0)
            sorted_imgs = df_img.sample(frac=1).sort_values('IMG_STATUS')
            for _, r in sorted_imgs.iterrows():
                try:
                    if requests.head(str(r['IMG_URL']).strip(), timeout=5).status_code == 200:
                        self.used_imgs.append(str(r['IMG_URL']).strip())
                        if len(self.used_imgs) >= 1: break
                except: continue
            if self.used_imgs:
                img_h = f"<br><p align='center'><img src='{self.used_imgs[0]}' alt='{self.all_kws[0]}'></p><br>"
                inserted = False
                for p in soup.find_all('p'):
                    if re.search(r'(?i)' + re.escape(self.all_kws[0]), p.get_text()):
                        p.insert_after(BeautifulSoup(img_h, 'html.parser'))
                        inserted = True; break
                if not inserted and soup.find_all('p'): soup.find_all('p')[0].insert_after(BeautifulSoup(img_h, 'html.parser'))
        self.add_log(ui_log, f"🖼️ [GẮN ẢNH] Thành công {len(self.used_imgs)} ảnh.")
        self.raw_html = str(soup)
        return True

    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "⚖️ [KCS] Đang chấm điểm và xóa H1 lặp...")
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
        ai = min(max(round(max(5, 50 - ((statistics.stdev(lens) if len(lens)>3 else 0)*4)), 1), 2.0), 99.0)
        rd = round(max(10, min(206.835 - (1.015*(sum(lens)/max(len(lens),1))) - 84.6*1.2, 100)), 1)
        
        self.kcs_metrics = {'SEO': seo, 'AI': ai, 'READ': rd}
        self.add_log(ui_log, f"   > SEO {seo}/100 | AI {ai}% | READ {rd}/100", "detail")
        
        if h1: h1.decompose() # DIỆT H1
        self.raw_html = str(soup)
        
        req = 35 if self.is_short_form else 70
        if seo < req or ai > 20 or rd < 60: return self.add_log(ui_log, "❌ KCS FAIL", "error") or "FAIL"
        self.add_log(ui_log, "✅ [KCS PASSED]", "success")
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
            
            if final_result == 'PENDING':
                ts = self.now_vn.strftime('%Y-%m-%d %H:%M')
                def upd(w, col_m, vals, col_s, col_d):
                    if not vals: return
                    s, d = ss.worksheet(w), ss.worksheet(w).get_all_values()
                    if len(d) > 1:
                        h = [str(x).strip() for x in d[0]]
                        im, is_, id_ = h.index(col_m), h.index(col_s) if col_s in h else -1, h.index(col_d) if col_d in h else -1
                        u = []
                        for i, r in enumerate(d[1:], 2):
                            if r[im].strip() in vals:
                                if is_ != -1: u.append({'range': f'{gspread.utils.rowcol_to_a1(i, is_+1)}', 'values': [[self.safe_int(r[is_])+1]]})
                                if id_ != -1: u.append({'range': f'{gspread.utils.rowcol_to_a1(i, id_+1)}', 'values': [[ts]]})
                        if u: s.batch_update(u)
                upd('KEYWORD', 'KW_TEXT', self.all_kws, 'KW_STATUS', 'KW_DATE')
                upd('IMAGE', 'IMG_URL', self.used_imgs, 'IMG_STATUS', 'IMG_DATE')
                upd('SPIN', 'SPIN_ORIGINAL', self.used_spins, None, 'SPIN_DATE')
                self.add_log(ui_log, "✅ Lưu DB xong.", "success")
        except Exception as e: self.add_log(ui_log, f"🛑 DB Error: {e}", "error")

# ==========================================
# 🖥 UI
# ==========================================
db_mock = load_data_from_gsheets()
if db_mock is None: st.stop()
d_rep, dash = db_mock.get('REPORT', pd.DataFrame()), {str(k).strip(): str(v).strip() for k, v in zip(db_mock.get('DASHBOARD')['DATA_KEY'], db_mock.get('DASHBOARD')['DATA_CONTENT'])}

st.title(f"🛡️ {dash.get('PROJECT_NAME', 'Auto SEO')}")
t1, t2, t3 = st.tabs(["📊 DASHBOARD", "📋 CONTENT", "🗄️ DATABASE"])

with t1:
    tdy = get_vn_now().strftime('%Y-%m-%d')
    p_tdy = len(d_rep[d_rep['REP_CREATED_AT'].astype(str).str.startswith(tdy)]) if not d_rep.empty else 0
    b_val = AutoSEOPipeline(db_mock, []).parse_random_range(dash.get('BATCH_SIZE', 10), 10)
    c1, c2, c3 = st.columns(3)
    c1.metric("Today", f"{p_tdy}/{b_val}"); c2.metric("DONE", len(d_rep[d_rep['REP_RESULT'] == 'DONE']) if not d_rep.empty else 0); c3.metric("PENDING", len(d_rep[d_rep['REP_RESULT'] == 'PENDING']) if not d_rep.empty else 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    bc1, bc2, bc3 = st.columns(3)
    b_start, b_force, b_ref = bc1.button("🔥 Soạn bài AI", use_container_width=True, type="primary"), bc2.button("⚡ Ép Lên bài ngay", use_container_width=True), bc3.button("🔄 Làm mới", use_container_width=True)
    
    if b_ref: load_data_from_gsheets.clear(); st.rerun()
    if b_force:
        st.info("⏳ ĐANG POST BÀI..."); load_data_from_gsheets.clear(); ui = st.empty(); bot = AutoSEOPipeline(db_mock, [])
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            ws, data = ss.worksheet('REPORT'), ss.worksheet('REPORT').get_all_values()
            df_w = db_mock.get('WEBSITE')
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
                                upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, ih+1)}', 'values': [['']]})
                                cnt += 1
                            else: bot.add_log(ui, f"🛑 {msg}", "error")
                if upds: ws.batch_update(upds); st.success(f"🎉 Bắn thành công {cnt} bài!"); time.sleep(2); st.rerun()
        except Exception as e: st.error(f"Lỗi: {e}")

    if b_start:
        load_data_from_gsheets.clear(); ui = st.empty(); need = b_val - p_tdy
        if need > 0:
            m_logs = []
            for i in range(need):
                bot = AutoSEOPipeline(db_mock, m_logs)
                bot.add_log(ui, f"<br>🚀 --- BÀI {i+1}/{need} ---", "success")
                st_t = time.time()
                try:
                    if bot.step1_allocate_slot(ui) and bot.step2_3_keyword_and_serp(ui) and bot.step4_llm_generation(ui):
                        bot.step5_6_spin_and_dom(ui)
                        bot.step8_sync_db(ui, bot.step7_qa_validation(ui))
                        db_mock = load_data_from_gsheets()
                except Exception as e: bot.add_log(ui, f"🛑 Lỗi: {e}", "error")
                if time.time() - st_t > 300: break
            st.success("🎉 XONG!")

with t2:
    if not d_rep.empty:
        st.dataframe(d_rep[['REP_CREATED_AT', 'REP_PUBLISH_DATE', 'REP_TITLE', 'REP_WS_NAME', 'REP_RESULT']].tail(15), use_container_width=True, hide_index=True)
        sel = st.selectbox("🔍 Soi Log:", d_rep['REP_TITLE'].tolist()[::-1])
        if sel:
            r = d_rep[d_rep['REP_TITLE'] == sel].iloc[0]
            c1, c2 = st.columns(2)
            c1.markdown(f'<div class="log-box">{str(r["REP_LOG"]).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            c2.text_area("HTML:", str(r["REP_HTML"]), height=800)
with t3: st.dataframe(d_rep, use_container_width=True)
