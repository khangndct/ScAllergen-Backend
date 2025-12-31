import requests
import json
import re
import time

# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌CONFIGURATION                            ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟
OUTPUT_FILE = "multilabel_dataset.json"
TARGET_PER_CATEGORY = 50

TAG_MAPPING = {
    "en:milk": "dairy food product",
    "en:eggs": "egg food product",
    "en:soybeans": "soybean food product",
    "en:peanuts": "peanut food product",
    "en:gluten": "wheat food product",
    "en:crustaceans": "shellfish food product",
    "en:fish": "fish food product",
    "en:nuts": "nut food product"
}

ENGLISH_COUNTRIES = ["en:united-states", "en:united-kingdom", "en:australia", "en:canada", "en:new-zealand"]

def clean_ingredients_text(raw_text):
    if not raw_text: return []
    text = raw_text.lower().split("contains:")[0]
    text = re.sub(r'\s*\d+([.,]\d+)?\s*%', '', text)
    text = text.replace("(", ",").replace(")", "").replace("[", "").replace("]", "").replace(".", "")
    items = [x.strip() for x in text.split(',') if x.strip()]
    return list(set([x for x in items if len(x) > 2]))

def is_english(text):
    return any(w in text.lower() for w in ["ingredients", "water", "sugar", "salt", "milk"])

def fetch_products(off_tag):
    products_found = []
    page = 1
    
    # SỬA 1: Tăng giới hạn trang lên 20 hoặc 30 để đảm bảo gom đủ hàng
    MAX_PAGES = 30 
    
    while len(products_found) < TARGET_PER_CATEGORY and page <= MAX_PAGES:
        print(f"   ↳ Page {page}...", end="", flush=True)
        
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        params = {
            "action": "process",
            "tagtype_0": "allergens",
            "tag_contains_0": "contains",
            "tag_0": off_tag,
            "json": "1",
            "page": page,
            "page_size": 100, # Lấy 100 món mỗi lần gọi
            "fields": "code,product_name,ingredients_text,allergens_tags,countries_tags"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=10)
            
            # SỬA 2: Xử lý trường hợp API lỗi hoặc hết hàng
            if resp.status_code != 200:
                print(f" (API Error {resp.status_code}) ", end="")
                break
                
            items = resp.json().get('products', [])
            if not items: 
                print(" (End of data) ", end="")
                break
            
            for p in items:
                # Nếu đã đủ chỉ tiêu thì dừng ngay lập tức
                if len(products_found) >= TARGET_PER_CATEGORY: break
                
                raw_ing = p.get('ingredients_text', '')
                off_tags = p.get('allergens_tags', [])
                countries = p.get('countries_tags', [])

                # Filter cơ bản
                if not raw_ing or not is_english(raw_ing): continue
                if not any(c in ENGLISH_COUNTRIES for c in countries): continue

                # Chuẩn hóa Ground Truth
                true_allergens = []
                for tag in off_tags:
                    if tag in TAG_MAPPING:
                        true_allergens.append(TAG_MAPPING[tag])
                
                if not true_allergens: continue

                # Thêm vào danh sách (đảm bảo không trùng ID trong list tạm này)
                current_ids = {p['id'] for p in products_found}
                p_id = p.get('code')
                
                if p_id not in current_ids:
                    products_found.append({
                        "id": p_id,
                        "product_name": p.get('product_name', 'Unknown'),
                        "scanned_ingredients": clean_ingredients_text(raw_ing),
                        "true_allergens": list(set(true_allergens))
                    })
            
            print(f" Got {len(products_found)}/{TARGET_PER_CATEGORY} ", end="")
            page += 1
            
            # SỬA 3: Ngủ 1 xíu để tôn trọng Server
            time.sleep(0.5) 
            
        except Exception as e: 
            print(f" (Error: {e}) ", end="")
            break
            
    print("✅")
    return products_found

def main():
    print("🚀 BẮT ĐẦU CRAWL DATA ĐA NHÃN...")
    final_db = {} # Dùng dict để tránh trùng lặp sản phẩm
    
    for tag in TAG_MAPPING.keys():
        print(f"📂 Scanning {tag}...")
        items = fetch_products(tag)
        for item in items:
            final_db[item['id']] = item # Tự động loại trùng lặp nhờ ID

    data_list = list(final_db.values())
    print(f"\n💾 Lưu {len(data_list)} sản phẩm độc nhất vào '{OUTPUT_FILE}'...")
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data_list, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()