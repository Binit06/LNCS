from index.tokenizer import ngrams

def levenshtein(a: str, b: str):
    previous = list(range(len(b) + 1))

    for i, char_a in enumerate(a, 1):
        current = [i]
        for j, char_b in enumerate(b, 1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            replace = previous[j - 1] + (char_a != char_b)
            current.append(min(insert, delete, replace))
        previous = current

    return previous[-1]

def get_candidates(db, word: str):
    word_ngrams = ngrams(word)
    if not word_ngrams:
        return []

    placeholders = ",".join(["%s"] * len(word_ngrams))
    query = f"""
        SELECT term, COUNT(*) AS matches
        FROM term_ngrams
        WHERE ngram IN ({placeholders})
        GROUP BY term
        ORDER BY matches DESC
        LIMIT 20
    """
    rows = db.query(query, word_ngrams)
    return [row[0] for row in rows]

def fuzzy_match(db, word: str):
    candidates = get_candidates(db, word)
    if not candidates:
        return None

    if len(word) <= 4:
        max_distance = 1
    elif len(word) <= 7:
        max_distance = 2
    else:
        max_distance = 3

    matches = []
    for term in candidates:
        distance = levenshtein(word, term)
        if distance <= max_distance:
            matches.append((term, distance))

    if not matches:
        return None

    matches.sort(key=lambda x: x[1])
    return matches[0][0]
