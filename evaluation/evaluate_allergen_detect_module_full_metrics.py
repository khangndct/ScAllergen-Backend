import requests
import json
from collections import defaultdict

# ================= CONFIGURATION =================
DATASET_FILE = "multilabel_dataset.json" # Use the multilabel dataset
SERVER_URL = "http://localhost:8000/check"

SUPPORTED_ALLERGENS = [
    "dairy food product", "egg food product", "soybean food product", 
    "peanut food product", "wheat food product", "shellfish food product", 
    "fish food product", "nut food product"
]

def evaluate():
    try:
        with open(DATASET_FILE, 'r', encoding='utf-8') as f: dataset = json.load(f)
    except:
        print(f"❌ Could not find file '{DATASET_FILE}'!"); return

    print(f"🚀 STARTING DIAGNOSTIC TEST & EVALUATION...\n")
    
    # Extended Stats
    stats = defaultdict(lambda: {
        "TP": 0, "TN": 0, "FP": 0, 
        "FN_Missing_Node": 0,   # Vocabulary not in DB
        "FN_Broken_Link": 0     # Node exists but no relationship
    })
    
    # Detailed logs for later printing
    broken_link_logs = []
    missing_node_logs = []

    total = len(dataset)
    
    for i, item in enumerate(dataset):
        prod_name = item['product_name'][:30]
        ingredients = item['scanned_ingredients']
        ground_truth_list = item['true_allergens']
        
        if i % 10 == 0: print(f"Checking {i}/{total}...", end="\r")

        # --- LOOP THROUGH 8 ALLERGEN TYPES ---
        for test_allergen in SUPPORTED_ALLERGENS:
            expected_unsafe = test_allergen in ground_truth_list
            
            try:
                # Call API
                resp = requests.post(SERVER_URL, json={
                    "user_allergens": [test_allergen],
                    "scanned_ingredients": ingredients
                }).json()

                # Get important data from backend
                # 1. List of mapped Node names (e.g., ["Milk", "", "Whey"])
                mapped_labels = resp.get("mapped_scanned_allergies_label", [])
                
                # 2. List of alerts (e.g., ["Unsafe", "", ""])
                alerts = resp.get("ingredients_allergies", [])
                
                # Check if there are any alerts
                actual_unsafe = any(x != "" for x in alerts)

            except Exception as e:
                continue

            # --- CLASSIFY RESULTS ---
            if expected_unsafe and actual_unsafe:
                stats[test_allergen]["TP"] += 1
                
            elif not expected_unsafe and not actual_unsafe:
                stats[test_allergen]["TN"] += 1
                
            elif not expected_unsafe and actual_unsafe:
                stats[test_allergen]["FP"] += 1
                
            elif expected_unsafe and not actual_unsafe:
                # === ANALYZE FALSE NEGATIVE (MISSED ALERT) ===
                
                is_broken_link = False
                
                # Iterate through submitted ingredients
                for idx, raw_ing in enumerate(ingredients):
                    if idx >= len(mapped_labels): break # Prevent index error
                    
                    node_name = mapped_labels[idx] # Node name in DB (or empty)
                    
                    if node_name != "":
                        # A. BROKEN LINK CASE:
                        # Server recognized the word (node_name has data)
                        # BUT did not alert (alert is empty)
                        is_broken_link = True
                        broken_link_logs.append({
                            "allergen": test_allergen,
                            "product": prod_name,
                            "raw_text": raw_ing,
                            "mapped_node": node_name,
                            "status": "Node Found but No Path"
                        })
                    else:
                        # B. MISSING NODE CASE:
                        # Server returned empty -> Word not found in DB
                        missing_node_logs.append({
                            "allergen": test_allergen,
                            "raw_text": raw_ing
                        })

                # Summary for this Test Case
                if is_broken_link:
                    stats[test_allergen]["FN_Broken_Link"] += 1
                else:
                    stats[test_allergen]["FN_Missing_Node"] += 1

    # ================= 1. DIAGNOSTIC REPORT =================
    print("\n" + "="*110)
    print(f"{'DIAGNOSTIC REPORT (RAW COUNTS)':^110}")
    print("="*110)
    print(f"{'ALLERGEN':<22} | {'TP':<5} {'TN':<5} {'FP':<5} | {'FN (Broken Graph)':<20} | {'FN (Missing Data)':<20}")
    print("-" * 110)

    for allergen in SUPPORTED_ALLERGENS:
        s = stats[allergen]
        print(f"{allergen:<22} | {s['TP']:<5} {s['TN']:<5} {s['FP']:<5} | {s['FN_Broken_Link']:<20} | {s['FN_Missing_Node']:<20}")

    print("-" * 110)

    # ================= 2. PERFORMANCE METRICS (NEW SECTION) =================
    print("\n" + "="*110)
    print(f"{'PERFORMANCE EVALUATION SCORECARD':^110}")
    print("="*110)
    print(f"{'ALLERGEN':<22} | {'Accuracy':<10} | {'Recall (Safety)':<15} | {'Precision':<10} | {'F1-Score':<10}")
    print(f"{'':<22} | {'(Overall)':<10} | {'(Avoid FN)':<15} | {'(Avoid FP)':<10} | {'(Balance)':<10}")
    print("-" * 110)

    total_tp = total_tn = total_fp = total_fn = 0

    for allergen in SUPPORTED_ALLERGENS:
        s = stats[allergen]
        # Combine both types of FN for total calculation
        fn_total = s['FN_Broken_Link'] + s['FN_Missing_Node']
        
        tp = s['TP']
        tn = s['TN']
        fp = s['FP']
        
        # Accumulate for system average
        total_tp += tp
        total_tn += tn
        total_fp += fp
        total_fn += fn_total

        # Calculate Metrics
        # Accuracy: (TP + TN) / Total
        accuracy = (tp + tn) / (tp + tn + fp + fn_total) * 100 if (tp + tn + fp + fn_total) > 0 else 0
        
        # Recall (Sensitivity): TP / (TP + FN) -> CRITICAL FOR SAFETY
        recall = tp / (tp + fn_total) * 100 if (tp + fn_total) > 0 else 0
        
        # Precision: TP / (TP + FP) -> Avoids false alarms
        precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
        
        # F1-Score: Harmonic mean
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        # Determine color/status for Recall (Safety)
        safety_status = "⚠️ LOW" if recall < 80 else "✅ GOOD"

        print(f"{allergen:<22} | {accuracy:6.2f}%    | {recall:6.2f}% {safety_status:<4} | {precision:6.2f}%    | {f1:6.2f}")

    print("-" * 110)
    
    # System Averages
    sys_acc = (total_tp + total_tn) / (total_tp + total_tn + total_fp + total_fn) * 100 if (total_tp + total_tn + total_fp + total_fn) > 0 else 0
    sys_recall = total_tp / (total_tp + total_fn) * 100 if (total_tp + total_fn) > 0 else 0
    sys_prec = total_tp / (total_tp + total_fp) * 100 if (total_tp + total_fp) > 0 else 0
    sys_f1 = 2 * (sys_prec * sys_recall) / (sys_prec + sys_recall) if (sys_prec + sys_recall) > 0 else 0

    print(f"{'SYSTEM OVERALL':<22} | {sys_acc:6.2f}%    | {sys_recall:6.2f}%          | {sys_prec:6.2f}%    | {sys_f1:6.2f}")
    print("=" * 110)

    # ================= 3. DEBUG LOGS =================
    
    print(f"\n🔴 URGENT: FIX BROKEN LINKS (Detected {len(broken_link_logs)} potential cases):")
    
    seen_broken = set()
    count = 0
    for item in broken_link_logs:
        key = f"{item['mapped_node']}->{item['allergen']}"
        if key not in seen_broken:
            print(f"   [x] Allergen: {item['allergen']:<20} | Node: '{item['mapped_node']}'")
            print(f"       => Fix: MATCH (a {{label: '{item['mapped_node']}'}}), (b {{label: '{item['allergen']}'}}) MERGE (a)-[:IS_A]->(b)")
            seen_broken.add(key)
            count += 1
            if count >= 5: 
                print("       (... and more)"); break

    print(f"\n🟡 DATA ENTRY: MISSING NODES (Sample):")
    seen_missing = set()
    count = 0
    for item in missing_node_logs:
        if item['raw_text'] not in seen_missing:
            print(f"   [?] '{item['raw_text']}'")
            seen_missing.add(item['raw_text'])
            count += 1
            if count >= 5:
                print("       (... and more)"); break

if __name__ == "__main__":
    evaluate()