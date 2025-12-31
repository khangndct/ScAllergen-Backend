from rapidfuzz import fuzz, process
import math


def load_data_from_neo4j(driver):
    global FOOD_CACHE, FOOD_NAMES_LIST
    print("⏳ Loading all nodes form Neo4j to RAM...")
    query = """
    MATCH (n:FoodOnTerm)
    OPTIONAL MATCH (child:FoodOnTerm)-[:IS_A]->(n)
    RETURN 
        n.name AS name, 
        n.label AS label, 
        n.synonyms AS synonyms, 
        count(child) AS weight
    """
    
    temp_cache = {}
    count = 0

    with driver.session() as session:
        result = session.run(query)
        for record in result:
            name = record["name"]
            label = record["label"]
            synonyms = record["synonyms"] or []
            weight = record["weight"]

            if label:
                clean_label = label.lower().strip()
                temp_cache[clean_label] = {
                    "name": name, 
                    "label": label,
                    "weight": weight,
                    "type": "main"
                }

            for syn in synonyms:
                clean_syn = syn.lower().strip()
                if clean_syn not in temp_cache:
                    temp_cache[clean_syn] = {
                        "name": name,
                        "label": label, 
                        "weight": weight,
                        "type": "synonym"
                    }
            count += 1


    FOOD_CACHE = temp_cache
    FOOD_NAMES_LIST = list(FOOD_CACHE.keys())
    print(f"✅ Load done! {len(FOOD_NAMES_LIST)} keys from {count} nodes.")

def hybrid_scorer_07_03(query, choice, **kwargs):
    """
    Strategy: Hybrid 0.7/0.3 (Winner)
    """
    score_char = fuzz.ratio(query, choice)
    score_token = fuzz.token_sort_ratio(query, choice)
    return (0.7 * score_char) + (0.3 * score_token)


def find_top_nodes_in_memory(text_input: str, limit: int = 1):
    if not text_input: return []
    
    query = text_input.lower().strip()
    
    results = process.extract(
        query, 
        FOOD_NAMES_LIST, 
        scorer=hybrid_scorer_07_03, 
        limit=10,               
        score_cutoff=60            
    )

    ranked_candidates = []
    
    for match_name, fuzzy_score, _ in results:
        node_data = FOOD_CACHE[match_name]

        weight = node_data.get("weight", 0)
        weight_bonus = math.log1p(weight) * 1.5

        len_diff = abs(len(query) - len(match_name))
        length_penalty = len_diff * 0.5

        final_score = fuzzy_score + weight_bonus - length_penalty

        ranked_candidates.append({
            "name": match_name,
            "score": final_score,     
            "fuzzy_score": fuzzy_score, 
            "node": node_data
        })

    ranked_candidates.sort(key=lambda x: x["score"], reverse=True)
    return ranked_candidates[:limit]

def find_best_node_text(search_term):
    result = find_top_nodes_in_memory(search_term,1)
    if len(result) == 0:
        return None
    item = result[0]
    return {
        "label": item["node"]["label"]
    }