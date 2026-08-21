from index.tokenizer import tokenise
from index.fuzzy import fuzzy_match
from index.scoring import idf, bm25_score
import time
import json

STOP_WORDS = {'a', 'an', 'the', 'and', 'or', 'into', 'in', 'of', 'to', 'is', 'it', 'for', 'with', 'on', 'at', 'who'}

def _resolve_tokens(db, query: str):
    raw_tokens = tokenise(query)
    tokens = []

    for word in raw_tokens:
        if word in STOP_WORDS:
            continue
        s = time.perf_counter();
        exact_match = bool(db.query("SELECT 1 FROM inverted_index WHERE term = %s LIMIT 1", (word,)))
        e = time.perf_counter();
        print(f"Execution Time for exact match query: {e - s}")

        if (exact_match):
            tokens.append(word)
        else:
            s = time.perf_counter()
            fuzzy = fuzzy_match(db, word)
            e = time.perf_counter()
            print(f"Execution time for fuzzy match: {e - s}")
            if fuzzy:
                tokens.append(fuzzy)

    return list(tokens)

def search(db, query: str, k1: float = 1.5, b: float = 0.75):
    s = time.perf_counter()
    tokens = _resolve_tokens(db, query)
    if not tokens:
        return []

    num_tokens = len(tokens)
    placeholders = ",".join(["%s"] * num_tokens)

    (total_docs,) = db.query("SELECT COUNT(*) FROM documents", ())[0];
    if total_docs == 0:
        return []
    e = time.perf_counter()
    print(f"First Compute took : {e - s}")
    s = time.perf_counter()
    df_rows = db.query(f"""
    SELECT term, COUNT(DISTINCT doc_id)
    FROM inverted_index
    WHERE term IN ({placeholders})
    GROUP BY term
    """, tokens)
    e = time.perf_counter()
    print(f"Count distinct query took : {e - s}")

    s = time.perf_counter()
    doc_freq = {term: n for term, n in df_rows}
    term_idf = {term: idf(total_docs, doc_freq.get(term, 0)) for term in tokens}
    print(term_idf)
    e = time.perf_counter()
    print(f"freq and term_idf calculation took : {e - s}")

    s = time.perf_counter()
    rows = db.query(f"""
    WITH matched_docs AS (
        SELECT i.doc_id
        FROM inverted_index i
        WHERE i.term = ANY(%s)
        GROUP BY i.doc_id
        HAVING COUNT(DISTINCT i.term) = %s
    ),
    corpus_stats AS (
        SELECT AVG(doc_length) AS avgdl FROM documents
    )
    SELECT
        d.novel_name as title,
        d.source,
        d.url,
        d.description,
        SUM(
            (%s::json->>i.term)::float *
            (i.frequency * (%s + 1)) /
            (i.frequency + %s * (1 - %s + %s * (d.doc_length / cs.avgdl)))
        ) AS score
    FROM matched_docs md
    JOIN inverted_index i ON md.doc_id = i.doc_id
    JOIN documents d ON md.doc_id = d.doc_id
    CROSS JOIN corpus_stats cs
    WHERE i.term = ANY(%s)
    GROUP BY d.doc_id, d.novel_name, d.source, d.url, d.description, d.doc_length, cs.avgdl
    ORDER BY score desc
    LIMIT 10
    """, (tokens, num_tokens, json.dumps(term_idf), k1, k1, b, b, tokens));

    e = time.perf_counter();
    print(f"Time take for final query: {e - s}")

    s = time.perf_counter()
    grouped = {}
    for row in rows:
        title, source, url, description, score = row[0], row[1], row[2], row[3], row[4]
        grouped.setdefault(source, []).append({
            "title": title,
            "source": source,
            "url": url,
            "description": description,
            "score": score
        })
    e = time.perf_counter()
    print(f"Time take for final grouping: {e - s}")

    return grouped
