import json
from typing import Optional

def extract_json_block(text: str) -> Optional[str]:
    text = (text or "").strip()
    if text.startswith("```"):
        parts = text.split("```")
        if len(parts) >= 3:
            text = parts[1]
    try:
        json.loads(text)
        return text
    except Exception:
        pass
    start = text.find("{")
    while start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{": depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    cand = text[start:i+1]
                    try:
                        json.loads(cand)
                        return cand
                    except Exception:
                        break
        start = text.find("{", start+1)
    return None
