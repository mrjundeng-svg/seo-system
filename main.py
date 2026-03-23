import streamlit as st
import pandas as pd
import time

# 1. CẤU HÌNH TRANG CHUYÊN NGHIỆP
st.set_page_config(
    page_title="Hệ thống SEO Quản trị - Lái Hộ & Giúp Việc",
    page_icon="🚀",
    layout="wide"
)

# 2. KIỂM TRA TRẠNG THÁI ĐĂNG NHẬP
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- GIAO DIỆN ĐĂNG NHẬP ---
if not st.session_state['logged_in']:
    st.title("🔐 Hệ thống Quản trị SEO Nội bộ")
    st.markdown("---")
    col1, col2, col3 = st.columns([1,2,1])
    
    with col2:
        with st.container(border=True):
            st.subheader("Đăng nhập để tiếp tục")
            user = st.text_input("Tên đăng nhập (User)")
            pw = st.text_input("Mật khẩu (Password)", type="password")
            if st.button("Xác nhận Đăng nhập", use_container_width=True):
                if (user == "admin" and pw == "123") or (user == "editor" and pw == "456"):
                    st.session_state['logged_in'] = True
                    st.success("Đang chuyển hướng...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Sai thông tin tài khoản. Vui lòng thử lại!")
    st.info("💡 Mẹo Demo: Dùng admin/123 để vào quyền quản trị.")

# --- GIAO DIỆN CHÍNH SAU KHI ĐĂNG NHẬP ---
else:
    # Sidebar: Menu điều hành
    with st.sidebar:
        st.title("🎮 Dashboard SEO")
        st.image("https://cdn-icons-png.flaticon.com/512/1055/1055644.png", width=100)
        st.markdown("---")
        
        project = st.selectbox("📂 Chọn Dự án thực thi", ["Lái Hộ - Xe Máy/Ô tô", "Giúp Việc Nhanh 24h"])
        
        menu = st.radio("📍 Danh mục tính năng", [
            "1. Cấu hình hệ thống", 
            "2. Quản lý Backlink", 
            "3. Hệ thống Website", 
            "4. Xử lý Hình ảnh AI", 
            "5. Spin Nội dung", 
            "6. Phủ sóng Địa phương", 
            "7. Báo cáo & KPI"
        ])
        
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # NỘI DUNG CHÍNH TỪNG TAB
    st.title(f"🚀 Dự án: {project}")
    st.caption(f"Đang làm việc tại mục: {menu}")
    st.markdown("---")

    # --- TAB 1: CONFIG ---
    if menu == "1. Cấu hình hệ thống":
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Cài đặt API")
            st.text_input("Gemini API Key", type="password", help="Dùng để chạy AI viết bài")
            st.text_input("Google Search Console API", type="password")
        with col2:
            st.subheader("Thông số dự án")
            st.number_input("Số bài viết mục tiêu/ngày", value=10)
            st.toggle("Tự động đăng bài lên WordPress", value=True)
        st.button("Lưu cấu hình", type="primary")

    # --- TAB 2: BACKLINK ---
    elif menu == "2. Quản lý Backlink":
        st.subheader("🔗 Danh sách Backlink đang thực thi")
        # Tạo dữ liệu mẫu cho sếp xem
        df_backlink = pd.DataFrame({
            "Ngày đăng": ["2026-03-20", "2026-03-21", "2026-03-22"],
            "Nguồn (Domain)": ["baomoi.com", "tinhte.vn", "forum.seo.vn"],
            "Anchor Text": ["Dịch vụ lái hộ", "Thuê tài xế", "Lái xe hộ giá rẻ"],
            "Trạng thái": ["Đã Index", "Chờ duyệt", "Đang xử lý"]
        })
        st.data_editor(df_backlink, num_rows="dynamic", use_container_width=True)
        st.button("Tải lên danh sách (.xlsx)")

    # --- TAB 3: WEBSITE ---
    elif menu == "3. Hệ thống Website":
        st.subheader("🌐 Quản lý hệ thống vệ tinh (PBN)")
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng Website", "15", "+2 mới")
        col2.metric("Tỷ lệ sống", "98%", "Rất tốt")
        col3.metric("Lưu lượng (Traffic)", "1.2k/ngày", "+15%")
        
        st.markdown("---")
        st.text_input("Thêm tên miền mới (Domain)")
        st.selectbox("Nền tảng", ["WordPress", "Blogger", "Google Site", "Custom HTML"])
        st.button("Thêm vào hệ thống")

    # --- TAB 4: IMAGE ---
    elif menu == "4. Xử lý Hình ảnh AI":
        st.subheader("🖼️ Tạo & Tối ưu hình ảnh chuẩn SEO")
        st.file_uploader("Tải ảnh gốc lên để AI tự đóng logo & nén ảnh")
        st.text_input("Mô tả ảnh muốn AI tạo (Prompt)")
        col1, col2 = st.columns(2)
        col1.button("Tạo ảnh bằng AI", use_container_width=True)
        col2.button("Nén & Chèn Alt Text", use_container_width=True)

    # --- TAB 5: SPIN ---
    elif menu == "5. Spin Nội dung":
        st.subheader("✍️ Trình Spin bài viết đa dạng hóa từ khóa")
        original_text = st.text_area("Nhập nội dung gốc", height=150, placeholder="Ví dụ: Dịch vụ lái hộ uy tín tại TP.HCM...")
        if st.button("Spin nội dung (X5 biến thể)"):
            with st.spinner("Đang xào nấu nội dung..."):
                time.sleep(1)
                st.success("Đã tạo ra 5 bản phối mới cho dự án!")
                st.text_area("Bản phối 1", "Dịch vụ đưa người say về nhà an toàn tại Sài Gòn...", height=100)

    # --- TAB 6: LOCAL ---
    elif menu == "6. Phủ sóng Địa phương":
        st.subheader("📍 Chiến dịch SEO Local (Google Maps)")
        locations = st.multiselect(
            "Chọn khu vực mục tiêu", 
            ["Hà Nội", "TP. HCM", "Đà Nẵng", "Cần Thơ", "Bình Dương", "Đồng Nai"],
            default=["TP. HCM", "Hà Nội"]
        )
        st.slider("Bán kính bao phủ (km)", 5, 100, 25)
        st.info(f"Hệ thống đang ưu tiên phủ sóng cho {len(locations)} khu vực trọng điểm.")
        st.button("Cập nhật tọa độ GPS")

    # --- TAB 7: REPORT ---
    elif menu == "7. Báo cáo & KPI":
        st.subheader("📊 Hiệu quả SEO dự kiến (1 tuần demo)")
        chart_data = pd.DataFrame({
            "Ngày": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"],
            "Traffic": [120, 150, 200, 180, 250, 310, 290]
        })
        st.line_chart(chart_data, x="Ngày", y="Traffic")
        st.write("✅ **Kết luận:** Dự án đang tăng trưởng đều đặn.")
