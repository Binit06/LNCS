from storage.database import Database
from index.schema import setup_schema
from index.indexer import add_page as _add_page
from index.query import search as _search

from datetime import datetime, timedelta
class SearchIndex:
    def __init__(self, db: Database) -> None:
        self.db = db
        setup_schema(db)

    def add_page(self, url, novel_name, description, source, content):
        return _add_page(self.db, url, novel_name, description, source, content)

    def search(self, query, k1=1.5, b=0.75):
        return _search(self.db, query, k1, b)

    # A page should be recrawled every 3 days to check for change in contents
    def should_crawl(self, url: str, recrawl_interval: timedelta = timedelta(days=3)) -> bool:
        rows = self.db.query(
            "SELECT last_crawled_at FROM documents WHERE url = %s", (url,)
        )
        if not rows or rows[0][0] is None:
            return True

        last = datetime.fromisoformat(rows[0][0])
        return datetime.utcnow() - last > recrawl_interval
