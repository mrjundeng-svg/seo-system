import streamlit as st
import pandas as pd
import io

# 1. CẤU HÌNH TRANG & CSS LUXURY
st.set_page_config(page_title="Hệ thống SEO Pro - Lái Hộ", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    /* Import font chữ hiện đại */
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Segoe UI', sans-serif; }
    
    /* Làm nền trang chuyên nghiệp */
    .main { background-color: #f0f2f5; }
    
    /* ÉP BẢNG HIỂN THỊ FULL - KHÔNG SCROLL NỘI BỘ */
    [data-testid="stDataFrame"] { width: 100% !important; }
    [data-testid="stDataFrame"] div[data-testid="stTable"] { height: auto !important; }
    
    /* Tùy chỉnh Sidebar (Xanh Navy đậm) */
    [data-testid="stSidebar"] { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] hr { border-color: #334155; }
    
    /* Thiết kế Card trắng cho bảng dữ liệu */
    .st-emotion-cache-12w0qpk { 
        background: white; 
        padding: 25px; 
        border-radius: 15px; 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Nút bấm (Gradients Blue) */
    .stButton>button {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        color: white; border: none; border-radius: 8px;
        height: 3.5em; font-weight: 700; transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 4px 12px rgba(37,99,235,0.4); }
    
    /* Tiêu đề bảng */
    .table-title { color: #1e293b; font-size: 24px; font-weight: 800; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# 2. ĐỒNG BỘ HÓA DỮ LIỆU (FIX KEYERROR)
MENU_MAP = {
    "⚙️ Config": "config",
    "🔗 Data Backlink": "backlink",
    "🌐 Data Website": "website",
    "🖼️ Data Image": "image",
    "✍️ Data Spin": "spin",
    "📍 Data Local": "local",
    "📊 Data Report": "report"
}

def init_data():
    for menu_label, key_suffix in MENU_MAP.items():
        key = f"df_{key_suffix}"
        if key not in st.session_state:
            # Khởi tạo chuẩn 100% theo ảnh Google Sheets của Đăng
            if key_suffix == "config":
                cols = ["Cột A (Nội dung)", "Cột B (Dữ liệu)"]
                data = [["GEMINI_API_KEY", ""], ["SERPAPI_KEY", ""], ["SENDER_EMAIL", "jundeng.po@gmail.com"], ["SENDER_PASSWORD", ""], ["RECEIVER_EMAIL", "jundeng.po@gmail.com"], ["Danh sách Keyword", ""], ["TARGET_URL", "https://laiho.vn/"], ["Website đối thủ", ""], ["Mục tiêu bài viết", ""], ["Số lượng bài", "10"], ["Số chữ", "900-1200"], ["Số backlink", "3-4"], ["FOLDER_DRIVE_ID", ""]]
                st.session_state[key] = pd.DataFrame(data, columns=cols)
            elif key_suffix == "backlink":
                cols = ["DatDat", "URL Đích (cách nhau dấu phẩy)", "Số lần dùng"]
                st.session_state[key] = pd.DataFrame([["lái xe hộ", "https://laiho.vn", 0]] * 5, columns=cols) # Mồi sẵn 5 dòng
            elif key_suffix == "website":
                cols = ["ID Blog", "Nền tảng", "URL / ID", "User (WP)", "Pass (WP)", "Trạng thái", "Bài/ngày"]
                st.session_state[key] = pd.DataFrame([["Blog 1", "Blogger", "...", "", "", "Bật", "1-2"]] * 3, columns=cols)
            elif key_suffix == "report":
                cols = ["Website", "Nền tảng", "URL/ID", "Ngày đăng", "Từ khóa 1", "Từ khóa 2", "Từ khóa 3", "Từ khóa 4", "Từ khóa 5", "Link bài", "Tiêu đề", "Drive ID", "Hẹn giờ", "Trạng thái"]
                st.session_state[key] = pd.DataFrame(columns=cols)
            else:
                st.session_state[key] = pd.DataFrame(columns=["Cột 1", "Cột 2", "Cột 3"])

init_data()

# 3. GIAO DIỆN ĐĂNG NHẬP
if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.markdown("<h1 style='text-align: center; color: #1e293b;'>🚀 SEO SYSTEM PRO</h1>", unsafe_allow_html=True)
    with st.columns([1,2,1])[1]:
        with st.container(border=True):
            st.subheader("Đăng nhập")
            u = st.text_input("Tài khoản", value="admin")
            p = st.text_input("Mật khẩu", type="password", value="123")
            if st.button("TRUY CẬP NGAY"):
                if u == "admin" and p == "123":
                    st.session_state['logged_in'] = True
                    st.rerun()
                else: st.error("Lỗi đăng nhập!")
else:
    # 4. SIDEBAR ĐẬM CHẤT SaaS
    with st.sidebar:
        st.markdown("<h2 style='color: white;'>🏢 SEO DASHBOARD</h2>", unsafe_allow_html=True)
        st.caption("Dự án: Lái Hộ | Ver 2.0 Premium")
        st.markdown("---")
        choice = st.radio("LỰA CHỌN DANH MỤC:", list(MENU_MAP.keys()))
        st.markdown("---")
        if st.button("🚪 Đăng xuất hệ thống"):
            st.session_state['logged_in'] = False
            st.rerun()

    # 5. VÙNG LÀM VIỆC CHÍNH
    st.markdown(f"<div class='table-title'>📍 Quản lý {choice}</div>", unsafe_allow_html=True)
    
    # Tool Card: Import / Export
    with st.container(border=True):
        c1, c2, c3 = st.columns([1.5, 1.5, 2])
        current_key = f"df_{MENU_MAP[choice]}"
        with c1:
            csv = st.session_state[current_key].to_csv(index=False).encode('utf-8-sig')
            st.download_button(f"📥 Xuất Excel (CSV)", data=csv, file_name=f"{choice}.csv", use_container_width=True)
        with c2:
            up = st.file_uploader("Nhập file (.csv)", type=["csv"], label_visibility="collapsed")
        with c3:
            if st.button("🚀 Nạp dữ liệu"):
                if up:
                    st.session_state[current_key] = pd.read_csv(up)
                    st.success("Đã cập nhật!")
                    st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # 6. HIỂN THỊ BẢNG FULL (Show ~25 dòng)
    with st.container(border=True):
        st.markdown(f"##### 📊 Dữ liệu trực tuyến: {choice}")
        key = f"df_{MENU_MAP[choice]}"
        
        # Sửa tham số height=800 để show ít nhất 20-25 dòng mà không cần scroll
        st.session_state[key] = st.data_editor(
            st.session_state[key],
            use_container_width=True,
            num_rows="dynamic",
            height=850  # Chiều cao này đủ để show ~25 dòng rõ ràng
        )
    
    st.caption("✅ Hệ thống tự động lưu tạm dữ liệu trong phiên làm việc. Nhấn (+) ở cuối bảng để thêm hàng.")
