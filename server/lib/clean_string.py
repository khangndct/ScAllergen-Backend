import re

def clean_string(text: str) -> str:
    """
    Cleaning ingredient text
    """
    if not text:
        return ""
    if '(' in text:
        text = text.split('(')[0]

    text = re.sub(r'\d+%', '', text)

    text = re.sub(r'[.,;:]+$', '', text)

    text = " ".join(text.split())

    return text

text="egg(18%)"

print(clean_string(text))