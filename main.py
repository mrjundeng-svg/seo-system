import pandas as pd
import random
import datetime
import re
import requests
from typing import List, Dict, Tuple

class AutoContentSEO:
    def __init__(self, data_frames: Dict[str, pd.DataFrame]):
        """
        Khởi tạo hệ thống với dữ liệu từ các tab Google Sheets (được parse thành pandas DataFrame)
        data_frames = {'DASHBOARD': df_dash, 'WEBSITE': df_web, 'KEYWORD': df_kw, ...}
        """
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.current_date = datetime.datetime.now()
        
        # Biến lưu trữ trạng thái chạy của 1 luồng bài viết
        self.target_date = None
        self.target_web = None
        self.main_kw = None
        self.secondary_kws = []
        self.serp_style = ""
        self.word_count = 0
        self.prompt_content = ""
        self.raw_html = ""
        self.final_html = ""
        self.publish_time = None

    def _parse_dashboard(self) -> dict:
        """Hàm phụ trợ chuyển tab DASHBOARD thành dictionary cho dễ gọi"""
        df = self.db['DASHBOARD']
        return dict(zip(df['DATA_KEY'], df['DATA_CONTENT']))

    # ==========================================
    # BƯỚC 1: KIỂM TRA HỆ THỐNG
    # ==========================================
    def step1_kiem_tra_he_thong(self) -> bool:
        print("--- BƯỚC 1: KIỂM TRA HỆ THỐNG ---")
        max_days = int(self.dashboard.get('MAX_SCHEDULE_DAYS', 7))
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        
        df_report = self.db['REPORT']
        df_web = self.db['WEBSITE']
        
        # Nhịp 1 & 2: Thiết lập ranh giới & Đối soát Giới hạn
        for day_offset in range(max_days + 1):
            check_date = self.current_date + datetime.timedelta(days=day_offset)
            date_str = check_date.strftime("%Y-%m-%d")
            
            # Tính tổng bài trong Ngày X
            if not df_report.empty and 'REP_PUBLISH_DATE' in df_report.columns:
                posts_in_day = df_report[df_report['REP_PUBLISH_DATE'].str.contains(date_str, na=False)]
            else:
                posts_in_day = pd.DataFrame()

            if len(posts_in_day) >= batch_size:
                continue # Ngày này đã đầy, nhảy sang ngày tiếp theo
                
            # Random chọn web còn slot
            available_webs = df_web.sample(frac=1).reset_index(drop=True)
            for _, web in available_webs.iterrows():
                web_name = web['WS_NAME']
                web_limit = int(web.get('WS_POST_LIMIT', 1)) # Cần ép kiểu cẩn thận từ sheet thực tế
                
                posts_for_web = posts_in_day[posts_in_day['REP_WS_NAME'] == web_name] if not posts_in_day.empty else []
                if len(posts_for_web) < web_limit:
                    self.target_web = web
                    self.target_date = check_date
                    break
            
            if self.target_web is not None:
                break # Đã chốt được Web và Ngày
                
        if not self.target_web:
            print(f"Log: Đã lên lịch full {max_days} ngày hoặc các web đều full. Dừng hệ thống để tránh spam.")
            return False

        # Nhịp 3: Khởi tạo Thời gian đăng tự nhiên
        run_time_start, run_time_end = self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30').split('-')
        
        if self.target_date.date() == self.current_date.date():
            # Xử lý chống xuyên không
            if self.current_date.strftime("%H:%M") > run_time_end:
                print("Lố giờ chạy hôm nay, đẩy sang ngày mai.")
                return False # Trong thực tế sẽ gọi đệ quy hoặc loop sang ngày mai
            
            base_time = max(self.current_date, self.current_date.replace(hour=int(run_time_start[:2]), minute=int(run_time_start[3:])))
        else:
            base_time = self.target_date.replace(hour=int(run_time_start[:2]), minute=int(run_time_start[3:]))

        # Tính toán giờ đăng thực tế (Giả lập khoảng cách ngẫu nhiên)
        spacing_min, spacing_max = map(int, self.dashboard.get('POST_SPACING_MINUTES', '30-90').replace(' phút', '').split('-'))
        random_minutes = random.randint(spacing_min, spacing_max)
        self.publish_time = base_time + datetime.timedelta(minutes=random_minutes)
        
        # Nhịp 4: Final Decision
        publish_time_str = self.publish_time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Chốt lịch xuất bản: {publish_time_str} lên web {self.target_web['WS_NAME']}. Khởi động Bước 2.")
        return True

    # ==========================================
    # BƯỚC 2: TÌM TỪ KHÓA & BÀI MẪU
    # ==========================================
    def step2_tim_tu_khoa_va_bai_mau(self) -> bool:
        print("--- BƯỚC 2: TÌM TỪ KHÓA & BÀI MẪU ---")
        df_kw = self.db['KEYWORD'].dropna(subset=['KW_TEXT'])
        
        # Nhịp 1: Min-Status
        min_status = df_kw['KW_STATUS'].min()
        candidate_kws = df_kw[df_kw['KW_STATUS'] == min_status]
        
        if candidate_kws.empty:
            print("Lỗi: Không có từ khóa phù hợp.")
            return False
            
        selected_kw_row = candidate_kws.sample(n=1).iloc[0]
        self.main_kw = selected_kw_row
        print(f"Đã chọn từ khóa chính: {self.main_kw['KW_TEXT']}")

        # Nhịp 2: Săn văn phong 2 tầng (Mô phỏng)
        # Tầng 1: SERPAPI (Giả lập gọi API và lấy Heading)
        competitors = self.dashboard.get('COMPETITOR_LIST', '').split(',')
        print("Đang quét Google lấy bố cục (Mock)...")
        # Logic thực tế sẽ request SERPAPI, check HTTP 200, bóc tách thẻ H1, H2, H3
        self.serp_style = "<h2>Giới thiệu dịch vụ</h2><p>...</p><h3>Bảng giá</h3><p>...</p>"
        
        if not self.serp_style:
            print("Kịch bản Thất bại: Không tìm được bài mẫu ổn định.")
            return False
            
        return True

    # ==========================================
    # BƯỚC 3: VIẾT CONTENT CHUẨN SEO THEO PROMPT
    # ==========================================
    def step3_viet_content_chuan_seo(self):
        print("--- BƯỚC 3: TẠO PROMPT CONTENT ---")
        # Nhịp 1: Tính toán chỉ tiêu và word count
        ws_link_out = int(self.target_web.get('WS_LINK_OUT_LIMIT', 1))
        # Giả sử WS_POST_LIMIT ở đây đóng vai trò tính Keyword content như trong Rule
        ws_post_limit = int(self.target_web.get('WS_POST_LIMIT', 1)) 
        target_kw_count = ws_post_limit + ws_link_out
        
        df_kw = self.db['KEYWORD']
        # Tìm từ khóa bổ trợ (Cùng Topic, khác Group - Trong file KEYWORD mẫu ko có KW_TOPIC, ta lấy tạm khác Group)
        secondary_pool = df_kw[(df_kw['KW_GROUP'] != self.main_kw['KW_GROUP'])].sort_values(by='KW_STATUS')
        self.secondary_kws = secondary_pool.head(target_kw_count - 1)['KW_TEXT'].tolist()
        
        word_range = self.dashboard.get('WORD_COUNT_RANGE', '900-1200').split('-')
        self.word_count = random.randint(int(word_range[0]), int(word_range[1]))
        if target_kw_count < 3:
            self.word_count = self.word_count // 2
            
        # Nhịp 2: Lắp ghép Prompt
        req_keys = ['PROMPT_TEMPLATE', 'PROMPT_CONTENT_STRATEGY', 'PROMPT_KEYWORD_SEARCH', 'PROMPT_SERP_STYLE', 'PROMPT_SEO_GLOBAL_RULE', 'PROMPT_AI_HUMANIZER']
        for key in req_keys:
            if not self.dashboard.get(key):
                raise ValueError(f"Hệ thống đình chỉ do thiếu dữ liệu cốt lõi: {key}")
                
        template = str(self.dashboard['PROMPT_TEMPLATE'])
        template = template.replace('{{keyword}}', str(self.main_kw['KW_TEXT']))
        template = template.replace('{{word_count}}', str(self.word_count))
        template = template.replace('{{secondary_keywords}}', ", ".join(self.secondary_kws))
        
        # Nối chuỗi phân tầng ép kỷ luật AI
        chuoi_ghep_1 = f"{template}\n\n{self.dashboard['PROMPT_CONTENT_STRATEGY']}\n\n{self.dashboard['PROMPT_KEYWORD_SEARCH']}\n\nDựa vào sườn này: {self.serp_style}\n\n{self.dashboard['PROMPT_SERP_STYLE']}"
        
        self.prompt_content = f"{chuoi_ghep_1}\n\nQUY TẮC TỐI THƯỢNG:\n{self.dashboard['PROMPT_SEO_GLOBAL_RULE']}\n\nHƯỚNG DẪN CUỐI CÙNG:\n{self.dashboard['PROMPT_AI_HUMANIZER']}"
        print("Lắp ráp Prompt thành công.")

    # ==========================================
    # BƯỚC 4: SPIN BÀI VIẾT (BẢO VỆ TỪ KHÓA)
    # ==========================================
    def step4_spin_bai_viet(self):
        print("--- BƯỚC 4: SPIN CONTENT BẢO VỆ SEO ---")
        # Giả lập gọi API Gemini bằng Prompt
        print(f"Calling LLM API (Gemini)... (Target words: {self.word_count})")
        # raw_content = call_gemini_api(self.prompt_content)
        raw_content = f"<h1>{self.main_kw['KW_TEXT']} - Bảng giá và dịch vụ cập nhật</h1><p>Nội dung thô chưa spin chứa từ {self.main_kw['KW_TEXT']} và {', '.join(self.secondary_kws)}</p>"
        
        # Nhịp 2 & 3: Spin đa tầng & Iron Shield
        all_kws = [str(self.main_kw['KW_TEXT'])] + self.secondary_kws
        
        # Kỹ thuật Iron Shield: Tạm thời mã hóa từ khóa SEO trước khi spin
        shielded_content = raw_content
        kw_mapping = {}
        for idx, kw in enumerate(all_kws):
            placeholder = f"[[SEO_KW_{idx}]]"
            kw_mapping[placeholder] = kw
            # CẤM biến đổi ký tự, phân biệt hoa thường khi Regex
            shielded_content = re.sub(rf"(?i)\b{re.escape(kw)}\b", placeholder, shielded_content)
            
        # Thực hiện thuật toán Spin trên shielded_content (Giả lập thay từ đồng nghĩa từ tab SPIN)
        shielded_content = shielded_content.replace("Nội dung", "Thông tin") 
        
        # Giải mã Iron Shield trả lại nguyên trạng 100% từ khóa
        for placeholder, kw in kw_mapping.items():
            shielded_content = shielded_content.replace(placeholder, kw)
            
        self.raw_html = shielded_content
        print("Đã hoàn tất Spin và bảo vệ từ khóa tuyệt đối.")

    # ==========================================
    # BƯỚC 5: CHECK CHUẨN SEO
    # ==========================================
    def step5_check_chuan_seo(self) -> dict:
        print("--- BƯỚC 5: KIỂM ĐỊNH ĐA TẦNG KCS ---")
        # Mô phỏng API chấm điểm
        seo_score = random.randint(75, 100) # DataForSEO API mock
        ai_rate = random.randint(0, 15)     # Sapling API mock
        
        # Tính Readability nội bộ theo Flesch Việt hóa (Mô phỏng)
        asl = 15.0
        asw = 1.2
        readability_score = 206.835 - (1.015 * asl) - (84.6 * asw)
        
        # Nhịp 2: KCS
        passed = True
        min_seo = 35 if self.word_count < int(self.dashboard.get('WORD_COUNT_RANGE', '900-1200').split('-')[1]) else 70
        
        if seo_score <= min_seo or ai_rate >= 20 or readability_score <= 60:
            passed = False
            
        result_status = "PENDING" if passed else "FAIL"
        print(f"KCS Result: {result_status} (SEO: {seo_score}, AI: {ai_rate}%, Read: {readability_score:.1f})")
        
        if passed:
            # Nhịp 3: Đồng bộ & Hồi sinh (Cập nhật tab KEYWORD trạng thái + 1)
            # Cập nhật trong db_frames của class
            pass 
            
        return {
            'seo': seo_score,
            'ai': ai_rate,
            'read': round(readability_score, 1),
            'status': result_status
        }

    # ==========================================
    # BƯỚC 6: GẮN BACKLINK VÀ ẢNH
    # ==========================================
    def step6_gan_backlink_va_anh(self):
        print("--- BƯỚC 6: GẮN BACKLINK & ẢNH ---")
        html_content = self.raw_html
        all_kws = [str(self.main_kw['KW_TEXT'])] + self.secondary_kws
        
        # Nhịp 1: Gắn Backlink 100%
        out_limit = int(self.target_web.get('WS_LINK_OUT_LIMIT', 1))
        out_link_pool = str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',')
        in_link = str(self.target_web.get('WS_LINK_IN_BACKLINK', ''))
        
        for i, kw in enumerate(all_kws):
            # Kỷ luật thép: 100% tỷ lệ chuyển đổi
            if i < out_limit and len(out_link_pool) > 0:
                link = out_link_pool[i % len(out_link_pool)].strip()
                anchor = f"<a href='{link}'>{kw}</a>"
            else:
                anchor = f"<a href='{in_link}'>{kw}</a>"
                
            html_content = html_content.replace(kw, anchor, 1) # Chỉ replace lần đầu tiên xuất hiện
            
        # Nhịp 2 & 3: Tuyển chọn và chèn ảnh
        # Mô phỏng bốc ảnh từ Tab IMAGE (ít dùng nhất)
        selected_img_url = "https://example.com/mock-image.jpg"
        img_tag = f"<br><p align='center'><img src='{selected_img_url}'></p><br>"
        
        # Chèn ảnh vào sau thẻ đóng </p> đầu tiên
        html_content = html_content.replace("</p>", f"</p>\n{img_tag}", 1)
        
        self.final_html = html_content
        print("Đã hoàn tất gắn Backlink và Ảnh chuẩn SEO.")

    # ==========================================
    # BƯỚC 7: REPORT & CẢNH BÁO
    # ==========================================
    def step7_report(self, kcs_stats: dict):
        print("\n--- BƯỚC 7: CONSOLE REPORT ---")
        all_kws_str = " | ".join([str(self.main_kw['KW_TEXT'])] + self.secondary_kws)
        
        # Nhịp 1: Console
        console_msg = f"""Bài 1 —
* Dashboard yêu cầu: 1 / {self.dashboard.get('BATCH_SIZE')}
* Report lượt đăng ngày: 1 / {self.target_web.get('WS_POST_LIMIT')}
* Report bài Chờ đăng: {self.publish_time.strftime("%Y-%m-%d %H:%M:%S")}
* Website: {self.target_web['WS_NAME']}
* Website tên bài: {str(self.main_kw['KW_TEXT']).title()} - Dịch vụ
* Từ khóa backlink: {all_kws_str}
* Report SEO | AI | Read: {kcs_stats['seo']} | {kcs_stats['ai']}% | {kcs_stats['read']}
* Report trạng thái: {kcs_stats['status']}"""
        print(console_msg)
        
        # Nhịp 2: Ghi sổ (Thêm vào cuối Tab REPORT DataFrame)
        # pd.concat(...)
        
        # Nhịp 3: Báo cáo Telegram
        if kcs_stats['status'] in ['DONE', 'PENDING']:
            tele_msg = f"""🔔 {self.dashboard.get('PROJECT_NAME')}
📝 Tên bài: {str(self.main_kw['KW_TEXT']).title()}
🔗 Link bài: pending_url
🔑 Từ khóa: {all_kws_str}
📊 Chỉ số: SEO: {kcs_stats['seo']} | AI: {kcs_stats['ai']}% | Read: {kcs_stats['read']}
✅ Trạng thái: {kcs_stats['status']}
🧱 Ngày đăng: {self.publish_time.strftime("%Y-%m-%d %H:%M:%S")}
📈 Tiến độ tổng: 1 / {self.dashboard.get('BATCH_SIZE')}"""
            
            # bot_token = self.dashboard.get('TELEGRAM_BOT_TOKEN')
            # chat_id = self.dashboard.get('TELEGRAM_CHAT_ID')
            # requests.post(f"https://api.telegram.org/bot{bot_token}/sendMessage", data={'chat_id': chat_id, 'text': tele_msg})
            print("\nĐã đẩy log qua Telegram thành công!")

# ==========================================
# KHU VỰC CHẠY THỬ NGHIỆM (MOCK DATA)
# ==========================================
if __name__ == "__main__":
    # Giả lập Load dữ liệu từ CSV (Trong thực tế thay bằng gspread lấy từ Google Sheets)
    try:
        # Thay đường dẫn thư mục chứa file CSV của bạn
        db_mock = {
            'DASHBOARD': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - DASHBOARD.csv', on_bad_lines='skip'),
            'WEBSITE': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - WEBSITE.csv', on_bad_lines='skip'),
            'KEYWORD': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - KEYWORD.csv', on_bad_lines='skip'),
            'REPORT': pd.DataFrame(columns=['REP_WS_NAME', 'REP_PUBLISH_DATE', 'REP_TITLE']) # Report rỗng lúc đầu
        }
        
        # Khởi tạo tiến trình
        bot = AutoContentSEO(db_mock)
        
        if bot.step1_kiem_tra_he_thong():
            if bot.step2_tim_tu_khoa_va_bai_mau():
                bot.step3_viet_content_chuan_seo()
                bot.step4_spin_bai_viet()
                stats = bot.step5_check_chuan_seo()
                if stats['status'] in ['DONE', 'PENDING']:
                    bot.step6_gan_backlink_va_anh()
                bot.step7_report(stats)
                
    except FileNotFoundError:
        print("Lưu ý: Bạn cần đặt các file CSV cùng thư mục với script hoặc sửa lại đường dẫn để test cục bộ.")
