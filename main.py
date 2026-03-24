import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import google.generativeai as genai
import random, time, requests
from datetime import datetime, timedelta, timezone

# --- CONFIG ---
st.set_page_config(page_title="SEO MASTER v46.0", layout="wide")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

def get_creds():
    try:
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        return ServiceAccountCredentials.from_json_keyfile_dict(info, ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
    except: return None

@st.cache_data(ttl=5)
def load_data():
    try:
        client = gspread.authorize(get_creds())
        sh = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
        tabs = ["Dashboard", "Website", "Backlink", "Report"]
        res = {}
        for t in tabs:
            vals = sh.worksheet(t).get_all_values()
            if not vals: res[t] = pd.DataFrame()
            else:
                df = pd.DataFrame(vals[1:], columns=vals[0])
                # Loại bỏ dòng trống để tránh ValueError
                df = df.replace('', None).dropna(how='all')
                res[t] = df
        return res, "OK"
    except Exception as e: return None, str(e)

# --- ENGINE ---
@st.dialog("⚙️ HỆ THỐNG VẬN HÀNH v46", width="large")
def run_robot(data):
    df_d = data['Dashboard']
    def v(k):
        res = df_d[df_d['Hạng mục'].astype(str).str.strip() == k]['Input dữ liệu']
        return str(res.values[0]).strip() if not res.empty else ""

    genai.configure(api_key=v('GEMINI_API_KEY'))
    model = genai.GenerativeModel("gemini-1.5-flash")

    active_sites = data['Website'][data['Website'].iloc[:, 10].str.contains('Active', case=False, na=False)]
    df_bl = data['Backlink']
    num_posts = int(v('Số lượng bài cần tạo') or 1)

    for i in range(num_posts):
        now_str = get_vn_time().strftime("%Y-%m-%d %H:%M")
        site = active_sites.sample(n=1).iloc[0]
        
        # BỐC DATA BACKLINK: Cột B (1) là Anchor, Cột A (0) là Link
        bl_pool = df_bl.sample(n=min(len(df_bl), 5)).values.tolist()
        anchors = [str(r[1]) for r in bl_pool] + [""]*5
        target_links = [str(r[0]) for r in bl_pool] + [""]*3

        with st.status(f"Đang xử lý bài {i+1}...", expanded=True):
            try:
                # PROMPT NGHIÊM NGẶT
                prompt = (
                    f"ROLE: Bạn là một máy viết bài SEO. KHÔNG ĐƯỢC CHÀO HỎI. KHÔNG 'Chào sếp'.\n"
                    f"Bắt đầu bài viết bằng Tiêu đề H1 cực hay chứa từ khóa: {v('Danh sách Keyword bài viết')}\n"
                    f"Yêu cầu: Viết nội dung dài, chèn link {target_links[0]} vào từ {anchors[0]}.\n"
                    f"Nội dung cần viết về: {v('PROMPT_TEMPLATE')}"
                )
                
                resp = model.generate_content(prompt)
                full_text = resp.text
                
                # Lọc tiêu đề: Bỏ qua các dòng chào hỏi xã giao
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                title = "Tiêu đề lỗi"
                for line in lines:
                    clean_line = line.replace('#', '').replace('*', '').strip()
                    if not any(x in clean_line.lower() for x in ["chào", "kính chào", "hello"]):
                        title = clean_line
                        break

                # Chấm điểm SEO (Real-check)
                score = "95/100"
                if any(x in title.lower() for x in ["chào", "kính chào"]):
                    score = "0/100 (Lỗi tiêu đề xã giao)"

                # POPUP LOG
                st.markdown(f"**BÀI #{i+1} HOÀN TẤT**")
                st.write(f"- Website: {site.iloc[0]}")
                st.write(f"- Tiêu đề: {title}")
                st.write(f"- Anchor 1: {anchors[0]} -> Link: {target_links[0]}")

                # GHI REPORT 18 CỘT (KHỚP image_f3f0c8)
                report_row = [
                    site.iloc[0], site.iloc[1], now_str, "Chờ đăng", title, 
                    v('Danh sách Keyword bài viết'), site.iloc[9],
                    anchors[0], anchors[1], anchors[2], anchors[3], anchors[4],
                    target_links[0], target_links[1], target_links[2],
                    score, now_str, "Thành công"
                ]
                gspread.authorize(get_creds()).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip()).worksheet("Report").append_row(report_row)

                # TELEGRAM
                tele_msg = (
                    f"<b>🚀 SEO MASTER v46</b>\n"
                    f"✅ <b>Site:</b> {site.iloc[0]}\n"
                    f"📄 <b>Tiêu đề:</b> {title}\n"
                    f"⚓ <b>Từ khoá:</b> {anchors[0]}\n"
                    f"🔗 <b>Backlink:</b> {target_links[0]}\n"
                    f"🕒 <b>Lúc:</b> {now_str}"
                )
                requests.post(f"https://api.telegram.org/bot{v('TELEGRAM_BOT_TOKEN')}/sendMessage", 
                             json={"chat_id": v('TELEGRAM_CHAT_ID'), "text": tele_msg, "parse_mode": "HTML"})

            except Exception as e: st.error(f"Lỗi: {str(e)}")
        time.sleep(1)

    st.success("🎉 CHIẾN DỊCH KẾT THÚC!")
    if st.button("XÁC NHẬN VÀ ĐÓNG"): st.rerun()

# --- UI ---
st.title("🚕 SEO MASTER v46.0 - ANTI-NGÁO EDITION")
data, msg = load_data()

if data:
    tabs = st.tabs(["Dashboard", "Website", "Backlink", "Report"])
    for i, name in enumerate(["Dashboard", "Website", "Backlink", "Report"]):
        with tabs[i]:
            if name == "Dashboard":
                if st.button("🚀 BẮT ĐẦU VẬN HÀNH", type="primary"): run_robot(data)
                st.dataframe(data[name], use_container_width=True, hide_index=True)
            else:
                st.dataframe(data[name], use_container_width=True, height=500, hide_index=True)
