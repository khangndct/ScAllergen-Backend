# lib/clean_input_text.py
import re

# lib/clean_string.py
import re

def clean_string(text: str) -> str:
    """
    Làm sạch tên nguyên liệu theo logic mạnh:
    Cắt bỏ toàn bộ nội dung tính từ dấu mở ngoặc '(' đầu tiên trở đi.
    """
    if not text:
        return ""

    # 1. CHIẾN THUẬT MỚI: Cắt chuỗi ngay tại dấu mở ngoặc '('
    # Ví dụ: "egg(18%)" -> Lấy phần trước '(' -> "egg"
    # Ví dụ: "Milk (18%)" -> Lấy "Milk "
    # Ví dụ: "egg(18%25" (Lỗi URL mất dấu đóng) -> Vẫn lấy được "egg"
    if '(' in text:
        text = text.split('(')[0]

    # 2. Xóa ký tự phần trăm và số đi kèm (phòng trường hợp viết không có ngoặc: "Milk 18%")
    text = re.sub(r'\d+%', '', text)

    # 3. Xóa các ký tự đặc biệt khác (chấm, phẩy...)
    text = re.sub(r'[.,;:]+$', '', text)

    # 4. Chuẩn hóa khoảng trắng
    text = " ".join(text.split())

    return text

text="egg(18%)"

print(clean_string(text))