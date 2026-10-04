import re
TOKEN_RE=re.compile(r"\[\[(.*?)\]\]",re.DOTALL)

def validate_libreoffice_markers(source:str):
    cursor=0
    while True:
        start=source.find("{{",cursor)
        closing=source.find("}}",cursor)
        if closing>=0 and (start<0 or closing<start):
            raise ValueError("Có dấu }} chưa ghép đúng cặp trong công thức LibreOffice.")
        if start<0: return
        depth=0
        quoted=False
        for index in range(start+2,len(source)):
            character=source[index]
            if character=='"': quoted=not quoted
            if quoted: continue
            if character=="{": depth+=1
            elif character=="}":
                if depth==0 and index+1<len(source) and source[index+1]=="}":
                    if not source[start+2:index].strip():
                        raise ValueError("Công thức LibreOffice {{...}} không được để trống.")
                    cursor=index+2
                    break
                depth=max(0,depth-1)
        else:
            raise ValueError("Có dấu {{ chưa ghép đúng cặp trong công thức LibreOffice.")

def validate_content(source:str):
    validate_libreoffice_markers(source)
    pos=0
    for m in TOKEN_RE.finditer(source):
        if not m.group(1).strip():
            raise ValueError("Công thức [[...]] không được để trống.")
        pos=m.end()
    tail=source[pos:]
    if "[[" in tail or "]]" in tail:
        raise ValueError("Có dấu [[ hoặc ]] chưa ghép đúng cặp.")
    return True
