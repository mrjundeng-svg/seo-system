import streamlit as st
import pandas as pd

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Hệ thống SEO Lái Hộ - Admin Panel", layout="wide")

# 2. LOGIN LOGIC
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống SEO")
    user = st.text_input("Tên đăng nhập")
    pw = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if (user == "admin" and pw == "123") or (user == "editor" and pw == "456"):
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Sai thông tin!")
else:
    # SIDEBAR MENU
    st.sidebar.title("🎮 ĐIỀU HÀNH")
    project = st.sidebar.selectbox("📂 Chọn Dự án", ["Lái Hộ", "Giúp Việc Nhanh"])
    menu = st.sidebar.radio("📍 Danh mục Quản lý", [
        "Config", 
        "Data_Backlink", 
        "Data_Website", 
        "Data_Image", 
        "Data_Spin", 
        "Data_Local", 
        "Data_Report"
    ])
    
    if st.sidebar.button("🚪 Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"🚀 {project} - {menu}")
    st.markdown("---")

    # --- 1. CONFIG (Theo image_3079ff.png) ---
    if menu == "Config":
        st.subheader("⚙️ Cấu hình thông số hệ thống")
        config_data = {
            "Cột A (Nội dung - Fix cứng)": [
                "GEMINI_API_KEY", "SERPAPI_KEY", "SENDER_EMAIL", "SENDER_PASSWORD", 
                "RECEIVER_EMAIL", "Danh sách Keyword bài viết", "TARGET_URL", 
                "Website đối thủ", "Mục tiêu bài viết", "Số lượng bài cần tạo", 
                "Thiết lập số lượng chữ", "Số lượng backlink/bài", "FOLDER_DRIVE_ID"
            ],
            "Cột B (Dữ liệu - Bạn điền vào đây)": [
                "", "", "jundeng.po@gmail.com", "", "jundeng.po@gmail.com", 
                "thuê tài xế lái hộ, đưa người say...", "https://laiho.vn/", 
                "lmd.vn, butl.vn...", "bài viết dạng tư vấn...", "10", "900 - 1200", "3 - 4", ""
            ]
        }
        st.data_editor(pd.DataFrame(config_data), use_container_width=True, num_rows="fixed")
        st.button("Lưu Config")

    # --- 2. DATA_BACKLINK (Theo image_307a1e.png) ---
    elif menu == "Data_Backlink":
        st.subheader("🔗 Quản lý Từ khóa & URL Đích")
        backlink_data = {
            "DatDat (Từ khóa)": ["lái xe hộ", "dịch vụ lái xe hộ", "giá thuê tài xế đi tỉnh"],
            "Cột B (Danh sách URL Đích)": ["https://laiho.vn", "https://laiho.vn", "https://laiho.vn"],
            "Cột C (Số lần đã dùng)": [0, 4, 3]
        }
        st.data_editor(pd.DataFrame(backlink_data), use_container_width=True, num_rows="dynamic")
        st.button("Cập nhật Backlink")

    # --- 3. DATA_WEBSITE (Theo image_307cc7.png) ---
    elif menu == "Data_Website":
        st.subheader("🌐 Quản lý Tài khoản Blog/Website")
        web_data = {
            "ID": ["Blog Lái Hộ 1", "Blog Lái Hộ 2", "Blog Lái Hộ 3"],
            "Nền tảng": ["Blogger", "Blogger", "Blogger"],
            "URL / ID": ["muontaixelaxe.laiho1@...", "muontaixelaxe.laiho2@...", "thuetaixelaxe.laiho3@..."],
            "Tài khoản (Chỉ WP)": ["", "", ""],
            "Mật khẩu ứng dụng (Chỉ WP)": ["", "", ""],
            "Trạng thái": ["Bật", "Bật", "Bật"],
            "Giới hạn bài/ngày": ["1 - 2", "1 - 2", "1 - 2"]
        }
        st.data_editor(pd.DataFrame(web_data), use_container_width=True, num_rows="dynamic")
        st.button("Lưu danh sách Web")

    # --- 4. DATA_IMAGE (Theo image_307ce6.png) ---
    elif menu == "Data_Image":
        st.subheader("🖼️ Kho ảnh SEO")
        image_data = {
            "Link Ảnh (URL)": ["https://i.postimg.cc/...", "https://i.postimg.cc/..."],
            "Số lần đã dùng": [3, 3]
        }
        st.data_editor(pd.DataFrame(image_data), use_container_width=True, num_rows="dynamic")
        st.button("Cập nhật kho ảnh")

    # --- 5. DATA_SPIN (Theo image_307d1d.png) ---
    elif menu == "Data_Spin":
        st.subheader("✍️ Từ điển Spin nội dung")
        spin_data = {
            "Từ khóa gốc": ["chúng tôi", "bạn", "dịch vụ lái xe hộ", "an toàn"],
            "Từ đồng nghĩa (Cách nhau bằng dấu phẩy)": [
                "tụi mình, bên mình, phía chúng tôi...", 
                "anh/chị, quý khách, khách hàng...", 
                "dịch vụ thuê tài xế, gọi tài xế...", 
                "an tâm, yên tâm, đảm bảo..."
            ]
        }
        st.data_editor(pd.DataFrame(spin_data), use_container_width=True, num_rows="dynamic")
        st.button("Lưu từ điển")

    # --- 6. DATA_LOCAL (Theo image_307d3c.png) ---
    elif menu == "Data_Local":
        st.subheader("📍 Phủ sóng địa phương")
        local_data = {
            "Tỉnh/Thành phố": ["Tp Hồ Chí Minh", "Tp Hồ Chí Minh", "Tp Hồ Chí Minh"],
            "Quận/Huyện": ["Quận 1", "Quận 1", "Bình Thạnh"],
            "Địa điểm/Tuyến đường": ["Bùi Viện", "Nguyễn Huệ", "Phạm Viết Chánh"]
        }
        st.data_editor(pd.DataFrame(local_data), use_container_width=True, num_rows="dynamic")
        st.button("Lưu địa điểm")

    # --- 7. DATA_REPORT (Theo image_307d5b.jpg) ---
    elif menu == "Data_Report":
        st.subheader("📊 Nhật ký thực thi (Log report)")
        report_data = {
            "Website": ["Blog Lái Hộ 1", "Blog Lái Hộ 2"],
            "Nền tảng": ["Blogger", "Blogger"],
            "Ngày đăng bài": ["2026-03-22", "2026-03-23"],
            "Từ khoá 1": ["thuê tài xế", "lái xe hộ"],
            "Link bài viết": ["Check link trên blog...", "Check link trên blog..."],
            "Trạng thái": ["DONE", "DONE"]
        }
        # Tab này cho phép xem và sửa log
        st.data_editor(pd.DataFrame(report_data), use_container_width=True, num_rows="dynamic")
        st.success("Hệ thống tự động cập nhật nhật ký sau mỗi lần đăng bài.")
