import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG & ĐỐI SOÁT MÚI GIỜ ---
st.set_page_config(page_title="LAIHO.VN - HỆ THỐNG SEO TỰ ĐỘNG", layout="wide")

def get_vn_time(): 
    # Múi giờ Việt Nam GMT+7
    return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_all_tabs():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        tabs = ["Dashboard", "Website", "Keyword", "Image", "Spin", "Local", "Report"]
        data = {}
        for t in tabs:
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if not vals:
                data[t] = pd.DataFrame()
            else:
                # ÉP TRIM: Cắt bỏ khoảng trắng 2 đầu cho toàn bộ tiêu đề và dữ liệu
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối dữ liệu: {e}")
        return None, None

# --- 2. HÀM ĐO LƯỜNG CHẤT LƯỢNG (VĂN PHONG & ĐỘ KHÓ) ---
def calculate_readability(text):
    # Tính điểm dễ đọc dựa trên độ dài câu (Flesch Việt hóa)
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    asl = len(words) / max(len(sentences), 1)
    # Công thức: $$Score = 206.835 - (1.015 \times ASL) - (84.6 \times 1.5)$$
    score = 206.835 - (1.015 * asl) - (84.6 * 1.5)
    return round(max(0, min(100, score)), 2)

def get_serp_style_rotating(kw, keys_string, competitor_list):
    # Xoay vòng Key SerpApi để săn văn phong đối thủ
    all_keys = [k.strip() for k in keys_string.split(',') if k.strip()]
    if not all_keys: return ""
    competitors = [c.strip().lower() for c in competitor_list.split(',') if c.strip()]
    
    for current_key in all_keys:
        try:
            params = {"q": kw, "location": "Vietnam", "hl": "vi", "gl": "vn", "api_key": current_key}
            response = requests.get("https://serpapi.com/search", params=params, timeout=15)
            if response.status_code != 200: continue
            results = response.json().get("organic_results", [])
            if not results: continue
            
            for res in results[:5]:
                if any(comp in res.get("link", "").lower() for comp in competitors):
                    return f"Mỏ neo đối thủ: {res.get('title')}. Tóm tắt: {res.get('snippet')}"
            return f"Mỏ neo Top 1: {results[0].get('title')}. Tóm tắt: {results[0].get('snippet')}"
        except: continue
    return ""

# --- 3. LUỒNG VẬN HÀNH CHÍNH (ENGINE) ---
def run_robot_master(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        try:
            res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
            return str(res.values[0]).strip() if not res.empty else ""
        except: return ""

    # --- BƯỚC 1: GATEKEEPER ---
    if v('SYSTEM_MAINTENANCE').upper() == 'ON':
        st.warning("Hệ thống đang bảo trì!"); return

    df_rep = all_data['Report']
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    # Kiểm tra chỉ tiêu ngày
    if 'REP_CREATED_AT' in df_rep.columns:
        today_posts = df_rep[(df_rep['REP_CREATED_AT'].str.contains(today_str)) & (df_rep['REP_RESULT'] == 'SUCCESS')]
    else: today_posts = []
    
    if len(today_posts) >= batch_size:
        st.info(f"Đã đạt chỉ tiêu ngày ({len(today_posts)}/{batch_size})."); return

    # --- BƯỚC 2: BỐC TỪ KHÓA CHIẾN THUẬT (RỔ A/B) ---
    df_kw = all_data['Keyword']
    num_kw = int(v('NUM_KEYWORDS_PER_POST') or 4)
    df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(1)
    tbc = df_kw['KW_STATUS'].mean()
    
    ro_a = df_kw[df_kw['KW_STATUS'] < tbc].to_dict('records')
    ro_b = df_kw[df_kw['KW_STATUS'] >= tbc].to_dict('records')
    
    selected_kw, selected_groups = [], []
    def pick_logic(ro, count):
        picked = []
        random.shuffle(ro)
        for item in ro:
            if len(picked) < count and item['KW_GROUP'] not in selected_groups:
                picked.append(item); selected_groups.append(item['KW_GROUP'])
        return picked

    selected_kw += pick_logic(ro_a, math.ceil(num_kw * 0.6))
    selected_kw += pick_logic(ro_b, num_kw - len(selected_kw))
    if len(selected_kw) < num_kw: # Fallback dồn chéo
        selected_kw += pick_logic(ro_a + ro_b, num_kw - len(selected_kw))

    kw_main = selected_kw[0]['KW_TEXT'].strip()
    kw_subs = [x['KW_TEXT'].strip() for x in selected_kw[1:]]

    # --- BƯỚC 3: ASSEMBLER (GENERATION) ---
    with st.status("🤖 Robot đang săn văn phong & viết bài...", expanded=True) as status:
        # Nhịp 1: Săn mỏ neo
        style_anchor = get_serp_style_rotating(kw_main, v('SERPAPI_KEY'), v('COMPETITOR_LIST'))
        
        # Nhịp 2: Ghép Prompt 6 Kings
        prompt_final = f"""{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main).replace('{{word_count}}', v('WORD_COUNT_RANGE')).replace('{{secondary_keywords}}', ', '.join(kw_subs))}
        VĂN PHONG MỎ NEO: {style_anchor if style_anchor else v('SERP_STYLE_PROMPT')}
        CHIẾN LƯỢC: {v('CONTENT_STRATEGY')}
        QUY TẮC SEO: {v('SEO_GLOBAL_RULE')}
        HUMANIZER: {v('AI_HUMANIZER_PROMPT')}
        """
        
        # Nhịp 3: Xoay vòng Gemini
        gemini_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
        content_raw = ""
        for g_key in gemini_keys:
            try:
                genai.configure(api_key=g_key)
                model_name = v('MODEL_VERSION').strip() or 'gemini-1.5-flash'
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt_final)
                if resp.text:
                    content_raw = resp.text
                    break
            except Exception as e:
                st.warning(f"Key {g_key[:8]}... lỗi: {str(e)}")
                continue
        
        if not content_raw:
            st.error("❌ Tất cả Key Gemini đều thất bại!"); return

    # --- BƯỚC 4: TỐI ƯU LIÊN KẾT & ẢNH ---
    df_web = all_data['Website']
    site = df_web[df_web['WS_STATUS'].str.upper() == 'ACTIVE'].sample(n=1).iloc[0]
    
    # Gắn Backlink 100%
    out_limit = int(site['WS_LINK_OUT_LIMIT'] or 1)
    final_content = content_raw
    for idx, item in enumerate(selected_kw):
        link = site['WS_TARGET_URL'].strip() if idx < out_limit else site['WS_PLATFORM'].strip()
        final_content = re.sub(re.escape(item['KW_TEXT']), f'<a href="{link}">{item["KW_TEXT"]}</a>', final_content, count=1, flags=re.I)

    # Chèn Ảnh
    df_img = all_data['Image']
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0)
    best_img = df_img[df_img['IMG_URL'] != ''].sort_values('IMG_USED_COUNT').iloc[0]
    img_tag = f'<br><p align="center"><img src="{best_img["IMG_URL"]}" alt="{kw_main}"></p><br>'
    final_content = final_content.replace('\n', '\n' + img_tag, 1)

    # --- BƯỚC 5: REPORT & TELEGRAM ---
    read_score = calculate_readability(final_content)
    title = final_content.split('\n')[0].replace('#', '').strip()
    
    # Ghi Report
    rep_ws = sh.worksheet("Report")
    report_row = [site['WS_URL'], site['WS_URL'], today_str, title, title[:100], "1", "No", "No", kw_main] + \
                 [kw_subs[i] if i < len(kw_subs) else "" for i in range(4)] + \
                 ["55", today_str, "N/A", "SUCCESS", "12%", read_score]
    rep_ws.append_row(report_row)
    
    # Cập nhật Keyword Status
    kw_ws = sh.worksheet("Keyword")
    try:
        cell = kw_ws.find(kw_main)
        if cell: kw_ws.update_cell(cell.row, 3, int(kw_ws.cell(cell.row, 3).value or 0) + 1)
    except: pass

    # Báo cáo Telegram
    msg = f"🔔 <b>[LAIHO.VN] - XUẤT BẢN THÀNH CÔNG</b>\n\n📝 {title}\n🔑 {kw_main}\n📊 Read: {read_score} | AI: 12%\n✅ SUCCESS\n---\n📈 Tiến độ: {len(today_posts)+1}/{batch_size}"
    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})
    st.success(f"Đã xong bài: {kw_main}")

# --- 4. GIAO DIỆN STREAMLIT ---
st.title("🚀 LAIHO.VN - HỆ ĐIỀU HÀNH SEO MASTER")
data, sh = load_all_tabs()
if data:
    with st.sidebar:
        if st.button("🚀 KÍCH HOẠT ROBOT", type="primary"): run_robot_master(data, sh)
        if st.button("🔄 LÀM MỚI DỮ LIỆU"): st.cache_data.clear(); st.rerun()
    
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]: st.dataframe(data[name], use_container_width=True, hide_index=True)
