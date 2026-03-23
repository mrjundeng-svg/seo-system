import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cấu hình trang - Giao diện RỘNG
st.set_page_config(layout="wide", page_title="HỆ THỐNG SEO LÁI HỘ V55.0")

# --- CSS Tùy chỉnh ---
# Ta có thể thêm một chút CSS tùy chỉnh để định dạng nút "Dừng khẩn cấp" màu đỏ
# và các tag "DONE" trong bảng, nhưng để giữ cho ví dụ đơn giản và hoạt động trên
# Streamlit tiêu chuẩn, ta sẽ tập trung vào bố cục và các thành phần cốt lõi.
# Để tạo nút màu đỏ, ta sẽ sử dụng tham số `type="primary"` của st.button và một ít CSS
# hoặc sử dụng HTML markdown tùy chỉnh cho nút này. Ta sẽ sử dụng một nút st.button đơn giản.

st.markdown("""
<style>
/* Tùy chỉnh nút màu đỏ */
.red-stop-btn button {
    background-color: #f44336;
    color: white;
}
</style>
""", unsafe_allow_html=True)


# --- 2. THANH ĐIỀU HƯỚNG BÊN TRÁI (SIDEBAR) ---
with st.sidebar:
    st.markdown("## 🏢 ĐƠN VỊ LÁI HỘ")
    # Sử dụng st.selectbox hoặc các component tương tự để mô phỏng menu
    # Tuy nhiên, st.sidebar.radio hoặc st.sidebar.button sẽ tốt hơn để tạo menu.
    # Trong ví dụ này, ta sẽ sử dụng st.sidebar.button và st.sidebar.expanders để mô phỏng.

    menu_options = [
        {"icon": "🏠", "label": "Tổng quan", "submenu": []},
        {"icon": "🗺️", "label": "Phủ sóng vùng", "submenu": ["Phủ sóng 1", "Dịch vụ lái hộ tphcm", "Phủ sóng 3"]},
        {"icon": "⚙️", "label": "Data Config", "submenu": []},
        {"icon": "📁", "label": "Data Image", "submenu": []},
        {"icon": "💬", "label": "Từ điển spin", "submenu": []},
        {"icon": "👥", "label": "Backlink Master", "submenu": []},
        {"icon": "📊", "label": "SEO Report", "submenu": []},
        {"icon": "📍", "label": "Local Map", "submenu": []},
        {"icon": "➕", "label": "Cài đặt khác", "submenu": []},
    ]

    for item in menu_options:
        # Sử dụng icon và label
        header_text = f"{item['icon']} {item['label']}"
        if item['submenu']:
            with st.expander(header_text, expanded=False):
                for sub in item['submenu']:
                    # Highlight item active "Dịch vụ lái hộ tphcm"
                    if sub == "Dịch vụ lái hộ tphcm":
                        st.markdown(f"**- {sub}**")
                    else:
                        st.markdown(f"- {sub}")
        else:
            if st.button(header_text, use_container_width=True):
                # Placeholder for menu action
                pass


# --- 3. TIÊU ĐỀ CHÍNH ---
st.markdown("<h1 style='text-align: left; color: black; font-weight: bold;'>HỆ THỐNG SEO LÁI HỘ V55.0 - [ PHỤC VỤ THEO NGÀY ]</h1>", unsafe_allow_html=True)
st.markdown("Hẹn giờ (Lập lịch Robot chạy tự động theo Quota của Mr. JunDeng)")

# Dòng người dùng ở trên cùng bên phải
# User area simulation in columns
col1, col2, col3, col4, col5 = st.columns([6, 1, 1, 1, 1])
with col1: pass
with col2: st.markdown("JunDeng [ Admin ]")
with col3: st.button("⚙️", help="Cài đặt")
with col4: st.button("P", help="Trang cá nhân") # Placeholder for user avatar
with col5: st.button("🚪", help="Đăng xuất")


# --- 4. BỐ CỤC CHÍNH ---
# Sử dụng 2 cột: Một cột lớn cho Bảng và Điều khiển, Một cột nhỏ cho Chart
main_col, chart_col = st.columns([3, 1], gap="small")


# --- 5. ĐIỀU KHIỂN CHIẾN DỊCH ---
with main_col:
    st.markdown("### Điều khiển chiến dịch:")
    c1, c2, c3, c4 = st.columns(4, gap="small")

    with c1:
        # Nút THÊM BÀI ĐĂNG NGAY (placeholder for high visibility)
        st.button("+ THÊM BÀI ĐĂNG NGAY", use_container_width=True)
    with c2:
        # Nút DỪNG KHẨN CẤP (màu đỏ - placeholder)
        st.markdown('<div class="red-stop-btn">', unsafe_allow_html=True)
        st.button("DỪNG KHẨN CẤP (STOP CAMPAIGN)", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.button("Tải Report về (Export CSV)", use_container_width=True)
    with c4:
        st.button("Lập lịch (Robot hoạt động theo Quota)", use_container_width=True)


    # --- 6. BẢNG DỮ LIỆU ---
    # Heading cho bảng với thống kê
    table_head_col1, table_head_col2, table_head_col3 = st.columns([3, 1, 1])
    with table_head_col1:
        st.markdown("### Sắp tới: [ **10 Bài** ] - Đã xong: [ **254 Bài** ]")
    with table_head_col2:
        # Mock hiển thị số dòng
        st.selectbox("Hiển thị:", options=[10, 20, 50, 100], index=0)
    with table_head_col3:
        pass # Placeholder for pagination logic space

    # Tạo mock DataFrame cho bảng
    data = {
        "Website": ["Blog Lái Hộ 1", "Blog Lái Hộ 2", "Blog Lái Hộ 3"],
        "Nền tảng": ["Blogger", "Wordpress", "Wordpress"],
        "URL / ID": ["blog-lai-ho-1.blogspot.com", "blog-lai-ho-2.wordpress.com", "laiho.vn/id3"],
        "Ngày đăng bài": ["2026-03-23", "2026-03-23", "2026-03-23"],
        "Từ khoá 1": ["lái xe hộ", "dịch vụ lái xe tphcm", "lái xe khi say"],
        "Từ khoá 2": ["lái hộ tphcm", "tài xế lái hộ", "thuê tài xế lái xe"],
        "Tiêu đề bài viết": ["Dịch vụ lái xe hộ uy tín tại TPHCM", "Tài xế lái xe khi say rượu - Phục vụ 24/7", "Thuê tài xế lái xe hộ theo ngày - Mr. JunDeng"],
        "File ID Drive": ["1vA8y0H...", "1xZ9y8Q...", "1bC5y2V..."],
        "Thời gian hẹn giờ": ["08:30", "10:15", "14:45"],
        "Trạng thái": ["DONE", "DONE", "PENDING"] # Placeholder for colored DONE labels
    }
    df = pd.DataFrame(data)

    # Hiển thị bảng
    # Sử dụng st.dataframe để có thể tương tác (sort, v.v.)
    # Lưu ý: Các icon và tags DONE có thể cần markdown tùy chỉnh nếu dùng st.table, nhưng để
    # script này hoạt động trên Streamlit tiêu chuẩn và giữ tính năng tương tác, st.dataframe là tốt nhất.
    # Cell styling like tags is limited in standard st.dataframe.
    st.dataframe(df, use_container_width=True)

    # Mock Pagination
    pagination_col1, pagination_col2 = st.columns([1, 4])
    with pagination_col1:
        st.markdown("<p style='text-align: left; color: gray;'>Tổng số: [ **264 Bài** ]</p>", unsafe_allow_html=True)
    with pagination_col2:
        # Pagination buttons simulation
        p_c1, p_c2, p_c3, p_c4, p_c5, p_c6 = st.columns(6, gap="small")
        with p_c1: st.button("Trước", key="prev", use_container_width=True)
        with p_c2: st.button("1", key="p1", use_container_width=True)
        with p_c3: st.button("2", key="p2", use_container_width=True)
        with p_c4: st.button("3", key="p3", use_container_width=True)
        with p_c5: st.button("...", key="pdot", use_container_width=True)
        with p_c6: st.button("Tiếp", key="next", use_container_width=True)


# --- 7. BỐ CỤC PHẢI (CHART) ---
with chart_col:
    st.markdown("### Index Google trong 30 Ngày")
    st.markdown("**Tỷ lệ Index (30 ngày gần nhất)**")

    # Mock dữ liệu Chart
    chart_data = {
        "Trạng thái Index": ["DONE Index", "PENDING Index", "FAILED Index"],
        "Số lượng": [254, 10, 5] # Mock counts
    }
    df_chart = pd.DataFrame(chart_data)

    # Tính toán phần trăm (cho Plotly hover or labels)
    total_index = df_chart["Số lượng"].sum()
    df_chart["Phần trăm"] = (df_chart["Số lượng"] / total_index) * 100

    # Tạo Pie chart sử dụng Plotly Express
    # Tùy chỉnh màu sắc để khớp với ảnh
    color_map = {
        "DONE Index": "#4CAF50", # Green
        "PENDING Index": "#2196F3", # Blue
        "FAILED Index": "#F44336" # Red
    }

    fig = px.pie(
        df_chart,
        values="Số lượng",
        names="Trạng thái Index",
        color="Trạng thái Index",
        color_discrete_map=color_map,
        hole=0.5, # Tạo Chart Donut giống ảnh
        # hover_data=["Phần trăm"], # Thêm phần trăm khi hover
    )

    # Tùy chỉnh layout để ẩn legend mặc định (có thể tái tạo custom legend)
    # hoặc giữ legend để trực quan. Trong ảnh, legend được hiển thị.
    #fig.update_layout(showlegend=False)
    # Hoặc tùy chỉnh legend
    fig.update_layout(legend=dict(
        orientation="v", # Vertical
        yanchor="middle",
        y=0.5,
        xanchor="left",
        x=1,
    ))
    # Hiển thị phần trăm và labels
    fig.update_traces(textposition='inside', textinfo='percent')

    st.plotly_chart(fig, use_container_width=True)

    # Custom Legend (nếu muốn ẩn legend Plotly mặc định và tạo cái khớp hơn)
    # Legend in image is vertical list of items.
    # The default Plotly legend is quite good. I'll stick with it for simplicity.
    # For a *perfect* match, more CSS or custom HTML for legend would be needed.


# --- 8. PHẦN CHÂN TRANG (FOOTER) ---
# st.markdown("---")
# st.markdown("<p style='text-align: center; color: gray;'>Hệ thống quản lý SEO Lái Hộ V55.0 - Bản quyền Mr. JunDeng</p>", unsafe_allow_html=True)
