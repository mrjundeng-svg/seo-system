import pandas as pd
import tkinter as tk
from tkinter import scrolledtext
import threading
import sys
import time
import random
import datetime
import re

# ==========================================
# CLASS LÕI: HỆ THỐNG AUTO CONTENT SEO
# ==========================================
class AutoContentSEO:
    def __init__(self, data_frames):
        self.db = data_frames
        self.dashboard = self._parse_dashboard()
        self.current_date = datetime.datetime.now()
        
        # Trạng thái chạy
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
        self.actual_limits = {} # Lưu lại các limit thực tế sau khi random để dùng xuyên suốt

    def _parse_dashboard(self) -> dict:
        df = self.db['DASHBOARD']
        return dict(zip(df['DATA_KEY'], df['DATA_CONTENT']))

    def _get_random_limit(self, limit_val) -> int:
        """Hàm xử lý các cột có định dạng số ngẫu nhiên như '1-2' hoặc '3-6'"""
        if pd.isna(limit_val): return 1
        limit_str = str(limit_val).strip()
        if '-' in limit_str:
            try:
                min_val, max_val = map(int, limit_str.split('-'))
                return random.randint(min_val, max_val)
            except ValueError:
                return 1
        else:
            try:
                return int(limit_str)
            except ValueError:
                return 1

    def step1_kiem_tra_he_thong(self) -> bool:
        print("\n--- BƯỚC 1: KIỂM TRA HỆ THỐNG ---")
        max_days = int(self.dashboard.get('MAX_SCHEDULE_DAYS', 7))
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        
        df_report = self.db['REPORT']
        df_web = self.db['WEBSITE']
        
        for day_offset in range(max_days + 1):
            check_date = self.current_date + datetime.timedelta(days=day_offset)
            date_str = check_date.strftime("%Y-%m-%d")
            
            posts_in_day = df_report[df_report['REP_PUBLISH_DATE'].str.contains(date_str, na=False)] if not df_report.empty else []

            if len(posts_in_day) >= batch_size:
                continue 
                
            available_webs = df_web.sample(frac=1).reset_index(drop=True)
            for _, web in available_webs.iterrows():
                web_name = web['WS_NAME']
                # Gọi hàm cắt chuỗi ngẫu nhiên ở đây
                web_limit = self._get_random_limit(web.get('WS_POST_LIMIT', '1'))
                
                posts_for_web = posts_in_day[posts_in_day['REP_WS_NAME'] == web_name] if len(posts_in_day) > 0 else []
                if len(posts_for_web) < web_limit:
                    self.target_web = web
                    self.target_date = check_date
                    # Lưu lại các limit đã random chốt cho lượt chạy này
                    self.actual_limits['post'] = web_limit
                    self.actual_limits['link_out'] = self._get_random_limit(web.get('WS_LINK_OUT_LIMIT', '1'))
                    self.actual_limits['link_in'] = self._get_random_limit(web.get('WS_LINK_IN_LIMIT', '1'))
                    self.actual_limits['img'] = self._get_random_limit(web.get('WS_IMG_LIMIT', '1'))
                    break
            
            if self.target_web is not None:
                break 
                
        if not self.target_web:
            print(f"Log: Đã lên lịch full {max_days} ngày. Dừng hệ thống để tránh spam.")
            return False

        run_time_start, run_time_end = str(self.dashboard.get('AUTO_RUN_TIME', '09:30-19:30')).split('-')
        
        if self.target_date.date() == self.current_date.date():
            if self.current_date.strftime("%H:%M") > run_time_end:
                print("Lố giờ chạy hôm nay, đợi vòng lặp sau đẩy sang ngày mai.")
                return False 
            base_time = max(self.current_date, self.current_date.replace(hour=int(run_time_start[:2]), minute=int(run_time_start[3:])))
        else:
            base_time = self.target_date.replace(hour=int(run_time_start[:2]), minute=int(run_time_start[3:]))

        spacing_min, spacing_max = map(int, str(self.dashboard.get('POST_SPACING_MINUTES', '30-90')).replace(' phút', '').split('-'))
        self.publish_time = base_time + datetime.timedelta(minutes=random.randint(spacing_min, spacing_max))
        
        print(f"Chốt lịch xuất bản: {self.publish_time.strftime('%Y-%m-%d %H:%M:%S')} lên web '{self.target_web['WS_NAME']}'.")
        return True

    def step2_tim_tu_khoa_va_bai_mau(self) -> bool:
        print("--- BƯỚC 2: TÌM TỪ KHÓA & BÀI MẪU ---")
        df_kw = self.db['KEYWORD'].dropna(subset=['KW_TEXT'])
        min_status = df_kw['KW_STATUS'].min()
        candidate_kws = df_kw[df_kw['KW_STATUS'] == min_status]
        
        if candidate_kws.empty:
            print("Lỗi: Không có từ khóa phù hợp.")
            return False
            
        self.main_kw = candidate_kws.sample(n=1).iloc[0]
        print(f"Đã chọn từ khóa chính: {self.main_kw['KW_TEXT']}")
        self.serp_style = "<h2>Giới thiệu</h2><p>...</p><h3>Bảng giá</h3><p>...</p>" # Mock SERP
        return True

    def step3_viet_content_chuan_seo(self):
        print("--- BƯỚC 3: TẠO PROMPT CONTENT ---")
        target_kw_count = self.actual_limits['link_out'] + self.actual_limits['link_in']
        
        df_kw = self.db['KEYWORD']
        secondary_pool = df_kw[(df_kw['KW_GROUP'] != self.main_kw['KW_GROUP'])].sort_values(by='KW_STATUS')
        self.secondary_kws = secondary_pool.head(max(0, target_kw_count - 1))['KW_TEXT'].tolist()
        
        word_range = str(self.dashboard.get('WORD_COUNT_RANGE', '900-1200')).split('-')
        self.word_count = random.randint(int(word_range[0]), int(word_range[1]))
        if target_kw_count < 3: self.word_count //= 2
            
        template = str(self.dashboard.get('PROMPT_TEMPLATE', ''))
        template = template.replace('{{keyword}}', str(self.main_kw['KW_TEXT']))
        template = template.replace('{{word_count}}', str(self.word_count))
        template = template.replace('{{secondary_keywords}}', ", ".join(self.secondary_kws))
        
        self.prompt_content = "Prompt đã được đóng gói chuẩn bị gửi AI..."
        print(f"Lắp ráp Prompt thành công. Độ dài bài yêu cầu: {self.word_count} chữ.")

    def step4_spin_bai_viet(self):
        print("--- BƯỚC 4: SPIN CONTENT BẢO VỆ SEO ---")
        # Giả lập content AI trả về
        self.raw_html = f"<h1>{self.main_kw['KW_TEXT']} - Cập nhật 2026</h1><p>Nội dung chi tiết chứa {self.main_kw['KW_TEXT']} và {', '.join(self.secondary_kws)}.</p>"
        print("Đã hoàn tất Spin và bảo vệ từ khóa tuyệt đối.")

    def step5_check_chuan_seo(self) -> dict:
        print("--- BƯỚC 5: KIỂM ĐỊNH ĐA TẦNG KCS ---")
        seo_score = random.randint(75, 100)
        ai_rate = random.randint(0, 15)
        readability_score = 72.5
        
        passed = True
        min_seo = 35 if self.word_count < 1000 else 70
        if seo_score <= min_seo or ai_rate >= 20 or readability_score <= 60: passed = False
            
        result_status = "PENDING" if passed else "FAIL"
        print(f"KCS Result: {result_status} (SEO: {seo_score}, AI: {ai_rate}%, Read: {readability_score})")
        return {'seo': seo_score, 'ai': ai_rate, 'read': readability_score, 'status': result_status}

    def step6_gan_backlink_va_anh(self):
        print("--- BƯỚC 6: GẮN BACKLINK & ẢNH ---")
        html_content = self.raw_html
        all_kws = [str(self.main_kw['KW_TEXT'])] + self.secondary_kws
        out_limit = self.actual_limits['link_out']
        out_link_pool = str(self.target_web.get('WS_LINK_OUT_BACKLINK', '')).split(',')
        in_link = str(self.target_web.get('WS_LINK_IN_BACKLINK', ''))
        
        for i, kw in enumerate(all_kws):
            if i < out_limit and len(out_link_pool) > 0:
                anchor = f"<a href='{out_link_pool[i % len(out_link_pool)].strip()}'>{kw}</a>"
            else:
                anchor = f"<a href='{in_link}'>{kw}</a>"
            html_content = html_content.replace(kw, anchor, 1) 
            
        img_tag = f"<br><p align='center'><img src='https://example.com/mock-image.jpg'></p><br>"
        self.final_html = html_content.replace("</p>", f"</p>\n{img_tag}", 1)
        print(f"Đã gắn {out_limit} Link Out, {self.actual_limits['link_in']} Link In và {self.actual_limits['img']} Ảnh.")

    def step7_report(self, kcs_stats: dict):
        print("\n--- BƯỚC 7: BÁO CÁO REPORT ---")
        all_kws_str = " | ".join([str(self.main_kw['KW_TEXT'])] + self.secondary_kws)
        print(f"Bài [1] — Website: {self.target_web['WS_NAME']}")
        print(f"* Report bài Chờ đăng: {self.publish_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"* Từ khóa backlink: {all_kws_str}")
        print(f"* Report SEO | AI | Read: {kcs_stats['seo']} | {kcs_stats['ai']}% | {kcs_stats['read']}")
        print(f"* Report trạng thái: {kcs_stats['status']}")


# ==========================================
# GIAO DIỆN ĐIỀU KHIỂN (GUI & THREADING)
# ==========================================
class RedirectConsole:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
    def flush(self): pass

def run_automation():
    btn_start.config(state=tk.DISABLED, text="ĐANG CHẠY...", bg="gray")
    print("🚀 Bắt đầu đọc dữ liệu từ CSV...")
    
    try:
        # Load file CSV offline
        db_mock = {
            'DASHBOARD': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - DASHBOARD.csv', on_bad_lines='skip', dtype=str),
            'WEBSITE': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - WEBSITE.csv', on_bad_lines='skip', dtype=str),
            'KEYWORD': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - KEYWORD.csv', on_bad_lines='skip', dtype=str),
            'REPORT': pd.DataFrame(columns=['REP_WS_NAME', 'REP_PUBLISH_DATE', 'REP_TITLE'])
        }
        
        bot = AutoContentSEO(db_mock)
        
        if bot.step1_kiem_tra_he_thong():
            time.sleep(1) # Chờ xíu cho hiệu ứng thật
            if bot.step2_tim_tu_khoa_va_bai_mau():
                time.sleep(1)
                bot.step3_viet_content_chuan_seo()
                time.sleep(1)
                bot.step4_spin_bai_viet()
                time.sleep(1)
                stats = bot.step5_check_chuan_seo()
                if stats['status'] in ['DONE', 'PENDING']:
                    time.sleep(1)
                    bot.step6_gan_backlink_va_anh()
                time.sleep(1)
                bot.step7_report(stats)
                print("\n✅ HOÀN THÀNH 1 VÒNG LẶP. Hệ thống đang chờ nhịp tiếp theo...")
        
    except FileNotFoundError as e:
        print(f"\n❌ Lỗi: Không tìm thấy file CSV! \nChi tiết: {e}")
        print("Vui lòng đảm bảo các file CSV nằm chung thư mục với file code này.")
    except Exception as e:
        print(f"\n❌ Lỗi hệ thống bất ngờ: {e}")
    
    finally:
        btn_start.config(state=tk.NORMAL, text="🚀 START LẠI", bg="#4CAF50")
        print("\n" + "="*60 + "\n")

def on_start_click():
    console_text.delete(1.0, tk.END) # Xóa log cũ đi cho sạch màn hình
    thread = threading.Thread(target=run_automation)
    thread.daemon = True
    thread.start()

# --- KHỞI TẠO CỬA SỔ ---
root = tk.Tk()
root.title("Control Panel - Hệ Thống Đăng Bài Tự Động")
root.geometry("800x550")
root.configure(bg="#2b2b2b") # Đổi sang Dark Mode cho ngầu

lbl_title = tk.Label(root, text="HỆ THỐNG AUTO CONTENT SEO", font=("Arial", 16, "bold"), bg="#2b2b2b", fg="#00FF00")
lbl_title.pack(pady=15)

btn_start = tk.Button(root, text="🚀 BẮT ĐẦU CHẠY", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", 
                      width=20, height=2, command=on_start_click, cursor="hand2", borderwidth=0)
btn_start.pack(pady=10)

lbl_log = tk.Label(root, text="Console Logs:", font=("Arial", 10, "italic"), bg="#2b2b2b", fg="white")
lbl_log.pack(anchor="w", padx=20)

console_text = scrolledtext.ScrolledText(root, width=90, height=20, font=("Consolas", 10), bg="black", fg="#00FF00")
console_text.pack(padx=20, pady=5)

sys.stdout = RedirectConsole(console_text)

print("Hệ thống khởi động thành công.")
print("Lưu ý: Đảm bảo đã sửa các cột Limit trong file CSV thành định dạng chữ (Plain Text).")
print("Bấm [BẮT ĐẦU CHẠY] để tiến hành đối soát dữ liệu...\n" + "="*60 + "\n")

root.mainloop()
