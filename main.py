def get_serp_style_rotating(kw, keys_string, competitor_list):
    # Tách danh sách Key và làm sạch (Trim) từng cái một
    all_serp_keys = [k.strip() for k in keys_string.split(',') if k.strip()]
    if not all_serp_keys: return ""

    competitors = [c.strip().lower() for c in competitor_list.split(',') if c.strip()]
    
    # Vòng lặp xoay vòng Key
    for current_key in all_serp_keys:
        try:
            params = {
                "q": kw,
                "location": "Vietnam",
                "hl": "vi",
                "gl": "vn",
                "api_key": current_key
            }
            # Cầu chì thời gian 15s cho mỗi lần thử
            response = requests.get("https://serpapi.com/search", params=params, timeout=15)
            
            # Nếu Key hết hạn hoặc sai (403/429), nhảy sang Key kế tiếp
            if response.status_code in [403, 429]:
                continue 
                
            results = response.json().get("organic_results", [])
            if not results: continue

            style_anchor = ""
            for res in results[:5]:
                link = res.get("link", "").lower()
                if any(comp in link for comp in competitors):
                    style_anchor = f"Tiêu đề đối thủ: {res.get('title')}. Tóm tắt: {res.get('snippet')}"
                    break
            
            if not style_anchor:
                style_anchor = f"Tiêu đề Top 1: {results[0].get('title')}. Tóm tắt: {results[0].get('snippet')}"
            
            return style_anchor # Trả về kết quả ngay khi 1 Key thành công
            
        except:
            continue # Lỗi mạng hoặc lỗi khác, thử Key tiếp theo

    return "" # Nếu thử hết sạch Key vẫn tạch thì trả về rỗng để dùng văn phong mặc định
