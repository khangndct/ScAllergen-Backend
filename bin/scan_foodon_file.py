import time
from owlready2 import *
from collections import Counter

# 1. Cấu hình đường dẫn file
ONTO_PATH = "/home/pak/Workspaces/Project/nutriviet/FoodOn/import/foodon-full.owl"  # Thay đường dẫn file của bạn vào đây

print(f"⏳ Đang load file {ONTO_PATH} (việc này có thể mất chút thời gian)...")
onto = get_ontology(ONTO_PATH).load()

# Biến để đếm tần suất xuất hiện của các quan hệ
property_counter = Counter()
property_labels = {}

print("🚀 Đang quét cấu trúc equivalent_to của toàn bộ các class...")

count_classes = 0

# 2. Duyệt qua tất cả các class trong Ontology
for cls in onto.classes():
    count_classes += 1
    
    # Chỉ quan tâm các class có định nghĩa tương đương (equivalent_to)
    if not cls.equivalent_to:
        continue

    # equivalent_to trả về một list các định nghĩa logic
    for definition in cls.equivalent_to:
        
        # Hàm đệ quy để đào sâu vào các cấu trúc lồng nhau (AND, OR, v.v.)
        def scan_construct(construct):
            # Nếu là Restriction (ví dụ: derives_from some Soybean)
            if isinstance(construct, Restriction):
                prop = construct.property
                if prop:
                    # Lưu lại IRI và Label để thống kê
                    property_counter[prop.iri] += 1
                    
                    # Cố gắng lấy label dễ đọc
                    if prop.label:
                        property_labels[prop.iri] = prop.label[0]
                    else:
                        property_labels[prop.iri] = prop.name
            
            # Nếu là phép giao (AND) - thường gặp nhất trong Equivalent
            # Trong owlready2, nó thường có thuộc tính .Classes chứa các phần tử con
            elif hasattr(construct, "Classes"):
                for item in construct.Classes:
                    scan_construct(item)
            
            # Xử lý các trường hợp khác nếu cần (OR, NOT...)
        
        scan_construct(definition)

# 3. In kết quả thống kê
print(f"\n✅ Đã quét xong {count_classes} classes.")
print("="*60)
print(f"{'IRI':<50} | {'LABEL':<30} | {'COUNT'}")
print("-" * 90)

# Sắp xếp theo số lần xuất hiện giảm dần
for iri, count in property_counter.most_common():
    label = property_labels.get(iri, "No Label")
    print(f"{iri:<50} | {str(label):<30} | {count}")

print("="*60)