import re
import inflect
import nltk
from nltk.corpus import wordnet as wn

# --- SETUP: Tải dữ liệu tối giản ---
# Chỉ cần WordNet, bỏ hết các model NLP nặng nề
try:
    nltk.data.find('corpora/wordnet.zip')
    nltk.data.find('corpora/omw-1.4.zip')
except LookupError:
    print("⬇️ Downloading NLTK data (Minimal)...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

p = inflect.engine()

# --- CẤU HÌNH STRICT MODE ---

# 1. DANH SÁCH ĐEN (Chặn đứng các từ quá rộng)
# Đây là lớp bảo vệ quan trọng nhất để chặn "shellfish" khi search "mollusk"
BLACKLIST_SYNONYMS = {
    "shellfish", "seafood", "meat", "vegetable", "fruit", "fish", 
    "ingredient", "nutrient", "matter", "object", "whole", "organism",
    "animal", "plant", "foodstuff", "produce", "chow", "edible"
}

# 2. NGƯỠNG TƯƠNG ĐỒNG (90%)
# Chỉ lấy từ đồng nghĩa nếu nó cực kỳ sát nghĩa gốc
STRICT_SIMILARITY_THRESHOLD = 0.90 

# 3. TỪ ĐIỂN TỪ RÁC (Thay thế cho NLP)
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
    Tra từ điển WordNet với chế độ lọc nghiêm ngặt
    """
    synonyms = set()
    word_clean = word.replace(" ", "_")
    
    synsets = wn.synsets(word_clean)
    if not synsets: return set()
    
    # Tìm nhóm nghĩa chính (Primary Synset)
    primary_synset = None
    for s in synsets:
        if s.lexname() in SAFE_LEXNAMES:
            primary_synset = s
            break
    if not primary_synset: primary_synset = synsets[0]

    for syn in synsets:
        # Lọc 1: Chỉ lấy nhóm nghĩa Thực phẩm/Động/Thực vật
        if syn.lexname() not in SAFE_LEXNAMES: continue
        
        # Lọc 2: Độ tương đồng phải rất cao (> 0.9)
        similarity = primary_synset.wup_similarity(syn)
        if similarity is None or similarity < STRICT_SIMILARITY_THRESHOLD:
            continue

        for lemma in syn.lemmas():
            clean_syn = lemma.name().replace("_", " ").lower()
            
            # Lọc 3: Blacklist (Chặn shellfish, seafood...)
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
        
        # --- BƯỚC 1: LỌC TỪ RÁC (Thay thế NLP) ---
        # "mollusk food product" -> bỏ "food", "product" -> còn "mollusk"
        words = variant.split()
        meaningful = [w for w in words if w not in FOODON_STOP_WORDS]
        
        # Nếu lọc xong mà còn lại từ có nghĩa thì lấy, không thì lấy gốc
        core_term = " ".join(meaningful) if meaningful else variant

        if len(core_term) < 2: continue
        unique_synonyms.add(core_term)
        
        # --- BƯỚC 2: SỐ ÍT/NHIỀU ---
        try:
            singular = p.singular_noun(core_term)
            if singular is False:
                plural_word = p.plural(core_term)
                if plural_word: unique_synonyms.add(plural_word)
            else:
                unique_synonyms.add(singular)
        except: pass
            
        # --- BƯỚC 3: TRA TỪ ĐIỂN SÁT NGHĨA ---
        # Chỉ tra những từ ngắn gọn (<= 2 từ đơn) để tránh rác
        if len(core_term.split()) <= 2:
            wn_syns = get_strict_synonyms(core_term)
            unique_synonyms.update(wn_syns)

        # Logic đảo từ (Apple Juice <-> Juice Apple)
        words = core_term.split()
        if len(words) == 2:
            reversed_term = f"{words[1]} {words[0]}"
            unique_synonyms.add(reversed_term)

    # Clean-up cuối cùng
    final_list = list(unique_synonyms)
    original_lower = original_label.lower().strip()
    if original_lower in final_list:
        final_list.remove(original_lower)
        
    return final_list