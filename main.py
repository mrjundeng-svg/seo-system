import streamlit as st
import pandas as pd
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 1. SCHEMA DỮ LIỆU & HỆ THỐNG LƯU TRỮ (BẤT TỬ)
SCHEMA = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Data_Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Data_Website": ["Tên web", "Nền tảng", "URL / ID", "Tài khoản (WP)", "Mật khẩu App", "Trạng thái", "Giới hạn bài/ngày"],
    "Data_Image": ["Link ảnh", "Đã dùng"],
    "Data_Spin": ["Từ Spin", "Bộ Spin"],
    "Data_Local": ["Tỉnh thành", "Quận", "Cung đường"],
    "Data_Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

def load_db(key):
    path = f"db_v12_{key}.csv"
    if os.path.exists(path):
        try: return pd.read_csv(path).fillna("")
        except: pass
    cols = SCHEMA[key]
    if key == "Dashboard":
        return pd.DataFrame([
            ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
            ["SENDER_EMAIL", "jundeng.po@gmail.com"],
            ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
            ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
            ["TARGET_URL", "https://laiho.vn/"],
            ["Số lượng bài/ngày", "10"],
            ["Mật độ Link", "3-5"]
        ] + [["...", ""]]*6, columns=cols)
    return pd.DataFrame([{c: "" for c in cols}], columns=cols)

def save_db(key, df):
    df.to_csv(f"db_v12_{key}.csv", index=False)

# KHỞI TẠO SESSION STATE
for k in SCHEMA.keys():
    if f"df_{k}" not in st.session_state:
        st.session_state[f"df_{k}"] = load_db(k)
if 'active_tab' not in st.session_state: st.session_state['active_tab'] = "Dashboard"

# =================================================================
# 2. HÀM GỬI EMAIL BÁO CÁO (CHUYÊN NGHIỆP)
# =================================================================
def send_email_report(df_report):
    # Lấy thông tin từ Dashboard
    config_df = st.session_state['df_Dashboard']
    sender = config_df.loc[config_df['Hạng mục'] == 'SENDER_EMAIL', 'Giá trị thực tế'].values[0]
    pwd = config_df.loc[config_df['Hạng mục'] == 'SENDER_PASSWORD', 'Giá trị thực tế'].values[0]
    receiver = config_df.loc[config_df['Hạng mục'] == 'RECEIVER_EMAIL', 'Giá trị thực tế'].values[0]
    
    if not sender or not pwd:
        st.error("Chưa cấu hình Email hoặc Mật khẩu trong Dashboard!")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = f"SEO Robot Lái Hộ <{sender}>"
        msg['To'] = receiver
        msg['Subject'] = f"🚕 [BÁO CÁO SEO] - {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}"
        
        # Tạo nội dung HTML cho bảng
        html_table = df_report.to_html(index=False)
        body = f"""
        <html>
            <body style="font-family: sans-serif;">
                <h2 style="color: #ffd700;">BÁO CÁO TỔNG HỢP HỆ THỐNG LÁI HỘ</h2>
                <p>Chào Admin, Robot v55.0 gửi Ní báo cáo dữ liệu SEO mới nhất:</p>
                <div style="overflow-x:auto;">
                    {html_table}
                </div>
                <br>
                <p><i>Hệ thống được vận hành tự động bởi SEO Lái Hộ v1200.0</i></p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, pwd)
        server.send_message(msg)
        server.quit()
        st.success(f"✅ Đã gửi báo cáo về mail: {receiver}")
    except Exception as e:
        st.error(f"❌ Lỗi gửi mail: {e}")

# =================================================================
# 3. GIAO DIỆN & STYLE (NÚT BẰNG NHAU, ICON RỰC RỠ)
# =================================================================
st.set_page_config(page_title="SEO Lái Hộ v1200", page_icon="🚕", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #000000; }
    header { visibility: hidden; }
    [data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

    /* MENU SIDEBAR: NÚT BẰNG NHAU, SÁT NHAU */
    .nav-btn button {
        width: 100% !important; height: 45px !important;
        text-align: left !important; background-color: #111111 !important;
        border: 1px solid #333 !important; border-radius: 6px !important;
        margin-bottom: -5px !important; color: #ffffff !important; font-weight: 600 !important;
    }
    .active-tab button { background-color: #222222 !important; border-left: 5px solid #ffd700 !important; color: #ffd700 !important; }
    
    /* TOOLBAR NÚT TÍNH NĂNG (BẰNG NHAU TRÊN 1 HÀNG) */
    .stButton>button { width: 100% !important; height: 42px !important; border-radius: 4px !important; font-weight: 700 !important; }
    .btn-red button { background-color: #ff0000 !important; color: #fff !important; border: none !important; }
    .btn-gold button { background-color: #ffd700 !important; color: #000 !important; border: none !important; }
    .btn-email button { background-color: #1e3a8a !important; color: #fff !important; border: none !important; }

    /* BẢNG DỮ LIỆU */
    [data-testid="stDataFrame"] { background-color: #111111 !important; border: 1px solid #333 !important; }
    [data-testid="stDataFrame"] div[role="columnheader"] p { color: #ffd700 !important; font-weight: 700 !important; }
    * { color: #ffffff; font-family: 'Inter', sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# 4. BỐ CỤC SIDEBAR CỐ ĐỊNH
nav_col, main_col = st.columns([1, 4.5], gap="small")
with nav_col:
    st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ</h2>", unsafe_allow_html=True)
    st.markdown("---")
    menu_icons = { "Dashboard": "🏠", "Data_Backlink": "🔗", "Data_Website": "🌐", "Data_Image": "🖼️", "Data_Spin": "🔄", "Data_Local": "📍", "Data_Report": "📊" }
    for m in SCHEMA.keys():
        is_active = st.session_state['active_tab'] == m
        st.markdown(f"<div class='nav-btn {'active-tab' if is_active else ''}'>", unsafe_allow_html=True)
        if st.button(f"{menu_icons.get(m, '▪️')} {m}", key=f"n_{m}"):
            st.session_state['active_tab'] = m
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# 5. NỘI DUNG CHÍNH
with main_col:
    tab = st.session_state['active_tab']
    st.markdown(f"### 📍 {tab}")
    
    # TOOLBAR: 4 NÚT BẰNG NHAU TRÊN 1 HÀNG
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("💾 LƯU CỨNG", use_container_width=True):
            for k in SCHEMA.keys(): save_db(k, st.session_state[f"df_{k}"])
            st.toast("Dữ liệu đã được khóa!")
    with c2: 
        st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
        st.button("📤 XUẤT EXCEL", key=f"ex_{tab}", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="btn-email">', unsafe_allow_html=True)
        if st.button("📧 GỬI MAIL REPORT", key=f"mail_{tab}", use_container_width=True):
            send_email_report(st.session_state['df_report'])
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        if tab == "Dashboard":
            st.markdown('<div class="btn-red">', unsafe_allow_html=True)
            if st.button("🔥 START ROBOT", use_container_width=True): st.info("Robot v55.0 đang vận hành...")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="btn-gold">', unsafe_allow_html=True)
            st.button("📥 NHẬP EXCEL", key=f"im_{tab}", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # HIỂN THỊ BẢNG (AUTO-SAVE)
    state_key = f"df_{tab}"
    st.session_state[state_key] = st.data_editor(
        st.session_state[state_key],
        use_container_width=True,
        num_rows="dynamic",
        height=700,
        hide_index=True,
        column_config={c: st.column_config.TextColumn(width="large") for c in SCHEMA[tab]}
    )

st.caption("🚀 SEO Automation Lái Hộ v1200.0 | Email Reporting Enabled")
