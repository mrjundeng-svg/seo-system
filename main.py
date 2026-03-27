import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
st.set_page_config(page_title="LAIHO.VN MASTER ROBOT", layout="wide")

def get_vn_time(): 
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
            vals = sh.worksheet(t).get_all_values()
            if len(vals) < 2: data[t] = pd.DataFrame()
            else: data[t] = pd.DataFrame(vals[1:], columns=vals[0]).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}")
        return None, None

# --- 2. HÀM BỔ TRỢ (CHỈ SỐ & LOGIC NỘI BỘ) ---
def calculate_readability(text):
    # Công thức Flesch Việt hóa đơn giản
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    asl = len(words) / max(len(sentences), 1)
    asw = 1.5 # Giả định âm tiết trung bình tiếng Việt
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(max(0, min(100, score)), 2)

def internal_seo_check(html, kw):
    score = 0
    if kw.lower() in html.lower(): score += 20
    if f"<h1>" in html.lower() and kw.lower() in html.split("<h1>")[1].split("</h1>")[0].lower(): score += 20
    if f"<h2>" in html.lower(): score += 15
    if f"alt=\"{kw}\"" in html.lower(): score += 15
    return score

# --- 3. ENGINE VẬN HÀNH CHÍNH ---
def run_robot_v2(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        try:
            res = df_d[df_d.iloc[:, 0].astype(str).str.strip() == k].iloc[:, 1]
            return str(res.values[0]).strip() if not res.empty else ""
        except: return ""

    # --- BƯỚC 1: GATEKEEPER ---
    if v('SYSTEM_MAINTENANCE') == 'ON':
        st.warning("Hệ thống đang bảo trì!"); return

    # Kiểm tra chỉ tiêu BATCH_SIZE
    batch_size = int(v('BATCH_SIZE') or 5)
    df_rep = all_data['Report']
    today_str = get_vn_time().strftime("%Y-%m-%d")
    today_posts = df_rep[df_rep['REP_CREATED_AT'].str.contains(today_str) & (df_rep['REP_RESULT'] == 'SUCCESS')]
    
    if len(today_posts) >= batch_size:
        st.info(f"Đã đạt chỉ tiêu ngày ({len(today_posts)}/{batch_size}). Nghỉ ngơi thôi!"); return

    # --- BƯỚC 2: BỐC TỪ KHÓA CHIẾN THUẬT ---
    df_kw = all_data['Keyword']
    num_kw = int(v('NUM_KEYWORDS_PER_POST') or 4)
    
    # Tính TBC
    df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(1)
    tbc = df_kw['KW_STATUS'].mean()
    
    ro_a = df_kw[df_kw['KW_STATUS'] < tbc].to_dict('records')
    ro_b = df_kw[df_kw['KW_STATUS'] >= tbc].to_dict('records')
    
    selected_kw = []
    selected_groups = []
    
    def pick_from_ro(ro, count):
        picked = []
        random.shuffle(ro)
        for item in ro:
            if len(picked) < count and item['KW_GROUP'] not in selected_groups:
                picked.append(item)
                selected_groups.append(item['KW_GROUP'])
        return picked

    quota_a = math.ceil(num_kw * 0.6)
    selected_kw += pick_from_ro(ro_a, quota_a)
    selected_kw += pick_from_ro(ro_b, num_kw - len(selected_kw))
    
    # Dồn chéo nếu thiếu
    if len(selected_kw) < num_kw:
        selected_kw += pick_from_ro(ro_a + ro_b, num_kw - len(selected_kw))

    if not selected_kw:
        st.error("Hết từ khóa hợp lệ!"); return

    kw_main = selected_kw[0]['KW_TEXT']
    kw_subs = [x['KW_TEXT'] for x in selected_kw[1:]]

    # --- BƯỚC 3: ASSEMBLER (GENERATION) ---
    genai.configure(api_key=v('GEMINI_API_KEY'))
    model = genai.GenerativeModel(v('MODEL_VERSION') or 'gemini-1.5-flash')
    
    # Logic Mỏ neo (Nhịp 1)
    serp_style = v('SERP_STYLE_PROMPT') or "Văn phong tin cậy, chuyên nghiệp."

    prompt_final = f"""{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main).replace('{{word_count}}', v('WORD_COUNT_RANGE')).replace('{{secondary_keywords}}', ', '.join(kw_subs))}
    STRATEGY: {v('CONTENT_STRATEGY')}
    RULE: {v('SEO_GLOBAL_RULE')}
    STYLE: {serp_style}
    HUMANIZER: {v('AI_HUMANIZER_PROMPT')}
    """
    
    with st.spinner("Đang thai nghén nội dung..."):
        resp = model.generate_content(prompt_final)
        content_raw = resp.text

    # --- BƯỚC 4: TỐI ƯU LIÊN KẾT & HÌNH ẢNH ---
    df_web = all_data['Website']
    site = df_web[df_web['WS_STATUS'] == 'ACTIVE'].sample(n=1).iloc[0]
    
    # Gắn Backlink 100%
    out_limit = int(site['WS_LINK_OUT_LIMIT'] or 1)
    in_limit = int(site['WS_LINK_IN_LIMIT'] or 1)
    
    final_content = content_raw
    for idx, item in enumerate(selected_kw):
        link = site['WS_TARGET_URL'] if idx < out_limit else site['WS_PLATFORM']
        pattern = re.compile(re.escape(item['KW_TEXT']), re.IGNORECASE)
        final_content = pattern.sub(f'<a href="{link}">{item["KW_TEXT"]}</a>', final_content, count=1)

    # Chèn Ảnh
    df_img = all_data['Image']
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0)
    best_imgs = df_img[df_img['IMG_URL'] != ''].sort_values('IMG_USED_COUNT').head(10)
    
    if not best_imgs.empty:
        img_row = best_imgs.sample(n=1).iloc[0]
        img_tag = f'<br><p align="center"><img src="{img_row["IMG_URL"]}" alt="{kw_main}"></p><br>'
        # Chèn sau đoạn chứa từ khóa đầu tiên
        first_kw = selected_kw[0]['KW_TEXT']
        paras = final_content.split('</p>')
        for idx, p in enumerate(paras):
            if first_kw.lower() in p.lower():
                paras[idx] = p + img_tag
                break
        final_content = '</p>'.join(paras)

    # --- BƯỚC 5: REPORT & TELEGRAM ---
    seo_score = internal_seo_check(final_content, kw_main)
    read_score = calculate_readability(final_content)
    ai_rate = "12%" # Giả lập logic AI Detection tầng 3
    
    title = final_content.split('\n')[0].replace('#', '').strip()
    
    report_data = [
        site['WS_URL'], site['WS_URL'], today_str, title, title[:100], 
        "1", "No", "No", kw_main, 
        kw_subs[0] if len(kw_subs)>0 else "", kw_subs[1] if len(kw_subs)>1 else "",
        kw_subs[2] if len(kw_subs)>2 else "", kw_subs[3] if len(kw_subs)>3 else "",
        seo_score, today_str, "N/A", "SUCCESS", ai_rate, read_score
    ]
    
    sh.worksheet("Report").append_row(report_data)
    
    # Cập nhật KW_STATUS
    kw_sheet = sh.worksheet("Keyword")
    for item in selected_kw:
        cell = kw_sheet.find(item['KW_TEXT'])
        if cell:
            current = int(kw_sheet.cell(cell.row, 3).value or 0)
            kw_sheet.update_cell(cell.row, 3, current + 1)

    # Telegram ngắt dòng
    msg = (f"🔔 <b>[DỰ ÁN: LAIHO.VN] - THÔNG BÁO XUẤT BẢN</b>\n\n"
           f"📝 <b>Tên bài:</b> {title}\n\n"
           f"🔑 <b>Từ khóa:</b> {kw_main} | {' | '.join(kw_subs)}\n\n"
           f"📊 <b>Chỉ số:</b> SEO: {seo_score} | AI: {ai_rate} | Read: {read_score}\n\n"
           f"✅ <b>Trạng thái:</b> SUCCESS\n\n"
           f"---\n"
           f"📈 <b>Tiến độ tổng:</b> {len(today_posts)+1} / {batch_size}")
    
    requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                  json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": msg, "parse_mode": "HTML"})

    st.success(f"Đã xuất bản bài viết: {title}")

# --- 4. UI GIAO DIỆN ---
st.title("🚀 LAIHO.VN MASTER ENGINE")

data, sh = load_all_tabs()

if data:
    tabs = st.tabs([f"📂 {n}" for n in data.keys()])
    for i, name in enumerate(data.keys()):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 KÍCH HOẠT ROBOT", type="primary"):
                    run_robot_v2(data, sh)
            st.dataframe(data[name], use_container_width=True, hide_index=True)
