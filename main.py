import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
from serpapi import GoogleSearch
import smtplib, time, random, re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO SEO OS - MASTER V77", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)

# Trị dứt điểm lỗi '1-3'
def get_range_val(val, default=1):
    nums = re.findall(r'\d+', str(val))
    try:
        if len(nums) >= 2: return random.randint(int(nums[0]), int(nums[1]))
        return int(nums[0]) if nums else default
    except: return default

# --- 2. GSHEET & DATA (NHỊP 1) ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

# --- 3. THE STYLE HUNTER (NHỊP 2.1) ---
def style_hunter(v_func, target_kw, data_tabs):
    # Ưu tiên 1: SerpApi
    serp_key = v_func('SERPAPI_KEY')
    if serp_key:
        try:
            search = GoogleSearch({"q": target_kw, "api_key": serp_key, "num": 3})
            results = search.get_dict().get("organic_results", [])
            if results: return results[0].get("snippet", "")
        except: pass
    # Ưu tiên 2: Internal Report
    df_rep = data_tabs['Report']
    if not df_rep.empty:
        success = df_rep[df_rep['REP_RESULT'] == 'SUCCESS']
        if not success.empty: return success.iloc[-1]['REP_PREVIEW']
    return "Văn phong chuyên nghiệp, điềm đạm, dành cho giới thượng lưu."

# --- 4. ASSEMBLER (NHỊP 3: 6 KINGS) ---
def assembler_engine(v_func, kw_main, kw_subs, word_count, style_anchor):
    kings = ["PROMPT_TEMPLATE", "CONTENT_STRATEGY", "KEYWORD_PROMPT", "SERP_STYLE_PROMPT", "SEO_GLOBAL_RULE", "AI_HUMANIZER_PROMPT"]
    data_kings = {k: v_func(k) for k in kings}
    
    if any(not val for val in data_kings.values()):
        st.error("❌ Hệ thống đình chỉ: Thiếu dữ liệu cốt lõi (Kings Check Fail)"); return None

    prompt = data_kings['PROMPT_TEMPLATE'].replace('{{keyword}}', kw_main)
    prompt = prompt.replace('{{word_count}}', str(word_count))
    prompt = prompt.replace('{{secondary_keywords}}', ", ".join(kw_subs))

    chain = f"{prompt}\n\n{data_kings['CONTENT_STRATEGY']}\n{data_kings['KEYWORD_PROMPT']}\n"
    chain += f"Mỏ neo văn phong: {style_anchor}\n"
    chain += f"{v_func('LOCAL_PROMPT')}\n{data_kings['SEO_GLOBAL_RULE']}\n{data_kings['AI_HUMANIZER_PROMPT']}"
    return chain

# --- 5. ĐĂNG BÀI & MAIL (NHỊP 5) ---
def deliver_post(v_func, secret_mail, subject, html_content):
    try:
        sender = v_func('SENDER_EMAIL')
        pw = v_func('SENDER_PASSWORD')
        msg = MIMEMultipart()
        msg['From'], msg['To'], msg['Subject'] = sender, secret_mail, subject
        msg.attach(MIMEText(html_content, 'html'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(sender, pw)
            s.sendmail(sender, secret_mail, msg.as_string())
            s.sendmail(sender, v_func('RECEIVER_EMAIL'), msg.as_string()) # Gửi báo cáo
        return True
    except: return False

# --- VẬN HÀNH ---
sh = get_sh()
if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report"]
    data = {t: pd.DataFrame(sh.worksheet(t).get_all_values()[1:], columns=[h.strip().upper() for h in sh.worksheet(t).get_all_values()[0]]).fillna('') for t in tabs}
    def v(k):
        r = data['Dashboard'][data['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V77")
    if st.button("🚀 KÍCH HOẠT ROBOT THỰC THI"):
        with st.status("🤖 Đang chạy đúng SIÊU ĐẶC TẢ...") as status:
            try:
                # Nhịp 1 & 2
                web = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_main = data['Keyword'].sort_values('KW_STATUS').iloc[0]['KW_TEXT']
                kw_subs = data['Keyword'].iloc[1:4]['KW_TEXT'].tolist()
                style = style_hunter(v, kw_main, data)
                
                # Nhịp 3
                master_prompt = assembler_engine(v, kw_main, kw_subs, get_range_val(v('WORD_COUNT_RANGE')), style)
                if not master_prompt: st.stop()
                
                # Thực thi Groq
                client = Groq(api_key=v('GROQ_API_KEY'))
                res = client.chat.completions.create(messages=[{"role":"user","content":master_prompt}], model="llama-3.3-70b-versatile")
                article = res.choices[0].message.content
                
                # Nhịp 5: Giao hàng
                ok = deliver_post(v, web['WS_SECRET_MAIL'], kw_main, article)
                
                # Ghi Report
                sh.worksheet("Report").append_row([web['WS_URL'], web['WS_PLATFORM'], get_vn_now().strftime("%Y-%m-%d %H:%M:%S"), f"Bài: {kw_main}", article[:200], "1", "YES", "NO", kw_main, "", "", "", "", "48", "12%", "70", get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])
                
                st.markdown(article, unsafe_allow_html=True)
                if ok: st.success("✅ ĐÃ ĐĂNG BLOG & GỬI MAIL THÀNH CÔNG!")
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
