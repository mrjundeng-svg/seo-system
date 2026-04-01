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
# ⚙️ CONFIG & AUTH
# ==========================================
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')
def get_vn_now(): return datetime.datetime.now(VN_TZ)

st.set_page_config(page_title="Auto SEO Pipeline | Lái Hộ", layout="wide", page_icon="🛡️")
st.markdown("""<style>.log-box {background-color: #0f172a; color: #10b981; font-family: monospace; font-size: 14px; padding: 15px; border-radius: 8px; height: 800px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6; word-wrap: break-word;} .log-error {color: #ef4444; font-weight: bold;} .log-warn {color: #f59e0b;} .log-success {color: #3b82f6; font-weight: bold;} .log-quota {color: #a855f7; font-weight: bold;} .log-detail {color: #94a3b8; font-size: 13px; font-style: italic;}</style>""", unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw'

def check_password():
    if not st.session_state.get("logged_in"):
        st.markdown("## 🔐 System Gateway Authentication")
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Access Pipeline"):
            if u == st.secrets.get("admin_user", "admin") and p == st.secrets.get("admin_pass", "admin123"):
                st.session_state["logged_in"], st.rerun() = True, None
            else: st.error("❌ Sai thông tin đăng nhập!")
        return False
    return True

if not check_password(): st.stop()

@st.cache_data(ttl=60)
def load_data():
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        ss = gspread.authorize(creds).open_by_key(SHEET_ID)
        return {tab: pd.DataFrame(ss.worksheet(tab).get_all_values()[1:], columns=[str(h).strip() or f"C_{i}" for i, h in enumerate(ss.worksheet(tab).get_all_values()[0])]) if ss.worksheet(tab).get_all_values() else pd.DataFrame() for tab in ['DASHBOARD', 'WEBSITE', 'KEYWORD', 'IMAGE', 'SPIN', 'REPORT']}
    except Exception as e: return st.error(f"❌ Lỗi kết nối Sheets: {e}") or None

# ==========================================
# 🚀 CMS AUTO-POST
# ==========================================
def post_to_cms(ws_row, title, html_content, dash_config):
    receiver = str(ws_row.get('WS_BLOG_CONTENT', '')).strip()
    u, p = str(ws_row.get('WS_LOGIN_USER', '')).strip(), str(ws_row.get('WS_LOGIN_PASS', '')).strip()
    
    if "@blogger.com" in receiver.lower():
        s_mail, s_pass = dash_config.get('EMAIL_SENDER', '').strip(), dash_config.get('EMAIL_SENDER_PASSWORD', '').strip()
        if not s_mail or not s_pass: return False, "Thiếu EMAIL_SENDER / PASSWORD trong DASHBOARD."
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = s_mail, receiver, title
            msg.attach(MIMEText(html_content, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(s_mail, s_pass)
            server.send_message(msg)
            server.quit()
            return True, f"Bắn Blogspot thành công -> {receiver}"
        except Exception as e: return False, f"Lỗi gửi Mail: {e}"
    else:
        domain = str(ws_row.get('WS_LINK_IN_BACKLINK', '')).split(',')[0].strip()
        if not domain: return False, "Thiếu Domain WordPress."
        try:
            res = requests.post(f"{domain.rstrip('/')}/wp-json/wp/v2/posts", auth=(u, p), json={'title': title, 'content': html_content, 'status': 'publish'}, timeout=30)
            return (True, f"Đăng WP thành công (ID: {res.json().get('id')})") if res.status_code in [200, 201] else (False, f"Lỗi WP API: {res.text[:100]}")
        except Exception as e: return False, f"Lỗi kết nối WP: {e}"

# ==========================================
# 🤖 CORE ENGINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, db, logs):
        self.db = db
        self.dash = {str(k).strip(): str(v).strip() for k, v in zip(self.db.get('DASHBOARD', pd.DataFrame())['DATA_KEY'], self.db.get('DASHBOARD', pd.DataFrame())['DATA_CONTENT'])}
        self.now, self.logs = get_vn_now(), logs
        self.web, self.pub_time, self.kw_row, self.kws, self.raw_html, self.title = None, None, None, [], "", ""
        self.out_lim, self.in_lim, self.inj_ext, self.inj_int = 0, 0, 0, 0
        self.metrics, self.imgs, self.spins = {}, [], []
        if 'evo_cache' not in st.session_state: st.session_state.evo_cache = ""

    def log(self, ui, msg, lvl="info"):
        fmt = f'<span class="log-{lvl}">{msg}</span>' if lvl in ["error", "warn", "success", "quota", "detail"] else msg
        self.logs.append(f"[{get_vn_now().strftime('%H:%M:%S')}] {fmt}")
        if ui: ui.markdown(f'<div class="log-box" id="lbox">{"<br>".join(self.logs)}</div><script>var d=document.getElementById("lbox");d.scrollTop=d.scrollHeight;</script>', unsafe_allow_html=True)

    def safe_int(self, v, d=0):
        try: return int(str(v).strip())
        except: return d

    def get_min_max(self, val_str, d_min, d_max):
        try:
            s = str(val_str).strip()
            if '-' in s: return min(int(s.split('-')[0]), int(s.split('-')[1])), max(int(s.split('-')[0]), int(s.split('-')[1]))
            return int(s), int(s)
        except: return d_min, d_max

    def parse_rng(self, val_str, d=0):
        min_v, max_v = self.get_min_max(val_str, d, d)
        return random.randint(min_v, max_v)

    def step1_slot(self, ui):
        df_rep, df_web = self.db.get('REPORT', pd.DataFrame()), self.db.get('WEBSITE', pd.DataFrame())
        batch, max_d = self.parse_rng(self.dash.get('BATCH_SIZE', 10), 10), self.parse_rng(self.dash.get('MAX_SCHEDULE_DAYS', 30), 30)
        try:
            h1, m1 = map(int, str(self.dash.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')[0].split(':'))
            h2, m2 = map(int, str(self.dash.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')[1].split(':'))
            s1, s2 = self.get_min_max(self.dash.get('POST_SPACING_MINUTES', '30-90'), 30, 90)
        except: return self.log(ui, "🛑 Lỗi Config Giờ.", "error") or False

        if len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(self.now.strftime('%Y-%m-%d'))]) >= batch: return False

        for d_off in range(max_d + 1):
            day_x = self.now.date() + datetime.timedelta(days=d_off)
            for _, w in df_web.sample(frac=1).reset_index(drop=True).iterrows():
                ws_name, ws_lim = str(w.get('WS_NAME', '')).strip(), self.parse_rng(w.get('WS_POST_LIMIT', 1), 1)
                day_posts = df_rep[(df_rep['REP_WS_NAME'] == ws_name) & (df_rep['REP_PUBLISH_DATE'].str.startswith(day_x.strftime('%Y-%m-%d')))] if not df_rep.empty else pd.DataFrame()
                
                self.log(ui, f"🔍 [QUOTA] Local '{ws_name}' ({day_x}): {len(day_posts)}/{ws_lim}", "quota")
                if len(day_posts) < ws_lim:
                    st_t, ed_t = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(h1, m1))), VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(h2, m2)))
                    if d_off == 0 and self.now > ed_t: continue 
                    
                    base = max(self.now, st_t) if d_off == 0 else st_t
                    try: last_p = VN_TZ.localize(datetime.datetime.strptime(str(day_posts['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M')) if not day_posts.empty else base
                    except: last_p = base
                    
                    pub_t = max(last_p, base) + datetime.timedelta(minutes=random.randint(s1, s2)) if not day_posts.empty else base + datetime.timedelta(minutes=random.randint(0, 30))
                    pub_t = max(pub_t, self.now + datetime.timedelta(minutes=5))
                    if pub_t > ed_t: continue 
                    
                    self.web, self.pub_time = w, pub_t
                    self.log(ui, f"✅ [CHỐT SLOT] {ws_name} | Lịch: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
        return self.log(ui, "🛑 Đã full lịch.", "error") or False

    def step2_3_kw_serp(self, ui):
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        self.kw_row = df_kw.sample(frac=1).sort_values('KW_STATUS').iloc[0]
        
        m_kw, m_cat, m_grp = str(self.kw_row['KW_TEXT']).strip(), str(self.kw_row.get('KW_CONTENT', '')).strip(), str(self.kw_row.get('KW_GROUP', '')).strip()
        self.out_lim, self.in_lim = self.parse_rng(self.web.get('WS_LINK_OUT_LIMIT', 0)), self.parse_rng(self.web.get('WS_LINK_IN_LIMIT', 0))
        
        subs = df_kw[(df_kw['KW_TEXT'] != m_kw) & (df_kw['KW_CONTENT'] == m_cat) & (df_kw['KW_GROUP'] != m_grp)].head(max(0, self.out_lim + self.in_lim - 1))['KW_TEXT'].tolist()
        self.kws = [m_kw] + subs
        self.log(ui, f"📦 [KWs] Cần {self.out_lim+self.in_lim} Links -> Gom: {', '.join(self.kws)}", "detail")

        min_w, max_w = self.get_min_max(self.dash.get('WORD_COUNT_RANGE', '900-1200'), 900, 1200)
        self.is_short_form, self.target_length = (True, random.randint(min_w, max_w)//2) if len(self.kws) < 3 else (False, random.randint(min_w, max_w))
        self.log(ui, f"📏 [RULE BÀI] Cần viết: ~{self.target_length} chữ.")

        s_key, c_list = self.dash.get('SERPAPI_KEY', ''), [c.strip() for c in str(self.dash.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        self.serp_style = "Văn phong chuyên gia sâu sắc, logic."
        if s_key:
            try:
                res = requests.get("https://serpapi.com/search", params={"q": m_kw, "hl": "vi", "gl": "vn", "api_key": s_key}, timeout=15).json().get("organic_results", [])
                t_link = ([r["link"] for r in res[:10] if c_list and any(c in r.get("link","") for c in c_list)] + [r["link"] for r in res[:3]] + [None])[0]
                if t_link:
                    rh = requests.get(t_link, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    if rh.status_code == 200:
                        soup = BeautifulSoup(rh.text, 'html.parser')
                        for t in soup(["script", "style", "nav", "footer"]): t.decompose()
                        self.serp_style = "\n".join([t.get_text(strip=True) for t in soup.find_all(['h2', 'h3', 'p'])])[:3000]
                        self.log(ui, f"✅ [SERP] Trích xuất văn phong từ: {t_link}")
                        return True
            except: pass
        self.log(ui, f"🕵️ [SERP] Fallback: Sử dụng Internal Cache.")
        return True

    def step4_llm(self, ui):
        pmt = {k: random.choice([p.strip() for p in re.split(r'\|\|\|', str(self.dash.get(k, ''))) if p.strip()] or [str(self.dash.get(k, '')).strip()]) for k in ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']}
        
        strict_rules = f"""
        \n[SYSTEM STRICT RULE - BẮT BUỘC TUÂN THỦ]:
        1. CẤM TUYỆT ĐỐI các từ chào hỏi ở đầu bài: "Kính thưa các Sếp", "Chào quý vị", "Thân gửi". VÀO THẲNG VẤN ĐỀ.
        2. THẺ H1: Chứa ngẫu nhiên ở GIỮA/CUỐI tiêu đề cụm "{self.kws[0]}" (Tuyệt đối ko đặt ở đầu).
        3. TỪ KHÓA TRONG BÀI: Rải "{self.kws[0]}" 2-3 lần. Các từ "{', '.join(self.kws[1:])}" mỗi từ xuất hiện đúng 1 lần. Tuyệt đối không dùng dấu in đậm `**` cho từ khóa.
        4. CẤU TRÚC SEO: Nếu có chia thẻ <h3> dưới <h2>, BẮT BUỘC đánh số thứ tự (1., 2., 3.,...). Cấm viết các đoạn dài bằng nhau, đan xen ngắn dài.
        5. ĐỘ DÀI: ~{self.target_length} chữ. Không lặp cấu trúc: {st.session_state.evo_cache}. TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>.
        """
        
        tpl = pmt['PROMPT_TEMPLATE'].replace('{{ws_persona}}', str(self.web.get('WS_PERSONA', ''))).replace('{{kw_intent}}', str(self.kw_row.get('KW_INTENT', ''))).replace('{{keyword}}', self.kws[0]).replace('{{word_count}}', str(self.target_length))
        for i, kw in enumerate(self.kws): tpl = re.sub(rf'\[?REP_KW_{i+1}\]?', kw, tpl, flags=re.IGNORECASE)
        master = f"{tpl}\n{pmt['PROMPT_CONTENT_STRATEGY']}\n{pmt['PROMPT_KEYWORD_SEARCH']}\n{pmt['PROMPT_SERP_STYLE']}\n[Dữ liệu SERP]:\n{self.serp_style}\n{pmt['PROMPT_SEO_GLOBAL_RULE']}\n{pmt['PROMPT_AI_HUMANIZER']}\n{strict_rules}"

        for m in [m.strip() for m in str(self.dash.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]:
            for k in [k.strip() for k in str(self.dash.get('GEMINI_API_KEY', '')).split(',') if k.strip()]:
                genai.configure(api_key=k)
                self.log(ui, f"🌐 [API] Gemini ({m})...", "detail")
                try: 
                    self.raw_html = genai.GenerativeModel(m).generate_content(master).text
                    break
                except Exception: self.log(ui, f"⚠️ Gemini sập, thử key dự phòng...", "warn")
            if self.raw_html: break

        if not self.raw_html: return self.log(ui, "🛑 [FATAL] Toàn bộ API sập.", "error") or False
            
        self.raw_html = self.raw_html.replace('```html', '').replace('```', '').strip()
        self.raw_html = re.sub(r'\*\*(.*?)\*\*', r'\1', self.raw_html) # Xóa dấu ** AI tự sinh
        
        for i, kw in enumerate(self.kws):
            self.raw_html = re.sub(rf'\[?REP_KW_{i+1}\]?', kw, self.raw_html, flags=re.IGNORECASE)
            if i == 0: self.raw_html = re.sub(r'\{\{keyword\}\}', kw, self.raw_html, flags=re.IGNORECASE)
        self.raw_html = re.sub(r'\[?REP_KW_\d+\]?', '', self.raw_html, flags=re.IGNORECASE) # Dọn rác
        
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        st.session_state.evo_cache = f"{len(soup.find_all('h2'))}H2,{len(soup.find_all('p'))}P"
        h1_m = soup.find('h1')
        self.title = h1_m.get_text(strip=True) if h1_m else f"Bài: {self.kws[0]}"
        self.log(ui, f"🏷️ [THÔNG TIN] Domain: {self.web.get('WS_NAME', '')} | Tiêu đề: {self.title}", "success")
        return True

    def step5_6_dom(self, ui):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        for i, k in enumerate(self.kws): self.raw_html = re.sub(r'(?i)' + re.escape(k), f'__I_{i}__', self.raw_html, count=1)
        
        if not df_spin.empty and 'SPIN_ORIGINAL' in df_spin.columns:
            for _, r in df_spin.iterrows():
                o, v_str = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_VARIANTS', r.get('SPIN_REPLACE', ''))).strip()
                if o and v_str: 
                    variants = [v.strip() for v in v_str.replace(';', ',').split(',') if v.strip()]
                    if variants and re.search(r'(?i)\b' + re.escape(o) + r'\b', self.raw_html):
                        self.raw_html = re.sub(r'(?i)\b' + re.escape(o) + r'\b', random.choice(variants), self.raw_html)
                        self.spins.append(o)

        for i, k in enumerate(self.kws): self.raw_html = self.raw_html.replace(f'__I_{i}__', k)
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        
        ou = [u.strip() for u in str(self.web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if u.strip()]
        iu = [u.strip() for u in str(self.web.get('WS_LINK_IN_BACKLINK', '')).split(',') if u.strip()]

        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        missed = []
        for k in self.kws:
            u, is_e = (random.choice(ou), True) if self.inj_ext < self.out_lim and ou else ((random.choice(iu), False) if self.inj_int < self.in_lim and iu else ("", False))
            if not u: continue 
            
            injected = False
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)' + re.escape(k), p.get_text()):
                    p.replace_with(BeautifulSoup(re.sub(r'(?i)' + re.escape(k), lambda m: f"<a href='{u}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                    injected = True
                    self.inj_ext += 1 if is_e else 0
                    self.inj_int += 1 if not is_e else 0
                    break
            if not injected: missed.append((k, u, is_e))

        if missed:
            avail_p = [p for p in soup.find_all('p') if len(p.get_text(strip=True)) > 20]
            for k, u, is_e in missed:
                pfx = random.choice(["Hơn nữa, Sếp có thể tham khảo thêm về", "Một lựa chọn đáng cân nhắc là", "Tìm hiểu thêm thông tin về"])
                if avail_p:
                    tp = random.choice(avail_p)
                    tp.append(BeautifulSoup(f" {pfx} <a href='{u}'>{k}</a>.", 'html.parser'))
                    avail_p.remove(tp)
                else: soup.append(BeautifulSoup(f"<p>{pfx} <a href='{u}'>{k}</a>.</p>", 'html.parser'))
                self.inj_ext += 1 if is_e else 0
                self.inj_int += 1 if not is_e else 0
                    
        self.log(ui, f"🛠️ [GẮN LINK] Ext: {self.inj_ext}/{self.out_lim} | Int: {self.inj_int}/{self.in_lim}", "success")

        max_img = self.parse_random_range(self.web.get('WS_IMG_LIMIT', 1))
        df_img = self.db.get('IMAGE', pd.DataFrame())
        if not df_img.empty and 'IMG_URL' in df_img.columns and max_img > 0:
            df_img['IMG_STATUS'] = pd.to_numeric(df_img.get('IMG_STATUS', 0), errors='coerce').fillna(0)
            for _, r in df_img.sample(frac=1).sort_values('IMG_STATUS').iterrows():
                try:
                    if requests.head(str(r['IMG_URL']).strip(), timeout=5).status_code == 200:
                        self.imgs.append(str(r['IMG_URL']).strip())
                        break
                except: continue
            if self.imgs:
                img_html = f"<br><p align='center'><img src='{self.imgs[0]}' alt='{self.kws[0]}'></p><br>"
                inserted = False
                for p in soup.find_all('p'):
                    if re.search(r'(?i)' + re.escape(self.kws[0]), p.get_text()):
                        p.insert_after(BeautifulSoup(img_html, 'html.parser'))
                        inserted = True; break
                if not inserted and soup.find_all('p'): soup.find_all('p')[0].insert_after(BeautifulSoup(img_html, 'html.parser'))
                    
        self.log(ui, f"🖼️ [GẮN ẢNH] Quota max: {max_img}. Thành công: {len(self.imgs)} ảnh.")
        self.raw_html = str(soup)
        return True

    def step7_kcs(self, ui):
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        txt, k0 = soup.get_text(' ', strip=True), self.kws[0].lower()
        
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
        
        self.metrics = {'SEO': seo, 'AI': ai, 'READ': rd}
        self.log(ui, f"> KCS: SEO {seo}/100 (H1:{s_h1}, H2:{s_h2}, D:{s_den}) | AI {ai}%", "detail")
        
        if h1: h1.decompose() # Cắt H1 tránh lặp
        self.raw_html = str(soup).strip()
        
        if seo < (35 if self.is_short_form else 70) or ai > 20 or rd < 60: return self.log(ui, "❌ KCS FAIL", "error") or "FAIL"
        self.log(ui, "✅ [KCS PASSED] Đã xóa thẻ H1 nội bộ.", "success")
        return "PENDING"

    def step8_db(self, ui, res):
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            rep_ws = ss.worksheet('REPORT')
            hdrs = [str(h).strip() for h in rep_ws.row_values(1)]
            def gc(pfx): return next((h for h in hdrs if h.startswith(pfx)), pfx)

            row_d = {
                'REP_WS_NAME': str(self.web.get('WS_NAME', '')), 'REP_CREATED_AT': self.now.strftime('%Y-%m-%d %H:%M'),
                'REP_TITLE': self.title, 'REP_IMG_COUNT': str(len(self.imgs)),
                'REP_KW_1': self.kws[0] if len(self.kws)>0 else "", 'REP_KW_2': self.kws[1] if len(self.kws)>1 else "",
                'REP_KW_3': self.kws[2] if len(self.kws)>2 else "", 'REP_KW_4': self.kws[3] if len(self.kws)>3 else "",
                'REP_KW_5': self.kws[4] if len(self.kws)>4 else "", 
                gc('REP_SEO_'): str(self.metrics.get('SEO', 0)), gc('REP_AI_'): f"{self.metrics.get('AI', 100)}%", gc('REP_READ'): str(self.metrics.get('READ', 0)),
                'REP_PUBLISH_DATE': self.pub_time.strftime('%Y-%m-%d %H:%M'), 'REP_POST_URL': "", 
                'REP_RESULT': res, 'REP_LOG': "\n".join(self.logs), 'REP_HTML': self.raw_html if res == 'PENDING' else ""
            }
            rep_ws.append_row([row_d.get(h, "") for h in hdrs])
            
            if res == 'PENDING':
                ts = self.now.strftime('%Y-%m-%d %H:%M')
                def batch_upd(w, k_col, vals, col_st, col_dt):
                    if not vals: return
                    s, d = ss.worksheet(w), ss.worksheet(w).get_all_values()
                    if len(d) > 1:
                        h = [str(x).strip() for x in d[0]]
                        im, i_s, idt = h.index(k_col) if k_col in h else -1, h.index(col_st) if col_st and col_st in h else -1, h.index(col_dt) if col_dt and col_dt in h else -1
                        upds = []
                        for i, r in enumerate(d[1:], 2):
                            if im != -1 and len(r) > im and r[im].strip() in vals:
                                if i_s != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_s+1)}', 'values': [[self.safe_int(r[i_s])+1]]})
                                if idt != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, idt+1)}', 'values': [[ts]]})
                        if upds: s.batch_update(upds)

                batch_upd('KEYWORD', 'KW_TEXT', self.kws, 'KW_STATUS', 'KW_DATE')
                batch_upd('IMAGE', 'IMG_URL', self.imgs, 'IMG_STATUS', 'IMG_DATE')
                batch_upd('SPIN', 'SPIN_ORIGINAL', self.spins, None, 'SPIN_DATE')
                self.log(ui, "✅ Đã lưu DB thành công.", "success")
        except Exception as e: self.log(ui, f"🛑 DB Error: {e}", "error")

# ==========================================
# 🖥 GIAO DIỆN UI
# ==========================================
db = load_data()
if not db: st.stop()
d_rep, dash = db.get('REPORT', pd.DataFrame()), {str(k).strip(): str(v).strip() for k, v in zip(db.get('DASHBOARD', pd.DataFrame())['DATA_KEY'], db.get('DASHBOARD', pd.DataFrame())['DATA_CONTENT'])}

st.title(f"🛡️ {dash.get('PROJECT_NAME', 'Auto SEO')}")
t1, t2, t3 = st.tabs(["📊 DASHBOARD", "📋 CONTENT", "🗄️ DATABASE"])

with t1:
    tdy = get_vn_now().strftime('%Y-%m-%d')
    p_tdy = len(d_rep[d_rep['REP_CREATED_AT'].astype(str).str.startswith(tdy)]) if not d_rep.empty and 'REP_CREATED_AT' in d_rep.columns else 0
    b_val = AutoSEOPipeline(db, []).parse_rng(dash.get('BATCH_SIZE', 10), 10)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Today", f"{p_tdy}/{b_val}")
    c2.metric("DONE", len(d_rep[d_rep['REP_RESULT'].astype(str).str.strip() == 'DONE']) if not d_rep.empty and 'REP_RESULT' in d_rep.columns else 0)
    c3.metric("PENDING", len(d_rep[d_rep['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if not d_rep.empty and 'REP_RESULT' in d_rep.columns else 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    bc1, bc2, bc3 = st.columns(3)
    b_run = bc1.button("🔥 Soạn bài AI", use_container_width=True, type="primary")
    b_frc = bc2.button("⚡ Ép Lên bài ngay", use_container_width=True)
    if bc3.button("🔄 Làm mới", use_container_width=True): load_data.clear(); st.rerun()
        
    if b_frc:
        st.info("⏳ ĐANG XỬ LÝ POST BÀI LÊN WEB...")
        load_data.clear()
        ui = st.empty()
        bot = AutoSEOPipeline(db, [])
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            ws, data = ss.worksheet('REPORT'), ss.worksheet('REPORT').get_all_values()
            df_w = db.get('WEBSITE', pd.DataFrame())
            
            if len(data) > 1:
                h = [str(x).strip() for x in data[0]]
                ir, ip, ih, il, iw, it = h.index('REP_RESULT') if 'REP_RESULT' in h else -1, h.index('REP_PUBLISH_DATE') if 'REP_PUBLISH_DATE' in h else -1, h.index('REP_HTML') if 'REP_HTML' in h else -1, h.index('REP_LOG') if 'REP_LOG' in h else -1, h.index('REP_WS_NAME') if 'REP_WS_NAME' in h else -1, h.index('REP_TITLE') if 'REP_TITLE' in h else -1
                
                if ir != -1 and ip != -1:
                    upd, cnt = [], 0
                    for i, r in enumerate(data[1:], 2):
                        if len(r) > max(ir, ip) and r[ir].strip() == 'PENDING' and str(r[ip]).startswith(tdy):
                            w_name, title, h_cnt = r[iw] if iw != -1 else "", r[it] if it != -1 else "", r[ih] if ih != -1 else ""
                            bot.log(ui, f"➤ Đăng: '{title}' -> {w_name}")
                            w_row = df_w[df_w['WS_NAME'].astype(str).str.strip() == w_name.strip()]
                            if not w_row.empty:
                                ok, msg = post_to_cms(w_row.iloc[0], title, h_cnt, dash)
                                if ok:
                                    bot.log(ui, f"✅ {msg}", "success")
                                    upd.extend([{'range': f'{gspread.utils.rowcol_to_a1(i, ir+1)}', 'values': [['DONE']]}])
                                    if ih != -1: upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, ih+1)}', 'values': [['']]})
                                    cnt += 1
                                else: bot.log(ui, f"🛑 {msg}", "error")
                    if upd:
                        ws.batch_update(upd)
                        st.success(f"🎉 Bắn thành công {cnt} bài!")
                        time.sleep(2); st.rerun()
                    else: bot.log(ui, "ℹ️ Không có bài PENDING hôm nay.", "warn")
        except Exception as e: bot.log(ui, f"🛑 Lỗi Post: {e}", "error")

    if b_run:
        load_data.clear()
        ui = st.empty()
        need = b_val - p_tdy
        if need <= 0: ui.error("🛑 Đủ Quota.")
        else:
            m_logs = []
            for i in range(need):
                bot = AutoSEOPipeline(db, m_logs)
                bot.log(ui, f"<br>🚀 --- BÀI {i+1}/{need} ---", "success")
                st_t = time.time()
                try:
                    if bot.step1_slot(ui) and bot.step2_3_kw_serp(ui) and bot.step4_llm(ui):
                        bot.step5_6_dom(ui)
                        bot.step8_db(ui, bot.step7_kcs(ui))
                        db = load_data()
                except Exception as e: bot.log(ui, f"🛑 Fatal: {e}", "error")
                if time.time() - st_t > 300: break
            st.success("🎉 HOÀN TẤT!")

with t2:
    if not d_rep.empty:
        st.dataframe(d_rep[['REP_CREATED_AT', 'REP_PUBLISH_DATE', 'REP_TITLE', 'REP_WS_NAME', 'REP_RESULT']].tail(15), use_container_width=True, hide_index=True)
        sel = st.selectbox("🔍 Soi Log:", d_rep['REP_TITLE'].tolist()[::-1])
        if sel:
            r = d_rep[d_rep['REP_TITLE'] == sel].iloc[0]
            lc1, lc2 = st.columns(2)
            lc1.markdown(f'<div class="log-box">{str(r.get("REP_LOG", "")).replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            lc2.text_area("HTML:", str(r.get('REP_HTML', '')), height=800, label_visibility="collapsed")
with t3: st.dataframe(d_rep, use_container_width=True)
