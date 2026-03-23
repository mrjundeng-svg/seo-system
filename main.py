import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="LÁI HỘ SEO", layout="wide")

TABS_CONFIG = {
    "Dashboard": ["Hạng mục", "Giá trị thực tế"],
    "Backlink": ["Từ khoá", "Website đích", "Đã dùng"],
    "Website": ["Tên web", "Nền tảng", "URL / ID", "Trạng thái", "Giới hạn bài/ngày"],
    "Image": ["Link ảnh", "Số lần dùng"],
    "Spin": ["Từ Spin", "Bộ Spin"],
    "Local": ["Tỉnh thành", "Quận", "Điểm nóng"],
    "Report": ["Website", "Nền tảng", "URL / ID", "Ngày đăng bài", "Từ khoá 1", "Từ khoá 2", "Từ khoá 3", "Từ khoá 4", "Từ khoá 5", "Link bài viết", "Tiêu đề bài viết", "File ID Drive", "Thời gian hẹn giờ", "Trạng thái"]
}

if 'db' not in st.session_state:
    st.session_state['db'] = {k: pd.DataFrame(columns=v) for k, v in TABS_CONFIG.items()}
    # Dữ liệu Ní setup sẵn tui giữ nguyên nhé
    st.session_state['db']['Dashboard'] = pd.DataFrame([
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["SERPAPI_KEY", "380c97c05d054e4633fa1333115cba7a26fcb50dcec0e915d10dc122b82fe17e"],
        ["SENDER_EMAIL", "jundeng.po@gmail.com"],
        ["SENDER_PASSWORD", "vddy misk nhbu vtsm"],
        ["RECEIVER_EMAIL", "jundeng.po@gmail.com"],
        ["Danh sách Keyword bài viết", "thuê tài xế lái hộ, đưa người say..."],
        ["TARGET_URL", "https://laiho.vn/"],
        ["Website đối thủ", "lmd.vn, butl.vn..."],
        ["Mục tiêu bài viết", "Bài viết dạng tư vấn..."],
        ["Số lượng bài cần tạo", "10"],
        ["Thiết lập số lượng chữ", "900 - 1200"],
        ["Số lượng backlink/bài", "3 - 4"],
        ["FOLDER_DRIVE_ID", "1STdk4mpDP2KOdyyJKf6rdHnnYdr8TLN4"]
    ], columns=["Hạng mục", "Giá trị thực tế"])

st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)

tabs = st.tabs(list(TABS_CONFIG.keys()))

for i, (name, cols) in enumerate(TABS_CONFIG.items()):
    with tabs[i]:
        # --- BỘ LỌC ÉP KHUÔN THÔNG MINH ---
        with st.expander(f"📥 NHẬP LIỆU NHANH {name}"):
            raw_data = st.text_area("Dán nội dung vào đây:", key=f"txt_{name}", height=150)
            if st.button("🔥 ĐỔ VÀO BẢNG", key=f"load_{name}") and raw_data:
                parsed_data = []
                for line in raw_data.strip().split('\n'):
                    if not line.strip(): continue
                    row = [x.strip() for x in re.split(r'\t|\s{2,}', line) if x.strip()]
                    if len(row) > len(cols): row = row[:len(cols)]
                    elif len(row) < len(cols): row.extend([''] * (len(cols) - len(row)))
                    parsed_data.append(row)
                st.session_state['db'][name] = pd.DataFrame(parsed_data, columns=cols)
                st.rerun()

        # --- TOOLBAR & BẢNG ---
        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 3])
        with c1: 
            st.button("☁️ LƯU CLOUD", key=f"up_{name}", use_container_width=True)
        with c2: 
            st.button("🔄 RESTORE", key=f"res_{name}", use_container_width=True)
        with c3:
            # TRẢ LẠI NÚT START ROBOT Ở ĐÂY NÈ NÍ
            if name == "Dashboard":
                if st.button("🔥 START ROBOT", key="run_robot", type="primary", use_container_width=True):
                    st.toast("Đang khởi động Robot SEO...", icon="🚀")
                    # Chỗ này sau này Ní nhúng code chạy AI vào nha

        st.session_state['db'][name] = st.data_editor(
            st.session_state['db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            hide_index=True,
            key=f"edit_{name}"
        )
