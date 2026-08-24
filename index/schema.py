def setup_schema(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id SERIAL PRIMARY KEY,
            url TEXT UNIQUE,
            novel_name VARCHAR(255),
            description TEXT,
            source VARCHAR(255),
            image_url TEXT,
            doc_length INTEGER DEFAULT 0,
            last_crawled_at VARCHAR(255),
            content_hash VARCHAR(255)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS inverted_index (
            term VARCHAR(255),
            doc_id INTEGER REFERENCES documents(doc_id),
            frequency INTEGER
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS term_ngrams (
            ngram VARCHAR(255),
            term VARCHAR(255)
        )
    """)

    db.execute("CREATE INDEX IF NOT EXISTS idx_ngram ON term_ngrams(ngram)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_inverted_doc_id ON inverted_index(doc_id)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_inverted_term_doc ON inverted_index(term, doc_id) INCLUDE (frequency)")
