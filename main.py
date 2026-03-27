import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
from serpapi import GoogleSearch
import smtplib, time, random, re, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG (CLEAN RUN & TIMING) ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V76", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)

def get_range_val(val, default=1):
    nums = re.findall(r'\d+', str(val))
    try:
        if len(nums) >= 2: return random.randint(int(nums[0]), int(nums[1]))
        return int(nums[0]) if nums else default
    except: return default

# --- 2. KẾT NỐI GSHEET (FIX LỖI _AUTH_REQUEST) ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"❌ Lỗi GSheet: {e}"); return None

# --- NHỊP 1 & 2.1: CLEAN RUN & STYLE HUNTER ---
def style_hunter(v_func, target_kw, sh, data_tabs):
    # Ưu tiên 1: SerpApi (Google Top 5)
    serp_key = v_func('SERPAPI_KEY')
    comp_list = [c.strip().lower() for c in v_func('COMPETITOR_LIST').split(',')]
    
    if serp_key:
        try:
            search = GoogleSearch({"q": target_kw, "api_key": serp_key, "num": 5})
            results = search.get_dict().get("organic_results", [])
            for res in results:
                link = res.get("link", "")
                if any(comp in link.lower() for comp in comp_list):
                    return res.get("snippet", "") # Mỏ neo văn phong
            if results: return results[0].get("snippet", "")
        except: pass

    # Ưu tiên 2: Internal Report (Bới kho báu cũ)
    df_rep = data_tabs['Report']
    if not df_rep.empty:
        success_posts = df_rep[df_rep['REP_RESULT'] == 'SUCCESS'].sort_values('REP_SEO_SCORE', ascending=False)
        if not success_posts.empty:
            return success_posts.iloc[0]['REP_PREVIEW']
            
    return None

# --- NHỊP 3: ASSEMBLER (6 KINGS & 2 KNIGHTS) ---
def assembler_engine(v_func, kw_main, kw_sub_list, word_count, style_anchor):
    # Lớp 1: Chốt chặn 6 Kings
    kings = {
        "PROMPT_TEMPLATE": v_func('PROMPT_TEMPLATE'),
        "CONTENT_STRATEGY": v_func('CONTENT_STRATEGY'),
        "KEYWORD_PROMPT": v_func('KEYWORD_PROMPT'),
        "SERP_STYLE_PROMPT": v_func('SERP_STYLE_PROMPT'),
        "SEO_GLOBAL_RULE": v_func('SEO_GLOBAL_RULE'),
        "AI_HUMANIZER_PROMPT": v_func('AI_HUMANIZER_PROMPT')
    }
    
    for key, val in kings.items():
        if not val or val.strip() == "":
            st.error(f"❌ Hệ thống đình chỉ do thiếu dữ liệu cốt lõi ({key} Fail)"); return None

    # Lớp 3: Data Mapping
    prompt = kings['PROMPT_TEMPLATE'].replace('{{keyword}}', kw_main)
    prompt = prompt.replace('{{word_count}}', str(word_count))
    prompt = prompt.replace('{{secondary_keywords}}', ", ".join(kw_sub_list))

    # Thứ tự nối chuỗi: Tiền đề -> Nội dung -> Kỷ luật
    chain = f"{prompt}\n\nSTRATEGY: {kings['CONTENT_STRATEGY']}\nKW RULE: {kings['KEYWORD_PROMPT']}\n"
    chain += f"STYLE ANCHOR: {style_anchor}\n"
    
    # 2 Knights (Optional)
    if v_func('TABLE_PROMPT'): chain += f"TABLE: {v_func('TABLE_PROMPT')}\n"
    if v_func('LOCAL_PROMPT'): chain += f"LOCAL: {v_func('LOCAL_PROMPT')}\n"
    
    # Kỷ luật sắt ở cuối
    chain += f"\nSEO RULE: {kings['SEO_GLOBAL_RULE']}\nHUMANIZER: {kings['AI_HUMANIZER_PROMPT']}"
    return chain

# --- NHỊP 4: SEO CHECK (FLESCH VIETNAMESE) ---
def internal_readability_score(text):
    # Công thức: 206.835 - (1.015 * ASL) - (84.6 * ASW)
    words = text.split()
    sentences = re.split(r'[.!?]', text)
    if not sentences: return 0
    asl = len(words) / len(sentences)
    asw = 1.5 # Giả định trung bình tiếng Việt
    score = 206.835 - (1.015 * asl) - (84.6 * asw)
    return round(score, 2)

# --- VẬN HÀNH CHÍNH ---
sh = get_sh()
if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report"]
    data = {t: pd.DataFrame(sh.worksheet(t).get_all_values()[1:], 
             columns=[h.strip().upper() for h in sh.worksheet(t).get_all_values()[0]]).fillna('') for t in tabs}
    
    def v(k):
        r = data['Dashboard'][data['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V76")

    if st.button("🚀 KÍCH HOẠT ROBOT (NHỊP 1-5)"):
        with st.status("🤖 Hệ điều hành đang vận hành...") as status:
            # NHỊP 1: GATEKEEPER
            active_webs = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE']
            if active_webs.empty: st.error("Lớp 1 Fail: Không có Web ACTIVE"); st.stop()
            web = active_webs.iloc[0].to_dict()
            
            # NHỊP 2.1: THE STYLE HUNTER
            kw_main = data['Keyword'].sort_values('KW_STATUS').iloc[0]['KW_TEXT']
            style_anchor = style_hunter(v, kw_main, sh, data)
            if not style_anchor: st.error("Nhịp 2.1 Fail: Không tìm thấy mỏ neo"); st.stop()
            
            # NHỊP 2.2: HỆ SINH THÁI KW & WORD COUNT
            word_target = get_range_val(v('WORD_COUNT_RANGE'), 1000)
            kw_subs = data['Keyword'].iloc[1:5]['KW_TEXT'].tolist()
            
            # NHỊP 3: ASSEMBLER
            master_prompt = assembler_engine(v, kw_main, kw_subs, word_target, style_anchor)
            
            # THỰC THI (GROQ)
            client = Groq(api_key=v('GROQ_API_KEY'))
            res = client.chat.completions.create(messages=[{"role":"user","content":master_prompt}], model="llama-3.3-70b-versatile")
            article = res.choices[0].message.content
            
            # NHỊP 4: SEO & READABILITY
            read_score = internal_readability_score(article)
            
            # NHỊP 5: GHI NHẬN & ĐĂNG BÀI
            # (Hàm gửi mail Blogger bồ đã có ở V75)
            st.markdown(article, unsafe_allow_html=True)
            st.metric("Readability Score (Flesch)", read_score)
            status.update(label="🏁 HOÀN TẤT THEO SIÊU ĐẶC TẢ!", state="complete")
