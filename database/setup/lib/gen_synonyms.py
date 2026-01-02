import re
import inflect
import nltk
from nltk.corpus import wordnet as wn

try:
    nltk.data.find('corpora/wordnet.zip')
    nltk.data.find('corpora/omw-1.4.zip')
except LookupError:
    print("⬇️ Downloading NLTK data (Minimal)...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

p = inflect.engine()

# --- STRICT MODE CONFIGURATION ---

# 1. BLACKLIST (ban over-narrow words)
# This is the most important guard layer to prevent returning "shellfish" when search "mollusk"
BLACKLIST_SYNONYMS = {
    "shellfish", "seafood", "meat", "vegetable", "fruit", "fish", 
    "ingredient", "nutrient", "matter", "object", "whole", "organism",
    "animal", "plant", "foodstuff", "produce", "chow", "edible"
}

# 2. SIMILAR THRESHOLD (90%)
# Only use synonyms if they are extremely close to the original meaning
STRICT_SIMILARITY_THRESHOLD = 0.90 

# 3. TRASH WORD DICTIONARY
FOODON_STOP_WORDS = {
    "product", "products", "item", "items", "food", "foods", 
    "beverage", "drink", "dish", "meal", "agent", "substance", 
    "substitute", "component", "part", "type", "brand", "source",
    "raw", "fresh", "dried", "cooked", "processed", "frozen", 
    "canned", "boiled", "fried", "sweetened", "unsweetened", 
    "pasteurized", "homogenized", "concentrate", "extract"
}

SAFE_LEXNAMES = {'noun.food', 'noun.plant', 'noun.animal'}

def clean_ontology_label(text):
    if not text: return ""
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^]]*\]', '', text)
    text = re.sub(r'[^a-zA-Z0-9\s/]', ' ', text) 
    return re.sub(r'\s+', ' ', text).strip().lower()

def split_compound_text(text):
    if not text: return []
    parts = re.split(r'\s+(?:or|and)\s+|/', text)
    return [x.strip() for x in parts if x.strip()]

def get_strict_synonyms(word):
    """
    Searching WordNet with strict mode
    """
    synonyms = set()
    word_clean = word.replace(" ", "_")
    
    synsets = wn.synsets(word_clean)
    if not synsets: return set()
    
    # Find primary synonyms (Primary Synset)
    primary_synset = None
    for s in synsets:
        if s.lexname() in SAFE_LEXNAMES:
            primary_synset = s
            break
    if not primary_synset: primary_synset = synsets[0]

    for syn in synsets:
        # Filter 1: Only get food/plant synonym set
        if syn.lexname() not in SAFE_LEXNAMES: continue
        
        # Filter 2: Similarity need to be extremely high (> 0.9)
        similarity = primary_synset.wup_similarity(syn)
        if similarity is None or similarity < STRICT_SIMILARITY_THRESHOLD:
            continue

        for lemma in syn.lemmas():
            clean_syn = lemma.name().replace("_", " ").lower()
            
            # Filter 3: Blacklist (prevent shellfish, seafood...)
            if clean_syn in BLACKLIST_SYNONYMS: continue
            
            if clean_syn != word.replace("_", " "):
                synonyms.add(clean_syn)
                
    return synonyms

def gen_synonyms(original_label):
    if not original_label: return []
    
    unique_synonyms = set()
    cleaned_base = clean_ontology_label(original_label)
    if not cleaned_base: return []

    variations_to_process = split_compound_text(cleaned_base)
    if cleaned_base not in variations_to_process:
        variations_to_process.append(cleaned_base)

    for variant in variations_to_process:
        
        # --- STEP 1: TRASH WORD FILTERING ---
        # "mollusk food product" -> remove "food", "product" -> remain only "mollusk"
        words = variant.split()
        meaningful = [w for w in words if w not in FOODON_STOP_WORDS]
        
        core_term = " ".join(meaningful) if meaningful else variant

        if len(core_term) < 2: continue
        unique_synonyms.add(core_term)
        
        # --- STEP 2: GENERATE SINGULAR/PLURAL ---
        try:
            singular = p.singular_noun(core_term)
            if singular is False:
                plural_word = p.plural(core_term)
                if plural_word: unique_synonyms.add(plural_word)
            else:
                unique_synonyms.add(singular)
        except: pass
            
        # --- STEP 3: SEARCHING DICTIONARY ---
        # Only search for short word (<= 2 single word) to avoid trash word
        if len(core_term.split()) <= 2:
            wn_syns = get_strict_synonyms(core_term)
            unique_synonyms.update(wn_syns)

        # Swapping word logic (Apple Juice <-> Juice Apple)
        words = core_term.split()
        if len(words) == 2:
            reversed_term = f"{words[1]} {words[0]}"
            unique_synonyms.add(reversed_term)

    # Final Clean-up
    final_list = list(unique_synonyms)
    original_lower = original_label.lower().strip()
    if original_lower in final_list:
        final_list.remove(original_lower)
        
    return final_list