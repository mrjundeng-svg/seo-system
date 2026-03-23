import streamlit as st
import pandas as pd
import io

# 1. CẤU HÌNH GIAO DIỆN CHUYÊN NGHIỆP
st.set_page_config(page_title="Hệ thống SEO Lái Hộ - Pro Admin", layout="wide")

# CSS để làm bảng hiển thị full, nút bấm đẹp và giao diện sạch sẽ
st.markdown("""
    <style>
    .stDataFrame div[data-testid="stTable"] { width: 100%; }
    .main { background-color: #f0f2f6; }
    .stButton>button { border-radius: 8px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    div[data-testid="stExpander"] { border: 1px solid #d1d5db; border-radius: 10px; background-color: white; }
    /* Ép bảng không hiện scroll bar nội bộ */
    div[data-testid="stDataFrame"] > div { height: auto !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. KHỞI TẠO DỮ LIỆU (SESSION STATE) - Khắc phục lỗi KeyError
def init_all_data():
    # Danh sách menu chuẩn theo ảnh của bạn
    menu_list = ["Config", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"]
    
    for m in menu_list:
        key = f"df_{m}"
        if key not in st.session_state:
            # Khởi tạo cấu trúc cột chính xác theo từng ảnh
            if m == "Config":
                cols = ["Cột A (Nội dung - Fix cứng)", "Cột B (Dữ liệu - Bạn điền vào đây)"]
                data = [
                    ["GEMINI_API_KEY", ""], ["SERPAPI_KEY", ""], ["SENDER_EMAIL", "jundeng.po@gmail.com"],
                    ["SENDER_PASSWORD", ""], ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
                    ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say..."],
                    ["TARGET_URL", "https://laiho.vn/"], ["Website đối thủ", "lmd.vn, butl.vn"],
                    ["Mục tiêu bài viết", "bài viết tư vấn..."], ["Số lượng bài cần tạo", "10"],
                    ["Thiết lập số lượng chữ", "900 - 1200"], ["Số lượng backlink/bài", "3 - 4"],
                    ["FOLDER_DRIVE_ID", ""]
                ]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            
            elif m == "Data_Backlink":
                cols = ["DatDat", "Cột B (Danh sách URL Đích - cách nhau bằng dấu phẩy)", "Cột C (Số lần đã dùng)"]
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]], columns=cols)
                
            elif m == "Data_Website":
                cols = ["c", "Nền tảng", "URL / ID", "Tài khoản (Chỉ WP)", "Mật khẩu ứng dụng (Chỉ WP)", "Trạng thái", "Giới hạn bài/ngày"]
                st.session_state[key] = pd.DataFrame([["Blog Lái Hộ 1", "Blogger", "muontaixelaxe.laiho1@...", "", "", "Bật", "1 - 2"]], columns=cols)
                
            elif m == "Data_Image":
                cols = ["Link Ảnh (URL)", "Số lần dùng"]
                st.session_state[key] = pd.DataFrame([["https://i.postimg.cc/...", 3]], columns=cols)
                
            elif m == "Data_Spin":
                cols = ["Từ khóa gốc", "Từ đồng nghĩa (Cách nhau bằng dấu phẩy)"]
                st.session_state[key] = pd.DataFrame([["chúng tôi", "tụi mình, bên mình..."]], columns=cols)
                
            elif m == "Data_Local":
                cols = ["Tỉnh/Thành phố", "Quận/Huyện", "Địa điểm/Tuyến đường"]
                st.session_state[key] = pd.DataFrame([["Tp Hồ Chí Minh", "Quận 1", "Bùi Viện"]], columns=cols)
                
            elif m == "Data_Report":
                cols = ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)

init_all_data()

# 3. HÀM XỬ LÝ FILE
def convert_df_to_csv(df):
    return df.to_csv(index=False).encode('utf-8-sig')

# 4. KIỂM TRA ĐĂNG NHẬP
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Hệ thống Quản trị SEO Lái Hộ")
    with st.container(border=True):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Đăng nhập Hệ thống"):
            if u == "admin" and p == "123":
                st.session_state['logged_in'] = True
                st.rerun()
            else: st.error("Thông tin không chính xác!")
else:
    # SIDEBAR
    with st.sidebar:
        st.header("🎮 ĐIỀU HÀNH SEO")
        menu = st.radio("Chọn danh mục:", ["Config", "Data_Backlink", "Data_Website", "Data_Image", "Data_Spin", "Data_Local", "Data_Report"])
        st.markdown("---")
        if st.button("🚪 Đăng xuất"):
            st.session_state['logged_in'] = False
            st.rerun()

    # NỘI DUNG CHÍNH
    st.title(f"📍 Quản lý {menu}")
    
    # Khu vực Công cụ File
    with st.expander("📥 Công cụ Import/Export (Nhập & Xuất File)"):
        c1, c2 = st.columns(2)
        with c1:
            st.write("📤 Xuất dữ liệu")
            st.download_button(
                label=f"Tải file {menu}.csv về máy",
                data=convert_df_to_csv(st.session_state[f"df_{menu}"]),
                file_name=f"{menu}_export.csv",
                mime='text/csv'
            )
        with c2:
            st.write("📥 Nhập dữ liệu")
            uploaded_file = st.file_uploader(f"Chọn file CSV cho {menu}", type=["csv"])
            if st.button("Nạp dữ liệu ngay"):
                if uploaded_file:
                    st.session_state[f"df_{menu}"] = pd.read_csv(uploaded_file)
                    st.success("Đã nạp dữ liệu thành công!")
                else: st.warning("Vui lòng chọn file!")

    st.markdown("---")

    # HIỂN THỊ BẢNG (height=2000 để đảm bảo hiển thị full, không bị roll)
    st.subheader(f"📊 Bảng dữ liệu: {menu}")
    key = f"df_{menu}"
    
    st.session_state[key] = st.data_editor(
        st.session_state[key],
        use_container_width=True,
        num_rows="dynamic",
        height=1000 # Tự động giãn nở cực rộng
    )

    st.success(f"💡 Hệ thống đã sẵn sàng cho mục {menu}. Bạn có thể gõ trực tiếp hoặc dán từ Excel vào.")
