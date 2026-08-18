def setup_schema(db):
    db.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            novel_name TEXT,
            description TEXT,
            source TEXT,
            doc_length INTEGER DEFAULT 0,
            last_crawled_at TEXT,
            content_hash TEXT
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS inverted_index (
            term TEXT,
            doc_id INTEGER,
            frequency INTEGER,
            FOREIGN KEY(doc_id) REFERENCES documents(doc_id)
        )
    """)

    db.execute("""
        CREATE TABLE IF NOT EXISTS term_ngrams (
            ngram TEXT,
            term TEXT
        )
    """)

    db.execute("CREATE INDEX IF NOT EXISTS idx_term ON inverted_index(term)")
    db.execute("CREATE INDEX IF NOT EXISTS idx_ngram ON term_ngrams(ngram)")

    try:
        db.execute("ALTER TABLE documents ADD COLUMN doc_length INTEGER DEFAULT 0")
        db.execute("ALTER TABLE documents ADD COLUMN last_crawled_at TEXT")
        db.execute("ALTER TABLE documents ADD COLUMN content_hash TEXT")
    except Exception:
        pass