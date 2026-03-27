import streamlit as st
import pandas as pd
import requests, json, re
from datetime import datetime, timedelta, timezone

# --- LOGIC GỌI "NÃO BỘ VẠN NĂNG" ---
def call_openrouter(api_key, model_name, prompt):
    # Model mặc định nếu bồ không nhập là Gemini 1.5 Flash qua OpenRouter
    target_model = model_name if model_name else "google/gemini-flash-1.5"
    
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": target_model,
        "messages": [{"role": "user", "content": prompt}]
    }
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        res_json = response.json()
        if 'choices' in res_json:
            return res_json['choices'][0]['message']['content']
        else:
            return f"❌ Lỗi từ OpenRouter: {res_json.get('error', {}).get('message', 'Unknown Error')}"
    except Exception as e:
        return f"❌ Lỗi kết nối mạng: {str(e)}"

# --- GIAO DIỆN POPUP KIỂM TRA ---
@st.dialog("⚙️ TRUNG TÂM ĐIỀU KHIỂN VẠN NĂNG", width="large")
def run_universal_robot(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k):
        res = df_d[df_d.iloc[:, 0].str.strip() == k.strip()].iloc[:, 1]
        return str(res.values[0]).strip() if not res.empty else ""

    st.write("🔍 **Đang kiểm tra chìa khóa vạn năng...**")
    
    # Giả định bốc từ khóa xong
    kw_main = "Dịch vụ lái xe hộ chuyên nghiệp"
    prompt_final = f"Viết bài SEO về {kw_main} dựa trên quy tắc: {v('SEO_GLOBAL_RULE')}"

    # TRIỆU HỒI AI
    api_key = v('OPENROUTER_API_KEY')
    model_choice = v('MODEL_VERSION') # Ví dụ: "google/gemini-flash-1.5" hoặc "meta-llama/llama-3-70b"

    with st.spinner(f"🤖 Đang gọi não bộ {model_choice}..."):
        content = call_openrouter(api_key, model_choice, prompt_final)
        
        if "❌" in content:
            st.error(content)
            st.info("💡 Mẹo: Kiểm tra lại xem bồ đã nạp tiền vào OpenRouter chưa hoặc Key có đúng sk-or-... không.")
        else:
            st.success("✅ Thành công! Nội dung đã sẵn sàng.")
            with st.expander("Xem trước nội dung"):
                st.write(content)
            # Tiếp tục logic ghi Sheet ở đây...

# --- HOME ---
# (Phần hiển thị nút bấm ở Home giữ nguyên như bản trước)
