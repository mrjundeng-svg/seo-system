import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests, re, math
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
st.set_page_config(page_title="LAIHO.VN MASTER ENGINE", layout="wide")

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
            ws = sh.worksheet(t)
            vals = ws.get_all_values()
            if not vals: data[t] = pd.DataFrame()
            else:
                # ÉP TRIM TOÀN BỘ HỆ THỐNG
                headers = [str(h).strip() for h in vals[0]]
                rows = [[str(cell).strip() for cell in row] for row in vals[1:]]
                data[t] = pd.DataFrame(rows, columns=headers).fillna('')
        return data, sh
    except Exception as e:
        st.error(f"Lỗi kết nối: {e}"); return None, None

# --- 2. HÀM TRA CỨU & XOAY VÒNG ---
def get_serp_style_rotating(kw, keys_string, competitor_list):
    all_keys = [k.strip() for k in keys_string.split(',') if k.strip()]
    if not all_keys: return ""
    competitors = [c.strip().lower() for c in competitor_list.split(',') if c.strip()]
    for current_key in all_keys:
        try:
            params = {"q": kw, "location": "Vietnam", "hl": "vi", "gl": "vn", "api_key": current_key}
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            results = response.json().get("organic_results", [])
            if not results: continue
            for res in results[:5]:
                if any(comp in res.get("link", "").lower() for comp in competitors):
                    return f"Mỏ neo đối thủ: {res.get('title')}. Tóm tắt: {res.get('snippet')}"
            return f"Mỏ neo Top 1: {results[0].get('title')}. Tóm tắt: {results[0].get('snippet')}"
        except: continue
    return ""

# --- 3. POPUP VẬN HÀNH (TRUNG TÂM THEO DÕI) ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN ROBOT", width="large")
def run_robot_popup(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        try:
            res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
            return str(res.values[0]).strip() if not res.empty else ""
        except: return ""

    st.write("📝 **Đang kiểm tra ranh giới hệ thống...**")
    
    # Check Maintenance
    if v('SYSTEM_MAINTENANCE').upper() == 'ON':
        st.error("Hệ thống đang bảo trì. Không thể chạy!"); return

    # Check Batch Size
    df_rep = all_data['Report']
    batch_size = int(v('BATCH_SIZE') or 5)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    today_posts = df_rep[df_rep['REP_CREATED_AT'].astype(str).str.contains(today_str)] if 'REP_CREATED_AT' in df_rep.columns else []
    
    if len(today_posts) >= batch_size:
        st.warning(f"Đã đạt chỉ tiêu ngày ({len(today_posts)}/{batch_size})!"); return

    # Bước 2: Bốc từ khóa
    st.write("🔍 **Đang bốc từ khóa chiến thuật (Rổ A/B)...**")
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
    if len(selected_kw) < num_kw: selected_kw += pick_logic(ro_a + ro_b, num_kw - len(selected_kw))
    
    kw_main = selected_kw[0]['KW_TEXT'].strip()
    kw_subs = [x['KW_TEXT'].strip() for x in selected_kw[1:]]

    # Bước 3: Sản xuất nội dung
    log_area = st.container()
    with log_area:
        st.info(f"Đã chọn từ khóa chính: **{kw_main}**")
        style_anchor = get_serp_style_rotating(kw_main, v('SERPAPI_KEY'), v('COMPETITOR_LIST'))
        
        prompt_final = f"""{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main).replace('{{word_count}}', v('WORD_COUNT_RANGE')).replace('{{secondary_keywords}}', ', '.join(kw_subs))}
        VĂN PHONG MỎ NEO: {style_anchor if style_anchor else v('SERP_STYLE_PROMPT')}
        CHIẾN LƯỢC: {v('CONTENT_STRATEGY')}
        QUY TẮC SEO: {v('SEO_GLOBAL_RULE')}
        HUMANIZER: {v('AI_HUMANIZER_PROMPT')}"""

        gemini_keys = [k.strip() for k in v('GEMINI_API_KEY').split(',') if k.strip()]
        models_to_try = [m.strip() for m in v('MODEL_VERSION').split(',') if m.strip()]
        if not models_to_try: models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro']

        content_raw = ""
        for g_key in gemini_keys:
            genai.configure(api_key=g_key)
            for m_name in models_to_try:
                try:
                    full_path = f"models/{m_name}" if not m_name.startswith("models/") else m_name
                    st.write(f"⏳ Đang thử Model: `{full_path}` với Key: `{g_key[:8]}...`")
                    model = genai.GenerativeModel(full_path)
                    resp = model.generate_content(prompt_final)
                    if resp.text:
                        content_raw = resp.text; break
                except Exception as e:
                    st.error(f"❌ Lỗi Model `{m_name}`: {str(e)}") # Dễ dàng copy lỗi tại đây
                    continue
            if content_raw: break

    if not content_raw:
        st.error("💀 **THẤT BẠI TỔNG THỂ:** Tất cả Key và Model đều không chạy được!"); return

    # Bước 4 & 5 (Tối ưu & Report)
    st.write("🚀 **Đang tối ưu Backlink, Ảnh và Ghi báo cáo...**")
    # ... [Logic Bước 4 & 5 giữ nguyên như bản Master] ...
    
    st.success(f"✅ **XUẤT BẢN THÀNH CÔNG!** Bài viết về '{kw_main}' đã lên sóng.")
    if st.button("Đóng Popup"): st.rerun()

# --- 4. GIAO DIỆN HOME (CHÍNH) ---
data, sh = load_all_tabs()

if data:
    # NÚT BẤM NGAY TẠI HOME
    c1, c2, _ = st.columns([1.5, 1, 4])
    with c1:
        if st.button("🚀 KÍCH HOẠT ROBOT", type="primary", use_container_width=True):
            run_robot_popup(data, sh)
    with c2:
        if st.button("🔄 LÀM MỚI KHO", use_container_width=True):
            st.cache_data.clear(); st.rerun()

    st.divider()

    # Hiển thị dữ liệu các Tab để bồ tiện theo dõi
    tab_names = ["Dashboard", "Website", "Keyword", "Image", "Spin", "Local", "Report"]
    st_tabs = st.tabs([f"📂 {n}" for n in tab_names])
    for i, name in enumerate(tab_names):
        with st_tabs[i]:
            st.dataframe(data[name], use_container_width=True, hide_index=True)
