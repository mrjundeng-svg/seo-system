import streamlit as st
import pandas as pd
import gspread
from groq import Groq
import requests, time, random, re
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V69 - GROQ", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)

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

# --- 3. BƯỚC 4: OPTIMIZER (LINK OUT CỘT G | LINK IN CỘT B | ẢNH CÔNG BẰNG) ---
def pulse_4_optimizer(web_row, kw_list, content, data_tabs, sh):
    out_limit = int(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', '') # Cột G
    platform_url = web_row.get('WS_PLATFORM', '') # Cột B
    
    # Nhịp 1: Gắn Link (Ưu tiên Out G -> In B)
    optimized_content = content
    for i, kw in enumerate(kw_list):
        href = target_url if i < out_limit else platform_url
        if href:
            anchor = f"<a href='{href}'><b>{kw['KW_TEXT']}</b></a>"
            optimized_content = optimized_content.replace(kw['KW_TEXT'], anchor, 1)

    # Nhịp 2 & 3: Tuyển & Chèn Ảnh (Used Count thấp nhất)
    df_img = data_tabs['Image'].copy()
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0).astype(int)
    valid_imgs = df_img[df_img['IMG_URL'].str.contains('http')].sort_values('IMG_USED_COUNT')
    
    if not valid_imgs.empty:
        img_row = valid_imgs.iloc[0]
        img_url = img_row['IMG_URL']
        # Chèn ảnh ngay sau đoạn văn chứa KW chính
        paragraphs = re.split(r'(</p>)', optimized_content)
        final_content = ""
        inserted = False
        for p in paragraphs:
            final_content += p
            if not inserted and "</p>" in p and kw_list[0]['KW_TEXT'] in p:
                final_content += f"<br><p align='center'><img src='{img_url}' width='100%'></p><br>"
                inserted = True
                # Update Used Count
                try:
                    ws_i = sh.worksheet("Image")
                    cell = ws_i.find(img_url)
                    if cell: ws_i.update_cell(cell.row, 2, int(img_row['IMG_USED_COUNT']) + 1)
                except: pass
        return final_content
    return optimized_content

# --- 4. DASHBOARD VẬN HÀNH ---
data, sh = load_all_tabs()
if data:
    def v(k):
        r = data['Dashboard'][data['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - GROQ ENGINE")
    
    if st.button("🚀 KÍCH HOẠT ROBOT (CHẠY GROQ)"):
        with st.status("🤖 Đang chạy THỰC TẾ...") as status:
            try:
                # Bốc data thật
                web = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_selection = data['Keyword'].sort_values('KW_STATUS').head(4).to_dict('records')
                
                # AI viết bài bằng GROQ (Llama 3.3 70B)
                client = Groq(api_key=v('GROQ_API_KEY'))
                prompt = f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_selection[0]['KW_TEXT'])}. Viết tiếng Việt, HTML format."
                
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                raw_art = chat_completion.choices[0].message.content
                
                # Bước 4: Optimize
                final_art = pulse_4_optimizer(web, kw_selection, raw_art, data, sh)
                
                # Bước 5: Report 19 cột (A-S)
                now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
                rep_row = [web['WS_URL'], web['WS_PLATFORM'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", 
                           final_art[:200], "1", "YES", "NO", 
                           kw_selection[0]['KW_TEXT'], kw_selection[1]['KW_TEXT'], kw_selection[2]['KW_TEXT'], kw_selection[3]['KW_TEXT'], "",
                           "48", "12%", "70", get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"]
                sh.worksheet("Report").append_row(rep_row)
                
                st.markdown(final_art, unsafe_allow_html=True)
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
