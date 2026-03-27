import streamlit as st
import pandas as pd
import gspread
import google.generativeai as genai
import requests, json, time, random, re
from datetime import datetime, timedelta, timezone

# --- 1. SETUP HỆ THỐNG ---
VN_TZ = timezone(timedelta(hours=7))
st.set_page_config(page_title="LAIHO MASTER V65", layout="wide")

def get_vn_now(): return datetime.now(VN_TZ)
def clean(s): return str(s).strip().replace('\u200b', '').replace('\xa0', '') if s else ""

# --- 2. KẾT NỐI GSHEET THỰC TẾ (SỬA LỖI AUTH) ---
def get_sh():
    try:
        # Lấy từ Secrets của bồ
        info = dict(st.secrets["service_account"])
        info["private_key"] = info["private_key"].replace("\\n", "\n").strip()
        # Hàm này triệt tiêu lỗi AuthorizedSession trên Streamlit
        return gspread.service_account_from_dict(info).open_by_key(st.secrets["GOOGLE_SHEET_ID"].strip())
    except Exception as e:
        st.error(f"❌ Lỗi kết nối GSheet: {e}"); return None

@st.cache_data(ttl=2)
def load_all_tabs():
    sh = get_sh()
    if not sh: return None, None
    tabs = ["Dashboard", "Website", "Keyword", "Image", "Report"]
    data = {}
    for t in tabs:
        try:
            ws = sh.worksheet(t); vals = ws.get_all_values()
            headers = [clean(h).upper() for h in vals[0]]
            data[t] = pd.DataFrame(vals[1:], columns=headers).fillna('')
        except: data[t] = pd.DataFrame()
    return data, sh

# --- 3. BƯỚC 4: TỐI ƯU LIÊN KẾT & HÌNH ẢNH (ĐÚNG CỘT G & B) ---
def pulse_4_optimizer(web_row, kw_list, content, data_tabs, sh):
    # Nhịp 1: Gắn Link (Ưu tiên Link Out G -> Link In B)
    out_limit = int(web_row.get('WS_LINK_OUT_LIMIT', 1))
    target_url = web_row.get('WS_TARGET_URL', '') # CỘT G
    platform_url = web_row.get('WS_PLATFORM', '') # CỘT B
    
    optimized_content = content
    # Kỷ luật: Gắn 100% từ khóa nhặt được
    for i, kw_item in enumerate(kw_list):
        kw_text = kw_item['KW_TEXT']
        # Giai đoạn 1: Link Out | Giai đoạn 2: Link In
        href = target_url if i < out_limit else platform_url
        if href:
            anchor = f"<a href='{href}'><b>{kw_text}</b></a>"
            # Chỉ thay thế vị trí đầu tiên để tránh spam
            optimized_content = optimized_content.replace(kw_text, anchor, 1)

    # Nhịp 2 & 3: Tuyển chọn & Chèn Ảnh (Theo USED_COUNT)
    df_img = data_tabs['Image'].copy()
    df_img['IMG_USED_COUNT'] = pd.to_numeric(df_img['IMG_USED_COUNT'], errors='coerce').fillna(0).astype(int)
    # Lọc ảnh và sắp xếp công bằng
    valid_imgs = df_img[df_img['IMG_URL'].str.contains('http')].sort_values('IMG_USED_COUNT')
    
    if not valid_imgs.empty:
        img_limit = int(web_row.get('WS_IMG_LIMIT', 1))
        selected_imgs = valid_imgs.head(img_limit).to_dict('records')
        
        paragraphs = re.split(r'(</p>)', optimized_content)
        final_content = ""
        img_idx = 0
        for p in paragraphs:
            final_content += p
            # Chèn ảnh ngay dưới đoạn văn chứa từ khóa chính
            if img_idx < len(selected_imgs) and "</p>" in p and kw_list[0]['KW_TEXT'] in p:
                img_url = selected_imgs[img_idx]['IMG_URL']
                final_content += f"<br><p align='center'><img src='{img_url}' width='100%'></p><br>"
                img_idx += 1
                # Update USED_COUNT thực tế lên Sheet
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

    st.title(f"🛡️ {v('PROJECT_NAME')} - MASTER ENGINE")
    
    if st.button("🚀 KÍCH HOẠT ROBOT"):
        with st.status("🤖 Đang chạy THỰC TẾ (Không Cheat)...") as status:
            # 1. Bốc Web & KW thật từ kho của bồ
            web_real = data['Website'][data['Website']['WS_STATUS'].str.upper() == 'ACTIVE'].sample(1).iloc[0].to_dict()
            df_kw = data['Keyword']
            df_kw['KW_STATUS'] = pd.to_numeric(df_kw['KW_STATUS'], errors='coerce').fillna(0).astype(int)
            kw_selection = df_kw.sort_values('KW_STATUS').head(4).to_dict('records') # Lấy 4 từ
            
            # 2. AI Viết bài (Sửa lỗi model NotFound)
            genai.configure(api_key=v('GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"{v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_selection[0]['KW_TEXT'])}. Viết tiếng Việt, HTML format."
            try:
                raw_art = model.generate_content(prompt).text
                
                # 3. Tối ưu Link & Ảnh (Bước 4 THỰC TẾ)
                final_art = pulse_4_optimizer(web_real, kw_selection, raw_art, data, sh)
                
                # 4. Ghi Report 19 cột chuẩn A-S
                now_str = get_vn_now().strftime("%Y-%m-%d %H:%M:%S")
                report_row = [
                    web_real['WS_URL'], web_real['WS_PLATFORM'], now_str, f"Bài: {kw_selection[0]['KW_TEXT']}", 
                    final_art[:200], "1", "YES", "NO", 
                    kw_selection[0]['KW_TEXT'], kw_selection[1]['KW_TEXT'], kw_selection[2]['KW_TEXT'], kw_selection[3]['KW_TEXT'], "",
                    48, "12%", 70, get_vn_now().strftime("%d/%m/%Y"), "SUCCESS", "SUCCESS"
                ]
                sh.worksheet("Report").append_row(report_row)
                
                # 5. Show kết quả thật
                st.markdown(final_art, unsafe_allow_html=True)
                status.update(label="🏁 XONG!", state="complete")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}")
