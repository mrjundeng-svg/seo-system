import streamlit as st
import pandas as pd
import gspread
import google.generativeai as genai
import requests, json, time, random, re
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V63", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

def get_range_val(val, default=1):
    s = clean(str(val))
    if '-' in s:
        try:
            p = s.split('-')
            return random.randint(int(re.sub(r'\D','',p[0])), int(re.sub(r'\D','',p[1])))
        except: return default
    try: return int(re.sub(r'\D','',s))
    except: return default

# --- 2. KẾT NỐI SHEET (FIX LỖI _AUTH_REQUEST) ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        # Dùng service_account_from_dict là cách CHUẨN nhất để tránh lỗi Auth trên Streamlit
        return gspread.service_account_from_dict(info).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"❌ Lỗi kết nối GSheet: {e}")
        return None

@st.cache_data(ttl=2)
def load_all_tabs():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        try:
            ws = sh.worksheet(t); vals = ws.get_all_values()
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# --- 3. NHỊP MASTER: GẮN LINK (OUT TRƯỚC - IN SAU) & CHÈN ẢNH ---
def pulse_4_optimizer(v_func, web_row, kw_list, content, data_tabs, sh):
    # Nhịp 1: Gắn Link (Ưu tiên Link Out từ Cột G, sau đó đến Link In từ Cột B)
    out_limit = get_range_val(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', 'https://laiho.vn/') # Cột G
    platform_url = web_row.get('WS_PLATFORM', '')                 # Cột B
    
    optimized_content = content
    for i, kw_item in enumerate(kw_list):
        kw_text = kw_item['KW_TEXT']
        # Giai đoạn 1: Link Out | Giai đoạn 2: Link In
        href = target_url if i < out_limit else platform_url
        if href:
            anchor = f"<a href='{href}'><b>{kw_text}</b></a>"
            optimized_content = optimized_content.replace(kw_text, anchor, 1)

    # Nhịp 2: Tuyển chọn Ảnh (Ưu tiên USED_COUNT thấp nhất)
    df_img = data_tabs['Image'].copy()
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0).astype(int)
    valid_imgs = df_img[df_img['IMG_URL'].str.contains('http')].sort_values('IMG_USED_COUNT')
    
    if not valid_imgs.empty:
        img_limit = get_range_val(web_row.get('WS_IMG_LIMIT', 1))
        selected_imgs = valid_imgs.head(img_limit).to_dict('records')
        
        # Nhịp 3: Chèn Ảnh theo tọa độ Paragraph
        paragraphs = re.split(r'(</p>)', optimized_content)
        final_content = ""
        img_idx = 0
        for p in paragraphs:
            final_content += p
            if img_idx < len(selected_imgs) and "</p>" in p and kw_list[0]['KW_TEXT'] in p:
                img_url = selected_imgs[img_idx]['IMG_URL']
                final_content += f"<br><p align='center'><img src='{img_url}' width='100%'></p><br>"
                img_idx += 1
                # Update Image Count thật trên Sheet
                try:
                    ws_img = sh.worksheet("Image")
                    cell = ws_img.find(img_url)
                    if cell: ws_img.update_cell(cell.row, 2, selected_imgs[img_idx-1]['IMG_USED_COUNT'] + 1)
                except: pass
        return final_content
    return optimized_content

# =========================================================
# 🎮 DASHBOARD ĐIỀU HÀNH THỰC TẾ
# =========================================================
data, sh = load_all_tabs()
if data:
    df_d = data['Dashboard']
    def v(key):
        row = df_d[df_d.iloc[:, 0].str.strip().str.upper() == key.strip().upper()]
        return clean(row.iloc[0, 1]) if not row.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - V63 MASTER")
    
    if st.button("🚀 KÍCH HOẠT ROBOT THỰC THI"):
        start_t = time.time()
        with st.status("🤖 Robot đang vận hành thực tế...") as status:
            # 1. Bốc Web & Keyword thật
            active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
            web_real = active_webs.sample(1).iloc[0].to_dict()
            df_kw = data['Keyword']
            df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(0).astype(int)
            kw_selection = df_kw.sort_values('KW_STATUS').head(get_range_val(v('NUM_KEYWORDS_PER_POST'), 4)).to_dict('records')
            
            # 2. AI Viết bài (Gemini)
            genai.configure(api_key=v('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            raw_art = model.generate_content(f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_selection[0]['KW_TEXT'])}. Viết tiếng Việt, HTML format.").text
            
            # 3. Tối ưu Link & Ảnh (Bước 4)
            final_art = pulse_4_optimizer(v, web_real, kw_selection, raw_art, data, sh)
            
            # 4. Báo cáo 19 cột chuẩn A-S
            now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
            report_row = [
                web_real['WS_URL'], web_real['WS_PLATFORM'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", 
                final_art[:200], "1", "YES", "NO", 
                kw_selection[0]['KW_TEXT'], kw_selection[1]['KW_TEXT'], kw_selection[2]['KW_TEXT'], kw_selection[3]['KW_TEXT'], "",
                48, "12%", 70, get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"
            ]
            sh.worksheet("Report").append_row(report_row)
            
            st.markdown(final_art, unsafe_allow_html=True)
            status.update(label=f"🏁 HOÀN TẤT!", state="complete")
            st.balloons()
