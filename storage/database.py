import os
import psycopg
import threading
import time
from contextlib import contextmanager

class Database:
    def __init__(self, db_name="search.db") -> None:
        self.username = os.getenv("POSTGRES_USERNAME")
        self.password = os.getenv("POSTGRES_PASSWD")
        self.dbname = os.getenv("POSTGRES_DBNAME")
        self.host = os.getenv("POSTGRES_HOST")
        self.port = os.getenv("POSTGRES_PORT")

        self.conn = None
        self.cursor = None

        self.lock = threading.Lock()

        self._connect()

    def _connect(self):
        if self.conn:
            try:
                self.conn.close()
            except Exception:
                pass

        self.conn = psycopg.connect(dbname=self.dbname, user=self.username, password=self.password, host=self.host, port=self.port);
        self.cursor = self.conn.cursor()

    def execute(self, query, params=()):
        for attempt in range(1, 4):
            try:
                with self.lock:
                    self.cursor.execute(query, params)
                    self.conn.commit()
                return
            except (psycopg.OperationalError, psycopg.InterfaceError) as e:
                print(f"Attempt {attempt - 1}: Connection lost, Retrying")
                time.sleep(2)
                try:
                    with self.lock:
                        self._connect()
                except Exception as reconnect_error:
                    print(f"Reconnection Failed: {reconnect_error}")
        raise Exception("Failed to execute query after 3 attempts")

    def executemany(self, query, params):
        for attempt in range(1, 4):
            try:
                with self.lock:
                    self.cursor.executemany(query, params)
                    self.conn.commit()
                return
            except (psycopg.OperationalError, psycopg.InterfaceError) as e:
                print(f"Attempt {attempt - 1}: Connection lost, Retrying")
                time.sleep(2)
                try:
                    with self.lock:
                        self._connect()
                except Exception as reconnect_error:
                    print(f"Reconnection Failed: {reconnect_error}")
        raise Exception("Failed to execute query after 3 attempts")

    def query(self, query, param=()):
        for attempt in range(1, 4):
            try:
                with self.lock:
                    self.cursor.execute(query, param)
                    return self.cursor.fetchall()
            except (psycopg.OperationalError, psycopg.InterfaceError) as e:
                print(f"Attempt {attempt - 1}: Connection lost, Retrying")
                time.sleep(2)
                try:
                    with self.lock:
                        self._connect()
                except Exception as reconnect_error:
                    print(f"Reconnection Failed: {reconnect_error}")
        raise Exception("Failed to execute query after 3 attempts")

    @contextmanager
    def transaction(self):
        with self.lock:
            try:
                yield self.cursor
                self.conn.commit()
            except Exception as e:
                try:
                    self.conn.rollback()
                except Exception:
                    pass
                raise
