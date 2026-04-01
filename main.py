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
        padding: 15px; border-radius: 8px; height: 500px; overflow-y: auto; border: 1px solid #334155; line-height: 1.6;
        word-wrap: break-word;
    }
    .log-error { color: #ef4444; font-weight: bold; }
    .log-warn { color: #f59e0b; }
    .log-success { color: #3b82f6; font-weight: bold; }
    .log-quota { color: #a855f7; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# SẾP ĐIỀN ID FILE GOOGLE SHEETS VÀO ĐÂY
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
# 🛠 HÀM KẾT NỐI GOOGLE SHEETS (CACHE 60s)
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
        self.serp_style = "Văn phong chuyên gia sâu sắc."
        self.raw_html = ""
        self.final_title = ""
        self.kcs_metrics = {}
        self.used_imgs = []
        
        # Đã thêm 2 biến này để FIX LỖI đỗ xúc xắc 2 lần cho Limit Link
        self.out_lim = 0
        self.in_lim = 0
        self.injected_ext, self.injected_int = 0, 0
        
        if 'evolution_cache' not in st.session_state: st.session_state.evolution_cache = ""

    def add_log(self, ui_placeholder, message, level="info"):
        t_str = get_vn_now().strftime('%H:%M:%S')
        fmt_msg = message
        if level == "error": fmt_msg = f'<span class="log-error">{message}</span>'
        elif level == "warn": fmt_msg = f'<span class="log-warn">{message}</span>'
        elif level == "success": fmt_msg = f'<span class="log-success">{message}</span>'
        elif level == "quota": fmt_msg = f'<span class="log-quota">{message}</span>'
        
        self.history_log.append(f"[{t_str}] {fmt_msg}")
        if ui_placeholder: 
            log_html = f'<div class="log-box" id="logbox">{"<br>".join(self.history_log)}</div><script>var objDiv = document.getElementById("logbox"); objDiv.scrollTop = objDiv.scrollHeight;</script>'
            ui_placeholder.markdown(log_html, unsafe_allow_html=True)

    def safe_int(self, value, default=0):
        try: return int(str(value).strip())
        except: return default

    def parse_random_range(self, val_str, default=0):
        try:
            s = str(val_str).strip()
            if not s: return default
            if '-' in s:
                parts = s.split('-')
                return random.randint(int(parts[0].strip()), int(parts[1].strip()))
            return int(s)
        except:
            return default

    # --- BƯỚC 1: TÌM SLOT TRỐNG THÔNG MINH ---
    def step1_allocate_slot(self, ui_log) -> bool:
        df_rep = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        
        batch_size = self.parse_random_range(self.dashboard.get('BATCH_SIZE', 10), 10)
        max_days = self.parse_random_range(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        
        try:
            trange = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
            start_h, start_m = map(int, trange[0].strip().split(':'))
            end_h, end_m = map(int, trange[1].strip().split(':'))
            min_s, max_s = self.parse_random_range(self.dashboard.get('POST_SPACING_MINUTES', '30-90'), 30), self.parse_random_range(self.dashboard.get('POST_SPACING_MINUTES', '30-90'), 90)
        except:
            self.add_log(ui_log, "🛑 [LỖI CONFIG] Khung giờ sai format.", "error")
            return False

        today_str = self.now_vn.strftime('%Y-%m-%d')
        posts_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else 0
        
        if posts_today >= batch_size:
            self.add_log(ui_log, f"🛑 Global Quota Exceeded (Đã chạy đủ {batch_size} bài).", "error")
            return False

        avail_webs = df_web.sample(frac=1).reset_index(drop=True)
        for d_off in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=d_off)
            day_x_str = day_x.strftime('%Y-%m-%d')
            
            for _, web in avail_webs.iterrows():
                ws_name = str(web.get('WS_NAME', '')).strip()
                ws_limit = self.parse_random_range(web.get('WS_POST_LIMIT', 1), 1)
                posts_day_x = df_rep[(df_rep['REP_WS_NAME'].astype(str).str.strip() == ws_name) & (df_rep['REP_PUBLISH_DATE'].astype(str).str.strip().str.startswith(day_x_str))] if not df_rep.empty and 'REP_PUBLISH_DATE' in df_rep.columns else pd.DataFrame()
                
                self.add_log(ui_log, f"🔍 [CHECK QUOTA] Global: {posts_today}/{batch_size} | Local '{ws_name}' ({day_x_str}): {len(posts_day_x)}/{ws_limit}", "quota")
                
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
                    self.add_log(ui_log, f"✅ [CHỐT SLOT] Web: {ws_name} | Giờ hẹn: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
        self.add_log(ui_log, f"🛑 Lịch đã full {max_days} ngày.", "error")
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
        
        # ĐÃ FIX: Chốt cứng Quota ngay từ đây, không roll xúc xắc lại ở Bước 6
        self.out_lim = self.parse_random_range(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        self.in_lim = self.parse_random_range(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        
        # ĐÃ FIX TÍNH TOÁN: Tổng Từ khóa = Tổng Link (1 Chính + Phần còn lại là Phụ)
        total_links = self.out_lim + self.in_lim
        kws_needed = max(1, total_links)
        subs_needed = max(0, kws_needed - 1)
        
        self.add_log(ui_log, f"📐 [QUOTA TỪ KHÓA] Link Ngoại ({self.out_lim}) + Nội ({self.in_lim}) = Cần tổng {kws_needed} KWs (1 Chính + {subs_needed} Phụ).", "quota")
        
        sub_df = df_sorted[(df_sorted['KW_TEXT'] != main_kw) & (df_sorted['KW_CONTENT'].astype(str).str.strip() == main_cat) & (df_sorted['KW_GROUP'].astype(str).str.strip() != main_grp)]
        subs = sub_df.head(subs_needed)['KW_TEXT'].tolist() if not sub_df.empty else []
        self.all_kws = [main_kw] + subs
        self.add_log(ui_log, f"📦 [GOM NHÓM] Lấy {len(self.all_kws)} KWs: {', '.join(self.all_kws)}")

        wrange = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        min_w, max_w = self.safe_int(wrange[0], 900), self.safe_int(wrange[-1], 1200)
        
        if len(self.all_kws) < 3:
            self.is_short_form = True
            self.target_length = random.randint(min_w, max_w) // 2
        else: self.target_length = random.randint(min_w, max_w)
        self.add_log(ui_log, f"📏 [RULE BÀI] Target: {self.target_length} chữ.")

        serp_key = self.dashboard.get('SERPAPI_KEY', '').strip()
        comp_list = [c.strip() for c in str(self.dashboard.get('COMPETITOR_LIST', '')).split(',') if c.strip()]
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
                        self.add_log(ui_log, f"🕵️ [SERP] Extract thành công từ đối thủ.")
                        serp_success = True
            except: pass
        if not serp_success: self.add_log(ui_log, f"🕵️ [SERP] Dùng Internal Cache.")
        return True

    # --- BƯỚC 4: GỌI AI ---
    def step4_llm_generation(self, ui_log) -> bool:
        req_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        prompts = {k: str(self.dashboard.get(k, '')).strip() for k in req_keys}
        if any(not v for v in prompts.values()):
            self.add_log(ui_log, "🛑 Tab DASHBOARD trống ô PROMPT.", "error")
            return False

        ws_per = str(self.target_web.get('WS_PERSONA', ''))
        kw_int = str(self.main_kw_row.get('KW_INTENT', ''))
        main_kw = self.all_kws[0]
        subs = ", ".join(self.all_kws[1:])
        dist = self.target_length // max(len(self.all_kws), 1)

        # Cường hóa lệnh ép H1 cho AI đỡ cãi
        force_kw = f"\n[LỆNH ÉP TỐI THƯỢNG - KHÔNG THỂ BỎ QUA]:\n1. TỪ KHÓA CHÍNH: '{main_kw}' -> Bắt buộc phải sinh ra thẻ <h1> chứa từ khóa này (vị trí ngẫu nhiên trong thẻ) và rải tự nhiên trong nội dung.\n2. TỪ KHÓA PHỤ: '{subs}' -> Rải đều cách nhau {dist} chữ."
        
        p_tpl = prompts['PROMPT_TEMPLATE'].replace('{{ws_persona}}', ws_per).replace('{{kw_intent}}', kw_int).replace('{{keyword}}', main_kw).replace('[REP_KW_1]', main_kw).replace('REP_KW_1', main_kw).replace('{{word_count}}', str(self.target_length))
        
        c1 = f"{p_tpl}\n{prompts['PROMPT_CONTENT_STRATEGY']}\n{prompts['PROMPT_KEYWORD_SEARCH']}\n{prompts['PROMPT_SERP_STYLE']}\n[Dữ liệu SERP]:\n{self.serp_style}"
        mut = f"\n[Tiến Hóa]: Cấm lặp cấu trúc: {st.session_state.evolution_cache}." if st.session_state.evolution_cache else ""
        c2 = f"{prompts['PROMPT_SEO_GLOBAL_RULE']}{mut}\n{prompts['PROMPT_AI_HUMANIZER']}\n{force_kw}\nCHỈ TRẢ VỀ HTML BẮT ĐẦU BẰNG THẺ <h1>."
        
        master_prompt = f"{c1}\n\n{c2}"

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
                except Exception as e: self.add_log(ui_log, f"⚠️ Gemini sập: {str(e)[:80]}", "warn")

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
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        st.session_state.evolution_cache = f"{len(soup.find_all('h2'))} H2, {len(soup.find_all('p'))} P"
        return True

    # --- BƯỚC 5 & 6: XÀO VÀ GẮN LINK ---
    def step5_6_spin_and_dom(self, ui_log):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        html_txt = self.raw_html
        
        # Sửa lại Regex Tiếng Việt để Link ăn ngon lành
        for i, kw in enumerate(self.all_kws): html_txt = re.sub(r'(?i)' + re.escape(kw), f'__IRON_{i}__', html_txt, count=1)
        if not df_spin.empty and 'SPIN_ORIGINAL' in df_spin.columns:
            for _, r in df_spin.iterrows():
                o, rp = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_REPLACE', '')).strip()
                if o and rp: html_txt = re.sub(r'(?i)' + re.escape(o), rp, html_txt)
        for i, kw in enumerate(self.all_kws): html_txt = html_txt.replace(f'__IRON_{i}__', kw)

        soup = BeautifulSoup(html_txt, 'html.parser')
        
        o_urls = [u.strip() for u in str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',') if u.strip()]
        i_urls = [u.strip() for u in str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).split(',') if u.strip()]
        
        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        for i, kw in enumerate(self.all_kws):
            if i == 0: continue 
            url = random.choice(o_urls) if self.injected_ext < self.out_lim and o_urls else (random.choice(i_urls) if self.injected_int < self.in_lim and i_urls else "")
            if not url: continue
            
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)' + re.escape(kw), p.get_text()):
                    # Bỏ \b trong regex để bypass lỗi unicode Tiếng Việt
                    p.replace_with(BeautifulSoup(re.sub(r'(?i)' + re.escape(kw), lambda m: f"<a href='{url}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                    if url in o_urls: self.injected_ext += 1
                    else: self.injected_int += 1
                    break
                    
        self.add_log(ui_log, f"🛠️ [GẮN LINK] {self.injected_ext}/{self.out_lim} Ngoại | {self.injected_int}/{self.in_lim} Nội.")

        df_img = self.db.get('IMAGE', pd.DataFrame())
        max_img = self.parse_random_range(self.target_web.get('WS_IMG_LIMIT', 1), 1)
        req_img = min(len(self.all_kws), max_img)
        if not df_img.empty and 'IMG_URL' in df_img.columns:
            df_img['IMG_STATUS'] = pd.to_numeric(df_img.get('IMG_STATUS', 0), errors='coerce').fillna(0)
            sorted_imgs = df_img.sample(frac=1).sort_values('IMG_STATUS')
            for _, r in sorted_imgs.iterrows():
                url = str(r['IMG_URL']).strip()
                try:
                    if requests.head(url, timeout=5).status_code == 200:
                        self.used_imgs.append(url)
                        if len(self.used_imgs) >= req_img: break
                except: continue
            if self.used_imgs:
                for idx, i_url in enumerate(self.used_imgs):
                    kw_tag = self.all_kws[idx] if idx < len(self.all_kws) else self.all_kws[-1]
                    for p in soup.find_all('p'):
                        if re.search(r'(?i)' + re.escape(kw_tag), p.get_text()):
                            p.insert_after(BeautifulSoup(f"<br><p align='center'><img src='{i_url}' alt='{kw_tag}'></p><br>", 'html.parser'))
                            break
        self.add_log(ui_log, f"🖼️ [GẮN ẢNH] Thành công {len(self.used_imgs)}/{max_img} ảnh.")
        self.raw_html = str(soup)
        h1_m = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.final_title = html.unescape(re.sub(r'<[^>]+>', '', h1_m.group(1)).strip()) if h1_m else f"Bài: {self.all_kws[0]}"
        return True

    # --- BƯỚC 7: KCS (MINH BẠCH BẢNG ĐIỂM SEO) ---
    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "⚖️ [KCS] Bắt đầu chấm điểm...")
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        txt = soup.get_text(separator=' ', strip=True)
        words = txt.split()
        kw_main_lower = self.all_kws[0].lower()
        
        # Đã thêm các biến rời để in log breakdown
        h1_pt = h2_pt = body_pt = alt_pt = den_pt = 0
        
        h1 = soup.find('h1')
        if h1 and kw_main_lower in str(h1.get_text(strip=True)).lower(): h1_pt = 30
        if any(kw_main_lower in str(h2.get_text()).lower() for h2 in soup.find_all('h2')): h2_pt = 20
        if kw_main_lower in txt.lower(): body_pt = 10
        if soup.find('img', alt=re.compile(r'(?i)' + re.escape(kw_main_lower))): alt_pt = 10
        
        density = (txt.lower().count(kw_main_lower) * len(self.all_kws[0].split())) / max(len(words), 1) * 100
        if 0.5 <= density <= 4.0: den_pt = 30
        
        seo = h1_pt + h2_pt + body_pt + alt_pt + den_pt
        
        lens = [len(s.split()) for s in re.split(r'[.!?\n]+', txt) if len(s.split()) > 3]
        ai = min(max(round(max(5, 50 - ((statistics.stdev(lens) if len(lens)>3 else 0) * 4)), 1), 2.0), 99.0)
        read = round(max(10, min(206.835 - (1.015 * (sum(lens) / max(len(lens), 1))) - 84.6 * 1.2, 100)), 1)
        
        self.kcs_metrics = {'SEO': min(seo, 100), 'AI': ai, 'READ': read}
        
        # MINH BẠCH LOG SEO Ở ĐÂY SẾP ƠI
        self.add_log(ui_log, f"> Chi tiết SEO: H1({h1_pt}) + H2({h2_pt}) + Body({body_pt}) + Alt({alt_pt}) + Density({den_pt}) = {seo}/100")
        self.add_log(ui_log, f"> AI Rate: {ai}% | Dễ đọc VN: {read}/100")
        
        req = 35 if self.is_short_form else 70
        fails = []
        if seo < req: fails.append(f"SEO thấp ({seo}/{req})")
        if ai > 20: fails.append(f"Văn AI ({ai}%)")
        if read < 60: fails.append(f"Khó đọc ({read})")
        
        if fails:
            self.add_log(ui_log, f"❌ [KCS FAILED] {', '.join(fails)}", "error")
            return "FAIL"
        return "PENDING"

    # --- BƯỚC 8: LƯU (DYNAMIC MAPPING) ---
    def step8_sync_db(self, ui_log, final_result):
        try:
            creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
            ss = gspread.authorize(creds).open_by_key(SHEET_ID)
            rep_ws = ss.worksheet('REPORT')
            
            f_html = self.raw_html if final_result == 'PENDING' else ""
            f_log = "\n".join(self.history_log) if final_result == 'PENDING' else ""
            
            row_data = {
                'REP_WS_NAME': str(self.target_web.get('WS_NAME', '')),
                'REP_CREATED_AT': self.now_vn.strftime('%Y-%m-%d %H:%M'),
                'REP_TITLE': self.final_title,
                'REP_IMG_COUNT': str(len(self.used_imgs)),
                'REP_KW_1': self.all_kws[0] if len(self.all_kws)>0 else "",
                'REP_KW_2': self.all_kws[1] if len(self.all_kws)>1 else "",
                'REP_KW_3': self.all_kws[2] if len(self.all_kws)>2 else "",
                'REP_KW_4': self.all_kws[3] if len(self.all_kws)>3 else "",
                'REP_KW_5': self.all_kws[4] if len(self.all_kws)>4 else "",
                'REP_SEO_SCORE': str(self.kcs_metrics.get('SEO', 0)),
                'REP_AI_RATE': f"{self.kcs_metrics.get('AI', 100)}%",
                'REP_READABILITY': str(self.kcs_metrics.get('READ', 0)),
                'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
                'REP_POST_URL': "", 
                'REP_RESULT': final_result,
                'REP_LOG': f_log,
                'REP_HTML': f_html
            }
            
            headers = rep_ws.row_values(1)
            new_row = [row_data.get(str(h).strip(), "") for h in headers]
            rep_ws.append_row(new_row)
            
            if final_result == 'PENDING':
                time_s = self.now_vn.strftime('%Y-%m-%d %H:%M')
                def batch_upd(ws, col_match, val_list, col_st, col_dt):
                    data = ws.get_all_values()
                    upds = []
                    if len(data) > 1:
                        h = [str(col).strip() for col in data[0]]
                        i_m = h.index(col_match) if col_match in h else -1
                        i_s = h.index(col_st) if col_st in h else -1
                        i_d = h.index(col_dt) if col_dt in h else -1
                        for i, r in enumerate(data[1:], 2):
                            if i_m != -1 and len(r) > i_m and str(r[i_m]).strip() in val_list:
                                if i_s != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_s+1)}', 'values': [[self.safe_int(r[i_s] if len(r)>i_s else 0) + 1]]})
                                if i_d != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_d+1)}', 'values': [[time_s]]})
                    if upds: ws.batch_update(upds)

                batch_upd(ss.worksheet('KEYWORD'), 'KW_TEXT', self.all_kws, 'KW_STATUS', 'KW_DATE')
                if self.used_imgs: batch_upd(ss.worksheet('IMAGE'), 'IMG_URL', self.used_imgs, 'IMG_STATUS', 'IMG_DATE')
                self.add_log(ui_log, f"✅ [HOÀN TẤT] Lưu thành công. Status: {final_result}", "success")
            else: self.add_log(ui_log, f"⚠️ [THẤT BẠI] Đã ghi log lỗi vào Sheet.", "warn")
                
            bot_t, chat_i = str(self.dashboard.get('TELEGRAM_BOT_TOKEN', '')).strip(), str(self.dashboard.get('TELEGRAM_CHAT_ID', '')).strip()
            if bot_t and chat_i:
                msg = f"🚀 {self.dashboard.get('PROJECT_NAME', '')}\n🌐 {self.target_web.get('WS_NAME', '')}\n📑 {self.final_title}\n🔑 KWs: {' | '.join(self.all_kws)}\n📊 SEO: {self.kcs_metrics.get('SEO',0)} | AI: {self.kcs_metrics.get('AI',0)}% | READ: {self.kcs_metrics.get('READ',0)}\n🚥 {final_result}\n🧱 {self.publish_time.strftime('%Y-%m-%d %H:%M')}"
                try: requests.post(f"https://api.telegram.org/bot{bot_t}/sendMessage", data={'chat_id': chat_i, 'text': msg}, timeout=10)
                except: pass

        except Exception as e: self.add_log(ui_log, f"🛑 [DB ERROR] Lỗi ghi Database: {str(e)[:100]}", "error")

# ==========================================
# 🖥 GIAO DIỆN CHÍNH (UI TABS)
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
        ui_log = st.empty()
        bot = AutoSEOPipeline(db_mock, [])
        bot.add_log(ui_log, f"⚡ Đang quét bài PENDING của ngày {today_str}...", "info")
        try:
            ss = gspread.authorize(Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])).open_by_key(SHEET_ID)
            ws = ss.worksheet('REPORT')
            data = ws.get_all_values()
            
            if len(data) > 1:
                headers = [str(h).strip() for h in data[0]]
                idx_res = headers.index('REP_RESULT') if 'REP_RESULT' in headers else -1
                idx_pub = headers.index('REP_PUBLISH_DATE') if 'REP_PUBLISH_DATE' in headers else -1
                idx_html = headers.index('REP_HTML') if 'REP_HTML' in headers else -1
                idx_log = headers.index('REP_LOG') if 'REP_LOG' in headers else -1

                if idx_res != -1 and idx_pub != -1:
                    upd, count = [], 0
                    for i, row in enumerate(data[1:], 2):
                        if len(row) > max(idx_res, idx_pub):
                            if row[idx_res].strip() == 'PENDING' and str(row[idx_pub]).startswith(today_str):
                                upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_res+1)}', 'values': [['DONE']]})
                                if idx_html != -1: upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_html+1)}', 'values': [['']]})
                                if idx_log != -1: upd.append({'range': f'{gspread.utils.rowcol_to_a1(i, idx_log+1)}', 'values': [['']]})
                                count += 1
                    if upd:
                        ws.batch_update(upd)
                        st.success(f"✅ Đã ép trạng thái DONE và dọn rác thành công {count} bài của ngày hôm nay!")
                        time.sleep(1)
                        load_data_from_gsheets.clear()
                        st.rerun()
                    else: 
                        bot.add_log(ui_log, "ℹ️ Không tìm thấy bài PENDING nào thuộc ngày hôm nay (Hoặc dữ liệu cũ đang bị lệch cột, hãy xóa các bài lỗi).", "warn")
                else: 
                    bot.add_log(ui_log, "🛑 Không tìm thấy cột REP_RESULT hoặc REP_PUBLISH_DATE trong Sheet REPORT.", "error")
        except Exception as e:
            bot.add_log(ui_log, f"🛑 Lỗi khi ép lên bài: {str(e)[:150]}", "error")

    if btn_start:
        st.markdown("---")
        ui_log = st.empty()
        needed = batch - p_today
        
        if needed <= 0:
            ui_log.markdown('<div class="log-box"><span class="log-error">🛑 Đã đạt BATCH_SIZE hôm nay. Không chạy thêm.</span></div>', unsafe_allow_html=True)
        else:
            master_logs = []
            for i in range(needed):
                bot = AutoSEOPipeline(db_mock, master_logs)
                bot.add_log(ui_log, f"<br>🚀 --- BẮT ĐẦU CHẠY BÀI {i+1}/{needed} ---", "success")
                
                start_time = time.time()
                try:
                    if bot.step1_allocate_slot(ui_log):
                        if bot.step2_3_keyword_and_serp(ui_log):
                            if bot.step4_llm_generation(ui_log):
                                bot.step5_6_spin_and_dom(ui_log)
                                res = bot.step7_qa_validation(ui_log)
                                bot.step8_sync_db(ui_log, res)
                                db_mock = load_data_from_gsheets()
                except Exception as e:
                    bot.add_log(ui_log, f"🛑 Lỗi chí mạng: {str(e)[:150]}", "error")
                
                if time.time() - start_time > 300:
                    bot.add_log(ui_log, "🛑 [WATCHDOG] Quá 5 phút, tự ngắt để cứu hệ thống.", "error")
                    break
                    
            bot.add_log(ui_log, "<br>✅ TOÀN BỘ TIẾN TRÌNH ĐÃ HOÀN TẤT.", "success")
            st.success("🎉 QUÁ TRÌNH TẠO BÀI ĐÃ XONG!")
            if st.button("🔄 Bấm vào đây để Tải lại dữ liệu trang Web", type="primary"):
                load_data_from_gsheets.clear()
                st.rerun()

with tab2:
    if not df_rep.empty:
        df_show = df_rep[['REP_CREATED_AT', 'REP_PUBLISH_DATE', 'REP_TITLE', 'REP_WS_NAME', 'REP_RESULT']].tail(15)
        st.dataframe(df_show, use_container_width=True, hide_index=True)
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
                st.text_area("", str(row.get('REP_HTML', '')), height=500, label_visibility="collapsed")
    else: st.info("Chưa có dữ liệu bài viết.")

with tab3:
    st.dataframe(df_rep, use_container_width=True)
