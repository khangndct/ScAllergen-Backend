
import requests
import json



dataset = []

dataset.append({
    "request": {
        "user_allergens": ["dairy food product"],
        "scanned_ingredients": ["custard","nougat","ghee","pudding","recaldent","simplesse","tagatose","casein","whey","diacetyl",
                                "sorbet", "soy milk", "almond milk", "oat milk", "coconut milk", "tofu", "nutrition yeast", "olive oil", "dark chocolate", "rice"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["egg food product"],
        "scanned_ingredients": ["mayonnaise", "meringue", "surimi", "eggnog", "marzipan", "marshmallow", "hollandaise sauce", "lysozyme", "albumin", "vitellin",
                                "applesauce", "chia seeds", "flaxseeds", "commercial egg replacer", "yogurt", "beans", "vegetables", "rice", "bread(vegan)", "pasta(egg-free)"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["soybean food product"],
        "scanned_ingredients": ["edamame", "miso", "natto", "shoyu", "soy sauce", "tamari", "tempeh", "tofu", "textured vegetable protein", "vegetable broth",
                                "fresh meat", "fresh fish", "egg", "cheese", "fresh fruit", "vegetables", "corn", "rice", "beans", "olive oil"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["peanut food product"],
        "scanned_ingredients": ["mole sauce", "beer nuts", "goobers", "mandelonas", "arachis oil", "nu-nuts", "lupine", "nougat", "marzipan", "egg rolls",
                                "sunflower butter", "soy nut butter", "almond butter", "cashew butter", "pumpkin seeds", "raisins", "pretzels", "popcorn", "cheese", "vegetables"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["nut food product"],
        "scanned_ingredients": ["pesto", "gianduja", "marzipan", "praline", "mortadella", "lychee nut", "pignoli", "filbert", "macadiaia nut", "nut distillates",
                                "nutmeg", "water chestnut", "butternut squash", "sunflower seeds", "sesame seeds", "pumpkin seeds", "oats", "chickpeas", "soybeans", "coconut"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["wheat food product"],
        "scanned_ingredients": ["seitan", "bulgur", "couscous", "farina", "semolina", "kamut", "spelt", "matzoh", "pasta", "bread",
                                "rice", "corn", "amaranth", "buckwheat", "millet", "tapioca", "potatoes", "tamari", "quinoa", "sorghum"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["fish food product"],
        "scanned_ingredients": ["worcestershire sauce", "caesar salad dressing", "bouillabaisse", "fish sauce", "caviar", "roe", "lutefisk", "fish gelatin", "caponata", "surimi",
                                "chicken", "beef", "pork", "lamb", "eggs", "beans", "tofu", "dairy", "vegetables", "shellfish"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})

dataset.append({
    "request": {
        "user_allergens": ["shellfish food product"],
        "scanned_ingredients": ["barnacle", "crawfish", "krill", "surimi", "bouillabaisse", "glucosamine", "cuttlefish ink", "scampi", "fish stock", "abalone",
                                "fin fish", "carrageenan", "chicken", "beef", "pork", "tofu", "eggs", "dairy", "grains", "fruits"]
    },
    "result": ["*","*","*","*","*","*","*","*","*","*", "","","","","","","","","",""]
})





SERVER_URL = "http://localhost:8000/check"

# ==========================================
# 3. HÀM ĐÁNH GIÁ (EVALUATION LOGIC)
# ==========================================
def evaluate_model():
    stats = {
        "total_items": 0,
        "true_positive": 0, # Đúng là có dị ứng
        "true_negative": 0, # Đúng là an toàn
        "false_positive": [], # Sai: Báo nhầm là có dị ứng (Gây phiền)
        "false_negative": [], # Sai: Bỏ sót dị ứng (NGUY HIỂM)
        "errors": 0
    }

    print("🚀 Đang gửi request và phân tích kết quả...\n")

    for idx, case in enumerate(dataset):
        payload = case["request"]
        expected_results = case["result"]
        allergen_type = payload["user_allergens"][0]

        try:
            # --- GỬI REQUEST THỰC TẾ ---
            response = requests.post(SERVER_URL, json=payload)
            data = response.json()
            actual_results = data.get("ingredients_allergies", [])

            if len(actual_results) != len(expected_results):
                print(f"⚠️ Lỗi: Server trả về số lượng không khớp ở case {allergen_type}")
                stats["errors"] += 1
                continue

            # So sánh từng nguyên liệu
            for i, ingredient in enumerate(payload["scanned_ingredients"]):
                stats["total_items"] += 1
                
                # Logic xác định
                is_expected_unsafe = (expected_results[i] == "*")
                is_actual_unsafe = (actual_results[i] != "")

                if is_expected_unsafe and is_actual_unsafe:
                    stats["true_positive"] += 1
                elif not is_expected_unsafe and not is_actual_unsafe:
                    stats["true_negative"] += 1
                elif not is_expected_unsafe and is_actual_unsafe:
                    # False Positive: Đáng lẽ an toàn -> Báo hại
                    stats["false_positive"].append({
                        "allergen": allergen_type,
                        "ingredient": ingredient,
                        "server_said": actual_results[i]
                    })
                elif is_expected_unsafe and not is_actual_unsafe:
                    # False Negative: Đáng lẽ hại -> Báo an toàn (NGUY HIỂM)
                    stats["false_negative"].append({
                        "allergen": allergen_type,
                        "ingredient": ingredient,
                        "server_said": "Safe (Empty)"
                    })

        except Exception as e:
            print(f"❌ Kết nối thất bại ở case {allergen_type}: {e}")
            stats["errors"] += 1

    # ==========================================
    # 4. BÁO CÁO KẾT QUẢ
    # ==========================================
    print("="*60)
    print(f"{'TESTING REPORT':^60}")
    print("="*60)
    
    total = stats['total_items']
    if total == 0:
        print("Không có dữ liệu để đánh giá.")
        return

    accuracy = (stats['true_positive'] + stats['true_negative']) / total * 100
    fn_count = len(stats['false_negative'])
    fp_count = len(stats['false_positive'])

    print(f"Amount of testcase: {total}")
    print(f"Accuracy: {accuracy:.2f}%")
    print("-" * 60)
    
    # BÁO CÁO FALSE NEGATIVE (QUAN TRỌNG NHẤT)
    print(f"⚠️  FALSE NEGATIVES (DANGER): {fn_count} cases")
    if fn_count > 0:
        print(f"{'Allergen':<15} | {'Food':<30}")
        print("-" * 50)
        for item in stats['false_negative']:
            print(f"{item['allergen']:<15} | {item['ingredient']:<30}")
    else:
        print("✅ Tuyệt vời! Không có trường hợp bỏ sót nguy hiểm nào.")

    print("\n" + "-" * 60)

    # BÁO CÁO FALSE POSITIVE
    print(f"⚠️  FALSE POSITIVES (ANNOYED): {fp_count} cases")
    if fp_count > 0:
        print(f"{'Allergen':<15} | {'Food':<30} | {'Server response'}")
        print("-" * 60)
        for item in stats['false_positive']:
            print(f"{item['allergen']:<15} | {item['ingredient']:<30} | {item['server_said']}")
    else:
        print("✅ Tuyệt vời! Không có trường hợp báo nhầm nào.")

    print("="*60)

if __name__ == "__main__":
    evaluate_model()

