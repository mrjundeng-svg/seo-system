import streamlit as st

# Cấu hình giao diện
st.set_page_config(page_title="Hệ thống SEO Lái Hộ", layout="wide")

# Kiểm tra đăng nhập
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 Đăng nhập Hệ thống")
    user = st.text_input("Tên đăng nhập")
    pw = st.text_input("Mật khẩu", type="password")
    if st.button("Đăng nhập"):
        if (user == "admin" and pw == "123") or (user == "editor" and pw == "456"):
            st.session_state['logged_in'] = True
            st.rerun()
        else:
            st.error("Sai tài khoản!")
else:
    # Sidebar menu
    st.sidebar.title("🛠️ QUẢN TRỊ SEO")
    project = st.sidebar.selectbox("📂 Dự án", ["Lái Hộ", "Giúp Việc Nhanh"])
    menu = st.sidebar.radio("📍 Danh mục", ["1. Config", "2. Backlink", "3. Website", "4. Image", "5. Spin", "6. Local", "7. Report"])
    
    if st.sidebar.button("Đăng xuất"):
        st.session_state['logged_in'] = False
        st.rerun()

    st.title(f"🚀 {project} - {menu}")
    
    if menu == "2. Backlink":
        st.subheader("Khai báo danh sách Backlink")
        st.data_editor({"URL": ["https://link1.com"], "Anchor Text": ["Từ khóa"]})
        st.button("Lưu dữ liệu")
    else:
        st.info(f"Mục {menu} đang sẵn sàng. Bạn có thể bắt đầu khai báo.")
