import re
TOKEN_RE=re.compile(r"\\[\\[(.*?)\\]\\]",re.DOTALL)

def validate_content(source:str):
    pos=0
    for m in TOKEN_RE.finditer(source):
        if not m.group(1).strip():
            raise ValueError("Công thức [[...]] không được để trống.")
        pos=m.end()
    tail=source[pos:]
    if "[[" in tail or "]]" in tail:
        raise ValueError("Có dấu [[ hoặc ]] chưa ghép đúng cặp.")
    return True
