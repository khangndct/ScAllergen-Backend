import re
import inflect
import nltk
from nltk.corpus import wordnet

# --- SETUP: Tải dữ liệu NLTK (Chạy 1 lần là đủ) ---
try:
    nltk.data.find('corpora/wordnet.zip')
    nltk.data.find('corpora/omw-1.4.zip')
except LookupError:
    print("⬇️ Downloading NLTK data...")
    nltk.download('wordnet', quiet=True)
    nltk.download('omw-1.4', quiet=True)

# Khởi tạo engine
p = inflect.engine()

# --- CẤU HÌNH: TỪ ĐIỂN TỪ RÁC (STOP WORDS) ---
FOODON_STOP_WORDS = {
    "product", "products", "item", "items", "food", "foods", 
    "beverage", "drink", "dish", "meal", "supplement", "agent",
    "substance", "derivative", "analog", "substitute", "component",
    "part", "variety", "type", "brand", "raw", "whole", "fresh", 
    "dried", "cooked", "processed", "frozen", "canned", "preserved", 
    "boiled", "fried", "based", "added", "containing", "flavored", 
    "artificial", "sweetened", "unsweetened", "enriched", "fortified"
}

# Các nhóm nghĩa an toàn
SAFE_LEXNAMES = {'noun.food', 'noun.plant', 'noun.animal'}

def clean_ontology_label(text):
    if not text: return ""
    # Xóa nội dung trong ngoặc và ký tự lạ
    text = re.sub(r'\([^)]*\)', '', text)
    text = re.sub(r'\[[^]]*\]', '', text)
    text = re.sub(r'[^a-zA-Z0-9]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def extract_core_term(clean_text):
    words = clean_text.split()
    meaningful_words = [w for w in words if w not in FOODON_STOP_WORDS]
    if not meaningful_words:
        return clean_text
    return " ".join(meaningful_words)

def get_wordnet_safe_synonyms(word):
    synonyms = set()
    lookup_word = word.replace(" ", "_")
    for syn in wordnet.synsets(lookup_word):
        if syn.lexname() in SAFE_LEXNAMES:
            for lemma in syn.lemmas():
                clean_syn = lemma.name().replace("_", " ").lower()
                if clean_syn != word:
                    synonyms.add(clean_syn)
    return synonyms

def gen_synonyms(original_label):
    """
    Hàm chính được gọi từ bên ngoài
    """
    if not original_label: return []
    
    unique_synonyms = set()
    
    # 1. Làm sạch & Lấy Core Term
    clean_text = clean_ontology_label(original_label)
    if not clean_text: return []
    
    core_term = extract_core_term(clean_text)
    
    if core_term != clean_text and len(core_term) > 2:
        unique_synonyms.add(core_term)
        
    # 2. Sinh biến thể ngữ pháp (Số ít/nhiều)
    try:
        singular = p.singular_noun(core_term)
        
        # p.singular_noun trả về False nếu từ đó đã là số ít
        if singular is False:
            plural_word = p.plural(core_term)
            if plural_word: # Kiểm tra thêm cho chắc chắn
                unique_synonyms.add(plural_word)
        else:
            unique_synonyms.add(singular)
            
    except (TypeError, ValueError, IndexError):
        # Nếu inflect gặp lỗi với từ dị biệt (VD: công thức hóa học), 
        # chỉ cần bỏ qua bước này và không làm crash chương trình.
        print(f"⚠️ Warning: 'inflect' could not process term: '{core_term}'")
        pass
        
    # 3. Sinh từ đồng nghĩa (WordNet)
    if len(core_term.split()) <= 2:
        wn_syns = get_wordnet_safe_synonyms(core_term)
        unique_synonyms.update(wn_syns)

    # 4. Logic đảo từ (Apple Juice <-> Juice Apple)
    words = core_term.split()
    if len(words) == 2:
        reversed_term = f"{words[1]} {words[0]}"
        unique_synonyms.add(reversed_term)

    # Convert về list và loại bỏ trùng lặp với label gốc
    final_list = list(unique_synonyms)
    if original_label.lower() in final_list:
        final_list.remove(original_label.lower())
        
    return final_list