import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import time
import random
import datetime

# --- CẤU HÌNH TRANG WEB ---
st.set_page_config(page_title="Hệ Thống Auto Content SEO", layout="wide")

# --- ID CỦA FILE GOOGLE SHEET ---
# Bạn thay bằng ID file Google Sheet của bạn vào đây
SHEET_ID = '1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw' 

# ==========================================
# HÀM KẾT NỐI & KÉO DỮ LIỆU TỪ GOOGLE SHEETS
# ==========================================
@st.cache_data(ttl=10)
def load_data_from_gsheets():
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Đọc cấu hình bảo mật từ Streamlit Secrets
        s_creds = dict(st.secrets["gcp_service_account"])
        creds = Credentials.from_service_account_info(s_creds, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Mở file Sheet
        spreadsheet = client.open_by_key(SHEET_ID)
        
        # Lấy tất cả các tab cần thiết
        db = {}
        tabs_to_fetch = ['DASHBOARD', 'WEBSITE', 'IMAGE', 'SPIN', 'KEYWORD', 'REPORT']
        
        for tab_name in tabs_to_fetch:
            worksheet = spreadsheet.worksheet(tab_name)
            data = worksheet.get_all_values()
            
            if data:
                headers = data[0]
                df = pd.DataFrame(data[1:], columns=headers)
                db[tab_name] = df
            else:
                db[tab_name] = pd.DataFrame()
                
        return db
        
    except Exception as e:
        st.error(f"Lỗi kết nối Google Sheets: {e}")
        return None

# ==========================================
# CLASS LÕI: LOGIC AUTO CONTENT SEO
# ==========================================
class AutoContentSEO:
    def __init__(self, data_frames):
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.current_date = datetime.datetime.now()
        
        self.target_date = None
        self.target_web = None
        self.main_kw = None
        self.secondary_kws = []
        self.publish_time = None
        self.actual_limits = {} 

    def _parse_dashboard(self) -> dict:
        df = self.db.get('DASHBOARD', pd.DataFrame())
        if df.empty: return {}
        return dict(zip(df['DATA_KEY'], df['DATA_CONTENT']))

    def _get_random_limit(self, limit_val) -> int:
        if pd.isna(limit_val): return 1
        limit_str = str(limit_val).strip()
        if '-' in limit_str:
            try:
                min_val, max_val = map(int, limit_str.split('-'))
                return random.randint(min_val, max_val)
            except ValueError: return 1
        else:
            try: return int(limit_str)
            except ValueError: return 1

    def step1_kiem_tra_he_thong(self, log_placeholder) -> bool:
        log_placeholder.info("--- BƯỚC 1: KIỂM TRA HỆ THỐNG ---")
        max_days = int(self.dashboard.get('MAX_SCHEDULE_DAYS', 7))
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        
        df_report = self.db.get('REPORT', pd.DataFrame())
        df_web = self.db.get('WEBSITE', pd.DataFrame())
        
        if df_web.empty:
            log_placeholder.error("Lỗi: Tab WEBSITE trống hoặc không kéo được dữ liệu!")
            return False

        for day_offset in range(max_days + 1):
            check_date = self.current_date + datetime.timedelta(days=day_offset)
            date_str = check_date.strftime("%Y-%m-%d")
            
            if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns:
                posts_in_day = df_report[df_report['REP_PUBLISH_DATE'].astype(str).str.contains(date_str, na=False)]
            else:
                posts_in_day = []

            if len(posts_in_day) >= batch_size: 
                continue 
                
            available_webs = df_web.sample(frac=1).reset_index(drop=True)
            for _, web in available_webs.iterrows():
                web_limit = self._get_random_limit(web.get('WS_POST_LIMIT', '1'))
                
                if len(posts_in_day) > 0 and 'REP_WS_NAME' in df_report.columns:
                    posts_for_web = posts_in_day[posts_in_day['REP_WS_NAME'] == web['WS_NAME']]
                else:
                    posts_for_web = []
                    
                if len(posts_for_web) < web_limit:
                    self.target_web = web
                    self.target_date = check_date
                    self.actual_limits['link_out'] = self._get_random_limit(web.get('WS_LINK_OUT_LIMIT', '1'))
                    break
                    
            if self.target_web is not None: 
                break 
                
        if not self.target_web:
            log_placeholder.error("Đã lên lịch full ngày hoặc full web. Dừng hệ thống.")
            return False

        run_time_raw = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30'))
        run_time_start, run_time_end = run_time_raw.split('-') if '-' in run_time_raw else ('09:30', '19:30')
        
        base_time = self.target_date.replace(hour=int(run_time_start[:2]), minute=int(run_time_start[3:]))

        spacing_raw = str(self.dashboard.get('POST_SPACING_MINUTES', '30-90')).replace(' phút', '')
        spacing_min, spacing_max = map(int, spacing_raw.split('-')) if '-' in spacing_raw else (30, 90)
        
        self.publish_time = base_time + datetime.timedelta(minutes=random.randint(spacing_min, spacing_max))
        log_placeholder.success(f"Chốt xuất bản: {self.publish_time.strftime('%Y-%m-%d %H:%M:%S')} - Web: {self.target_web.get('WS_NAME', 'Unknown')}")
        return True

    def step2_to_step6_mock(self, log_placeholder):
        log_placeholder.info("Đang xử lý Bước 2 -> Bước 6 (Tìm Keyword, Spin Content, Check KCS...)")
        df_kw = self.db.get('KEYWORD', pd.DataFrame())
        
        if df_kw.empty or 'KW_TEXT' not in df_kw.columns:
            return {"Lỗi": "Tab KEYWORD trống hoặc sai định dạng"}
            
        df_kw_clean = df_kw.dropna(subset=['KW_TEXT'])
        if 'KW_STATUS' in df_kw_clean.columns:
            # Ép kiểu KW_STATUS về số để tìm từ khóa dùng ít nhất (min)
            df_kw_clean['KW_STATUS'] = pd.to_numeric(df_kw_clean['KW_STATUS'], errors='coerce').fillna(0)
            min_status = df_kw_clean['KW_STATUS'].min()
            candidate_kws = df_kw_clean[df_kw_clean['KW_STATUS'] == min_status]
        else:
            candidate_kws = df_kw_clean
            
        self.main_kw = candidate_kws.sample(n=1).iloc[0]
        
        time.sleep(2) # Giả lập chờ AI viết bài
        
        return {
            'REP_WS_NAME': self.target_web.get('WS_NAME', ''),
            'REP_TITLE': f"{str(self.main_kw['KW_TEXT']).title()} - Thông tin cập nhật",
            'REP_KW_1': self.main_kw['KW_TEXT'],
            'REP_SEO_SCORE': str(random.randint(75, 100)),
            'AI_DETECTOR_RATE': str(random.randint(0, 15)),
            'READABILITY_SCORE': str(random.randint(60, 90)),
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_POST_URL': "https://pending...",
            'REP_RESULT': "PENDING"
        }

# ==========================================
# GIAO DIỆN WEB (UI)
# ==========================================
st.title("🚀 HỆ THỐNG AUTO CONTENT SEO")
st.markdown("---")

# 1. KÉO DỮ LIỆU TỪ GOOGLE SHEETS
db_mock = load_data_from_gsheets()

# 2. KHU VỰC BẢNG REPORT
st.subheader("📊 BẢNG REPORT DỮ LIỆU (CHỈ XEM)")
if db_mock is not None and not db_mock.get('REPORT', pd.DataFrame()).empty:
    st.dataframe(db_mock['REPORT'], use_container_width=True, hide_index=True)
else:
    st.info("Bảng Report hiện đang trống hoặc chưa có dữ liệu bài viết.")

st.markdown("---")

# 3. KHU VỰC ĐIỀU KHIỂN
st.subheader("⚙️ ĐIỀU KHIỂN HỆ THỐNG")

col1, col2 = st.columns([1, 3])

with col1:
    start_btn = st.button("🚀 BẮT ĐẦU CHẠY", type="primary", use_container_width=True)

with col2:
    log_container = st.container()
    
# Logic khi bấm nút Bắt Đầu Chạy
if start_btn:
    if db_mock is None:
        st.error("Dữ liệu lỗi hoặc chưa kết nối được Google Sheets. Không thể khởi động!")
    else:
        with log_container:
            status_text = st.empty()
            status_text.info("Đang khởi động tiến trình...")
            
            bot = AutoContentSEO(db_mock)
            
            if bot.step1_kiem_tra_he_thong(status_text):
                new_data = bot.step2_to_step6_mock(status_text)
                if "Lỗi" in new_data:
                    status_text.error(new_data["Lỗi"])
                else:
                    status_text.success(f"✅ Đã tạo thành công bài: {new_data.get('REP_TITLE', '')}")
                    
                    st.write("Dữ liệu bài viết mới sinh ra (Sẵn sàng chờ hàm ghi vào Sheet):")
                    st.json(new_data)
                    
                    st.balloons()
