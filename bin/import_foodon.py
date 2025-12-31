import time
from owlready2 import *
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌INITIAL CONFIGURATION                    ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "NXBn~JR4teZss;q")
ONTO_PATH = "/home/pak/Workspaces/Project/nutriviet/FoodOn/import/foodon-full.owl"
BATCH_SIZE = 1000

# Khởi tạo biến lưu thời gian
execution_times = {}
total_start_time = time.time()

print(">>> BẮT ĐẦU QUÁ TRÌNH BUILD KNOWLEDGE GRAPH...")


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 1: LOADING OWL FILE                 ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[1/5] Loading OWL file...")

# ... (Giữ nguyên logic cũ) ...
FOOD_CLASS_IRI = "http://purl.obolibrary.org/obo/FOODON_00002403"
CHEMICAL_CLASS_IRI = "http://purl.obolibrary.org/obo/CHEBI_24431"
ORGANISM_CLASS_IRI = "http://purl.obolibrary.org/obo/OBI_0100026"
INGREDIENT_CLASS_IRI = "http://purl.obolibrary.org/obo/FOODON_00004272"
PLANT_CLASS_IRI = "http://purl.obolibrary.org/obo/PO_0025131"
PROCESS_CLASS_IRI = "http://purl.obolibrary.org/obo/BFO_0000015"

onto = get_ontology(ONTO_PATH).load()
total_classes = []

execution_times['Load OWL'] = time.time() - step_start
print(f"-> Done in {execution_times['Load OWL']:.2f} seconds")

# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌IMPORT FUNCTIONS DEFINITION              ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

driver = GraphDatabase.driver(URI, auth=AUTH)

def get_descendants(root_class_iri):
    root_class = onto.search_one(iri=root_class_iri)
    if not root_class:
        print(f"Not found root class IRI: {root_class_iri}")
        exit()
    return root_class.descendants()

def import_batch(tx, data_list, root_label):
    query = (
        f"UNWIND $batch AS row "
        f"MERGE (n:FoodOnTerm {{iri: row.iri}}) "
        f"SET n.name = row.name, "
        f"    n.label = row.label "
        f"SET n:`{root_label}`"
    )
    tx.run(query, batch=data_list)

def setup_constraints():
    query = "CREATE CONSTRAINT IF NOT EXISTS FOR (n:FoodOnTerm) REQUIRE n.iri IS UNIQUE"
    session.run(query)
    print(f"-> Has setup UNIQUE Constraint for FoodOnTerm")

def clean_label(raw_name):
    clean = re.sub(r'\s*\((efsa foodex2|gs1 gpc|perishable|cp|ccpr)\)', '', raw_name)
    clean = re.sub(r'^\d+\s*-\s*', '', clean)
    clean = clean.strip('-')
    clean = clean.lower()
    return clean.strip()

def import_descendants(classes, root_label):
    print(f"Importing {root_label} nodes...")
    batch_data = []
    count = 0
    for cls in classes:
        total_classes.append(cls)

        # try:
        #     node_label = cls.label[0] if cls.label else cls.name
        # except ValueError:
        #     node_label = cls.name
        # node_label = clean_label(node_label)

        # node_data = {
        #     "iri": cls.iri,
        #     "name": cls.name,
        #     "label": node_label
        # }
        #----------------------------------
        try:
            # 1. Mặc định raw_label là ID ngắn của Term (cls.name)
            raw_label = cls.name 
            
            # 2. Kiểm tra và cố gắng lấy label
            if hasattr(cls, 'label') and cls.label:
                english_label = None
                for lbl in cls.label:
                    if isinstance(lbl, str) and lbl.endswith('@en'): 
                        english_label = lbl.split('@')[0]
                        break
                    if isinstance(lbl, str): 
                        english_label = lbl 
                
                if english_label:
                    raw_label = english_label
                elif cls.label:
                    raw_label = cls.label[0]
            
            # 3. Làm sạch label
            final_label = clean_label(raw_label)
            
        except Exception as e:
            # Bắt lỗi ValueError (Cannot read literal...) hoặc bất kỳ lỗi nào khác 
            # xảy ra trong quá trình đọc Term này.
            # Dùng ID Term làm label dự phòng an toàn.
            print(f"⚠️ Warning: Failed to read label for {cls.name} ({cls.iri}). Error: {e}. Using ID as label.")
            final_label = clean_label(cls.name)
        #----------------------------------

        final_label = clean_label(raw_label)
        node_data = {
            "iri": cls.iri,
            "name": cls.name,
            "label": final_label
        }


        batch_data.append(node_data)

        if len(batch_data) >= BATCH_SIZE:
            session.execute_write(import_batch, batch_data, root_label)
            batch_data = []
            count += BATCH_SIZE
            print(f"Import {count} nodes...")

    if batch_data:
        session.execute_write(import_batch, batch_data, root_label)
    print("Done!")

RELATION_MAP = {
    "http://purl.obolibrary.org/obo/FOODON_00001301": "HAS_FOOD_SUBSTANCE_ANALOG",
    "http://purl.obolibrary.org/obo/RO_0001000":      "DERIVES_FROM",
    "http://purl.obolibrary.org/obo/RO_0002350":      "MEMBER_OF",
    "http://purl.obolibrary.org/obo/RO_0009001":      "HAS_SUBSTANCE_ADDED",
    "http://purl.obolibrary.org/obo/RO_0002162":      "IN_TAXON",
    "http://purl.obolibrary.org/obo/BFO_0000051":     "HAS_PART",
    "http://purl.obolibrary.org/obo/FOODON_00002420": "HAS_INGREDIENT",
    "http://purl.obolibrary.org/obo/FOODON_00001563": "HAS_DEFINING_INGREDIENT",
}

all_rels = {"IS_A": []}
for k in RELATION_MAP.values():
    all_rels[k] = []

def import_relationships_batch(tx, batch, rel_type):
    query = (
        f"UNWIND $batch AS row "
        f"MATCH (source: FoodOnTerm {{iri: row.source}}) " 
        f"MERGE (target: FoodOnTerm {{iri: row.target}}) " 
        f"MERGE (source)-[:{rel_type}]->(target)"
    )
    tx.run(query, batch=batch)

def import_relations(classes):
    rel_batch = []
    # Logic cũ của bạn
    for cls in classes:
        for item in cls.is_a:
            if hasattr(item, "iri"):
                all_rels["IS_A"].append({
                    "source": cls.iri,
                    "target": item.iri
                })
            elif isinstance(item, Restriction):
                prop_iri = item.property.iri
                target_val = item.value
                if prop_iri in RELATION_MAP and hasattr(target_val, "iri"):
                    rel_name = RELATION_MAP[prop_iri]
                    all_rels[rel_name].append({
                        "source": cls.iri,
                        "target": target_val.iri
                    })

    for rel_type, data_list in all_rels.items():
        if not data_list:
            continue
        print(f"-> Importing {rel_type} ({len(data_list)} pairs)...")
        for i in range(0, len(data_list), BATCH_SIZE):
            batch = data_list[i : i + BATCH_SIZE]
            session.execute_write(import_relationships_batch, batch, rel_type)

def remove_nameless_nodes():
    """
    Xóa các node FoodOnTerm không có thuộc tính 'name' HOẶC 'label' 
    (dùng cú pháp Cypher mới: IS NULL/IS NOT NULL).
    """
    # Đã sửa lỗi cú pháp Cypher: thay NOT EXISTS(n.name) bằng n.name IS NULL
    query = """
    MATCH (n:FoodOnTerm) 
    WHERE n.label IS NULL
    DETACH DELETE n
    """
    with driver.session() as session:
        try:
            # Chạy query đếm trước để biết số lượng node bị xóa
            count_query = """
            MATCH (n:FoodOnTerm) 
            WHERE n.name IS NULL OR n.label IS NULL
            RETURN count(n) AS deleted_count
            """
            count_result = session.run(count_query).single()
            deleted_count = count_result["deleted_count"] if count_result else 0
            
            # Thực thi lệnh xóa
            session.run(query)
            
            print(f"✅ Đã xóa thành công {deleted_count} node thiếu 'name' hoặc 'label'.")
            
        except Exception as e:
            print(f"❌ Lỗi khi xóa node thiếu thuộc tính: {e}")


def import_allergen_nodes():
    print("Import Allergen nodes")
    allergen_node_labels = [
        "nut", "walnut", "almond", "hazelnut", "cashew", "pistachio",
        "dairy", "milk", "cow milk", "goat milk", "fish",
        "shellfish", "crustacean", "crayfish", "crawfish", "lobster",
        "crab", "shrimp", "mollusc", "scallop", "oyster", "mussel",
        "snail", "clam", "egg", "chicken egg",
        "fruit", "melon", "apple", "apricot", "cherry", "plum",
        "tomato", "orange", "legume",
        "peas", "soybeans", "lentil", "peanut", "beans",
        "sesame", "wheat", "gluten"
    ]
    for node_label in allergen_node_labels:
        session.run(r"MERGE (n:FoodOnTerm {label: $node_label}) SET n:Allergen", node_label=node_label)

def import_allergen_relations():
    print("Import Allergen relations...")
    # IS_ALLERGEN relation
    IS_ALLERGEN_relations = [
        {"source": "walnut", "target": "nut"},
        {"source": "almond", "target": "nut"},
        {"source": "hazelnut", "target": "nut"},
        {"source": "cashew", "target": "nut"},
        {"source": "pistachio", "target": "nut"},

        {"source": "milk", "target": "dairy"},
        {"source": "cow milk", "target": "milk"},
        {"source": "goat milk", "target": "milk"},

        {"source": "crayfish", "target": "crustacean"},
        {"source": "crawfish", "target": "crustacean"},
        {"source": "shrimp", "target": "crustacean"},
        {"source": "crab", "target": "crustacean"},
        {"source": "lobster", "target": "crustacean"},

        {"source": "scallop", "target": "mollusc"},
        {"source": "oyster", "target": "mollusc"},
        {"source": "mussel", "target": "mollusc"},
        {"source": "clam", "target": "mollusc"},
        {"source": "snail", "target": "mollusc"},

        {"source": "crustacean", "target": "shellfish"},
        {"source": "mollusc", "target": "shellfish"},

        {"source": "chicken egg", "target": "egg"},

        {"source": "melon", "target": "fruit"},
        {"source": "apple", "target": "fruit"},
        {"source": "apricot", "target": "fruit"},
        {"source": "cherry", "target": "fruit"},
        {"source": "plum", "target": "fruit"},
        {"source": "tomato", "target": "fruit"},
        {"source": "orange", "target": "fruit"},
        {"source": "legume", "target": "fruit"},

        {"source": "peas", "target": "legume"},
        {"source": "soybeans", "target": "legume"},
        {"source": "beans", "target": "legume"},
        {"source": "peanut", "target": "legume"},
        {"source": "lentil", "target": "legume"},

    ]

    for relation in IS_ALLERGEN_relations:
        session.run(r"MATCH (source:FoodOnTerm {label:$source_label}),(target:FoodOnTerm {label:$target_label}) CREATE (source)-[:IS_ALLERGEN]->(target)",
                    source_label=relation["source"],
                    target_label=relation["target"]
        )

    # HAS_ALLERGEN relation   
    queries = [
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'nut'})       WHERE n.label CONTAINS ' nut ' OR n.label CONTAINS ' nut' OR n.label CONTAINS 'nut ' OR n.label CONTAINS ' nuts ' OR n.label CONTAINS ' nuts' OR n.label CONTAINS 'nuts ' OR n.label='nut' OR n.label='nuts' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'walnut'})    WHERE n.label CONTAINS 'walnut' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'almond'})    WHERE n.label CONTAINS 'almond' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'hazelnut'})  WHERE n.label CONTAINS 'hazelnut' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'cashew'})    WHERE n.label CONTAINS 'cashew' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'pistachio'}) WHERE n.label CONTAINS 'pistachio' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'milk'})      WHERE n.label CONTAINS 'milk' AND NOT n.label CONTAINS 'nut' AND NOT n.label CONTAINS 'oat' AND NOT n.label CONTAINS 'peanut' AND NOT n.label CONTAINS 'soybean' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'cow milk'})  WHERE n.label CONTAINS 'cow milk' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'goat milk'}) WHERE n.label CONTAINS 'goat milk' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'cow milk'})  WHERE n.label CONTAINS 'dairy' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'shellfish'}) WHERE n.label CONTAINS 'shellfish' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'crustacean'})WHERE n.label CONTAINS 'crustacean' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'mollusc'})   WHERE n.label CONTAINS 'mollusc' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'crayfish'})  WHERE n.label CONTAINS 'crayfish' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'crawfish'})  WHERE n.label CONTAINS 'crawfish' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'shrimp'})    WHERE n.label CONTAINS 'shrimp' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'crab'})      WHERE n.label CONTAINS 'crab' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'lobster'})   WHERE n.label CONTAINS 'lobster' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'scallop'})   WHERE n.label CONTAINS 'scallop' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'oyster'})    WHERE n.label CONTAINS 'oyster' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'mussel'})    WHERE n.label CONTAINS 'mussel' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'clam'})      WHERE n.label CONTAINS 'clam' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'snail'})     WHERE n.label CONTAINS 'snail' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'fish'})      WHERE n.label CONTAINS 'fish' AND NOT n.label CONTAINS 'shellfish' AND NOT n.label CONTAINS 'crayfish' AND NOT n.label CONTAINS 'crawfish' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'egg'})       WHERE n.label CONTAINS 'egg' AND NOT n.label CONTAINS 'fish' AND NOT n.label CONTAINS 'rohu' AND NOT n.label CONTAINS 'reptile' AND NOT n.label CONTAINS 'turtle' AND NOT n.label CONTAINS 'shrimp' AND NOT n.label CONTAINS 'waterfly' AND NOT n.label CONTAINS 'eggplant' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'chicken egg'}) WHERE n.label CONTAINS 'chicken egg' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'fruit'})     WHERE n.label CONTAINS 'fruit' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'melon'})     WHERE n.label CONTAINS 'melon' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'apple'})     WHERE n.label CONTAINS 'apple' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'apricot'})   WHERE n.label CONTAINS 'apricot' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'cherry'})    WHERE n.label CONTAINS 'cherry' OR n.label CONTAINS 'cherries' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'plum'})      WHERE n.label CONTAINS 'plum' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'tomato'})    WHERE n.label CONTAINS 'tomato' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'orange'})    WHERE n.label CONTAINS 'orange' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'legume'})    WHERE n.label CONTAINS 'legume' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'peas'})      WHERE n.label CONTAINS ' pea ' OR n.label CONTAINS ' pea' OR n.label CONTAINS 'pea ' OR n.label CONTAINS ' peas ' OR n.label CONTAINS ' peas' OR n.label CONTAINS 'peas ' OR n.label='pea' OR n.label='peas' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'beans'})     WHERE n.label CONTAINS 'bean' AND NOT n.label CONTAINS 'soy' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'soybeans'})  WHERE n.label CONTAINS 'soy' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'lentil'})    WHERE n.label CONTAINS 'lentil' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'peanut'})    WHERE n.label CONTAINS 'peanut' CREATE (n)-[:HAS_ALLERGEN]->(m)",

        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'sesame'})    WHERE n.label CONTAINS 'sesame' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'wheat'})     WHERE n.label CONTAINS 'wheat' CREATE (n)-[:HAS_ALLERGEN]->(m)",
        r"MATCH (n:FoodOnTerm) MATCH (m:FoodOnTerm {label:'gluten'})    WHERE n.label CONTAINS 'gluten' CREATE (n)-[:HAS_ALLERGEN]->(m)",
    ]  
    for query in queries:
        session.run(query)


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 2: EXECUTE IMPORTING DATA (Nodes & Relations)▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[2/5] Importing Nodes & Relations to Neo4j...")

with driver.session() as session:
    setup_constraints()
    import_descendants(get_descendants(FOOD_CLASS_IRI), "FoodMaterial")
    import_descendants(get_descendants(CHEMICAL_CLASS_IRI), "Chemical")
    import_descendants(get_descendants(INGREDIENT_CLASS_IRI), "Ingredient")
    import_descendants(get_descendants(ORGANISM_CLASS_IRI), "Organism")
    import_descendants(get_descendants(PLANT_CLASS_IRI), "Plant")
    import_relations(total_classes)

execution_times['Import Data'] = time.time() - step_start
print(f"-> Done in {execution_times['Import Data']:.2f} seconds")


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 2.5: REMOVE UNLABELED NODES                  ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[2.5/5] Removing Nameless/Labelless Nodes...")

# Gọi hàm xóa node
remove_nameless_nodes() 

execution_times['Remove Nameless'] = time.time() - step_start
print(f"-> Done in {execution_times['Remove Nameless']:.2f} seconds")




# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 3: MERGE DUPLICATE NODES                     ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[3/5] Merging Duplicate Nodes (APOC)...")

def merge_duplicate_nodes_by_label():
    # 1. Kiểm tra APOC
    with driver.session() as session:
        try:
            session.run("RETURN apoc.version()")
        except Exception:
            print("⚠️ CẢNH BÁO: Chưa cài APOC Plugin.")
            return

    # 2. Merge Query (Đã cập nhật name: 'combine')
    merge_query = """
    MATCH (n:FoodOnTerm)
    WITH n.label AS lbl, collect(n) AS nodes
    WHERE size(nodes) > 1
    
    CALL apoc.refactor.mergeNodes(nodes, {
      properties: {
        iri: 'combine',        
        name: 'combine',       
        label: 'overwrite',    
        embedding: 'discard',  
        `.*`: 'overwrite'      
      },
      mergeRels: true
    })
    YIELD node
    RETURN count(node) AS merged_groups
    """
    
    try:
        with driver.session() as session:
            result = session.run(merge_query)
            record = result.single()
            count = record["merged_groups"] if record else 0
            print(f"✅ Đã gộp thành công {count} nhóm node trùng tên.")
            
            print("-> Creating UNIQUE constraint for Label...")
            session.run("CREATE CONSTRAINT unique_food_label IF NOT EXISTS FOR (n:FoodOnTerm) REQUIRE n.label IS UNIQUE")
            
    except Exception as e:
        print(f"❌ Lỗi khi Merge: {e}")

merge_duplicate_nodes_by_label()

execution_times['Merge Nodes'] = time.time() - step_start
print(f"-> Done in {execution_times['Merge Nodes']:.2f} seconds")


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 3.5:  ADD ALLERGEN NODES AND RELATIONS       ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

with driver.session() as session:
    import_allergen_nodes()
    import_allergen_relations()


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 4:  EMBEDDING GRAPH                           ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[4/5] Generating Embeddings...")

print("Loading Embedding Model (all-MiniLM-L6-v2)...")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def update_embeddings_batch(tx, batch_data):
    """
    Sửa lại: Tìm node bằng Label để update embedding 
    (Vì label là duy nhất và không bị biến thành List như IRI)
    """
    query = """
    UNWIND $batch AS row
    MATCH (n:FoodOnTerm {label: row.label}) 
    SET n.embedding = row.embedding
    """
    tx.run(query, batch=batch_data)

def generate_and_store_embeddings():
    print("Start generating embeddings (Fixing missing nodes)...")
    
    # Chỉ lấy những node CHƯA CÓ embedding
    fetch_query = """
    MATCH (n:FoodOnTerm) 
    WHERE n.label IS NOT NULL AND n.embedding IS NULL
    RETURN n.label AS label
    """
    
    with driver.session() as session:
        # Lấy danh sách label cần xử lý
        result = session.run(fetch_query)
        nodes = [record['label'] for record in result]
    
    total_nodes = len(nodes)
    print(f"-> Found {total_nodes} nodes missing embeddings.")
    
    if total_nodes == 0:
        print("✅ Tất cả node đều đã có embedding. Không cần chạy lại.")
        return

    batch_data = []
    processed_count = 0
    
    for text in nodes:
        # Tạo vector
        vector = embed_model.encode(text).tolist()
        
        # Chỉ cần lưu label và vector để update
        batch_data.append({
            "label": text,
            "embedding": vector
        })
        
        if len(batch_data) >= BATCH_SIZE:
            with driver.session() as session:
                session.execute_write(update_embeddings_batch, batch_data)
            processed_count += len(batch_data)
            print(f"   Embedded & Updated: {processed_count}/{total_nodes}")
            batch_data = []

    if batch_data:
        with driver.session() as session:
            session.execute_write(update_embeddings_batch, batch_data)
        print(f"   Embedded & Updated: {total_nodes}/{total_nodes}")
generate_and_store_embeddings()

execution_times['Embedding'] = time.time() - step_start
print(f"-> Done in {execution_times['Embedding']:.2f} seconds")


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 5:  INDEXING                                 ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[5/5] Creating Indexes...")

def create_indexes():
    with driver.session() as session:
        print("-> Creating VECTOR INDEX...")
        session.run("""
            CREATE VECTOR INDEX food_vector_index IF NOT EXISTS
            FOR (n:FoodOnTerm)
            ON (n.embedding)
            OPTIONS {indexConfig: {
             `vector.dimensions`: 384,
             `vector.similarity_function`: 'cosine'
            }}
        """)
        
        print("-> Creating FULLTEXT INDEX...")
        session.run("""
            CREATE FULLTEXT INDEX food_text_index IF NOT EXISTS
            FOR (n:FoodOnTerm)
            ON EACH [n.label]
        """)

create_indexes()

execution_times['Indexing'] = time.time() - step_start
print(f"-> Done in {execution_times['Indexing']:.2f} seconds")


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌SUMMARIZE                                         ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

driver.close()
total_time = time.time() - total_start_time

print("\n" + "="*50)
print(f"✅ BUILD COMPLETE in {total_time:.2f} seconds")
print("="*50)
print(f"{'STEP':<25} | {'TIME (s)':<15}")
print("-" * 43)
for step, duration in execution_times.items():
    print(f"{step:<25} | {duration:.2f}")
print("-" * 43)