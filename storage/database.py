import os
import psycopg
import threading
from contextlib import contextmanager

class Database:
    def __init__(self, db_name="search.db") -> None:
        self.username = os.getenv("POSTGRES_USERNAME")
        self.password = os.getenv("POSTGRES_PASSWD")
        self.dbname = os.getenv("POSTGRES_DBNAME")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")

        self.conn = psycopg.connect(dbname=self.dbname, user=self.username, password=self.password, host=self.host, port=self.port);
        self.cursor = self.conn.cursor()

        self.lock = threading.Lock()

    def execute(self, query, params=()):
        with self.lock:
            self.cursor.execute(query, params)
            self.conn.commit()

    def executemany(self, query, params):
        with self.lock:
            self.cursor.executemany(query, params)
            self.conn.commit()

    def query(self, query, param=()):
        with self.lock:
            self.cursor.execute(query, param)
            return self.cursor.fetchall()

    @contextmanager
    def transaction(self):
        with self.lock:
            try:
                yield self.cursor
                self.conn.commit()
            except Exception as e:
                self.conn.rollback()
                raise
