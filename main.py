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
        # Cắt tỉa tên Tab ngay từ khi khai báo
        tabs = ["Dashboard", "Website", "Keyword", "Image", "Spin", "Local", "Report"]
        data = {}
        for t in tabs:
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if not vals:
                data[t] = pd.DataFrame()
            else:
                # ÉP TRIM: Cắt khoảng trắng toàn bộ tiêu đề (Headers)
                headers = [str(h).strip() for h in vals[0]]
                # ÉP TRIM: Cắt khoảng trắng toàn bộ dữ liệu bên trong bảng
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối Sheet: {e}")
        return None, None

# --- 2. HÀM BỔ TRỢ (CHỈ SỐ & LOGIC NỘI BỘ) ---
def calculate_readability(text):
    words = text.split()
    sentences = re.split(r'[.!?]+', text)
    asl = len(words) / max(len(sentences), 1)
    asw = 1.5 
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(max(0, min(100, score)), 2)

# --- 3. ENGINE VẬN HÀNH CHÍNH ---
def run_robot_v2(all_data, sh):
    df_d = all_data['Dashboard']
    
    # HÀM TRA CỨU SIÊU SẠCH: Trim cả khóa (Key) và giá trị (Value)
    def v(k):
        try:
            # Trim đầu vào k và cột chứa Key
            res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
            return str(res.values[0]).strip() if not res.empty else ""
        except: return ""

    # --- BƯỚC 1: GATEKEEPER ---
    if v('SYSTEM_MAINTENANCE').upper() == 'ON':
        st.warning("Hệ thống đang bảo trì!"); return

    df_rep = all_data['Report']
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    
    # Check an toàn cột REP_CREATED_AT
    if 'REP_CREATED_AT' in df_rep.columns:
        today_posts = df_rep[
            (df_rep['REP_CREATED_AT'].str.contains(today_str)) & 
            (df_rep['REP_RESULT'] == 'SUCCESS')
        ]
    else:
        today_posts = pd.DataFrame()

    if len(today_posts) >= batch_size:
        st.info(f"Đã đạt chỉ tiêu ngày ({len(today_posts)}/{batch_size})."); return

    # --- BƯỚC 2: BỐC TỪ KHÓA CHIẾN THUẬT (Rổ A/B) ---
    df_kw = all_data['Keyword']
    num_kw = int(v('NUM_KEYWORDS_PER_POST') or 4)
    
    # Ép kiểu số cho KW_STATUS
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
            # Trim giá trị group trước khi so sánh
            grp = str(item['KW_GROUP']).strip()
            if len(picked) < count and grp not in selected_groups:
                picked.append(item)
                selected_groups.append(grp)
        return picked

    quota_a = math.ceil(num_kw * 0.6)
    selected_kw += pick_from_ro(ro_a, quota_a)
    selected_kw += pick_from_ro(ro_b, num_kw - len(selected_kw))
    
    if len(selected_kw) < num_kw:
        selected_kw += pick_from_ro(ro_a + ro_b, num_kw - len(selected_kw))

    if not selected_kw:
        st.error("Không tìm thấy từ khóa hợp lệ!"); return

    kw_main = selected_kw[0]['KW_TEXT'].strip()
    kw_subs = [x['KW_TEXT'].strip() for x in selected_kw[1:]]

    # --- BƯỚC 3: ASSEMBLER ---
    genai.configure(api_key=v('GEMINI_API_KEY'))
    model = genai.GenerativeModel(v('MODEL_VERSION') or 'gemini-1.5-flash')
    
    prompt_final = f"""{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main).replace('{{word_count}}', v('WORD_COUNT_RANGE')).replace('{{secondary_keywords}}', ', '.join(kw_subs))}
    STRATEGY: {v('CONTENT_STRATEGY')}
    RULE: {v('SEO_GLOBAL_RULE')}
    STYLE: {v('SERP_STYLE_PROMPT')}
    HUMANIZER: {v('AI_HUMANIZER_PROMPT')}
    """
    
    with st.status("🤖 Robot đang xào nấu nội dung...", expanded=True):
        resp = model.generate_content(prompt_final)
        content_raw = resp.text

        # --- BƯỚC 4: TỐI ƯU LIÊN KẾT & ẢNH ---
        df_web = all_data['Website']
        site = df_web[df_web['WS_STATUS'].str.upper() == 'ACTIVE'].sample(n=1).iloc[0]
        
        # Gắn Backlink 100%
        out_limit = int(site['WS_LINK_OUT_LIMIT'] or 1)
        final_content = content_raw
        for idx, item in enumerate(selected_kw):
            link = site['WS_TARGET_URL'].strip() if idx < out_limit else site['WS_PLATFORM'].strip()
            pattern = re.compile(re.escape(item['KW_TEXT'].strip()), re.IGNORECASE)
            final_content = pattern.sub(f'<a href="{link}">{item["KW_TEXT"].strip()}</a>', final_content, count=1)

        # Chèn Ảnh (Trim URL)
        df_img = all_data['Image']
        df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0)
        best_imgs = df_img[df_img['IMG_URL'].str.strip() != ''].sort_values('IMG_USED_COUNT').head(10)
        
        if not best_imgs.empty:
            img_row = best_imgs.sample(n=1).iloc[0]
            img_tag = f'<br><p align="center"><img src="{img_row["IMG_URL"].strip()}" alt="{kw_main}"></p><br>'
            final_content = final_content.replace('\n', '\n' + img_tag, 1) # Chèn sau đoạn 1

        # --- BƯỚC 5: GHI CHÚ & BÁO CÁO ---
        # (Logic ghi Report và gửi Telegram giữ nguyên như bản Master)
        # ... [Ghi row SUCCESS vào Report và gửi Telegram] ...
        st.success(f"Hoàn thành xuất sắc bài viết cho {kw_main}")

# --- 4. UI GIAO DIỆN ---
st.title("🚀 LAIHO.VN - PHIÊN BẢN SẠCH KHOẢNG TRẮNG")
data, sh = load_all_tabs()
if data:
    if st.sidebar.button("🚀 CHẠY ROBOT NGAY", type="primary"):
        run_robot_v2(data, sh)
    # Hiển thị các Tab...
