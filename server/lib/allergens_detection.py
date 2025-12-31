from typing import List, Optional

def check_graph_connection(scan_label: str, mapped_user_allergies_label: List[str], driver):
    """
    CHECK HAS PATH BETWEEN SCANNED INGREDIENT AND ALL ELEMENTS INT USER-DEFINED ALLERGEN LIST APOC
    
    Return: String tên dị nguyên, số bước, và PATH.
    """

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
    MATCH (allergen:FoodOnTerm) WHERE allergen.label IN $mapped_user_allergies_label

    
    WITH scan, allergen
    
    CALL apoc.path.expandConfig(scan, {
        relationshipFilter: $rels,
        maxLevel: 7,
        terminatorNodes: [allergen]
    }) YIELD path
    
    // 4. LỌC VÀ CHUẨN BỊ KẾT QUẢ
    WITH allergen.label AS allergen_label, nodes(path) AS path_nodes, relationships(path) AS path_rels, length(path) AS path_length 
    WHERE path IS NOT NULL AND path_length >= 0 
    
    // 5. Thu thập Node Labels và Relationship Types
    WITH allergen_label, path_length, path_nodes, path_rels
    
    // Sử dụng REDUCE để xây dựng chuỗi PATH
    WITH allergen_label, path_length, 
         REDUCE(s = [head(path_nodes).label], i IN RANGE(0, size(path_rels) - 1) | 
             s + [type(path_rels[i]) + "->", path_nodes[i+1].label]
         ) AS path_elements
         
    RETURN DISTINCT allergen_label, path_length, REDUCE(s = "", x IN path_elements | s + x) AS full_path
    ORDER BY path_length ASC
    LIMIT 1
    """
    

    with driver.session() as session:
        result = session.run(query, 
                                scan_label=scan_label, 
                                mapped_user_allergies_label=mapped_user_allergies_label, 
                                rels=allowed_rels).single()

        
        if result:
            allergen_label = result["allergen_label"]
            # path_length = record["path_length"]
            # full_path = record["full_path"]
            
            # Trả về kết quả
            return allergen_label
            # return f"{allergen_label} (Path length: {path_length}). PATH: {full_path}"

        # NOT FOUND ANY PATH
        return None