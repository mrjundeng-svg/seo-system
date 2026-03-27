import streamlit as st
import pandas as pd
import gspread
import google.generativeai as genai
import requests, time, random, re
from datetime import datetime, timedelta, timezone

# --- SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V67", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)

# --- FIX LỖI AUTH TRIỆT ĐỂ ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        # Dùng trực tiếp hàm này để không bị lỗi AuthorizedSession
        return gspread.service_account_from_dict(info).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"Lỗi kết nối GSheet: {e}"); return None

# --- LOAD DATA ---
def load_data():
    sh = get_sh()
    if not sh: return None, None
    data = {}
    for t in ["Dashboard", "Website", "Keyword", "Image", "Report"]:
        try:
            ws = sh.worksheet(t); vals = ws.get_all_values()
            data[t] = pd.DataFrame(vals[1:], columns=[h.strip().upper() for h in vals[0]]).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# --- THỰC THI BƯỚC 4 (LINK OUT CỘT G - LINK IN CỘT B) ---
def pulse_4_optimize(web_row, kw_list, content, sh):
    out_limit = int(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', '') # CỘT G
    platform_url = web_row.get('WS_PLATFORM', '') # CỘT B
    
    optimized_content = content
    for i, kw_item in enumerate(kw_list):
        href = target_url if i < out_limit else platform_url
        if href:
            anchor = f"<a href='{href}'><b>{kw_item['KW_TEXT']}</b></a>"
            optimized_content = optimized_content.replace(kw_item['KW_TEXT'], anchor, 1)
    return optimized_content

# --- GIAO DIỆN CHÍNH ---
data, sh = load_data()
if data:
    df_d = data['Dashboard']
    def v(k):
        r = df_d[df_d.iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')}")
    
    if st.button("🚀 KÍCH HOẠT ROBOT"):
        with st.status("🤖 Đang chạy thật...") as status:
            try:
                # 1. Bốc Web & KW
                web = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_selection = data['Keyword'].head(4).to_dict('records') # Lấy 4 từ đầu
                
                # 2. AI Viết (Sửa lỗi 404 bằng cách dùng model chuẩn)
                genai.configure(api_key=v('GEMINI_API_KEY'))
                model = genai.GenerativeModel('gemini-1.5-flash') # Không dùng v1beta nữa
                
                prompt = f"Viết bài SEO về {kw_selection[0]['KW_TEXT']} bằng tiếng Việt, HTML format."
                res = model.generate_content(prompt)
                
                # 3. Tối ưu Link (BƯỚC 4)
                final_art = pulse_4_optimize(web, kw_selection, res.text, sh)
                
                # 4. Ghi Report (BƯỚC 5)
                report_row = [web['WS_URL'], web['WS_PLATFORM'], get_vn_now().strftime("%Y-%m-%d %H:%M:%S"), 
                              f"Bài: {kw_selection[0]['KW_TEXT']}", final_art[:200], "1", "YES", "NO",
                              kw_selection[0]['KW_TEXT'], kw_selection[1]['KW_TEXT'], kw_selection[2]['KW_TEXT'], 
                              kw_selection[3]['KW_TEXT'], "", "48", "12%", "70", 
                              get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"]
                sh.worksheet("Report").append_row(report_row)
                
                st.markdown(final_art, unsafe_allow_html=True)
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
