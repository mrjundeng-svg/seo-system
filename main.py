import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="SEO Admin - Lái Hộ", layout="wide")

# 2. KIỂM TRA ĐĂNG NHẬP (Giữ nguyên để bảo mật)
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống Quản trị")
    user = st.text_input("Tên đăng nhập")
    pw = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if (user == "admin" and pw == "123") or (user == "editor" and pw == "456"):
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Sai tài khoản!")
else:
    # SIDEBAR MENU
    st.sidebar.title("🎮 ĐIỀU HÀNH SEO")
    project = st.sidebar.selectbox("📂 Dự án", ["Lái Hộ", "Giúp Việc Nhanh"])
    menu = st.sidebar.radio("📍 Danh mục", [
        "1. Config", 
        "2. Data_Backlink", 
        "3. Data_Website", 
        "4. Data_Local", 
        "5. Data_Report"
    ])
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"🚀 {project} - {menu}")
    st.markdown("---")

    # --- TAB 2: DATA_BACKLINK (Dạng Bảng tính Google Sheets) ---
    if menu == "2. Data_Backlink":
        st.subheader("📝 Bảng quản lý Link (Có thể gõ trực tiếp)")
        st.write("Bạn có thể nhấn vào ô để sửa hoặc nhấn dấu (+) ở bên phải để thêm hàng mới.")
        
        # Tạo khung bảng trắng để nhân viên tự nhập
        df_init = pd.DataFrame([
            {"Ngày": "2026-03-23", "Nguồn": "Baomoi.com", "Link": "https://...", "Anchor Text": "Lái hộ"},
        ])
        
        # Đây là tính năng "Bảng tương tác" giống Google Sheets
        st.data_editor(
            df_init, 
            num_rows="dynamic", # Cho phép thêm/xóa hàng
            use_container_width=True,
            column_config={
                "Link": st.column_config.LinkColumn("Đường dẫn Link"),
                "Ngày": st.column_config.DateColumn("Ngày đăng")
            }
        )
        st.button("💾 Lưu vào Database")

    # --- TAB 4: DATA_LOCAL (Dạng Form nhập liệu) ---
    elif menu == "4. Data_Local":
        st.subheader("📍 Form khai báo địa phương (Google Map Style)")
        
        with st.form("local_form"):
            col1, col2 = st.columns(2)
            with col1:
                city = st.selectbox("Tỉnh/Thành phố", ["Hà Nội", "TP.HCM", "Đà Nẵng", "Cần Thơ"])
                district = st.text_input("Quận/Huyện", placeholder="Ví dụ: Quận 1, Quận 7...")
            with col2:
                lat_long = st.text_input("Tọa độ GPS (Nếu có)", placeholder="10.762622, 106.660172")
                keywords = st.text_area("Từ khóa mục tiêu vùng này", placeholder="Lái hộ Quận 1, Tài xế Quận 1...")
            
            submitted = st.form_submit_button("📌 Ghim địa điểm lên hệ thống")
            if submitted:
                st.success(f"Đã lưu địa điểm {district}, {city} vào bản đồ SEO!")

    # --- TAB 3: DATA_WEBSITE ---
    elif menu == "3. Data_Website":
        st.subheader("🌐 Quản lý hệ thống Web vệ tinh")
        st.info("Nhập danh sách Website bạn đang quản lý vào bảng dưới đây.")
        
        df_web = pd.DataFrame([
            {"Domain": "laiho24h.com", "Loại": "WordPress", "User Admin": "admin_seo", "Ghi chú": "Web chính"},
        ])
        st.data_editor(df_web, num_rows="dynamic", use_container_width=True)
        st.button("🔄 Kiểm tra trạng thái Index")

    else:
        st.info(f"Mục {menu} đang được tối ưu hóa giao diện...")
