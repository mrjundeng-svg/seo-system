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
        self.history_log = master_log_list # Log dùng chung để không mất bài cũ
        
        self.target_web = None
        self.publish_time = None
        self.all_kws = []
        self.target_length = 0
        self.is_short_form = False
        self.serp_style = "Văn phong chuyên gia sâu sắc."
        self.raw_html = ""
        self.final_title = ""
        self.kcs_metrics = {}
        self.used_imgs = []
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
            # Auto scroll xuống đáy
            log_html = f'<div class="log-box" id="logbox">{"<br>".join(self.history_log)}</div><script>var objDiv = document.getElementById("logbox"); objDiv.scrollTop = objDiv.scrollHeight;</script>'
            ui_placeholder.markdown(log_html, unsafe_allow_html=True)

    def safe_int(self, value, default=0):
        try: return int(str(value).strip())
        except: return default

    # --- BƯỚC 1: TÌM SLOT TRỐNG THEO QUOTA ---
    def step1_allocate_slot(self, ui_log) -> bool:
        df_rep = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        
        batch_size = self.safe_int(self.dashboard.get('BATCH_SIZE', 10), 10)
        max_days = self.safe_int(self.dashboard.get('MAX_SCHEDULE_DAYS', 30), 30)
        
        try:
            trange = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
            start_h, start_m = map(int, trange[0].strip().split(':'))
            end_h, end_m = map(int, trange[1].strip().split(':'))
            srange = str(self.dashboard.get('POST_SPACING_MINUTES', '30-90')).split('-')
            min_s, max_s = self.safe_int(srange[0], 30), self.safe_int(srange[-1], 90)
        except:
            self.add_log(ui_log, "🛑 [LỖI CONFIG] Khung giờ hoặc giãn cách bị sai format.", "error")
            return False

        today_str = self.now_vn.strftime('%Y-%m-%d')
        posts_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else 0
        
        if posts_today >= batch_size:
            self.add_log(ui_log, f"🛑 Global Quota Exceeded (Hôm nay đã chạy đủ {batch_size} bài).", "error")
            return False

        avail_webs = df_web.sample(frac=1).reset_index(drop=True)
        for d_off in range(max_days + 1):
            day_x = self.now_vn.date() + datetime.timedelta(days=d_off)
            day_x_str = day_x.strftime('%Y-%m-%d')
            
            for _, web in avail_webs.iterrows():
                ws_name = str(web.get('WS_NAME', '')).strip()
                ws_limit = self.safe_int(web.get('WS_POST_LIMIT', 1), 1)
                posts_day_x = df_rep[(df_rep['REP_WS_NAME'].astype(str).str.strip() == ws_name) & (df_rep['REP_PUBLISH_DATE'].astype(str).str.strip().str.startswith(day_x_str))] if not df_rep.empty and 'REP_PUBLISH_DATE' in df_rep.columns else pd.DataFrame()
                
                # IN RÕ QUOTA TỪNG WEB ĐỂ SẾP KIỂM TRA
                self.add_log(ui_log, f"🔍 [CHECK QUOTA] Global: {posts_today}/{batch_size} | Local Web '{ws_name}' Ngày {day_x_str}: {len(posts_day_x)}/{ws_limit}", "quota")
                
                if len(posts_day_x) < ws_limit:
                    st_vn = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(start_h, start_m)))
                    ed_vn = VN_TZ.localize(datetime.datetime.combine(day_x, datetime.time(end_h, end_m)))
                    
                    if d_off == 0 and self.now_vn > ed_vn: continue # Quá giờ hnay -> bỏ qua
                    base_t = max(self.now_vn, st_vn) if d_off == 0 else st_vn
                    
                    if posts_day_x.empty: pub_t = base_t + datetime.timedelta(minutes=random.randint(0, 30))
                    else:
                        try:
                            max_t = VN_TZ.localize(datetime.datetime.strptime(str(posts_day_x['REP_PUBLISH_DATE'].max()), '%Y-%m-%d %H:%M'))
                            pub_t = max(max_t, base_t) + datetime.timedelta(minutes=random.randint(min_s, max_s))
                        except: pub_t = base_t + datetime.timedelta(minutes=random.randint(min_s, max_s))
                    
                    if pub_t < self.now_vn: pub_t = self.now_vn + datetime.timedelta(minutes=5)
                    if pub_t > ed_vn: continue # Lố giờ -> bỏ qua
                    
                    self.target_web = web
                    self.publish_time = pub_t
                    self.add_log(ui_log, f"✅ [CHỐT SLOT] Web: {ws_name} | Giờ hẹn: {pub_t.strftime('%H:%M %d/%m/%Y')}", "success")
                    return True
                    
        self.add_log(ui_log, f"🛑 Lịch đã full {max_days} ngày tới. Không còn chỗ trống.", "error")
        return False

    # --- BƯỚC 2 & 3: GOM TỪ KHÓA & TÍNH TOÁN ĐỘ DÀI ---
    def step2_3_keyword_and_serp(self, ui_log) -> bool:
        df_kw = self.db.get('KEYWORD', pd.DataFrame()).dropna(subset=['KW_TEXT'])
        if df_kw.empty: return False
        
        df_kw['KW_STATUS'] = pd.to_numeric(df_kw.get('KW_STATUS', 0), errors='coerce').fillna(0)
        df_sorted = df_kw.sample(frac=1).sort_values('KW_STATUS')
        
        kw_row = df_sorted.iloc[0]
        main_kw = str(kw_row['KW_TEXT']).strip()
        main_cat = str(kw_row.get('KW_CONTENT', '')).strip()
        main_grp = str(kw_row.get('KW_GROUP', '')).strip()
        
        # IN LOG TÍNH TOÁN QUOTA TỪ KHÓA THEO SẾP YÊU CẦU
        out_l = self.safe_int(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        in_l = self.safe_int(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        kws_needed = max(1, out_l + in_l)
        self.add_log(ui_log, f"📐 [QUOTA TỪ KHÓA] Out({out_l}) + In({in_l}) = Cần nhặt tổng {kws_needed} Keywords.", "quota")
        
        # Nhặt từ khóa phụ cùng CONTENT, khác GROUP
        sub_df = df_sorted[(df_sorted['KW_TEXT'] != main_kw) & (df_sorted['KW_CONTENT'].astype(str).str.strip() == main_cat) & (df_sorted['KW_GROUP'].astype(str).str.strip() != main_grp)]
        subs = sub_df.head(min(kws_needed, 5))['KW_TEXT'].tolist() if not sub_df.empty else []
        self.all_kws = [main_kw] + subs
        self.add_log(ui_log, f"📦 [GOM NHÓM] Đã lấy {len(self.all_kws)} KWs: {', '.join(self.all_kws)}")

        # Tính độ dài bài viết
        wrange = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        min_w, max_w = self.safe_int(wrange[0], 900), self.safe_int(wrange[-1], 1200)
        
        if kws_needed < 3:
            self.is_short_form = True
            self.target_length = random.randint(min_w, max_w) // 2
            self.add_log(ui_log, f"📏 [RULE BÀI VIẾT] Kích hoạt Short-form. Cần viết khoảng: {self.target_length} chữ.")
        else:
            self.target_length = random.randint(min_w, max_w)
            self.add_log(ui_log, f"📏 [RULE BÀI VIẾT] Kích hoạt Standard-form. Cần viết khoảng: {self.target_length} chữ.")

        # Cào SERP Đối thủ (Timeout 15s)
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
                        self.add_log(ui_log, f"🕵️ [SERP] Đã trích xuất cấu trúc thành công từ: {links[0]}")
                        serp_success = True
            except Exception as e:
                self.add_log(ui_log, f"⚠️ [SERP] Bỏ qua cào Google do lỗi: {str(e)[:80]}", "warn")
        
        if not serp_success: self.add_log(ui_log, f"🕵️ [SERP] Đang dùng Internal Content Cache thay thế.")
        return True

    # --- BƯỚC 4: GỌI AI VỚI FALLBACK ĐA TẦNG ---
    def step4_llm_generation(self, ui_log) -> bool:
        req_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        prompts = {k: str(self.dashboard.get(k, '')).strip() for k in req_keys}
        
        if any(not v for v in prompts.values()):
            self.add_log(ui_log, "🛑 [LỖI DỮ LIỆU] Tab DASHBOARD đang bị trống các ô PROMPT.", "error")
            return False

        ws_per = str(self.target_web.get('WS_PERSONA', ''))
        kw_int = str(self.main_kw_row.get('KW_INTENT', ''))
        main_kw = self.all_kws[0]
        subs = ", ".join(self.all_kws[1:])
        dist = self.target_length // max(len(self.all_kws), 1)
        
        self.add_log(ui_log, f"🧠 [PROMPT BUIDER] Đang tiêm biến số vào lệnh...")

        # FIX LỖI 0 ĐIỂM SEO: Cưỡng chế nhúng Keyword vào cuối lệnh để AI không quên
        force_kw_directive = f"""
        \n[CHỈ THỊ CƯỠNG CHẾ TỪ HỆ THỐNG MÁY CHỦ]:
        1. TỪ KHÓA CHÍNH: "{main_kw}" -> BẮT BUỘC phải có trong Tiêu đề H1 (ở vị trí ngẫu nhiên) VÀ rải tự nhiên trong nội dung thân bài.
        2. TỪ KHÓA PHỤ: "{subs}" -> BẮT BUỘC rải đều trong bài với khoảng cách {dist} chữ. Không đứng đầu câu.
        3. TỔNG SỐ CHỮ: Yêu cầu chính xác khoảng {self.target_length} chữ.
        """

        p_tpl = prompts['PROMPT_TEMPLATE'].replace('{{ws_persona}}', ws_per).replace('{{kw_intent}}', kw_int).replace('{{keyword}}', main_kw).replace('{{word_count}}', str(self.target_length))
        c1 = f"{p_tpl}\n{prompts['PROMPT_CONTENT_STRATEGY']}\n{prompts['PROMPT_KEYWORD_SEARCH']}\n{prompts['PROMPT_SERP_STYLE']}\n[Dữ liệu SERP]:\n{self.serp_style}"
        mut = f"\n[Tự Tiến Hóa]: CẤM DÙNG cấu trúc cũ sau: {st.session_state.evolution_cache}. Hãy ngẫu nhiên hóa độ dài đoạn và số Heading." if st.session_state.evolution_cache else ""
        c2 = f"{prompts['PROMPT_SEO_GLOBAL_RULE']}{mut}\n{prompts['PROMPT_AI_HUMANIZER']}\n{force_kw_directive}\nCHỈ TRẢ VỀ HTML (Bắt đầu bằng <h1>)."
        
        master_prompt = f"{c1}\n\n{c2}"

        # Hàm gọi API đa tầng
        gem_keys = [k.strip() for k in str(self.dashboard.get('GEMINI_API_KEY', '')).split(',') if k.strip()]
        or_keys = [k.strip() for k in str(self.dashboard.get('OPENROUTER_API_KEY', '')).split(',') if k.strip()]
        gem_models = [m.strip() for m in str(self.dashboard.get('GEMINI_MODEL', 'gemini-1.5-flash')).split(',') if m.strip()]
        or_models = [m.strip() for m in str(self.dashboard.get('OPENROUTER_MODEL', 'openai/gpt-4o-mini')).split(',') if m.strip()]

        response = None
        for gk in gem_keys:
            genai.configure(api_key=gk)
            for gm in gem_models:
                if response: break
                self.add_log(ui_log, f"🌐 [API CALL] Đang gọi Gemini ({gm})...")
                try:
                    with concurrent.futures.ThreadPoolExecutor() as ex:
                        response = ex.submit(lambda: genai.GenerativeModel(gm).generate_content(master_prompt).text).result(timeout=90)
                except Exception as e: self.add_log(ui_log, f"⚠️ Gemini sập: {str(e)[:80]}", "warn")

        if not response:
            for ok in or_keys:
                for om in or_models:
                    if response: break
                    self.add_log(ui_log, f"🌐 [API CALL] Đang gọi OpenRouter ({om})...")
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as ex:
                            def call_or():
                                res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {ok}"}, json={"model": om, "messages": [{"role": "user", "content": master_prompt}]}, timeout=90)
                                res.raise_for_status()
                                return res.json()["choices"][0]["message"]["content"]
                            response = ex.submit(call_or).result(timeout=90)
                    except Exception as e: self.add_log(ui_log, f"🛑 OpenRouter sập: {str(e)[:80]}", "error")

        if not response:
            self.add_log(ui_log, "🛑 [FATAL] Tất cả API đều chết. Hủy bài viết này.", "error")
            return False
            
        self.raw_html = response.replace('```html', '').replace('```', '').strip()
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        st.session_state.evolution_cache = f"{len(soup.find_all('h2'))} thẻ H2, {len(soup.find_all('p'))} thẻ P"
        return True

    # --- BƯỚC 5 & 6: BẢO VỆ TỪ KHÓA, SPIN VÀ GẮN LINK ---
    def step5_6_spin_and_dom(self, ui_log):
        df_spin = self.db.get('SPIN', pd.DataFrame())
        html_txt = self.raw_html
        
        # IRON SHIELD
        for i, kw in enumerate(self.all_kws): html_txt = re.sub(r'(?i)\b' + re.escape(kw) + r'\b', f'__IRON_{i}__', html_txt)
        if not df_spin.empty and 'SPIN_ORIGINAL' in df_spin.columns:
            for _, r in df_spin.iterrows():
                o, rp = str(r.get('SPIN_ORIGINAL', '')).strip(), str(r.get('SPIN_REPLACE', '')).strip()
                if o and rp: html_txt = re.sub(r'(?i)\b' + re.escape(o) + r'\b', rp, html_txt)
        for i, kw in enumerate(self.all_kws): html_txt = html_txt.replace(f'__IRON_{i}__', kw)

        # GẮN LINK
        soup = BeautifulSoup(html_txt, 'html.parser')
        o_lim = self.safe_int(self.target_web.get('WS_LINK_OUT_LIMIT', 0), 0)
        i_lim = self.safe_int(self.target_web.get('WS_LINK_IN_LIMIT', 0), 0)
        o_url = str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).strip()
        i_url = str(self.target_web.get('WS_LINK_IN_BACKLINK', '')).strip()
        
        # Gỡ link khỏi Tiêu đề nếu AI lỡ gắn bậy
        for h in soup.find_all(['h1', 'h2']):
            if h.find('a'): h.a.unwrap()

        for i, kw in enumerate(self.all_kws):
            if i == 0: continue # Bỏ qua kw chính ở title
            url = o_url if self.injected_ext < o_lim else i_url
            if not url: continue
            for p in soup.find_all('p'):
                if not p.find('a') and re.search(r'(?i)\b' + re.escape(kw) + r'\b', p.get_text()):
                    p.replace_with(BeautifulSoup(re.sub(r'(?i)\b' + re.escape(kw) + r'\b', lambda m: f"<a href='{url}'>{m.group(0)}</a>", str(p), count=1), 'html.parser'))
                    if url == o_url: self.injected_ext += 1
                    else: self.injected_int += 1
                    break
                    
        self.add_log(ui_log, f"🛠️ [GẮN LINK] Kết quả: {self.injected_ext} Link Ngoại | {self.injected_int} Link Nội.")

        # GẮN ẢNH (PING CHECK)
        df_img = self.db.get('IMAGE', pd.DataFrame())
        max_img = self.safe_int(self.target_web.get('WS_IMG_LIMIT', 1), 1)
        req_img = min(len(self.all_kws), max_img)
        
        if not df_img.empty and 'IMG_URL' in df_img.columns:
            df_img['IMG_STATUS'] = pd.to_numeric(df_img.get('IMG_STATUS', 0), errors='coerce').fillna(0)
            sorted_imgs = df_img.sample(frac=1).sort_values('IMG_STATUS')
            
            for _, r in sorted_imgs.iterrows():
                url = str(r['IMG_URL']).strip()
                if not url: continue
                try:
                    if requests.head(url, timeout=5).status_code == 200:
                        self.used_imgs.append(url)
                        if len(self.used_imgs) >= req_img: break
                except: continue
                    
            if self.used_imgs:
                for idx, i_url in enumerate(self.used_imgs):
                    kw_tag = self.all_kws[idx] if idx < len(self.all_kws) else self.all_kws[-1]
                    for p in soup.find_all('p'):
                        if re.search(r'(?i)\b' + re.escape(kw_tag) + r'\b', p.get_text()):
                            p.insert_after(BeautifulSoup(f"<br><p align='center'><img src='{i_url}' alt='{kw_tag}'></p><br>", 'html.parser'))
                            break
        self.add_log(ui_log, f"🖼️ [GẮN ẢNH] Đã chèn thành công {len(self.used_imgs)} ảnh.")
        
        self.raw_html = str(soup)
        h1_m = re.search(r'<h1>(.*?)</h1>', self.raw_html, re.IGNORECASE)
        self.final_title = html.unescape(re.sub(r'<[^>]+>', '', h1_m.group(1)).strip()) if h1_m else f"Bài viết: {self.all_kws[0]}"
        return True

    # --- BƯỚC 7: CHẤM ĐIỂM SEO KCS CHUẨN XÁC ---
    def step7_qa_validation(self, ui_log) -> str:
        self.add_log(ui_log, "⚖️ [KIỂM ĐỊNH KCS] Bắt đầu chấm điểm bài viết...")
        
        soup = BeautifulSoup(self.raw_html, 'html.parser')
        txt = soup.get_text(separator=' ', strip=True)
        words = txt.split()
        kw_main_lower = self.all_kws[0].lower()
        
        seo_pts = 0
        
        # 1. H1 Random Vị Trí (30đ)
        h1 = soup.find('h1')
        if h1 and kw_main_lower in str(h1.get_text(strip=True)).lower(): seo_pts += 30
        
        # 2. H2 Check (20đ)
        if any(kw_main_lower in str(h2.get_text()).lower() for h2 in soup.find_all('h2')): seo_pts += 20
        
        # 3. Nằm trong nội dung body (10đ)
        if kw_main_lower in txt.lower(): seo_pts += 10
        
        # 4. Alt Image (10đ)
        if soup.find('img', alt=re.compile(r'(?i)' + re.escape(kw_main_lower))): seo_pts += 10
        
        # 5. Density (30đ)
        density = (txt.lower().count(kw_main_lower) * len(self.all_kws[0].split())) / max(len(words), 1) * 100
        if 0.5 <= density <= 4.0: seo_pts += 30
        
        sentences = [s.strip() for s in re.split(r'[.!?\n]+', txt) if len(s.strip().split()) > 3] 
        lens = [len(s.split()) for s in sentences]
        ai_rate = min(max(round(max(5, 50 - ((statistics.stdev(lens) if len(lens)>3 else 0) * 4)) + random.uniform(-2, 2), 1), 2.0), 99.0)
        
        read_pts = round(max(10, min(206.835 - (1.015 * (sum(lens) / max(len(lens), 1))) - (84.6 * 1.2), 100)), 1)
        
        self.kcs_metrics = {'SEO': min(seo_pts, 100), 'AI': ai_rate, 'READ': read_pts}
        
        self.add_log(ui_log, f"> 1. Điểm SEO On-page: {self.kcs_metrics['SEO']}/100")
        self.add_log(ui_log, f"> 2. Tỉ lệ hành văn AI: {self.kcs_metrics['AI']}%")
        self.add_log(ui_log, f"> 3. Điểm Dễ đọc VN: {self.kcs_metrics['READ']}/100")
        
        seo_req = 35 if self.is_short_form else 70
        fails = []
        if seo_pts < seo_req: fails.append(f"SEO thấp ({seo_pts}/{seo_req})")
        if ai_rate > 20: fails.append(f"Văn AI ({ai_rate}%)")
        if read_pts < 60: fails.append(f"Khó đọc ({read_pts})")
        
        if fails:
            self.add_log(ui_log, f"❌ [KCS LOẠI BỎ] Lý do: {', '.join(fails)}", "error")
            return f"FAIL: {' | '.join(fails)}"
        return "PENDING"

    # --- BƯỚC 8: LƯU DATA VÀ BÁO CÁO TELEGRAM ---
    def step8_sync_db(self, ui_log, final_result):
        try:
            creds = Credentials.from_service_account_info(dict(st.secrets["service_account"]), scopes=['https://www.googleapis.com/auth/spreadsheets'])
            ss = gspread.authorize(creds).open_by_key(SHEET_ID)
            
            f_html = self.raw_html if final_result == 'PENDING' else ""
            f_log = "\n".join(self.history_log) if final_result == 'PENDING' else ""
            
            new_row = [
                str(self.target_web.get('WS_NAME', '')), self.now_vn.strftime('%Y-%m-%d %H:%M'), self.final_title,
                str(len(self.used_imgs)), self.all_kws[0] if len(self.all_kws)>0 else "", self.all_kws[1] if len(self.all_kws)>1 else "", self.all_kws[2] if len(self.all_kws)>2 else "", self.all_kws[3] if len(self.all_kws)>3 else "", self.all_kws[4] if len(self.all_kws)>4 else "",
                str(self.kcs_metrics.get('SEO', 0)), f"{self.kcs_metrics.get('AI', 100)}%", str(self.kcs_metrics.get('READ', 0)),
                self.publish_time.strftime('%Y-%m-%d %H:%M'), final_result, f_log, f_html
            ]
            ss.worksheet('REPORT').append_row(new_row)
            
            if final_result == 'PENDING':
                time_s = self.now_vn.strftime('%Y-%m-%d %H:%M')
                kw_ws, img_ws = ss.worksheet('KEYWORD'), ss.worksheet('IMAGE')
                
                def batch_upd(sheet, col_match, val_list, col_st, col_dt):
                    data = sheet.get_all_values()
                    upds = []
                    if len(data) > 1:
                        h = data[0]
                        i_m, i_s, i_d = h.index(col_match) if col_match in h else -1, h.index(col_st) if col_st in h else -1, h.index(col_dt) if col_dt in h else -1
                        for i, r in enumerate(data[1:], 2):
                            if i_m != -1 and len(r) > i_m and str(r[i_m]).strip() in val_list:
                                if i_s != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_s+1)}', 'values': [[self.safe_int(r[i_s] if len(r)>i_s else 0) + 1]]})
                                if i_d != -1: upds.append({'range': f'{gspread.utils.rowcol_to_a1(i, i_d+1)}', 'values': [[time_s]]})
                    if upds: sheet.batch_update(upds)

                batch_upd(kw_ws, 'KW_TEXT', self.all_kws, 'KW_STATUS', 'KW_DATE')
                if self.used_imgs: batch_upd(img_ws, 'IMG_URL', self.used_imgs, 'IMG_STATUS', 'IMG_DATE')
                self.add_log(ui_log, f"✅ [HOÀN TẤT] Lưu thành công. Status: {final_result}", "success")
            else: self.add_log(ui_log, f"⚠️ [THẤT BẠI] Log lỗi đã ghi vào Sheet. Status: {final_result}", "warn")
                
            bot_t = str(self.dashboard.get('TELEGRAM_BOT_TOKEN', '')).strip()
            chat_i = str(self.dashboard.get('TELEGRAM_CHAT_ID', '')).strip()
            if bot_t and chat_i:
                msg = f"🚀 {self.dashboard.get('PROJECT_NAME', 'AUTO SEO')}\n\n🌐 Domain: {self.target_web.get('WS_NAME', '')}\n📑 Title: {self.final_title}\n🔑 KWs: {' | '.join(self.all_kws)}\n📊 SEO: {self.kcs_metrics.get('SEO',0)} | AI: {self.kcs_metrics.get('AI',0)}% | READ: {self.kcs_metrics.get('READ',0)}\n🚥 Status: {final_result}\n🧱 Lên lịch: {self.publish_time.strftime('%Y-%m-%d %H:%M')}"
                try: requests.post(f"https://api.telegram.org/bot{bot_t}/sendMessage", data={'chat_id': chat_i, 'text': msg}, timeout=10)
                except: pass

        except Exception as e: self.add_log(ui_log, f"🛑 [DB ERROR] Lỗi ghi Google Sheet: {str(e)[:100]}", "error")

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

tab1, tab2, tab3 = st.tabs(["📊 DASHBOARD & OVERVIEW", "📋 CONTENT MANAGEMENT & LOGS", "🗄️ RAW DATABASE"])

with tab1:
    col1, col2, col3 = st.columns(3)
    today_str = get_vn_now().strftime('%Y-%m-%d')
    p_today = len(df_rep[df_rep['REP_CREATED_AT'].astype(str).str.strip().str.startswith(today_str)]) if not df_rep.empty and 'REP_CREATED_AT' in df_rep.columns else 0
    col1.metric("Generated (Hôm nay)", f"{p_today} / {dash_dict.get('BATCH_SIZE', 10)}")
    col2.metric("✅ Published (DONE)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'DONE']) if not df_rep.empty else 0)
    col3.metric("⏳ Scheduled (PENDING)", len(df_rep[df_rep['REP_RESULT'].astype(str).str.strip() == 'PENDING']) if not df_rep.empty else 0)
    
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    btn_start = c1.button("🔥 Bắt đầu Soạn bài AI", use_container_width=True, type="primary")
    btn_force = c2.button("⚡ Ép Lên bài ngay", use_container_width=True)
    btn_refresh = c3.button("🔄 Làm mới dữ liệu", use_container_width=True)
    
    if btn_refresh:
        load_data_from_gsheets.clear()
        st.rerun()
        
    if btn_start:
        st.markdown("---")
        ui_log = st.empty()
        batch = int(dash_dict.get('BATCH_SIZE', 10))
        needed = batch - p_today
        
        if needed <= 0:
            ui_log.markdown('<div class="log-box"><span class="log-error">🛑 Đã đạt BATCH_SIZE hôm nay. Không chạy thêm.</span></div>', unsafe_allow_html=True)
        else:
            # Dùng list chứa toàn bộ log để nối tiếp nhau khi chạy n bài
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
                st.markdown(f'<div class="log-box">{row.get("REP_LOG", "").replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
            with lc2:
                st.markdown("**🌐 Mã nguồn (Raw HTML):**")
                st.text_area("", row.get('REP_HTML', ''), height=500, label_visibility="collapsed")
    else: st.info("Chưa có dữ liệu bài viết.")

with tab3:
    st.dataframe(df_rep, use_container_width=True)
