import pandas as pd
import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import sys
import time
import random
import datetime

# ==========================================
# CLASS LÕI: HỆ THỐNG AUTO CONTENT SEO 
# (Giữ nguyên logic xử lý data như bản trước)
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
        self.word_count = 0
        self.publish_time = None
        self.actual_limits = {} 

    def _parse_dashboard(self) -> dict:
        df = self.db['DASHBOARD']
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

    def step1_kiem_tra_he_thong(self) -> bool:
        print("\n--- BƯỚC 1: KIỂM TRA HỆ THỐNG ---")
        max_days = int(self.dashboard.get('MAX_SCHEDULE_DAYS', 7))
        batch_size = int(self.dashboard.get('BATCH_SIZE', 2))
        df_report = self.db['REPORT']
        df_web = self.db['WEBSITE']
        
        for day_offset in range(max_days + 1):
            check_date = self.current_date + datetime.timedelta(days=day_offset)
            date_str = check_date.strftime("%Y-%m-%d")
            posts_in_day = df_report[df_report['REP_PUBLISH_DATE'].astype(str).str.contains(date_str, na=False)] if not df_report.empty else []

            if len(posts_in_day) >= batch_size: continue 
                
            available_webs = df_web.sample(frac=1).reset_index(drop=True)
            for _, web in available_webs.iterrows():
                web_limit = self._get_random_limit(web.get('WS_POST_LIMIT', '1'))
                posts_for_web = posts_in_day[posts_in_day['REP_WS_NAME'] == web['WS_NAME']] if len(posts_in_day) > 0 else []
                if len(posts_for_web) < web_limit:
                    self.target_web = web
                    self.target_date = check_date
                    self.actual_limits['link_out'] = self._get_random_limit(web.get('WS_LINK_OUT_LIMIT', '1'))
                    break
            if self.target_web is not None: break 
                
        if not self.target_web:
            print(f"Log: Đã lên lịch full. Dừng hệ thống.")
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
        print(f"Chốt xuất bản: {self.publish_time.strftime('%Y-%m-%d %H:%M:%S')} - Web: {self.target_web['WS_NAME']}")
        return True

    def step2_to_step6_mock(self):
        """Gộp chạy nhanh các bước để test hiển thị lên Dashboard"""
        print("--- ĐANG CHẠY BƯỚC 2 -> BƯỚC 6 (Tạo Content, Spin, KCS, Backlink) ---")
        df_kw = self.db['KEYWORD'].dropna(subset=['KW_TEXT'])
        self.main_kw = df_kw[df_kw['KW_STATUS'] == df_kw['KW_STATUS'].min()].sample(n=1).iloc[0]
        
        seo_score = random.randint(75, 100)
        ai_rate = random.randint(0, 15)
        status = "PENDING"
        
        # Trả về data để nhét vào Report
        return {
            'REP_WS_NAME': self.target_web['WS_NAME'],
            'REP_TITLE': f"{str(self.main_kw['KW_TEXT']).title()} - Bảng giá 2026",
            'REP_KW_1': self.main_kw['KW_TEXT'],
            'REP_SEO_SCORE': seo_score,
            'AI_DETECTOR_RATE': ai_rate,
            'REP_PUBLISH_DATE': self.publish_time.strftime('%Y-%m-%d %H:%M'),
            'REP_RESULT': status
        }

# ==========================================
# GIAO DIỆN DASHBOARD (UI)
# ==========================================
class RedirectConsole:
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, string):
        self.text_widget.insert(tk.END, string)
        self.text_widget.see(tk.END)
    def flush(self): pass

class AppDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Dashboard - Auto Content SEO")
        self.root.geometry("1100x700")
        self.root.configure(bg="#f4f6f9")
        
        # --- PHẦN 1: BẢNG REPORT (VIEW ONLY) ---
        frame_top = tk.Frame(self.root, bg="#f4f6f9", padx=20, pady=10)
        frame_top.pack(fill=tk.BOTH, expand=True)
        
        lbl_title = tk.Label(frame_top, text="📊 DASHBOARD: TAB REPORT (CHỈ XEM)", font=("Arial", 14, "bold"), bg="#f4f6f9", fg="#333")
        lbl_title.pack(anchor="w", pady=(0, 10))
        
        # Tạo Treeview (Bảng)
        columns = ("WS_NAME", "TITLE", "KEYWORD", "SEO", "AI", "PUBLISH_DATE", "STATUS")
        self.tree = ttk.Treeview(frame_top, columns=columns, show="headings", height=10)
        
        # Định nghĩa tiêu đề cột và độ rộng
        self.tree.heading("WS_NAME", text="Website")
        self.tree.column("WS_NAME", width=180)
        self.tree.heading("TITLE", text="Tiêu đề bài viết")
        self.tree.column("TITLE", width=250)
        self.tree.heading("KEYWORD", text="Từ khóa chính")
        self.tree.column("KEYWORD", width=150)
        self.tree.heading("SEO", text="Điểm SEO")
        self.tree.column("SEO", width=80, anchor="center")
        self.tree.heading("AI", text="AI (%)")
        self.tree.column("AI", width=80, anchor="center")
        self.tree.heading("PUBLISH_DATE", text="Ngày chờ đăng")
        self.tree.column("PUBLISH_DATE", width=150, anchor="center")
        self.tree.heading("STATUS", text="Trạng thái")
        self.tree.column("STATUS", width=100, anchor="center")
        
        # Thêm thanh cuộn cho bảng
        scrollbar = ttk.Scrollbar(frame_top, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(fill=tk.BOTH, expand=True)

        # --- PHẦN 2: CONTROL PANEL (NÚT BẤM & LOG) ---
        frame_bottom = tk.Frame(self.root, bg="#ffffff", padx=20, pady=15, relief="groove", borderwidth=2)
        frame_bottom.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Khu vực Nút bấm
        frame_btn = tk.Frame(frame_bottom, bg="#ffffff")
        frame_btn.pack(side=tk.LEFT, padx=(0, 20))
        
        self.btn_start = tk.Button(frame_btn, text="🚀 BẮT ĐẦU CHẠY", font=("Arial", 14, "bold"), bg="#4CAF50", fg="white", 
                                   width=18, height=2, cursor="hand2", command=self.on_start_click)
        self.btn_start.pack()
        
        # Khu vực Log
        frame_log = tk.Frame(frame_bottom, bg="#ffffff")
        frame_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        lbl_log = tk.Label(frame_log, text="Console Logs:", font=("Arial", 10, "italic"), bg="#ffffff")
        lbl_log.pack(anchor="w")
        
        self.console_text = scrolledtext.ScrolledText(frame_log, width=60, height=10, font=("Consolas", 10), bg="#1e1e1e", fg="#00FF00")
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        sys.stdout = RedirectConsole(self.console_text)
        
        # Tải dữ liệu ban đầu lên bảng
        self.load_initial_data()

    def load_initial_data(self):
        """Đọc file REPORT.csv và đưa lên bảng"""
        print("Đang tải dữ liệu từ file csv...")
        try:
            df_report = pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - REPORT.csv', on_bad_lines='skip', dtype=str)
            for _, row in df_report.iterrows():
                # Xử lý trường hợp file rỗng hoặc thiếu cột
                ws = row.get('REP_WS_NAME', '')
                title = row.get('REP_TITLE', '')
                kw = row.get('REP_KW_1', '')
                seo = row.get('REP_SEO_SCORE', '')
                ai = row.get('AI_DETECTOR_RATE', '')
                pub_date = row.get('REP_PUBLISH_DATE', '')
                status = row.get('REP_RESULT', '')
                
                # Chỉ chèn nếu có dữ liệu
                if pd.notna(ws) and str(ws).strip() != '':
                    self.tree.insert("", "end", values=(ws, title, kw, seo, ai, pub_date, status))
            print("Tải dữ liệu thành công. Sẵn sàng chạy!")
        except FileNotFoundError:
            print("Chưa tìm thấy file REPORT.csv. Bảng dữ liệu sẽ trống.")

    def run_automation_thread(self):
        self.btn_start.config(state=tk.DISABLED, text="ĐANG XỬ LÝ...", bg="gray")
        try:
            # Load lại DB mới nhất
            db_mock = {
                'DASHBOARD': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - DASHBOARD.csv', on_bad_lines='skip', dtype=str),
                'WEBSITE': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - WEBSITE.csv', on_bad_lines='skip', dtype=str),
                'KEYWORD': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - KEYWORD.csv', on_bad_lines='skip', dtype=str),
                'REPORT': pd.read_csv('MKT_content_auto content_ver 260330 1400.xlsx - REPORT.csv', on_bad_lines='skip', dtype=str)
            }
            
            bot = AutoContentSEO(db_mock)
            if bot.step1_kiem_tra_he_thong():
                time.sleep(1) # Chờ cho giống thật
                
                # Chạy gộp bước 2 đến 6 để lấy kết quả
                new_row_data = bot.step2_to_step6_mock()
                time.sleep(1)
                
                print(f"\n✅ Đã tạo xong bài: {new_row_data['REP_TITLE']}")
                print("Đang đẩy dữ liệu lên Dashboard Tab REPORT...")
                
                # Update UI table (Phải dùng root.after để an toàn khi update UI từ Thread khác)
                self.root.after(0, self.add_row_to_table, new_row_data)
                
        except Exception as e:
            print(f"\n❌ Lỗi: {e}")
        finally:
            self.btn_start.config(state=tk.NORMAL, text="🚀 BẮT ĐẦU CHẠY", bg="#4CAF50")

    def add_row_to_table(self, data):
        """Hàm nhét dòng dữ liệu mới vừa sinh ra vào Bảng Treeview"""
        self.tree.insert("", "end", values=(
            data['REP_WS_NAME'], 
            data['REP_TITLE'], 
            data['REP_KW_1'], 
            data['REP_SEO_SCORE'], 
            data['AI_DETECTOR_RATE'], 
            data['REP_PUBLISH_DATE'], 
            data['REP_RESULT']
        ))
        # Tự động cuộn bảng xuống dòng cuối cùng vừa thêm
        for item in self.tree.get_children():
            self.tree.see(item)

    def on_start_click(self):
        self.console_text.delete(1.0, tk.END)
        print("Khởi động hệ thống...")
        threading.Thread(target=self.run_automation_thread, daemon=True).start()

# --- KHỞI ĐỘNG APP ---
if __name__ == "__main__":
    root = tk.Tk()
    app = AppDashboard(root)
    root.mainloop()
