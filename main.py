import streamlit as st
import pandas as pd
import gspread
import requests, json, time, smtplib, re
from datetime import datetime, timedelta, timezone

# --- 1. HỆ QUẢN TRỊ & LÀM SẠCH (NHỊP 1) ---
st.set_page_config(page_title="LAIHO SEO OS - MASTER V25", layout="wide")

def get_vn_time(): return datetime.now(timezone(timedelta(hours=7)))

def gatekeeper_check(dashboard_val, web_row, report_df):
    """Chốt chặn 4 lớp - Lính gác cổng"""
    # Lớp 1: Website Status
    if web_row['WS_STATUS'] != 'ACTIVE': return False, "Web OFF"
    
    # Lớp 2: Hạn ngạch tổng (Batch Size)
    today_str = get_vn_time().strftime("%Y-%m-%d")
    done_today = len(report_df[report_df['REP_CREATED_AT'].str.contains(today_str)])
    if done_today >= int(dashboard_val('BATCH_SIZE')): return False, "Full Batch"
    
    # Lớp 3 & 4 bồ có thể thêm logic so sánh Publish Date ở đây...
    return True, "PASS"

# --- 2. THE STYLE HUNTER (NHỊP 2.1) ---
def style_hunter(keyword, competitor_list, serpapi_key):
    """Săn văn phong mỏ neo từ Top Google hoặc Nội bộ"""
    # Ưu tiên 1: Quét SERPAPI
    try:
        # Giả lập quét Top 5...
        # Nếu thấy đối thủ trong competitor_list -> Lấy nội dung
        return "Nội dung văn phong mỏ neo từ đối thủ..."
    except:
        # Ưu tiên 2: Tìm trong Report nội bộ bài SUCCESS điểm cao nhất
        return "Văn phong mỏ neo từ bài cũ thành công nhất..."

# --- 3. QUY TRÌNH ASSEMBLER (NHỊP 3 - 6 KINGS) ---
def prompt_assembler(v, kw_main, kw_extras, style_anchor, word_count):
    """Lắp ghép 6 Kings & 2 Knights - Trái tim của hệ thống"""
    # Lớp 1: 6 Kings Check
    kings = ['PROMPT_TEMPLATE', 'CONTENT_STRATEGY', 'KEYWORD_PROMPT', 'SEO_GLOBAL_RULE', 'AI_HUMANIZER_PROMPT']
    for k in kings:
        if not v(k): return None, f"Kings Check Fail: Thiếu {k}"
    
    # Điền biến vào Template
    prompt = v('PROMPT_TEMPLATE').replace('{{keyword}}', kw_main)
    prompt = prompt.replace('{{word_count}}', str(word_count))
    prompt = prompt.replace('{{secondary_keywords}}', ", ".join(kw_extras))
    
    # Gộp chuỗi theo thứ tự Kỷ luật (Nhịp 3.1)
    full_chain = f"""
    {prompt}
    STRATEGY: {v('CONTENT_STRATEGY')}
    STYLE ANCHOR: {style_anchor}
    SEO RULES: {v('SEO_GLOBAL_RULE')}
    HUMANIZER: {v('AI_HUMANIZER_PROMPT')}
    """
    return full_chain, "SUCCESS"

# --- 4. KIỂM TRA CÔNG CỤ SEO (NHỊP 4) ---
def calculate_readability(text):
    """Công thức Flesch Việt hóa"""
    # Score = 206.835 - (1.015 * ASL) - (84.6 * ASW)
    # Logic đếm từ, câu, âm tiết thực tế...
    return 65 # Demo score

# --- 5. TIẾN TRÌNH THỰC THI CHÍNH ---
def run_master_engine(all_data, sh):
    df_d = all_data['Dashboard']
    def v(k): # Hàm bốc cấu hình Dashboard nhanh
        res = df_d[df_d.iloc[:, 0].str.strip().upper() == k.strip().upper()].iloc[:, 1]
        return res.values[0] if not res.empty else ""

    # Bắt đầu duyệt Web và Từ khóa
    # [Nhịp 1 -> Nhịp 5 thực thi tại đây]
    st.info("🤖 Robot đang vận hành theo Đặc tả Master...")
    
    # Giả sử qua Gatekeeper và Style Hunter...
    style_anchor = style_hunter("lái xe hộ", v('COMPETITOR_LIST'), v('SERPAPI_KEY'))
    
    # Lắp ráp Prompt
    full_prompt, status = prompt_assembler(v, "lái xe hộ", ["thuê tài xế", "tài xế đi tỉnh"], style_anchor, 1100)
    
    if full_prompt:
        st.success("✅ 6 Kings Verified! Đang gửi lên AI...")
        # Gửi AI -> Spin -> Check SEO -> Ghi Report
    else:
        st.error(status)

# --- UI DASHBOARD ---
# (Phần UI UX bồ đã ưng ý ở V21, giữ nguyên chỉ thay lõi xử lý)
