import re

def check_reply(reply: str, forbidden: list[str]) -> list[str]:
    flags = []
    for word in forbidden:
        term = word.strip()
        if not term:
            continue
        pattern = rf"\b{re.escape(term)}\b"
        if re.search(pattern, reply, re.IGNORECASE):
            flags.append(term)
    return flags
