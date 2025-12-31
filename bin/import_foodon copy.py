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

print(">>> START BUILDING KNOWLEDGE GRAPH...")


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 1: LOADING OWL FILE                 ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n > [1/5] Loading OWL file...")




replacements = [
    {"name": "CHEBI_16811", "label": "methionine"},
    {"name": "CHEBI_17015", "label": "riboflavin"},
    {"name": "CHEBI_36005", "label": "docosahexaenoic acid"},
    {"name": "CHEBI_166967", "label": "cis-fatty acid"},
    {"name": "CHEBI_27781", "label": "myristoleic acid"},
    {"name": "CHEBI_32036", "label": "potassium sulfate"},
    {"name": "CHEBI_28822", "label": "icosanoic acid"},
    {"name": "CHEBI_33237", "label": "vitamin D4"},
    {"name": "CHEBI_63005", "label": "sodium nitrate"},
    {"name": "CHEBI_28946", "label": "theobromine"},
    {"name": "CHEBI_22315", "label": "alkaloid"},
    {"name": "CHEBI_17351", "label": "linoleic acid"},
    {"name": "CHEBI_28716", "label": "palmitoleic acid"},
    {"name": "CHEBI_166968", "label": "trans-fatty acid"},
    {"name": "CHEBI_35150", "label": "calcium hydroxide"},
    {"name": "CHEBI_28941", "label": "docosanoic acid"},
    {"name": "CHEBI_25017", "label": "leucine"},
    {"name": "CHEBI_28384", "label": "vitamin K"},
    {"name": "CHEBI_33279", "label": "vitamin D5"},
    {"name": "CHEBI_27013", "label": "tocopherol"},
    {"name": "CHEBI_63017", "label": "sodium L-tartrate"},
    {"name": "CHEBI_27732", "label": "caffeine"},
    {"name": "CHEBI_28064", "label": "cyanidin 3-O-rutinoside"},
    {"name": "CHEBI_15940", "label": "nicotinic acid"},
    {"name": "CHEBI_15640", "label": "5-formyltetrahydrofolic acid"},
    {"name": "CHEBI_16196", "label": "oleic acid"},
    {"name": "CHEBI_30768", "label": "propionic acid"},
    {"name": "CHEBI_28044", "label": "phenylalanine"},
    {"name": "CHEBI_53486", "label": "all-cis-icosa-8,11,14-trienoic acid"},
    {"name": "CHEBI_22470", "label": "α-tocopherol"},
    {"name": "CHEBI_3312", "label": "calcium dichloride"},
    {"name": "CHEBI_53258", "label": "sodium citrate"},
    {"name": "CHEBI_31968", "label": "pelargonidin 3-O-rutinoside"},
    {"name": "CHEBI_28838", "label": "lutein"},
    {"name": "CHEBI_3962", "label": "curcumin"},
    {"name": "CHEBI_30911", "label": "glucitol"},
    {"name": "CHEBI_59265", "label": "palmitelaidic acid"},
    {"name": "CHEBI_27266", "label": "valine"},
    {"name": "CHEBI_80438", "label": "Cyanidin 3-O-sophoroside"},
    {"name": "CHEBI_6650", "label": "malic acid"},
    {"name": "CHEBI_16709", "label": "pyridoxine"},
    {"name": "CHEBI_27997", "label": "elaidic acid"},
    {"name": "CHEBI_26208", "label": "polyunsaturated fatty acid"},
    {"name": "CHEBI_17883", "label": "hydrogen chloride"},
    {"name": "CHEBI_72850", "label": "icosadienoic acid"},
    {"name": "CHEBI_28808", "label": "mannan"},
    {"name": "CHEBI_83820", "label": "non-proteinogenic amino acid"},
    {"name": "CHEBI_17113", "label": "erythritol"},
    {"name": "CHEBI_36023", "label": "vaccenic acid"},
    {"name": "CHEBI_22653", "label": "asparagine"},
    {"name": "CHEBI_35149", "label": "magnesium hydroxide"},
    {"name": "CHEBI_26948", "label": "vitamin B1"},
    {"name": "CHEBI_15843", "label": "arachidonic acid"},
    {"name": "CHEBI_37166", "label": "xylan"},
    {"name": "CHEBI_22660", "label": "aspartic acid"},
    {"name": "CHEBI_24898", "label": "isoleucine"},
    {"name": "CHEBI_28300", "label": "glutamine"},
    {"name": "CHEBI_142263", "label": "isopeonidin 3-rutinoside"},
    {"name": "CHEBI_32425", "label": "(11Z)-icos-11-enoic acid"},
    {"name": "CHEBI_75115", "label": "docosadienoic acid"},
    {"name": "CHEBI_3311", "label": "calcium carbonate"},
    {"name": "CHEBI_18233", "label": "xyloglucan"},
    {"name": "CHEBI_15356", "label": "cysteine"},
    {"name": "CHEBI_17750", "label": "glycine betaine"},
    {"name": "CHEBI_24741", "label": "hydroxyproline"},
    {"name": "CHEBI_42111", "label": "(R)-lactic acid"},
    {"name": "CHEBI_38021", "label": "cyanin chloride"},
    {"name": "CHEBI_28869", "label": "menadione"},
    {"name": "CHEBI_28792", "label": "erucic acid"},
    {"name": "CHEBI_15428", "label": "glycine"},
    {"name": "CHEBI_22652", "label": "ascorbic acid"},
    {"name": "CHEBI_12777", "label": "vitamin A"},
    {"name": "CHEBI_131693", "label": "7,10,13,16-docosatetraenoic acid"},
    {"name": "CHEBI_18422", "label": "sulfur dioxide"},
    {"name": "CHEBI_176839", "label": "vitamin B3"},
    {"name": "CHEBI_17020", "label": "glucomannan"},
    {"name": "CHEBI_18237", "label": "glutamic acid"},
    {"name": "CHEBI_29016", "label": "arginine"},
    {"name": "CHEBI_3435", "label": "carrageenan"},
    {"name": "CHEBI_85533", "label": "trans-4-hydroxy-L-proline betaine"},
    {"name": "CHEBI_38698", "label": "anthocyanin chlorides"},
    {"name": "CHEBI_16374", "label": "menaquinone"},
    {"name": "CHEBI_44247", "label": "(15Z)-tetracosenoic acid"},
    {"name": "CHEBI_26119", "label": "phytoene"},
    {"name": "CHEBI_176840", "label": "vitamin B5"},
    {"name": "CHEBI_28427", "label": "arabinoxylan"},
    {"name": "CHEBI_15354", "label": "choline"},
    {"name": "CHEBI_75323", "label": "lactitol"},
    {"name": "CHEBI_17754", "label": "glycerol"},
    {"name": "CHEBI_17439", "label": "cyanocob(III)alamin"},
    {"name": "CHEBI_15956", "label": "biotin"},
    {"name": "CHEBI_16726", "label": "cyanidin 3-O-rutinoside chloride"},
    {"name": "CHEBI_31793", "label": "magnesium carbonate"},
    {"name": "CHEBI_62466", "label": "7,7',9,9'-tetra-cis-lycopene"},
    {"name": "CHEBI_28346", "label": "mescaline"},
    {"name": "CHEBI_50211", "label": "retinol"},
    {"name": "CHEBI_30805", "label": "dodecanoic acid"},
    {"name": "CHEBI_27570", "label": "histidine"},
    {"name": "CHEBI_6636", "label": "magnesium dichloride"},
    {"name": "CHEBI_67016", "label": "tetrahydrofolate"},
    {"name": "CHEBI_15741", "label": "succinic acid"},
    {"name": "CHEBI_37586", "label": "sodium phosphate"},
    {"name": "CHEBI_35366", "label": "fatty acid"},
    {"name": "CHEBI_17336", "label": "all-trans-retinol"},
    {"name": "CHEBI_17933", "label": "calcidiol"},
    {"name": "CHEBI_77366", "label": "(6Z,9Z,12Z,15Z,18Z,21Z)-tetracosahexaenoic acid"},
    {"name": "CHEBI_27306", "label": "vitamin B6"},
    {"name": "CHEBI_25094", "label": "lysine"},
    {"name": "CHEBI_18067", "label": "phylloquinone"},
    {"name": "CHEBI_15366", "label": "acetic acid"},
    {"name": "CHEBI_422", "label": "(S)-lactic acid"},
    {"name": "CHEBI_28837", "label": "octanoic acid"},
    {"name": "CHEBI_176841", "label": "vitamin B7"},
    {"name": "CHEBI_17822", "label": "serine"},
    {"name": "CHEBI_32389", "label": "all-cis-octadeca-6,9,12,15-tetraenoic acid"},
    {"name": "CHEBI_29073", "label": "L-ascorbic acid"},
    {"name": "CHEBI_25413", "label": "monounsaturated fatty acid"},
    {"name": "CHEBI_57455", "label": "(6R)-5,10-methenyltetrahydrofolate"},
    {"name": "CHEBI_25140", "label": "maltodextrin"},
    {"name": "CHEBI_42504", "label": "pentadecanoic acid"},
    {"name": "CHEBI_15948", "label": "lycopene"},
    {"name": "CHEBI_176842", "label": "vitamin B9"},
    {"name": "CHEBI_17309", "label": "pectin"},
    {"name": "CHEBI_16449", "label": "alanine"},
    {"name": "CHEBI_38697", "label": "anthocyanin"},
    {"name": "CHEBI_32139", "label": "sodium hydrogencarbonate"},
    {"name": "CHEBI_53460", "label": "all-cis-icosa-11,14,17-trienoic acid"},
    {"name": "CHEBI_30769", "label": "citric acid"},
    {"name": "CHEBI_26607", "label": "saturated fatty acid"},
    {"name": "CHEBI_27300", "label": "vitamin D"},
    {"name": "CHEBI_28866", "label": "tetracosanoic acid"},
    {"name": "CHEBI_75769", "label": "B vitamin"},
    {"name": "CHEBI_176843", "label": "vitamin B12"},
    {"name": "CHEBI_32149", "label": "sodium sulfate"},
    {"name": "CHEBI_166893", "label": "eicosatetraenoic acid"},
    {"name": "CHEBI_26986", "label": "threonine"},
    {"name": "CHEBI_25048", "label": "linolenic acid"},
    {"name": "CHEBI_29864", "label": "mannitol"},
    {"name": "CHEBI_28940", "label": "calciol"},
    {"name": "CHEBI_28875", "label": "tetradecanoic acid"},
    {"name": "CHEBI_3374", "label": "capsaicin"},
    {"name": "CHEBI_61266", "label": "hemicellulose"},
    {"name": "CHEBI_31346", "label": "calcium sulfate"},
    {"name": "CHEBI_72785", "label": "9-hydroxy-5E,7Z,11Z,14Z-eicosatetraenoic acid"},
    {"name": "CHEBI_26271", "label": "proline"},
    {"name": "CHEBI_49105", "label": "thiamine hydrochloride"},
    {"name": "CHEBI_26709", "label": "sodium hydrogensulfite"},
    {"name": "CHEBI_15756", "label": "hexadecanoic acid"},
    {"name": "CHEBI_73558", "label": "D3 vitamins"},
    {"name": "CHEBI_32145", "label": "sodium hydroxide"},
    {"name": "CHEBI_23456", "label": "cyclodextrin"},
    {"name": "CHEBI_46905", "label": "(R)-pantothenic acid"},
    {"name": "CHEBI_27897", "label": "tryptophan"},
    {"name": "CHEBI_36006", "label": "icosapentaenoic acid"},
    {"name": "CHEBI_27956", "label": "L-dehydroascorbic acid"},
    {"name": "CHEBI_17151", "label": "xylitol"},
    {"name": "CHEBI_27470", "label": "folic acid"},
    {"name": "CHEBI_176838", "label": "vitamin B2"},
    {"name": "CHEBI_32365", "label": "heptadecanoic acid"},
    {"name": "CHEBI_33235", "label": "tocotrienol"},
    {"name": "CHEBI_18186", "label": "tyrosine"},
    {"name": "CHEBI_61204", "label": "docosapentaenoic acid"},
    {"name": "CHEBI_78320", "label": "2-hydroxypropanoic acid"},
    {"name": "CHEBI_33709", "label": "amino acid"},
    {"name": "CHEBI_32588", "label": "potassium chloride"},
    {"name": "CHEBI_26078", "label": "phosphoric acid"},
    {"name": "CHEBI_28842", "label": "octadecanoic acid"},
    {"name": "CHEBI_28934", "label": "vitamin D2"},
    {"name": "CHEBI_33234", "label": "vitamin E"},
    {"name": "CHEBI_17548", "label": "alginic acid"},
    {"name": "CHEBI_68428", "label": "maltitol"}
]


onto = get_ontology(ONTO_PATH).load()
total_classes = []

execution_times['Load OWL'] = time.time() - step_start
print(f"-> Done in {execution_times['Load OWL']:.2f} seconds")

# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌IMPORT FUNCTIONS DEFINITION              ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

driver = GraphDatabase.driver(URI, auth=AUTH)


def get_exact_synonyms(entity):
    """Lấy danh sách exact synonyms, trả về list string hoặc list rỗng."""
    synonyms = []
    
    # 1. Thử lấy từ thuộc tính python (nếu owlready2 tự map)
    if hasattr(entity, "hasExactSynonym"):
        synonyms = entity.hasExactSynonym
    
    # 2. Nếu không thấy, thử tìm theo IRI chuẩn OBO (an toàn hơn)
    if not synonyms:
        target_iri = "http://www.geneontology.org/formats/oboInOwl#hasExactSynonym"
        for prop in entity.get_properties(entity):
            if prop.iri == target_iri:
                synonyms = getattr(entity, prop.name)
                break
    
    # 3. Làm sạch dữ liệu
    if synonyms:
        # Chuyển về string, chữ thường, xóa khoảng trắng thừa
        return [str(s).lower().strip() for s in synonyms if s]
    
    return []


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
        f"    n.label = row.label, "
        f"    n.synonyms = row.synonyms "
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
        final_label = clean_label(raw_label)


        synonyms_list = get_exact_synonyms(cls)


        node_data = {
            "iri": cls.iri,
            "name": cls.name,
            "label": final_label,
            "synonyms": synonyms_list
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
    # --- NHÓM CỐT LÕI (CORE) ---
    "http://purl.obolibrary.org/obo/RO_0001000":      "DERIVES_FROM",     
    "http://purl.obolibrary.org/obo/RO_0002162":      "IN_TAXON",        
    "http://purl.obolibrary.org/obo/BFO_0000051":     "HAS_PART",      
    "http://purl.obolibrary.org/obo/BFO_0000050":     "PART_OF",          
    "http://purl.obolibrary.org/obo/FOODON_00002420": "HAS_INGREDIENT",   
    "http://purl.obolibrary.org/obo/FOODON_00001563": "HAS_DEFINING_INGREDIENT", 
    "http://purl.obolibrary.org/obo/RO_0009001":      "HAS_SUBSTANCE_ADDED", 

    # --- NHÓM NGUỒN GỐC (PROCESSING) ---
    "http://purl.obolibrary.org/obo/RO_0003001":      "PRODUCED_BY",    

    # --- NHÓM THAY THẾ (SUBSTITUTE) ---
    "http://purl.obolibrary.org/obo/FOODON_00001301": "HAS_FOOD_SUBSTANCE_ANALOG", 
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

def rename_nodes():
    for replacement in replacements:
        session.run(r"MATCH (n:FoodOnTerm{name: $name_value}) SET n.label = $new_label_value",
                    name_value=replacement["name"],new_label_value=replacement["label"]
        )

FOOD_BY_ORGANISM_IRI = "http://purl.obolibrary.org/obo/FOODON_03420116"
FOOD_COMPONENT_IRI = "http://purl.obolibrary.org/obo/FOODON_00001714"
FOOD_PRODUCT_IRI = "http://purl.obolibrary.org/obo/FOODON_00001002"


# ▛▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▜
# ▌PART 2: EXECUTE IMPORTING DATA (Nodes & Relations)▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[2/5] Importing Nodes & Relations to Neo4j...")

with driver.session() as session:
    setup_constraints()
    import_descendants(get_descendants(FOOD_BY_ORGANISM_IRI), "Food")
    import_descendants(get_descendants(FOOD_COMPONENT_IRI), "Food")
    import_descendants(get_descendants(FOOD_PRODUCT_IRI), "Food")
    import_relations(total_classes)
    print("replacing some nodes label")
    rename_nodes()
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
# ▌PART 4:  EMBEDDING GRAPH                           ▐
# ▙▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▟

step_start = time.time()
print("\n[4/5] Generating Embeddings...")

print("Loading Embedding Model (all-MiniLM-L6-v2)...")
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def update_embeddings_batch(tx, batch_data):
    """
    Update vector embedding vào node.
    """
    query = """
    UNWIND $batch AS row
    MATCH (n:FoodOnTerm {label: row.label}) 
    SET n.embedding = row.embedding
    """
    tx.run(query, batch=batch_data)

def generate_and_store_embeddings():
    print("Start generating embeddings...")
    
    # 1. Lấy dữ liệu cần thiết: Label + Synonyms
    # Chỉ lấy node chưa có embedding để tiết kiệm thời gian (nếu chạy lại)
    # Hoặc bỏ điều kiện `AND n.embedding IS NULL` nếu muốn chạy lại từ đầu
    fetch_query = """
    MATCH (n:FoodOnTerm) 
    WHERE n.label IS NOT NULL 
    RETURN n.label AS label, n.synonyms AS synonyms
    """
    
    with driver.session() as session:
        result = session.run(fetch_query)
        # Lưu vào list dict để xử lý dần
        nodes_data = [{"label": r['label'], "synonyms": r['synonyms']} for r in result]
    
    total_nodes = len(nodes_data)
    print(f"-> Found {total_nodes} nodes to embed.")
    
    if total_nodes == 0:
        return

    batch_data = []
    processed_count = 0
    
    for item in nodes_data:
        label = item['label']
        syns = item['synonyms']
        
        # --- LOGIC QUAN TRỌNG: GỘP TEXT ---
        # "Tofu. Synonyms: bean curd, soybean curd"
        text_to_embed = label
        if syns and isinstance(syns, list) and len(syns) > 0:
            # Nối các synonym lại bằng dấu phẩy
            syn_str = ", ".join(syns)
            text_to_embed = f"{label}. Synonyms: {syn_str}"
            
        # Tạo vector từ đoạn văn bản giàu thông tin này
        vector = embed_model.encode(text_to_embed).tolist()
        
        batch_data.append({
            "label": label,
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


        print("-> Dropping old FULLTEXT INDEX (to ensure schema update)...")
        session.run("DROP INDEX food_text_index IF EXISTS")
        
        print("-> Creating FULLTEXT INDEX (Label + Synonyms)...")
        session.run("""
            CREATE FULLTEXT INDEX food_text_index IF NOT EXISTS
            FOR (n:FoodOnTerm)
            ON EACH [n.label, n.synonyms]
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