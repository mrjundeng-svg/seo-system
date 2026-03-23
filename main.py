import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hệ thống SEO Pro - Lái Hộ", page_icon="🚀", layout="wide")

# CSS (Giữ nguyên bộ giao diện đẹp hôm trước)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
    .main { background-color: #f0f2f5; }
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stSidebar"] { background-color: #0f172a; color: #f8fafc; }
    .stButton>button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%); /* Đổi sang màu Xanh Lá cho nút Run */
        color: white; border: none; border-radius: 8px;
        height: 3.5em; font-weight: 700; width: 100%;
    }
    .run-btn>div>button {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important; /* Nút Dừng màu đỏ */
    }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU
MENU_MAP = {
    "⚙️ Config & Chạy bài": "config",
    "🔗 Data Backlink": "backlink",
    "🌐 Data Website": "website",
    "🖼️ Data Image": "image",
    "✍️ Data Spin": "spin",
    "📍 Data Local": "local",
    "📊 Data Report": "report"
}

if 'df_config' not in st.session_state:
    st.session_state['df_config'] = pd.DataFrame([["GEMINI_API_KEY", ""], ["TARGET_URL", "https://laiho.vn/"], ["Số lượng bài", "10"]], columns=["Hạng mục", "Giá trị"])
if 'df_report' not in st.session_state:
    st.session_state['df_report'] = pd.DataFrame(columns=["Website", "Ngày đăng", "Tiêu đề", "Trạng thái"])

# 3. KIỂM TRA ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    with st.columns([1,2,1])[1]:
        st.title("🚀 LOGIN")
        u = st.text_input("User")
        p = st.text_input("Pass", type="password")
        if st.button("ĐĂNG NHẬP"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
else:
    # 4. SIDEBAR
    with st.sidebar:
        st.header("🏢 SEO PANEL")
        choice = st.radio("MENU:", list(MENU_MAP.keys()))
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. VÙNG LÀM VIỆC CHÍNH
    st.title(f"📍 {choice}")

    if "Config" in choice:
        # --- PHẦN 1: BẢNG CẤU HÌNH ---
        st.subheader("⚙️ 1. Thiết lập thông số")
        st.session_state.df_config = st.data_editor(st.session_state.df_config, use_container_width=True, height=300)

        st.markdown("---")
        
        # --- PHẦN 2: NÚT CHẠY BÀI (QUAN TRỌNG NHẤT) ---
        st.subheader("🚀 2. Điều khiển chiến dịch")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔥 BẮT ĐẦU CHẠY SEO (RUN SYSTEM)"):
                # Mô phỏng quá trình chạy bài để demo cho sếp
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i in range(1, 11):
                    # Giả lập các bước AI làm việc
                    status_text.text(f" đang xử lý bài viết số {i}/10...")
                    time.sleep(0.5) # Giả lập AI đang viết
                    progress_bar.progress(i * 10)
                    
                    if i == 3: status_text.text("🤖 AI đang tối ưu hình ảnh...")
                    if i == 6: status_text.text("🔗 Đang chèn Backlink & Spin nội dung...")
                    if i == 9: status_text.text("🌐 Đang đẩy bài lên Blogger/WordPress...")
                
                st.success("✅ CHIẾN DỊCH HOÀN TẤT! 10 bài viết đã được đăng thành công.")
                # Cập nhật thử 1 dòng vào Report cho sếp xem
                new_data = pd.DataFrame([{"Website": "Blog Lái Hộ 1", "Ngày đăng": "2026-03-23", "Tiêu đề": "Dịch vụ lái hộ uy tín", "Trạng thái": "DONE"}])
                st.session_state.df_report = pd.concat([new_data, st.session_state.df_report], ignore_index=True)

        with col2:
            st.button("🛑 DỪNG KHẨN CẤP", help="Dừng mọi tiến trình đang chạy", type="secondary")

    elif "Report" in choice:
        st.subheader("📊 Nhật ký đăng bài")
        st.data_editor(st.session_state.df_report, use_container_width=True, height=600)

    else:
        st.info("Tính năng đang được kết nối dữ liệu...")
