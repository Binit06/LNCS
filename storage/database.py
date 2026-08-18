import sqlite3
import threading
from contextlib import contextmanager

class Database:
    def __init__(self, db_name="search.db") -> None:
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
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