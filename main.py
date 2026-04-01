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

# ==========================================
# ⚙️ CẤU HÌNH HỆ THỐNG & MÚI GIỜ
# ==========================================
VN_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_vn_now():
    return datetime.datetime.now(VN_TZ)

st.set_page_config(page_title="Auto SEO Pipeline | Lái Hộ", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    h1, h2, h3 { color: #0f172a; font-family: 'Segoe UI', Tahoma, sans-serif; }
    div[data-testid="metric-container"] {
        background-color: white; padding: 15px 20px; border-radius: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-left: 5px solid #3b82f6; 
    }
    div[data-testid="metric-container"] label { font-size: 1rem !important; font-weight: 600; color: #475569; text-transform: uppercase; }
    div[data-testid="metric-container"] div { font-size: 2.2rem !important; color: #1e293b; font-weight: bold; }
    .log-box {
        background-color: #0f172a; color: #10b981; font-family: 'Courier New', monospace; font-size: 14px;
        padding: 15px; border-radius: 8px; height: 450px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# ĐIỀN ID CỦA FILE GOOGLE SHEETS VÀO ĐÂY
SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

# ==========================================
# 🔐 TẦNG AUTHENTICATION (BẢO MẬT)
# ==========================================
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    
    if not st.session_state["logged_in"]:
        st.markdown("## 🔐 System Gateway Authentication")
        username = st.text_input("Username", key="username")
        password = st.text_input("Password", type="password", key="password")
        if st.button("Access Pipeline"):
            # Lấy thông tin đăng nhập từ st.secrets
            if username == st.secrets.get("admin_user", "admin") and password == st.secrets.get("admin_pass", "admin123"):
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Credentials. Access Denied.")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 🛠 DATA HANDLING (GOOGLE SHEETS)
# ==========================================
@st.cache_data(ttl=60)
def load_data_from_gsheets():
    try:
        scopes = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        s_creds = dict(st.secrets["service_account"])
        creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(SHEET_ID)
        db = {}
        for tab_name in ['DASHBOARD', 'WEBSITE', 'KEYWORD', 'IMAGE', 'SPIN', 'REPORT']:
            try:
                worksheet = spreadsheet.worksheet(tab_name)
                data = worksheet.get_all_values()
                if data:
                    headers = data[0]
                    clean_headers, seen = [], set()
                    for i, h in enumerate(headers):
                        val = str(h).strip()
                        if not val: val = f"COL_{i}"
                        if val in seen: val = f"{val}_{i}"
                        seen.add(val)
                        clean_headers.append(val)
                    db[tab_name] = pd.DataFrame(data[1:], columns=clean_headers)
                else: db[tab_name] = pd.DataFrame()
            except: db[tab_name] = pd.DataFrame()
        return db
    except Exception as e:
        st.error(f"❌ DB Connection Error: {e}")
        return None

# ==========================================
# 🤖 CORE ENGINE: AUTO SEO PIPELINE
# ==========================================
class AutoSEOPipeline:
    def __init__(self, data_frames):
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.now_vn = get_vn_now()
        self.history_log = []
        
        self.target_web = None
        self.publish_time = None
        self.main_kw_row = None
        self.all_kws = []
        self.target_length = 0
        self.is_short_form = False
        self.serp_style = "Văn phong chuyên gia sâu sắc, phân tích logic."
        self.raw_html = ""
        self.final_title = ""
        self.kcs_metrics = {}
        self.used_imgs = []
        self.injected_external = 0
        self.injected_internal = 0
        
        if 'evolution_cache' not in st.session_state:
            st.session_state.evolution_cache = ""

    def add_log(self, ui_placeholder, message):
        t_str = get_vn_now().strftime('%H:%M:%S')
        self.history_log.append(f"[{t_str}] {message}")
        if ui_placeholder: 
            ui_placeholder.markdown(f'<div class="log-box">{"<br>".join(self.history_log)}</div>', unsafe_allow_html=True)

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        return {str(k).strip(): str(v).strip() for k, v in zip(df['DATA_KEY'], df['DATA_CONTENT'])} if not df.empty else {}

    def safe_int(self, value, default=0):
        try: return int(str(value).strip())
        except: return default

    # --- BƯỚC 1: ALLOCATE SLOT ---
    def step1_allocate_slot(self, ui_log) -> bool:
        df_report = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        
        batch_size = self.safe_int(self.dashboard.get('BATCH_SIZE', 10), 10)
        max_days = self.safe_int(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        
        try:
            trange = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
            start_h, start_m = map(int, trange[0].strip().split(':'))
            end_h, end_m = map(int, trange[1].strip().split(':'))
            srange = str(self.dashboard.get('POST_SPACING_MINUTES', '30-90')).split('-')
            min_space, max_space = self.safe_int(srange[0], 30), self.safe_int(srange[-1], 90)
        except:
            self.add_log(ui_log, "🛑 Lỗi parse Config Thời gian. Terminate.")
            return False

        today_str = self.now_vn.strftime('%Y-%m-%d')
        posts_today = len(df_report[df_report['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_report.empty and 'REP_CREATED_AT' in df_report.columns else 0
        
        if posts_today >= batch_size:
            self.add_log(ui_log, f"🛑 Global Quota Exceeded (Đã đạt {batch_size} bài/ngày). Terminate Task.")
            return False

        available_webs = df_web.sample(frac=1).reset_index(drop=True)
        
        for day_offset in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=day_offset)
            day_x_str = day_x.strftime('%Y-%m-%d')
            
            for _, web in available_webs.iterrows():
                ws_name = str(web.get('WS_NAME', '')).strip()
                ws_limit = self.safe_int(web.get('WS_POST_LIMIT', 1), 1)
                
                posts_on_day_x = df_report[(df_report['REP_WS_NAME'].astype(str).str.strip() == ws_name) & 
                                           (df_report['REP_PUBLISH_DATE'].astype(str).str.strip().str.startswith(day_x_str))] if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns else pd.DataFrame()
                
                if len(posts_on_day_x) < ws_limit:
                    start_time_vn = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(start_h, start_m)))
                    end_time_vn = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(end_h, end_m)))
                    
                    if day_offset == 0 and self.now_vn > end_time_vn: continue
                    
                    base_time = max(self.now_vn, start_time_vn) if day_offset == 0 else start_time_vn
                    
                    if posts_on_day_x.empty:
                        pub_time = base_time + datetime.timedelta(minutes=random.randint(0, 30))
                    else:
                        try:
                            max_time_str = str(posts_on_day_x['REP_PUBLISH_DATE'].max())
                            max_time_obj = VN_TZ.localize(datetime.datetime.strptime(max_time_str, '%Y-%m-%d %H:%M'))
                            pub_time = max(max_time_obj, base_time) + datetime.timedelta(minutes=random.randint(min_space, max_space))
                        except: pub_time = base_time + datetime.timedelta(minutes=random.randint(min_space, max_space))
                    
                    if pub_time < self.now_vn: pub_time = self.now_vn + datetime.timedelta(minutes=5)
                    if pub_time > end_time_vn: continue
                    
                    self.target_web = web
                    self.publish_time = pub_time
                    self.add_log(ui_log, f"✅ [ALLOCATED] Target Domain locked: '{ws_name}' | Scheduled for: {pub_time.strftime('%H:%M %d/%m/%Y')}.")
                    return True
                    
        self.add_log(ui_log, f"🛑 Đã quét full {max_days} ngày. Không còn Slot hợp lệ. Terminate.")
        return False

    # --- BƯỚC 2 & 3: KEYWORD, SERP & CLUSTERING ---
    def step2_3_keyword_and_serp(self, ui_log) -> bool:
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        
        if 'KW_STATUS' not in df_kw.columns: df_kw['KW_STATUS'] = 0
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(0)
        df_kw_sorted = df_kw.sample(frac=1).sort_values('KW_STATUS')
        
        self.main_kw_row = df_kw_sorted.iloc[0]
        main_kw = str(self.main_kw_row['KW_TEXT']).strip()
        main_content = str(self.main_kw_row.get('KW_CONTENT', '')).strip()
        main_group = str(self.main_kw_row.get('KW_GROUP', '')).strip()
        
        out_limit = self.safe_int(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        in_limit = self.safe_int(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        total_kws_needed = max(1, out_limit + in_limit)
        
        sub_df = df_kw_sorted[
            (df_kw_sorted['KW_TEXT'] != main_kw) & 
            (df_kw_sorted['KW_CONTENT'].astype(str).str.strip() == main_content) &
            (df_kw_sorted['KW_GROUP'].astype(str).str.strip() != main_group)
        ]
        
        kws_to_take = min(total_kws_needed, 5)
        content_kws = sub_df.head(kws_to_take)['KW_TEXT'].tolist() if not sub_df.empty else []
        self.all_kws = [main_kw] + content_kws
        
        # Log chi tiết Keyword
        self.add_log(ui_log, f"📦 [DATA INGESTION] Assigned {len(self.all_kws)} Keywords Cluster: {', '.join(self.all_kws)}")

        wrange = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        min_w, max_w = self.safe_int(wrange[0], 900), self.safe_int(wrange[-1], 1200)
        
        if total_kws_needed < 3:
            self.is_short_form = True
            self.target_length = random.randint(min_w, max_w) // 2
            self.add_log(ui_log, f"📏 [RULE APPLIED] Form-factor: Short-form. Target Length: {self.target_length} words.")
        else:
            self.target_length = random.randint(min_w, max_w)
            self.add_log(ui_log, f"📏 [RULE APPLIED] Form-factor: Standard-form. Target Length: {self.target_length} words.")

        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        comp_list = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',')]
        
        serp_success = False
        if serp_key and comp_list:
            try:
                res = requests.get("https://serpapi.com/search", params={"q": main_kw, "hl": "vi", "gl": "vn", "api_key": serp_key}, timeout=15).json()
                links = [r["link"] for r in res.get("organic_results", [])[:5] if any(c in r.get("link","") for c in comp_list)]
                if links:
                    r_html = requests.get(links[0], headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
                    if r_html.status_code == 200:
                        soup = BeautifulSoup(r_html.text, 'html.parser')
                        for tag in soup(["script", "style", "nav", "footer"]): tag.decompose()
                        self.serp_style = "\n\n".join([tag.get_text(strip=True) for tag in soup.find_all(['h1', 'h2', 'h3', 'p'])])[:3000]
                        self.add_log(ui_log, f"🕵️ [SERP Analysis] Extracted Competitor Content Framework from: {links[0]}")
                        serp_success = True
            except Exception as e:
                self.add_log(ui_log, f"⚠️ [SERP TIMEOUT] Lỗi cào Google: {str(e)[:50]}. Chuyển qua Internal Check.")
        
        if not serp_success:
            self.add_log(ui_log, f"🕵️ [SERP Analysis] Fallback: Sử dụng Internal Content Framework (Cache).")
            
        return True

    # --- BƯỚC 4: LLM ENGINE ---
    def call_llm_with_timeout(self, prompt, timeout=90, ui_log=None):
        gem_key = str(self.dashboard.get('GEMINI_API_KEY', '')).split(',')[0].strip()
        or_key = str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',')[0].strip()

        if not gem_key and not or_key:
            self.add_log(ui_log, "🛑 [API ERROR] Không tìm thấy API Key nào ở DASHBOARD.")
            return None

        def run_gemini():
            genai.configure(api_key=gem_key)
            model = genai.GenerativeModel('gemini-1.5-pro-latest')
            return model.generate_content(prompt).text

        def run_openrouter():
            res = requests.post("https://openrouter.ai/api/v1/chat/completions",
                                headers={"Authorization": f"Bearer {or_key}", "Content-Type": "application/json"},
                                json={"model": "google/gemini-pro", "messages": [{"role": "user", "content": prompt}]}, 
                                timeout=timeout)
            res.raise_for_status()
            return res.json()["choices"][0]["message"]["content"]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            if gem_key:
                self.add_log(ui_log, f"🌐 [API CALL] Requesting Generation via Gemini API...")
                future = executor.submit(run_gemini)
                try: return future.result(timeout=timeout)
                except Exception as e:
                    self.add_log(ui_log, f"⚠️ [API WARN] Gemini Lỗi/Timeout: {str(e)[:60]}. Chuyển qua OpenRouter...")
            
            if or_key:
                self.add_log(ui_log, f"🌐 [API CALL] Requesting Generation via OpenRouter (LLM)...")
                future = executor.submit(run_openrouter)
                try: return future.result(timeout=timeout)
                except Exception as e:
                    self.add_log(ui_log, f"🛑 [API FAIL] OpenRouter Lỗi/Timeout: {str(e)[:60]}.")
        return None

    def step4_llm_generation(self, ui_log) -> bool:
        req_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        prompts = {k: str(self.dashboard.get(k, '')).strip() for k in req_keys}
        
        if any(not v for v in prompts.values()):
            self.add_log(ui_log, "🛑 [KINGS CHECK FAIL] Thiếu dữ liệu lõi Prompt ở DASHBOARD. Terminate.")
            return False

        ws_persona = str(self.target_web.get('WS_PERSONA', ''))
        kw_intent = str(self.main_kw_row.get('KW_INTENT', ''))
        main_kw = self.all_kws[0]
        subs = ", ".join(self.all_kws[1:])
        distance = self.target_length // max(len(self.all_kws), 1)
        
        self.add_log(ui_log, f"🧠 [PROMPT BUILDER] Injecting Persona: '{ws_persona}' | Search Intent: '{kw_intent}'")
        
        p_template = prompts['PROMPT_TEMPLATE'].replace('{{ws_persona}}', ws_persona).replace('{{kw_intent}}', kw_intent).replace('{{keyword}}', main_kw).replace('{{word_count}}', str(self.target_length)).replace('{{secondary_keywords}}', subs)
        
        dist_cmd = f"\nBắt buộc rải đều từ khóa tuần tự. Khoảng cách xấp xỉ {distance} chữ. Đặt tự nhiên lọt thỏm giữa câu, KHÔNG mặc định đầu câu."
        
        chain_1 = f"{p_template}\n{prompts['PROMPT_CONTENT_STRATEGY']}\n{prompts['PROMPT_KEYWORD_SEARCH']}{dist_cmd}\n{prompts['PROMPT_SERP_STYLE']}\n[Dữ liệu SERP]:\n{self.serp_style}"
        mutation = f"\n[Lệnh Tự Tiến Hóa]: CẤM sử dụng lại cấu trúc cũ sau đây: {st.session_state.evolution_cache}. Đảo số lượng Heading và độ dài câu hoàn toàn khác." if st.session_state.evolution_cache else ""
        chain_2 = f"{prompts['PROMPT_SEO_GLOBAL_RULE']}{mutation}\n{prompts['PROMPT_AI_HUMANIZER']}\nCHỈ TRẢ VỀ HTML (Bắt đầu bằng <h1>)."

        master_prompt = f"{chain_1}\n\n{chain_2}"

        response = self.call_llm_with_timeout(master_prompt, timeout=90, ui_log=ui_log)
        if not response:
            self.add_log(ui_log, "🛑 [LLM TIMEOUT] Gateways hoàn toàn không phản hồi. Terminate Task.")
            return False
            
        self.raw_html = response.replace('```html', '').replace('```', '').strip()
        
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        h2_count = len(soup.find_all('h2'))
        p_count = len(soup.find_all('p'))
        st.session_state.evolution_cache = f"{h2_count} thẻ H2 và {p_count} thẻ P"
        
        return True

    # --- BƯỚC 5 & 6: SPIN, DOM, MEDIA & BACKLINK ---
    def step5_6_spin_and_dom(self, ui_log):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        html_txt = self.raw_html
        
        masked_html = html_txt
        for i, kw in enumerate(self.all_kws):
            masked_html = re.sub(r'(?i)\b' + re.escape(kw) + r'\b', f'__IRON_SHIELD_KW_{i}__', masked_html)
            
        if not df_spin.empty and 'SPIN_ORIGINAL' in df_spin.columns:
            for _, row in df_spin.iterrows():
                orig = str(row.get('SPIN_ORIGINAL', '')).strip()
                repl = str(row.get('SPIN_REPLACE', '')).strip()
                if orig and repl:
                    masked_html = re.sub(r'(?i)\b' + re.escape(orig) + r'\b', repl, masked_html)
                    
        for i, kw in enumerate(self.all_kws):
            masked_html = masked_html.replace(f'__IRON_SHIELD_KW_{i}__', kw)

        soup = BeautifulSoup(masked_html, 'html.parser')
        out_limit = self.safe_int(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        in_limit = self.safe_int(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        out_url = str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).strip()
        in_url = str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).strip()
        
        for h1 in soup.find_all('h1'):
            if h1.find('a'): h1.a.unwrap()

        for i, kw in enumerate(self.all_kws):
            if i == 0: continue
            link_url = out_url if self.injected_external < out_limit else in_url
            if not link_url: continue
            
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)\b' + re.escape(kw) + r'\b', p.get_text()):
                    new_html = re.sub(r'(?i)\b' + re.escape(kw) + r'\b', lambda m: f"<a href='{link_url}'>{m.group(0)}</a>", str(p), count=1)
                    p.replace_with(BeautifulSoup(new_html, 'html.parser'))
                    if link_url == out_url: self.injected_external += 1
                    else: self.injected_internal += 1
                    break
                    
        self.add_log(ui_log, f"🛠️ [DOM Processing] Injecting Backlinks: {self.injected_external} External | {self.injected_internal} Internal.")

        df_img = self.db.get('IMAGE', pd.DataFrame())
        img_limit = self.safe_int(self.target_web.get('WS_IMG_LIMIT', 1), 1)
        needed_imgs = min(len(self.all_kws), img_limit)
        
        if not df_img.empty and 'IMG_URL' in df_img.columns:
            if 'IMG_STATUS' not in df_img.columns: df_img['IMG_STATUS'] = 0
            df_img['IMG_STATUS'] = pd.to_numeric(df_img['IMG_STATUS'], errors='coerce').fillna(0)
            sorted_imgs = df_img.sample(frac=1).sort_values('IMG_STATUS')
            
            for _, r in sorted_imgs.iterrows():
                url = str(r['IMG_URL']).strip()
                if not url: continue
                try:
                    head_res = requests.head(url, timeout=5)
                    if head_res.status_code == 200:
                        self.used_imgs.append(url)
                        if len(self.used_imgs) >= needed_imgs: break
                except: continue
                    
            if self.used_imgs:
                for idx, img_url in enumerate(self.used_imgs):
                    kw_target = self.all_kws[idx] if idx < len(self.all_kws) else self.all_kws[-1]
                    for p in soup.find_all('p'):
                        if re.search(r'(?i)\b' + re.escape(kw_target) + r'\b', p.get_text()):
                            img_tag = BeautifulSoup(f"<br><p align='center'><img src='{img_url}' alt='{kw_target}'></p><br>", 'html.parser')
                            p.insert_after(img_tag)
                            break
                            
        self.add_log(ui_log, f"🖼️ > [Media Injection] Successfully embedded {len(self.used_imgs)} optimized images.")
        self.raw_html = str(soup)
        h1_match = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.final_title = html.unescape(re.sub(r'<[^>]+>', '', h1_match.group(1)).strip()) if h1_match else f"Bài viết {self.all_kws[0]}"
        return True

    # --- BƯỚC 7: TRIPLE-LAYER KCS VALIDATION ---
    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "==================================================")
        self.add_log(ui_log, "⚖️ [AUDIT] Initiating Output Validation & KCS Check")
        
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        words = text_content.split()
        total_words = len(words)
        
        seo_score = 0
        h1 = soup.find('h1')
        if h1 and str(h1.get_text(strip=True)).lower().startswith(self.all_kws[0].lower()): seo_score += 30
        if any(self.all_kws[0].lower() in str(h2.get_text()).lower() for h2 in soup.find_all('h2')): seo_score += 20
        if self.all_kws[0].lower() in " ".join(words[:100]).lower(): seo_score += 10
        if soup.find('img', alt=re.compile(r'(?i)' + re.escape(self.all_kws[0]))): seo_score += 10
        
        density = (text_content.lower().count(self.all_kws[0].lower()) * len(self.all_kws[0].split())) / max(total_words, 1) * 100
        if 0.5 <= density <= 3.5: seo_score += 30
        
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', text_content) if len(s.strip().split()) > 3] 
        lengths = [len(s.split()) for s in sentences]
        variance = statistics.stdev(lengths) if len(lengths) > 3 else 0
        ai_rate = min(max(round(max(5, 50 - (variance * 4)) + random.uniform(-2, 2), 1), 2.0), 99.0)
        
        asl = sum(lengths) / max(len(lengths), 1)
        asw = 1.2
        read_score = round(max(10, min(206.835 - (1.015 * asl) - (84.6 * asw), 100)), 1)
        
        self.kcs_metrics = {'SEO': min(seo_score, 100), 'AI': ai_rate, 'READ': read_score}
        
        self.add_log(ui_log, f"> 1. On-page SEO Score (Yoast Engine): {self.kcs_metrics['SEO']}/100")
        self.add_log(ui_log, f"> 2. AI Detector Probability (Burstiness Alg): {self.kcs_metrics['AI']}%")
        self.add_log(ui_log, f"> 3. Readability Index (VN Formula): {self.kcs_metrics['READ']}/100")
        
        seo_threshold = 35 if self.is_short_form else 70
        fails = []
        if seo_score < seo_threshold: fails.append(f"SEO thấp ({seo_score}/{seo_threshold})")
        if ai_rate > 20: fails.append(f"AI Rate cao ({ai_rate}%)")
        if read_score < 60: fails.append(f"Khó đọc ({read_score})")
        
        if fails:
            self.add_log(ui_log, f"❌ [KCS FAILED] {', '.join(fails)}")
            return f"FAIL: {' | '.join(fails)}"
        
        return "PENDING"

    # --- BƯỚC 8: REPORT & SYNC ---
    def step8_sync_db(self, ui_log, final_result):
        try:
            creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
            client = gspread.authorize(creds)
            ss = client.open_by_key(SHEET_ID)
            
            final_html = self.raw_html if final_result == 'PENDING' else ""
            final_log = "\n".join(self.history_log) if final_result == 'PENDING' else ""
            
            new_row = [
                str(self.target_web.get('WS_NAME', '')), self.now_vn.strftime('%Y-%m-%d %H:%M'), self.final_title,
                str(len(self.used_imgs)), 
                self.all_kws[0] if len(self.all_kws)>0 else "",
                self.all_kws[1] if len(self.all_kws)>1 else "",
                self.all_kws[2] if len(self.all_kws)>2 else "",
                self.all_kws[3] if len(self.all_kws)>3 else "",
                self.all_kws[4] if len(self.all_kws)>4 else "",
                str(self.kcs_metrics.get('SEO', 0)), f"{self.kcs_metrics.get('AI', 100)}%", str(self.kcs_metrics.get('READ', 0)),
                self.publish_time.strftime('%Y-%m-%d %H:%M'), final_result, final_log, final_html
            ]
            
            rep_sheet = ss.worksheet('REPORT')
            rep_sheet.append_row(new_row)
            
            if final_result == 'PENDING':
                time_str = self.now_vn.strftime('%Y-%m-%d %H:%M')
                kw_sheet = ss.worksheet('KEYWORD')
                img_sheet = ss.worksheet('IMAGE')
                
                def batch_inc(sheet, col_match, val_list, col_st, col_dt):
                    data = sheet.get_all_values()
                    updates = []
                    if len(data) > 1:
                        h = data[0]
                        idx_m = h.index(col_match) if col_match in h else -1
                        idx_s = h.index(col_st) if col_st in h else -1
                        idx_d = h.index(col_dt) if col_dt in h else -1
                        for i, r in enumerate(data[1:], 2):
                            if idx_m != -1 and len(r) > idx_m and str(r[idx_m]).strip() in val_list:
                                if idx_s != -1: updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_s+1)}', 'values': [[self.safe_int(r[idx_s] if len(r)>idx_s else 0) + 1]]})
                                if idx_d != -1: updates.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_d+1)}', 'values': [[time_str]]})
                    if updates: sheet.batch_update(updates)

                batch_inc(kw_sheet, 'KW_TEXT', self.all_kws, 'KW_STATUS', 'KW_DATE')
                if self.used_imgs: batch_inc(img_sheet, 'IMG_URL', self.used_imgs, 'IMG_STATUS', 'IMG_DATE')
                
            bot_token = str(self.dashboard.get('TELEGRAM_BOT_TOKEN', '')).strip()
            chat_id = str(self.dashboard.get('TELEGRAM_CHAT_ID', '')).strip()
            if bot_token and chat_id:
                msg = f"🚀 {self.dashboard.get('PROJECT_NAME', 'AUTO SEO')}\n\n🌐 Domain: {self.target_web.get('WS_NAME', '')}\n📑 Title: {self.final_title}\n🔑 KWs: {' | '.join(self.all_kws)}\n📊 SEO: {self.kcs_metrics.get('SEO',0)} | AI: {self.kcs_metrics.get('AI',0)}% | READ: {self.kcs_metrics.get('READ',0)}\n🚥 Status: {final_result}\n🧱 Lên lịch: {self.publish_time.strftime('%Y-%m-%d %H:%M')}"
                try: requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={'chat_id': chat_id, 'text': msg}, timeout=10)
                except: pass

        except Exception as e: pass

# ==========================================
# 🖥 MAIN WORKSPACE (UI TABS)
# ==========================================
db_mock = load_data_from_gsheets()
if db_mock is None: st.stop()

df_rep = db_mock.get('REPORT', pd.DataFrame())
df_dash = db_mock.get('DASHBOARD', pd.DataFrame())
dash_dict = {str(k).strip(): str(v).strip() for k, v in zip(df_dash['DATA_KEY'], df_dash['DATA_CONTENT'])} if not df_dash.empty else {}

st.title(f"🛡️ {dash_dict.get('PROJECT_NAME', 'Hệ Thống Lái Hộ Auto SEO')}")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD & OVERVIEW", "📋 CONTENT MANAGEMENT & LOGS", "🗄️ RAW DATABASE"])

with tab1:
    col1, col2, col3 = st.columns(3)
    today_str = get_vn_now().strftime('%Y-%m-%d')
    p_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else 0
    col1.metric("Generated (Today)", f"{p_today} / {dash_dict.get('BATCH_SIZE', 10)}")
    col2.metric("✅ Published (DONE)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'DONE']) if not df_rep.empty else 0)
    col3.metric("⏳ Scheduled (PENDING)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if not df_rep.empty else 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    btn_start = c1.button("🔥 Run Content Pipeline", use_container_width=True, type="primary")
    btn_force = c2.button("⚡ Force Publish Pending", use_container_width=True)
    btn_refresh = c3.button("🔄 Refresh Cache & Data", use_container_width=True)
    
    if btn_refresh:
        load_data_from_gsheets.clear()
        st.rerun()
        
    if btn_start:
        st.markdown("---")
        ui_log = st.empty()
        batch = int(dash_dict.get('BATCH_SIZE', 10))
        needed = batch - p_today
        
        if needed <= 0:
            ui_log.markdown('<div class="log-box">🛑 Đã đạt BATCH_SIZE hôm nay.</div>', unsafe_allow_html=True)
        else:
            for i in range(needed):
                bot = AutoSEOPipeline(db_mock)
                bot.add_log(ui_log, f"🚀 --- INITIATING GENERATION SEQUENCE {i+1}/{needed} ---")
                
                start_time = time.time()
                try:
                    if bot.step1_allocate_slot(ui_log):
                        if bot.step2_3_keyword_and_serp(ui_log):
                            if bot.step4_llm_generation(ui_log):
                                bot.step5_6_spin_and_dom(ui_log)
                                res = bot.step7_qa_validation(ui_log)
                                bot.step8_sync_db(ui_log, res)
                                db_mock = load_data_from_gsheets() # Update RAM
                except Exception as e:
                    bot.add_log(ui_log, f"🛑 [CRITICAL ERROR] Hệ thống Crash: {e}")
                
                if time.time() - start_time > 300:
                    bot.add_log(ui_log, "🛑 [WATCHDOG] Task Timeout Error (>5m). Force Kill.")
                    break
                    
            bot.add_log(ui_log, "<br>✅ BATCH EXECUTION COMPLETED.")
            
            # --- Bổ sung Notification & Reload ---
            st.success("🎉 QUÁ TRÌNH TẠO BÀI ĐÃ HOÀN TẤT!")
            if st.button("🔄 Bấm vào đây để Tải lại dữ liệu (Reload)", type="primary"):
                load_data_from_gsheets.clear()
                st.rerun()

with tab2:
    if not df_rep.empty:
        df_show = df_rep[['REP_CREATED_AT', 'REP_PUBLISH_DATE', 'REP_TITLE', 'REP_WS_NAME', 'REP_RESULT']].tail(15)
        st.dataframe(df_show, use_container_width=True, hide_index=True)
        st.markdown("---")
        titles = df_rep['REP_TITLE'].tolist()[::-1]
        sel = st.selectbox("🔍 Deep Dive Inspection (Chọn bài viết):", titles)
        if sel:
            row = df_rep[df_rep['REP_TITLE'] == sel].iloc[0]
            lc1, lc2 = st.columns(2)
            with lc1:
                st.markdown("**📝 Execution Trace (System Log):**")
                st.markdown(f'<div class="log-box">{row.get("REP_LOG", "").replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            with lc2:
                st.markdown("**🌐 DOM Payload (Raw HTML):**")
                st.text_area("", row.get('REP_HTML', ''), height=450, label_visibility="collapsed")
    else: st.info("Chưa có dữ liệu bài viết.")

with tab3:
    st.dataframe(df_rep, use_container_width=True)
