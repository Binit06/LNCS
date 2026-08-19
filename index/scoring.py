import math

def idf(total_docs: int, doc_freq: int) -> float:
    return math.log((total_docs - doc_freq + 0.5)/(doc_freq + 0.5) + 1)

def bm25_score(freq: int, doc_len: int, avgdl: float, term_idf: float, k1: float = 1.5, b: float = 0.75) -> float:
    num = freq * (k1 + 1)
    den = freq + k1 * (1 - b + b * float(doc_len)/float(avgdl))
    return term_idf * (num / den)
