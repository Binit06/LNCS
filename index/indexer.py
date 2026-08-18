import hashlib
from datetime import datetime
from collections import Counter

from index.tokenizer import tokenise, ngrams

def add_page(db, url: str, novel_name: str, description: str, source: str, content: str):
    tokens = tokenise(content)
    term_count = Counter(tokens)
    doc_length = len(tokens)
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    now = datetime.utcnow().isoformat()

    existing = db.query("SELECT doc_id, content_hash FROM documents WHERE url = ?", (url,))

    with db.transaction() as cursor:
        if existing:
            doc_id, old_hash = existing[0]
            if old_hash == content_hash:
                cursor.execute("UPDATE documents SET last_crawled_at = ? WHERE doc_id = ?", (now, doc_id))
                print(f"[Index] Unchange: {url}")
                return

            cursor.execute("DELETE FROM inverted_index WHERE doc_id = ?", (doc_id,))
            cursor.execute(
                """
                UPDATE documents
                SET novel_name = ?, description = ?, source = ?,
                    doc_length = ?, content_hash = ?, last_crawled_at = ?
                """,
                (novel_name, description, source, doc_length, content_hash, doc_id)
            )
        else:
            cursor.execute(
                """
                INSERT INTO documents(url, novel_name, description, source, doc_length, last_crawled_at, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (url, novel_name, description, source, doc_length, now, content_hash)
            )

            doc_id = cursor.lastrowid

        postings = [
            (term, doc_id, count)
            for term, count in term_count.items()
        ]
        cursor.executemany(
            "INSERT INTO inverted_index (term, doc_id, frequency) VALUES (?, ?, ?)",
            postings
        )

        ngram_postings = [
            (ngram, term)
            for term in term_count
            for ngram in ngrams(term)
        ]
        cursor.executemany(
            "INSERT INTO term_ngrams (ngram, term) VALUES (?, ?)",
            ngram_postings
        )

    print(f"[Index] Indexed {url} | {len(term_count)} unique terms")