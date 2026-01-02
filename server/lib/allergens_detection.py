from typing import List, Optional
from lib.create_synonym_cache import get_synonyms_of_label, get_nodes_by_keyword

def check_graph_connection(scan_label: str, mapped_user_allergies_label: List[str], driver):
    """
    CHECK HAS PATH BETWEEN SCANNED INGREDIENT AND ALL ELEMENTS INT USER-DEFINED ALLERGEN LIST APOC
    """

    clean_allergen_labels = [l for l in mapped_user_allergies_label if l and l.strip()]
    if not clean_allergen_labels:
        return None
        
    # 1. Calculating terminated nodes in RAM (use function in create_synonym_cache module)
    sensitive_keywords = set()
    for allergen_label in clean_allergen_labels:
        syns = get_synonyms_of_label(allergen_label)
        sensitive_keywords.update(syns)
    
    target_node_labels = set()
    for kw in sensitive_keywords:
        nodes = get_nodes_by_keyword(kw)
        target_node_labels.update(nodes)
        
    target_labels_list = list(target_node_labels)
    
    # 2. Check nhanh
    if scan_label in target_labels_list:
        return scan_label

    allowed_rels = (
        "IS_A>|"                      # Quan hệ phân loại (Bắt buộc)
        "DERIVES_FROM>|"              # Nguồn gốc (Tofu -> Soybean)
        "IN_TAXON>|"                  # Sinh học (Salmon -> Fish)
        "PRODUCED_BY>|"               # Sinh vật tạo ra (Honey -> Bee)
        "PART_OF>|"                   # Là một phần (Yolk -> Egg)
        "HAS_PART<|"                  # (Ngược) Từ bộ phận -> Tổng thể
        "HAS_INGREDIENT>|"            # Thành phần món ăn
        "HAS_DEFINING_INGREDIENT>|"   # Thành phần chính
        "HAS_SUBSTANCE_ADDED>"        # Phụ gia thêm vào
    )
    
    
    query = """
        MATCH (scan:FoodOnTerm) WHERE scan.label = $scan_label
        
        // Neo4j chỉ cần Match vào đúng danh sách ID này (dùng Index Lookup cực nhanh)
        MATCH (terminator:FoodOnTerm)
        WHERE terminator.label IN $target_labels
        
        WITH scan, collect(terminator) AS final_terminator_nodes
        
        // SỬA 2: minLevel: 1 vì level 0 đã check ở Python rồi
        CALL apoc.path.expandConfig(scan, {
            relationshipFilter: $rels,
            minLevel: 0, 
            maxLevel: 7,
            terminatorNodes: final_terminator_nodes
        }) YIELD path
        
        // Lấy node đích (chỉ cần label để báo lỗi)
        RETURN last(nodes(path)).label AS allergen_label
        LIMIT 1
    """
    

    with driver.session() as session:
        result = session.run(query, 
                                scan_label=scan_label, 
                                target_labels=target_labels_list,
                                rels=allowed_rels).single()

        
        if result:
            allergen_label = result["allergen_label"]
            # path_length = record["path_length"]
            # full_path = record["full_path"]
            
            # Return result
            return allergen_label
            # return f"{allergen_label} (Path length: {path_length}). PATH: {full_path}"

        # NOT FOUND ANY PATH
        return None