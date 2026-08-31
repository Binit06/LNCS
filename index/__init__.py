from datetime import datetime, timedelta

from config.settings import RECRAWL_INTERVAL_DAYS
from index.indexer import add_page as _add_page
from index.schema import setup_schema
from storage.database import Database


class SearchIndex:
    def __init__(self, db: Database) -> None:
        self.db = db
        setup_schema(db)

    def add_page(self, url, novel_name, description, source, image_url, content):
        return _add_page(self.db, url, novel_name, description, source, image_url, content)

    # A page should be recrawled periodically to check for change in contents
    def should_crawl(self, url: str, recrawl_interval: timedelta | None = None) -> bool:
        if recrawl_interval is None:
            recrawl_interval = timedelta(days=RECRAWL_INTERVAL_DAYS)
        rows = self.db.query(
            "SELECT last_crawled_at FROM documents WHERE url = %s", (url,)
        )
        if not rows or rows[0][0] is None:
            return True

        last = datetime.fromisoformat(rows[0][0])
        return datetime.utcnow() - last > recrawl_interval  # noqa: DTZ003
