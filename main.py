import streamlit as st
import pandas as pd

# Cấu hình cực nhẹ
st.set_page_config(page_title="FIXED", layout="wide")

st.title("🚕 LÁI HỘ SEO - ĐÃ TỈNH TÁO!")
st.balloons() # Hiện bong bóng ăn mừng nếu chạy thành công

# Khởi tạo data đơn giản
if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame([
        ["Trạng thái", "Đại dương đã hiện ra!"],
        ["Hướng dẫn", "Bây giờ Ní có thể dán lại code 7 Tab rồi đó."]
    ], columns=["Hạng mục", "Giá trị"])

st.success("Chúc mừng Ní! Hệ thống đã thoát khỏi vòng xoáy tử thần.")

st.data_editor(st.session_state['df'], use_container_width=True, hide_index=True)
