# ==========================================
# GIAO DIỆN CHÍNH (UI) - BẢO MẬT CHỐNG XÓA SỬA
# ==========================================
st.markdown("<h2 style='color:#ffd700;'>🚕 LÁI HỘ SEO MASTER</h2>", unsafe_allow_html=True)
tabs = st.tabs(list(TABS_CONFIG.keys()))

for i, (name, cols) in enumerate(TABS_CONFIG.items()):
    with tabs[i]:
        # KHU VỰC THÊM MỚI DỮ LIỆU (CHỈ ĐƯỢC THÊM, KHÔNG ĐƯỢC XÓA)
        with st.expander(f"📥 THÊM DỮ LIỆU MỚI VÀO {name}"):
            with st.form(key=f"form_nhaplieu_{name}", clear_on_submit=True):
                raw_data = st.text_area("Dán nội dung vào đây (Hệ thống sẽ nối thêm vào Data hiện tại):", height=150)
                submit_button = st.form_submit_button("🔥 THÊM VÀO BẢNG")
                
                if submit_button and raw_data:
                    parsed_data = []
                    for line in raw_data.strip().split('\n'):
                        if not line.strip(): continue
                        row = [x.strip() for x in re.split(r'\t|\s{2,}', line) if x.strip()]
                        if len(row) > len(cols): row = row[:len(cols)]
                        elif len(row) < len(cols): row.extend([''] * (len(cols) - len(row)))
                        parsed_data.append(row)
                    
                    # LOGIC MỚI: DÙNG HÀM CONCAT ĐỂ NỐI THÊM DATA, TUYỆT ĐỐI KHÔNG GHI ĐÈ
                    df_new_input = pd.DataFrame(parsed_data, columns=cols)
                    st.session_state['db'][name] = pd.concat([st.session_state['db'][name], df_new_input], ignore_index=True)
                    st.rerun()

        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 3])
        with c1: st.button("☁️ ĐỒNG BỘ GOOGLE SHEET", key=f"up_{name}", use_container_width=True)
        with c2: st.button("🔄 LÀM MỚI (PULL DATA)", key=f"res_{name}", use_container_width=True)
        with c3:
            if name == "Dashboard":
                if st.button("🔥 START ROBOT AI", key="run_robot", type="primary", use_container_width=True):
                    hacker_terminal()

        # BỘ LỌC BẢO MẬT HIỂN THỊ
        if name == "Report":
            # RIÊNG TAB REPORT: MỞ FULL QUYỀN SỬA/XÓA TỪ GIAO DIỆN BẰNG DATA_EDITOR
            st.session_state['db'][name] = st.data_editor(
                st.session_state['db'][name],
                use_container_width=True,
                num_rows="dynamic",
                height=500,
                hide_index=True,
                key=f"edit_{name}"
            )
        else:
            # TẤT CẢ CÁC TAB CÒN LẠI (DASHBOARD, WEBSITE, BACKLINK...): KHÓA CỨNG BẰNG DATAFRAME
            st.dataframe(
                st.session_state['db'][name],
                use_container_width=True,
                height=500,
                hide_index=True
            )
