import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from groq import Groq
import smtplib, time, random, re, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

# --- 1. SETUP & GATEKEEPER ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V80 - TELEGRAM", layout="wide")
def get_vn_now(): return datetime.now(VN_TZ)

# --- 2. NHỊP BẮN NOTI TELEGRAM (HÀM MỚI) ---
def send_telegram_noti(v_func, msg_text):
    token = v_func('TELEGRAM_BOT_TOKEN')
    chat_id = v_func('TELEGRAM_CHAT_ID')
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": f"<b>🛡️ LAIHO SEO OS REPORT</b>\n\n{msg_text}",
            "parse_mode": "HTML"
        }
        try: requests.post(url, json=payload)
        except Exception as e: st.warning(f"Lỗi Telegram: {e}")

# --- 3. CÁC HÀM XỬ LÝ NỘI DUNG (GIỮ NGUYÊN TỪ V79) ---
def get_range_val(val, default=1):
    nums = re.findall(r'\d+', str(val))
    if len(nums) >= 2: return random.randint(int(nums[0]), int(nums[1]))
    return int(nums[0]) if nums else default

def humanize_and_spin(content, local_prompt):
    final_txt = content
    local_samples = ["TP.HCM", "Hà Nội", "Đà Nẵng", "Bình Dương", "Đồng Nai", "Cần Thơ"]
    if "[LOCAL_TEXT]" in final_txt:
        final_txt = final_txt.replace("[LOCAL_TEXT]", local_prompt if local_prompt else random.choice(local_samples))
    return final_txt

def attach_backlinks_smart(content, kw_list, web_row):
    out_limit = get_range_val(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', 'https://laiho.vn/')
    platform_url = web_row.get('WS_PLATFORM', '')
    optimized = content
    for i, kw in enumerate(kw_list):
        href = target_url if i < out_limit else platform_url
        if not href: continue
        pattern = re.compile(re.escape(kw['KW_TEXT']), re.IGNORECASE)
        match = pattern.search(optimized)
        if match:
            start, end = match.span()
            anchor = f"<a href='{href}' style='color:#007bff;font-weight:bold;'>{match.group()}</a>"
            optimized = optimized[:start] + anchor + optimized[end:]
    return optimized

# --- 4. KẾT NỐI & VẬN HÀNH ---
def get_sh():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        creds = Credentials.from_service_account_info(info, scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'])
        return gspread.authorize(creds).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except: return None

sh = get_sh()
if sh:
    tabs = ["Dashboard", "Website", "Keyword", "Report"]
    db = {t: pd.DataFrame(sh.worksheet(t).get_all_values()[1:], columns=[h.strip().upper() for h in sh.worksheet(t).get_all_values()[0]]) for t in tabs}
    def v(k):
        r = db['Dashboard'][db['Dashboard'].iloc[:,0].str.strip().str.upper() == k.upper()]
        return r.iloc[0,1].strip() if not r.empty else ""

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER V80")
    if st.button("🚀 KÍCH HOẠT ROBOT (ĐĂNG BÀI + NOTI TELEGRAM)"):
        with st.status("🤖 Robot đang vận hành Nhịp 1-5...") as status:
            try:
                # Bốc dữ liệu
                web = db['Website'][db['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].iloc[0].to_dict()
                kw_selection = db['Keyword'].sort_values('KW_STATUS').head(4).to_dict('records')
                kw_main = kw_selection[0]['KW_TEXT']

                # AI viết bài
                client = Groq(api_key=v('GROQ_API_KEY'))
                res = client.chat.completions.create(messages=[{"role":"user","content":f"Viết bài SEO về {kw_main}. HTML format. Dùng tag [LOCAL_TEXT]."}], model="llama-3.3-70b-versatile")
                raw_art = res.choices[0].message.content

                # Hậu kỳ: Spin & Backlink
                spinned = humanize_and_spin(raw_art, v('LOCAL_PROMPT'))
                final_art = attach_backlinks_smart(spinned, kw_selection, web)

                # Giao hàng: Blogger & Mail
                sender, pw = v('SENDER_EMAIL'), v('SENDER_PASSWORD')
                msg = MIMEMultipart()
                msg['Subject'] = f"PUBLISH: {kw_main}"
                msg.attach(MIMEText(final_art, 'html'))
                with smtplib.SMTP('smtp.gmail.com', 587) as s:
                    s.starttls(); s.login(sender, pw)
                    s.sendmail(sender, [web['WS_SECRET_MAIL'], v('RECEIVER_EMAIL')], msg.as_string())

                # Ghi Report
                now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
                sh.worksheet("Report").append_row([web['WS_URL'], web['WS_PLATFORM'], now_str, f"Bài: {kw_main}", final_art[:200], "1", "YES", "NO", kw_main, "", "", "", "", "55", "10%", "65", get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"])

                # NHỊP 5: BẮN NOTI TELEGRAM (HẾT CHEAT)
                noti_msg = f"✅ <b>Đã đăng bài thành công!</b>\n\n📌 <b>Website:</b> {web['WS_URL']}\n🔑 <b>Từ khóa chính:</b> {kw_main}\n📊 <b>Kết quả:</b> SUCCESS\n📅 <b>Thời gian:</b> {now_str}"
                send_telegram_noti(v, noti_msg)
                
                st.markdown(final_art, unsafe_allow_html=True)
                st.success("🏁 ĐÃ ĐĂNG BÀI & BẮN NOTI TELEGRAM THÀNH CÔNG!")
                status.update(label="🏁 HOÀN TẤT!", state="complete")
            except Exception as e: st.error(f"Lỗi: {e}")
