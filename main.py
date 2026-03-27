import streamlit as st
import pandas as pd
import gspread
from groq import Groq
import requests, time, random, re
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V70 - GROQ", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# HÀM QUAN TRỌNG: Xử lý dải số '1-3' hoặc '2' từ Sheet của bồ
def get_range_val(val, default=1):
    s = clean(str(val))
    if not s: return default
    if '-' in s:
        try:
            parts = s.split('-')
            low = int(re.sub(r'\D', '', parts[0]))
            high = int(re.sub(r'\D', '', parts[1]))
            return random.randint(low, high)
        except: return default
    try: return int(re.sub(r'\D', '', s))
    except: return default

# --- 2. AUTH GSHEET (DIỆT LỖI _AUTH_REQUEST) ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return gspread.service_account_from_dict(info).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"Lỗi GSheet: {e}"); return None

@st.cache_data(ttl=2)
def load_all_tabs():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        try:
            ws = sh.worksheet(t); vals = ws.get_all_values()
            headers = [h.strip().upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# --- 3. BƯỚC 4: OPTIMIZER (ĐÚNG ĐẶC TẢ - LINK NGOẠI TRƯỚC) ---
def pulse_4_optimizer(web_row, kw_list, content, data_tabs, sh):
    # Lấy hạn ngạch từ Sheet (Dùng hàm get_range_val để tránh lỗi '1-3')
    out_limit = get_range_val(web_row.get('WS_LINK_OUT_LIMIT', 1))
    in_limit = get_range_val(web_row.get('WS_LINK_IN_LIMIT', 1))
    
    target_url = web_row.get('WS_TARGET_URL', 'https://laiho.vn/') # Cột G
    platform_url = web_row.get('WS_PLATFORM', '')                 # Cột B
    
    # Nhịp 1: Gắn Link (Ưu tiên Giai đoạn 1: Out -> Giai đoạn 2: In)
    optimized_content = content
    for i, kw_item in enumerate(kw_list):
        kw_text = kw_item['KW_TEXT']
        # Theo đúng rule: if (i < out_limit) -> Outbound else -> Inbound
        href = target_url if i < out_limit else platform_url
        if href:
            anchor = f"<a href='{href}'><b>{kw_text}</b></a>"
            optimized_content = optimized_content.replace(kw_text, anchor, 1)

    # Nhịp 2: Tuyển & Chèn Ảnh (Used Count thấp nhất)
    df_img = data_tabs['Image'].copy()
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0).astype(int)
    valid_imgs = df_img[df_img['IMG_URL'].str.contains('http')].sort_values('IMG_USED_COUNT')
    
    if not valid_imgs.empty:
        img_limit = get_range_val(web_row.get('WS_IMG_LIMIT', 1))
        selected_imgs = valid_imgs.head(img_limit).to_dict('records')
        
        # Nhịp 3: Chèn ảnh vào sau Paragraph chứa Keyword đầu tiên
        paras = re.split(r'(</p>)', optimized_content)
        final_content = ""
        img_idx = 0
        for p in paras:
            final_content += p
            if img_idx < len(selected_imgs) and "</p>" in p and kw_list[0]['KW_TEXT'] in p:
                img_url = selected_imgs[img_idx]['IMG_URL']
                final_content += f"<br><p align='center'><img src='{img_url}' width='100%'></p><br>"
                # Update Used Count ngay trên Sheet
                try:
                    ws_i = sh.worksheet("Image")
                    cell = ws_i.find(img_url)
                    if cell: ws_i.update_cell(cell.row, 2, int(selected_imgs[img_idx]['IMG_USED_COUNT']) + 1)
                except: pass
                img_idx += 1
        return final_content
    return optimized_content

# --- 4. DASHBOARD VẬN HÀNH ---
data, sh = load_all_tabs()
if data:
    def v(k):
        r = data['Dashboard'][data['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - GROQ V70")
    
    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY GROQ)"):
        with st.status("🤖 Đang thực thi luồng THỰC TẾ...") as status:
            try:
                # 1. Bốc data thật
                web = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                
                # Tính số KW cần nhặt (Dùng dải số)
                num_kw = get_range_val(v('NUM_KEYWORDS_PER_POST'), 4)
                kw_selection = data['Keyword'].sort_values('KW_STATUS').head(num_kw).to_dict('records')
                
                # 2. AI viết bài bằng GROQ (Llama 3.3 70B)
                client = Groq(api_key=v('GROQ_API_KEY'))
                prompt = f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_selection[0]['KW_TEXT'])}. Viết tiếng Việt, HTML format."
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                raw_art = chat_completion.choices[0].message.content
                
                # 3. Bước 4: Optimize (Link & Image)
                final_art = pulse_4_optimizer(web, kw_selection, raw_art, data, sh)
                
                # 4. Bước 5: Report 19 cột (A-S)
                now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
                rep_row = [web['WS_URL'], web['WS_PLATFORM'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", 
                           final_art[:200], "1", "YES", "NO", 
                           kw_selection[0]['KW_TEXT'], 
                           kw_selection[1]['KW_TEXT'] if len(kw_selection)>1 else "",
                           kw_selection[2]['KW_TEXT'] if len(kw_selection)>2 else "",
                           kw_selection[3]['KW_TEXT'] if len(kw_selection)>3 else "",
                           kw_selection[4]['KW_TEXT'] if len(kw_selection)>4 else "",
                           "48", "12%", "70", get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"]
                sh.worksheet("Report").append_row(rep_row)
                
                st.markdown(final_art, unsafe_allow_html=True)
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
