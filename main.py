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
    st.session_state['db']['Dashboard'] = pd.DataFrame([
        ["GOOGLE_SHEET_ID", "1bSc4nd7HPTNXkUZ5cFW3mfkcbuZumHQxhN5uIhfIguw"],
        ["GEMINI_API_KEY", "AlzAsyD-tq8Eksdpb0QW2af6imjTydyhORzbtP8"],
        ["Số lượng bài cần tạo", "3"]
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
                    
                    # TUYỆT CHIÊU: Cắt bằng Tab hoặc từ 2 khoảng trắng trở lên, và vứt bỏ các ô rác
                    row = [x.strip() for x in re.split(r'\t|\s{2,}', line) if x.strip()]
                    
                    # Tự động canh lề: Thiếu cột thì bù trống, dư cột thì cắt bỏ
                    if len(row) > len(cols): 
                        row = row[:len(cols)]
                    elif len(row) < len(cols): 
                        row.extend([''] * (len(cols) - len(row)))
                        
                    parsed_data.append(row)
                
                # Ghi đè vào bảng và chạy lại
                st.session_state['db'][name] = pd.DataFrame(parsed_data, columns=cols)
                st.rerun()

        # --- TOOLBAR & BẢNG ---
        c1, c2, c3 = st.columns([1, 1, 4])
        with c1: st.button("☁️ LƯU CLOUD", key=f"up_{name}", use_container_width=True)
        with c2: st.button("🔄 RESTORE", key=f"res_{name}", use_container_width=True)

        st.session_state['db'][name] = st.data_editor(
            st.session_state['db'][name],
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            hide_index=True,
            key=f"edit_{name}"
        )
