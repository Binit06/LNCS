import sqlite3
import psycopg

def main():
    sqlite_conn = sqlite3.connect("search.db", check_same_thread=False)
    psql_conn = psycopg.connect("postgres://<user_name>:<password>@<host_name>:<port>/<db_name>?sslmode=require")

    sqlite_cursor = sqlite_conn.cursor()
    psql_cursor = psql_conn.cursor()

    doc_insert_query="""
    INSERT INTO documents (doc_id, url, novel_name, description, source, doc_length, last_crawled_at, content_hash)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """

    inverted_index_query="""
    INSERT INTO inverted_index (term, doc_id, frequency)
    VALUES (%s, %s, %s);
    """

    term_ngrams="""
    INSERT INTO term_ngrams (ngram, term)
    VALUES (%s, %s);
    """

    sqlite_cursor.execute("SELECT * FROM documents")
    result = sqlite_cursor.fetchall()
    print("SUCCESS: Data fetched from sqlite")

    try:
        psql_cursor.executemany(doc_insert_query, result)
        psql_conn.commit()
    except Exception as e:
        print(f"ERROR: Failed to insert doc into psql : {e}")
        psql_conn.rollback()
        return

    sqlite_cursor.execute("SELECT * FROM inverted_index")
    result = sqlite_cursor.fetchall()

    try:
        psql_cursor.executemany(inverted_index_query, result)
        psql_conn.commit()
    except Exception as e:
        print(f"ERROR: Failed to insert inverted index into psql : {e}")
        psql_conn.rollback()
        return


    sqlite_cursor.execute("SELECT * FROM term_ngrams")
    result = sqlite_cursor.fetchall()

    try:
        psql_cursor.executemany(term_ngrams, result)
        psql_conn.commit()
    except Exception as e:
        print(f"ERROR: Failed to insert term_ngrams into psql : {e}")
        psql_conn.rollback()
        return

if __name__ == "__main__":
    main()
