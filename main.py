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

st.set_page_config(page_title="Auto SEO Pipeline", layout="wide", page_icon="🛡️")
st.markdown("""<style>.log-box {background-color: #0f172a; color: #10b981; font-family: monospace; font-size: 14px; padding: 15px; border-radius: 8px; height: 600px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6; word-wrap: break-word;} .log-error {color: #ef4444; font-weight: bold;} .log-warn {color: #f59e0b;} .log-success {color: #3b82f6; font-weight: bold;} .log-quota {color: #a855f7; font-weight: bold;} .log-detail {color: #94a3b8; font-size: 13px; font-style: italic;}</style>""", unsafe_allow_html=True)

SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw'

def check_password():
    if not st.session_state.get("logged_in"):
        st.markdown("## 🔐 Gateway")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("Login"):
            if u == st.secrets.get("admin_user", "admin") and p == st.secrets.get("admin_pass", "admin123"):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("❌ Denied")
        return False
    return True

if not check_password(): st.stop()

@st.cache_data(ttl=60)
def load_db():
    try:
        creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        ss = gspread.authorize(creds).open_by_key(SHEET_ID)
        return {tab: pd.DataFrame(ss.worksheet(tab).get_all_values()[1:], columns=[str(h).strip() or f"C_{i}" for i, h in enumerate(ss.worksheet(tab).get_all_values()[0])]) if ss.worksheet(tab).get_all_values() else pd.DataFrame() for tab in ['DASHBOARD', 'WEBSITE', 'KEYWORD', 'IMAGE', 'SPIN', 'REPORT']}
    except Exception as e:
        st.error(f"DB Error: {e}")
        return None

# ==========================================
# 🚀 HÀM POST CMS
# ==========================================
def post_to_cms(ws_row, title, html_content, dash_config):
    receiver = str(ws_row.get('WS_BLOG_CONTENT', '')).strip()
    u, p = str(ws_row.get('WS_LOGIN_USER', '')).strip(), str(ws_row.get('WS_LOGIN_PASS', '')).strip()
    
    if "@blogger.com" in receiver.lower():
        s_mail, s_pass = dash_config.get('EMAIL_SENDER', '').strip(), dash_config.get('EMAIL_SENDER_PASSWORD', '').strip()
        if not s_mail or not s_pass: return False, "Thiếu EMAIL_SENDER/PASSWORD"
        try:
            msg = MIMEMultipart()
            msg['From'], msg['To'], msg['Subject'] = s_mail, receiver, title
            msg.attach(MIMEText(html_content, 'html'))
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(s_mail, s_pass)
            server.send_message(msg)
            server.quit()
            return True, f"Bắn Blogspot OK ({receiver})"
        except Exception as e: return False, f"Lỗi Mail: {e}"
    else:
        domain = str(ws_row.get('WS_LINK_IN_BACKLINK', '')).split(',')[0].strip()
        if not domain: return False, "Thiếu Domain WP"
        api = f"{domain.rstrip('/')}/wp-json/wp/v2/posts"
        try:
            res = requests.post(api, auth=(u, p), json={'title': title, 'content': html_content, 'status': 'publish'}, timeout=30)
            if res.status_code in [200, 201]: return True, f"Bắn WP OK (ID: {res.json().get('id')})"
            return False, f"Lỗi WP API: {res.text[:100]}"
        except Exception as e: return False, f"Lỗi WP: {e}"

# ==========================================
# 🤖 CORE ENGINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, db, logs):
        self.db = db
        self.dash = {str(k).strip(): str(v).strip() for k, v in zip(self.db.get('DASHBOARD', pd.DataFrame())['DATA_KEY'], self.db.get('DASHBOARD', pd.DataFrame())['DATA_CONTENT'])}
        self.now, self.logs = get_vn_now(), logs
        self.web, self.pub_time, self.main_kw_row, self.kws, self.raw_html, self.title = None, None, None, [], "", ""
        self.out_lim, self.in_lim, self.inj_ext, self.inj_int = 0, 0, 0, 0
        self.metrics, self.imgs = {}, []
        if 'evo_cache' not in st.session_state: st.session_state.evo_cache = ""

    def log(self, ui, msg, lvl="info"):
        fmt = f'<span class="log-{lvl}">{msg}</span>' if lvl in ["error", "warn", "success", "quota", "detail"] else msg
        self.logs.append(f"[{get_vn_now().strftime('%H:%M:%S')}] {fmt}")
        if ui: ui.markdown(f'<div class="log-box" id="lbox">{"<br>".join(self.logs)}</div><script>var d=document.getElementById("lbox");d.scrollTop=d.scrollHeight;</script>', unsafe_allow_html=True)

    def parse_rng(self, val, def_val=0):
        try:
            if '-' in str(val): return random.randint(*sorted([int(x) for x in str(val).split('-')]))
            return int(str(val))
        except: return def_val

    def pick_random_prompt_variant(self, text):
        parts = [p.strip() for p in re.split(r'\|\|\|', str(text)) if p.strip()]
        return random.choice(parts) if parts else str(text).strip()

    def step1_slot(self, ui):
        df_rep, df_web = self.db.get('REPORT', pd.DataFrame()), self.db.get('WEBSITE', pd.DataFrame())
        batch, max_d = self.parse_rng(self.dash.get('BATCH_SIZE', 10)), self.parse_rng(self.dash.get('MAX_SCHEDULE_DAYS', 30))
        try:
            h1, m1 = map(int, str(self.dash.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')[0].split(':'))
            h2, m2 = map(int, str(self.dash.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')[1].split(':'))
            s1, s2 = sorted([int(x) for x in str(self.dash.get('POST_SPACING_MINUTES', '30-90')).split('-')])
        except: return self.log(ui, "🛑 Lỗi Config Giờ.", "error") or False

        today_posts = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.startswith(self.now.strftime('%Y-%m-%d'))]) if not df_rep.empty else 0
        if today_posts >= batch: return False

        for d_off in range(max_d + 1):
            day_x = self.now.date() + datetime.timedelta(days=d_off)
            for _, w in df_web.sample(frac=1).reset_index(drop=True).iterrows():
                ws_name, ws_lim = str(w.get('WS_NAME', '')).strip(), self.parse_rng(w.get('WS_POST_LIMIT', 1), 1)
                day_posts = df_rep[(df_rep['REP_WS_NAME'] == ws_name) & (df_rep['REP_PUBLISH_DATE'].str.startswith(day_x.strftime('%Y-%m-%d')))] if not df_rep.empty else pd.DataFrame()
                
                self.log(ui, f"🔍 [QUOTA] Web '{ws_name}' ({day_x}): {len(day_posts)}/{ws_lim}", "quota")
                if len(day_posts) < ws_lim:
                    st_t = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(h1, m1)))
                    ed_t = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(h2, m2)))
                    if d_off == 0 and self.now > ed_t: continue 
                    
                    base = max(self.now, st_t) if d_off == 0 else st_t
                    try: last_p = VN_TZ.localize(datetime.datetime.strptime(str(day_posts['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M')) if not day_posts.empty else base
                    except: last_p = base
                    
                    pub_t = max(last_p, base) + datetime.timedelta(minutes=random.randint(s1, s2)) if not day_posts.empty else base + datetime.timedelta(minutes=random.randint(0, 30))
                    pub_t = max(pub_t, self.now + datetime.timedelta(minutes=5))
                    if pub_t > ed_t: continue 
                    
                    self.web, self.pub_time = w, pub_t
                    self.log(ui, f"✅ [SLOT] {ws_name} | Lịch: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
        self.log(ui, "🛑 Full lịch.", "error")
        return False

    def step2_3_kw_serp(self, ui):
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        
        # ĐÃ FIX: Khôi phục lại biến self.main_kw_row
        self.main_kw_row = df_kw.sample(frac=1).sort_values('KW_STATUS').iloc[0]
        
        m_kw, m_cat, m_grp = str(self.main_kw_row['KW_TEXT']).strip(), str(self.main_kw_row.get('KW_CONTENT', '')).strip(), str(self.main_kw_row.get('KW_GROUP', '')).strip()
        self.out_lim, self.in_lim = self.parse_rng(self.web.get('WS_LINK_OUT_LIMIT', 0)), self.parse_rng(self.web.get('WS_LINK_IN_LIMIT', 0))
        subs_needed = max(0, (self.out_lim + self.in_lim) - 1)
        
        subs = df_kw[(df_kw['KW_TEXT'] != m_kw) & (df_kw['KW_CONTENT'] == m_cat) & (df_kw['KW_GROUP'] != m_grp)].head(subs_needed)['KW_TEXT'].tolist()
        self.kws = [m_kw] + subs
        self.log(ui, f"📦 [KWs] Cần {self.out_lim+self.in_lim} Links -> Gắn {len(self.kws)} KWs: {', '.join(self.kws)}", "detail")

        w_len = sorted([int(x) for x in str(self.dash.get('WORD_COUNT_RANGE', '900-1200')).split('-')])
        self.target_length = random.randint(w_len[0], w_len[1]) if len(self.kws) >= 3 else random.randint(w_len[0], w_len[1]) // 2
        
        s_key, c_list = self.dash.get('SERPAPI_KEY', ''), [c.strip() for c in str(self.dash.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
        self.serp_style = "Văn phong chuyên gia sâu sắc."
        if s_key:
            try:
                res = requests.get("https://serpapi.com/search", params={"q": m_kw, "hl": "vi", "gl": "vn", "api_key": s_key}, timeout=10).json().get("organic_results", [])
                links = [r["link"] for r in res[:10] if c_list and any(c in r.get("link","") for c in c_list)] or [r["link"] for r in res[:3]]
                if links:
                    rh = requests.get(links[0], headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                    if rh.status_code == 200:
                        soup = BeautifulSoup(rh.text, 'html.parser')
                        for t in soup(["script", "style", "nav", "footer"]): t.decompose()
                        self.serp_style = "\n".join([t.get_text(strip=True) for t in soup.find_all(['h2', 'h3', 'p'])])[:2500]
                        self.log(ui, f"✅ [SERP] Cào: {links[0]}")
            except: pass
        return True

    def step4_llm(self, ui):
        pmt = {k: self.pick_random_prompt_variant(self.dash.get(k, '')) for k in ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']}
        dist = self.target_length // max(len(self.kws), 1)

        strict_rules = f"""
        [SYSTEM STRICT RULE - BẮT BUỘC TUÂN THỦ MỌI KHOẢN]:
        1. CẤM TUYỆT ĐỐI các từ ngữ chào hỏi/dẫn dắt: "Kính thưa các Sếp", "Chào quý vị", "Thân gửi", "Tuyệt vời", "Dưới đây là". VÀO THẲNG VẤN ĐỀ BẰNG ĐOẠN SAPO.
        2. TỪ KHÓA CHÍNH "{self.kws[0]}": PHẢI NẰM Ở GIỮA HOẶC CUỐI TIÊU ĐỀ (Thẻ <h1>). TUYỆT ĐỐI KHÔNG ĐỂ Ở ĐẦU. Rải thêm 2 lần trong nội dung.
        3. TỪ KHÓA PHỤ: "{', '.join(self.kws[1:])}". Mỗi cụm xuất hiện 1 lần, cách nhau {dist} chữ. Không đổi dấu, không viết hoa đầu câu vô lý.
        4. TỔNG SỐ CHỮ: Chính xác {self.target_length} chữ. KHÔNG LẶP CẤU TRÚC: {st.session_state.evo_cache}.
        5. ĐA DẠNG ĐOẠN VĂN: Các đoạn văn phải có độ dài ngắn khác nhau ngẫu nhiên. Cấm viết các đoạn dài bằng nhau.
        6. TRẢ VỀ DUY NHẤT HTML CODE, BẮT ĐẦU BẰNG <h1>.
        """
        
        tpl = pmt['PROMPT_TEMPLATE'].replace('{{ws_persona}}', str(self.web.get('WS_PERSONA', ''))).replace('{{kw_intent}}', str(self.main_kw_row.get('KW_INTENT', ''))).replace('{{keyword}}', self.kws[0]).replace('{{word_count}}', str(self.target_length))
        for i, k in enumerate(self.kws): tpl = re.sub(rf'\[?REP_KW_{i+1}\]?', k, tpl, flags=re.IGNORECASE)
        
        master = f"{tpl}\n{pmt['PROMPT_CONTENT_STRATEGY']}\n{pmt['PROMPT_KEYWORD_SEARCH']}\n{pmt['PROMPT_SERP_STYLE']}\n[SERP Data]:\n{self.serp_style}\n{pmt['PROMPT_SEO_GLOBAL_RULE']}\n{pmt['PROMPT_AI_HUMANIZER']}\n{strict_rules}"

        g_keys = [k.strip() for k in str(self.dash.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        g_mods = [m.strip() for m in str(self.dash.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        
        for k in g_keys:
            genai.configure(api_key=k)
            for m in g_mods:
                self.log(ui, f"🌐 [API] Gen = {m}...", "detail")
                try: 
                    self.raw_html = genai.GenerativeModel(m).generate_content(master).text
                    break
                except: pass
            if self.raw_html: break

        if not self.raw_html: return self.log(ui, "🛑 API Sập.", "error") or False
            
        self.raw_html = self.raw_html.replace('```html', '').replace('```', '').strip()
        self.raw_html = re.sub(r'\*\*(.*?)\*\*', r'\1', self.raw_html) # Xóa dấu **
        
        for i, k in enumerate(self.kws): self.raw_html = re.sub(rf'\[?REP_KW_{i+1}\]?', k, self.raw_html, flags=re.IGNORECASE)
        self.raw_html = re.sub(r'\{\{keyword\}\}', self.kws[0], self.raw_html, flags=re.IGNORECASE)

        soup = BeautifulSoup(self.raw_html, 'html.parser')
        st.session_state.evo_cache = f"{len(soup.find_all('h2'))}H2,{len(soup.find_all('p'))}P"
        
        h1 = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.title = html.unescape(re.sub(r'<[^>]+>', '', h1.group(1)).strip()) if h1 else f"Bài: {self.kws[0]}"
        return True

    def step5_6_dom(self, ui):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        txt = self.raw_html
        for i, k in enumerate(self.kws): txt = re.sub(r'(?i)' + re.escape(k), f'__I_{i}__', txt, count=1)
        if not df_spin.empty:
            for _, r in df_spin.iterrows():
                o, rp = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_REPLACE', '')).strip()
                if o and rp: txt = re.sub(r'(?i)' + re.escape(o), rp, txt)
        for i, k in enumerate(self.kws): txt = txt.replace(f'__I_{i}__', k)

        soup = BeautifulSoup(txt, 'html.parser')
        ou = [u.strip() for u in str(self.web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if u.strip()]
        iu = [u.strip() for u in str(self.web.get('WS_LINK_IN_BACKLINK', '')).split(',') if u.strip()]
        
        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        missed_kws = []
        for k in self.kws:
            u = random.choice(ou) if self.inj_ext < self.out_lim and ou else (random.choice(iu) if self.inj_int < self.in_lim and iu else "")
            if not u: continue 
            
            injected = False
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)' + re.escape(k), p.get_text()):
                    p.replace_with(BeautifulSoup(re.sub(r'(?i)' + re.escape(k), lambda m: f"<a href='{u}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                    injected = True; break
            
            if not injected: missed_kws.append((k, u))
            else:
                if u in ou: self.inj_ext += 1
                else: self.inj_int += 1

        if missed_kws:
            avail_p = [p for p in soup.find_all('p') if not p.find('a') and len(p.get_text().split()) > 10]
            for k, u in missed_kws:
                success = False
                if avail_p:
                    tp = random.choice(avail_p)
                    words = [w for w in tp.get_text().split() if len(w) > 3 and w.isalpha()]
                    if words:
                        new_txt = tp.get_text().replace(random.choice(words), f"<a href='{u}'>{k}</a>", 1)
                        tp.replace_with(BeautifulSoup(f"<p>{new_txt}</p>", 'html.parser'))
                        avail_p.remove(tp)
                        success = True
                if not success: soup.append(BeautifulSoup(f"<p>Gợi ý thêm cho dịch vụ <a href='{u}'>{k}</a>.</p>", 'html.parser'))
                
                if u in ou: self.inj_ext += 1
                else: self.inj_int += 1

        self.log(ui, f"🛠️ [LINKS] {self.inj_ext}/{self.out_lim} Ext | {self.inj_int}/{self.in_lim} Int.", "success")
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
        
        self.raw_html = re.sub(r'<h1[^>]*>.*?</h1>', '', self.raw_html, count=1, flags=re.IGNORECASE|re.DOTALL).strip()
        
        if seo < (35 if self.is_short_form else 70) or ai > 20 or rd < 60: return self.log(ui, "❌ KCS FAIL", "error") or "FAIL"
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
                'REP_RESULT': res, 'REP_LOG': "\n".join(self.logs) if res == 'PENDING' else "", 'REP_HTML': self.raw_html if res == 'PENDING' else ""
            }
            rep_ws.append_row([row_d.get(h, "") for h in hdrs])
            
            if res == 'PENDING':
                ts = self.now.strftime('%Y-%m-%d %H:%M')
                for w, k_col, vals in [('KEYWORD', 'KW_TEXT', self.kws), ('IMAGE', 'IMG_URL', self.imgs)]:
                    if not vals: continue
                    sheet, d = ss.worksheet(w), ss.worksheet(w).get_all_values()
                    if len(d) > 1:
                        h = [str(x).strip() for x in d[0]]
                        im, i_s, idt = h.index(k_col) if k_col in h else -1, h.index(f"{w[:3]}_STATUS") if f"{w[:3]}_STATUS" in h else -1, h.index(f"{w[:3]}_DATE") if f"{w[:3]}_DATE" in h else -1
                        upds = []
                        for i, r in enumerate(d[1:], 2):
                            if im != -1 and len(r) > im and r[im].strip() in vals:
                                if i_s != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_s+1)}', 'values': [[self.parse_rng(r[i_s])+1]]})
                                if idt != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, idt+1)}', 'values': [[ts]]})
                        if upds: sheet.batch_update(upds)
                self.log(ui, "✅ Đã lưu DB.", "success")
        except Exception as e: self.log(ui, f"🛑 DB Error: {e}", "error")

# ==========================================
# 🖥 UI
# ==========================================
db = load_db()
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
    b_frc = bc2.button("⚡ Ép Lên bài", use_container_width=True)
    if bc3.button("🔄 Làm mới", use_container_width=True): load_db.clear(); st.rerun()
        
    if b_frc:
        st.info("⏳ ĐANG XỬ LÝ POST BÀI LÊN WEB...")
        load_db.clear()
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
                                    if il != -1: upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, il+1)}', 'values': [['']]})
                                    cnt += 1
                                else: bot.log(ui, f"🛑 {msg}", "error")
                    if upd:
                        ws.batch_update(upd)
                        st.success(f"🎉 Bắn thành công {cnt} bài!")
                        time.sleep(2); st.rerun()
                    else: bot.log(ui, "ℹ️ Không có bài PENDING hôm nay.", "warn")
        except Exception as e: bot.log(ui, f"🛑 Lỗi Post: {e}", "error")

    if b_run:
        load_db.clear()
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
                        db = load_db()
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
            lc2.text_area("HTML:", str(r.get('REP_HTML', '')), height=600, label_visibility="collapsed")
with t3: st.dataframe(d_rep, use_container_width=True)
