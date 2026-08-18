from index.tokenizer import tokenise
from index.fuzzy import fuzzy_match
from index.scoring import idf, bm25_score

STOP_WORDS = {'a', 'an', 'the', 'and', 'or', 'into', 'in', 'of', 'to', 'is', 'it', 'for', 'with', 'on', 'at', 'who'}

def _resolve_tokens(db, query: str):
    raw_tokens = tokenise(query)
    tokens = []

    for word in raw_tokens:
        if word in STOP_WORDS:
            continue

        exact_match = bool(db.query("SELECT 1 FROM inverted_index WHERE term = ? LIMIT 1", (word,)))

        if (exact_match):
            tokens.append(word)
        else:
            fuzzy = fuzzy_match(db, word)
            if fuzzy:
                tokens.append(fuzzy)

    return list(tokens)

def search(db, query: str, k1: float = 1.5, b: float = 0.75):
    tokens = _resolve_tokens(db, query)
    if not tokens:
        return []

    num_tokens = len(tokens)
    placeholders = ",".join(["?"] * num_tokens)

    (total_docs,) = db.query("SELECT COUNT(*) FROM documents", ())[0]
    if total_docs == 0:
        return []

    (avgdl,) = db.query("SELECT AVG(doc_length) FROM documents", ())[0]
    avgdl = avgdl or 1

    df_rows = db.query(
        f"""
        SELECT term, COUNT(DISTINCT doc_id)
        FROM inverted_index
        WHERE term IN ({placeholders})
        GROUP BY term
        """,
        tokens
    )

    doc_freq = {term: n for term, n in df_rows}
    term_idf = {term: idf(total_docs, doc_freq.get(term, 0)) for term in tokens}

    posting_rows = db.query(
        f"""
        SELECT i.doc_id, 
            i.term, 
            i.frequency, 
            d.url,
            d.novel_name as title,
            d.description,
            d.source,
            d.doc_length
        FROM inverted_index i
        JOIN documents d ON i.doc_id = d.doc_id
        WHERE i.term IN ({placeholders})
        """,
        tokens
    )

    docs = {}
    for doc_id, term, freq, url, title, description, source, doc_length in posting_rows:
        entry = docs.setdefault(doc_id, {"url": url, "doc_length": doc_length or 1, "terms": {}, "title": title, "source": source, "description": description})
        entry["terms"][term] = freq

    scored = []
    for doc_id, entry in docs.items():
        if (len(entry["terms"]) != num_tokens):
            continue

        dl = entry["doc_length"]
        score = sum(
            bm25_score(freq, dl, avgdl, term_idf[term], k1, b)
            for term, freq in entry["terms"].items()
        )

        scored.append({"title": entry["title"], "source": entry["source"], "url": entry["url"], "score": score, "description": entry["description"]})

    scored.sort(key=lambda x: x["score"], reverse=True)

    grouped = {}

    for result in scored:
        source = result["source"]

        grouped.setdefault(source, []).append(result)

    for source in grouped:
        grouped[source] = grouped[source][:10]

    return grouped