# lib/create_synonym_cache.py
from neo4j import Driver

# --- BIẾN TOÀN CỤC ---
# 1. Map xuôi: Label -> [syn1, syn2...] (Để bung rộng User Allergen)
LABEL_TO_SYNONYMS = {} 

# 2. Map ngược: Keyword -> {Label1, Label2...} (Để tìm đích nhanh từ Scan)
KEYWORD_TO_LABELS = {}

def load_synonym_cache(driver: Driver):
    """
    Load toàn bộ Label và Synonyms từ Neo4j để xây dựng Reverse Index.
    Chạy độc lập với Fuzzy Matching để dễ debug.
    """
    global LABEL_TO_SYNONYMS, KEYWORD_TO_LABELS
    
    print("⏳ Building Synonym Reverse Index (Exact Match)...")
    
    # Reset cache
    LABEL_TO_SYNONYMS = {}
    KEYWORD_TO_LABELS = {}
    
    # Query chỉ lấy những trường cần thiết cho Synonym
    query = """
    MATCH (n:FoodOnTerm)
    RETURN n.label AS label, n.synonyms AS synonyms
    """
    
    count = 0
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            label = record["label"]
            synonyms = record["synonyms"] or [] # Bảo vệ chống None
            
            if not label:
                continue

            # Chuẩn hóa
            clean_label = label.lower().strip()
            
            # Tạo tập hợp keywords cho node này
            # Bao gồm chính label của nó và các synonyms
            all_keywords = set()
            all_keywords.add(clean_label)
            
            for s in synonyms:
                if s:
                    all_keywords.add(s.lower().strip())
            
            # -------------------------------------------------------
            # 1. LƯU MAP XUÔI (LABEL -> LIST SYNONYMS)
            # -------------------------------------------------------
            # Dùng để: User nhập "Egg Product" -> Hệ thống hiểu là ["egg", "eggs", "egg product"]
            LABEL_TO_SYNONYMS[label] = list(all_keywords)

            # -------------------------------------------------------
            # 2. LƯU MAP NGƯỢC (KEYWORD -> LIST LABELS)
            # -------------------------------------------------------
            # Dùng để: Scan thấy "egg" -> Hệ thống biết nó thuộc về ["Egg Product", "Raw Egg"...]
            for kw in all_keywords:
                if kw not in KEYWORD_TO_LABELS:
                    KEYWORD_TO_LABELS[kw] = set()
                KEYWORD_TO_LABELS[kw].add(label)
            
            count += 1

    print(f"✅ Synonym Cache Built! Indexed {len(KEYWORD_TO_LABELS)} keywords from {count} nodes.")

# --- GETTERS ---
def get_synonyms_of_label(label: str):
    """Lấy danh sách synonym mở rộng của một label"""
    return LABEL_TO_SYNONYMS.get(label, [])

def get_nodes_by_keyword(keyword: str):
    """Tìm danh sách các Node Label có chứa keyword này"""
    return KEYWORD_TO_LABELS.get(keyword.lower().strip(), set())