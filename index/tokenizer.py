import re

def tokenise(text: str):
    text = text.lower()
    return re.findall(r'\b[a-z0-9]+\b', text)

def ngrams(word: str, n: int = 3):
    if len(word) < n:
        return [word]
    return [word[i:i + n] for i in range(len(word) - n + 1)]