from __future__ import annotations

import logging
import hashlib
from crawler.parser import PageParser
from frontier.task import Task
from datetime import date
from urllib.parse import urljoin, urlparse
from typing import TypedDict, TYPE_CHECKING

if TYPE_CHECKING:
    from crawler.controller import CrawlController

class PageData(TypedDict):
    title: str
    description: str
    slug: str
    links: list[str]

class VisitedURLs:
    def __init__(self, redis_client, namespace: str) -> None:
        self.redis = redis_client
        self.namespace = namespace

    def _key(self) -> str:
        return f"crawler:visited:{self.namespace}:{date.today().isoformat()}" #each day gets a new redis storage

    def normalize(self, url: str) -> str:
        return url.split("#")[0].rstrip("/")

    def _hash(self, url: str) -> str:
        return hashlib.sha1(self.normalize(url).encode()).hexdigest()

    def mark_visited(self, url: str) -> bool:
        key = self._key()
        added = bool(self.redis.sadd(key, self._hash(url)))
        self.redis.expire(key, 172800) # today's storage expires yesterday
        return added

class Seeder:
    def __init__(self, base_url: str, seed_url: str, controller: "CrawlController", name: str, blocklist: list, user_agent: str, allowindb: list, rate_limit: float = 1.0) -> None:
        self.base_url = base_url
        self.seed_url = seed_url
        self.seeder_name = name
        self.controller = controller

        self.logger = logging.getLogger(f"seeder.{base_url}")

        self.blocklist = blocklist
        self.allowindb = allowindb
        self.robots = controller.robots

        self.user_agent = user_agent
        self.rate_limit = rate_limit

        self.parser = PageParser()

        self.concurrentvisits = 0
        self.visited = VisitedURLs(self.controller.redis, namespace=base_url)

    def seed(self):
        url = urljoin(self.base_url, self.seed_url)
        self.logger.info(f"Seeding initial URL: {url}")
        task = self.controller.create_task(
            url=url,
            site=self.base_url,
            rate_limit=self.rate_limit,
            headers={
                "User-Agent": self.user_agent
            }
        )
        self.visited.mark_visited(url)

        self.controller.add_task(task)

    def process(self, task: Task, raw_html: str) -> None:
        self.logger.info(f"Parsing: {task.url}")

        page: PageData = self.parser.parse(
            task.url,
            raw_html
        )

        self.index_page(task.url, page)

        for url in page["links"]:
            nurl = urljoin(task.site, url)
            self.handle_url(nurl)

    def index_page(self, url: str, page: PageData) -> None:
        if not self.check_allowindb(url):
            return

        title = page["title"]
        description = page["description"]
        slug = page["slug"]

        page_content = (
            f"{title} "
            f"{description} "
            f"{slug}"
        )

        self.controller.index.add_page(
            url,
            novel_name=title,
            description=description,
            source=self.seeder_name,
            content=page_content
        )

    def handle_url(self, url: str) -> None:
        if not url.startswith(self.base_url):
            self.logger.info(f"Rejected url: {url} since it does not starts with {self.base_url}")
            return

        if self.check_blocklist(url):
            self.logger.info(f"Blocked: {url}")
            return

        if not self.robots.can_fetch(url):
            self.logger.info(f"Rejected url: {url} since it is blocked by robots.txt")
            return

        if not self.visited.mark_visited(url):
            self.logger.info(f"Visited url: {url} has already been visited today")
            return

        if self.check_allowindb(url) and not self.controller.index.should_crawl(url):
            self.logger.info(f"Skipping, recently indexed: {url}")
            return
        
        self.controller.stats.url_discovered()
        self.logger.info(f"Discovered: {url}")

        task = self.controller.create_task(
            url=url,
            site=self.base_url,
            rate_limit=self.rate_limit,
            headers={
                "User-Agent": self.user_agent
            }
        )

        self.controller.add_task(task)

    def check_blocklist(self, url: str) -> bool:
        return any(
            item in url
            for item in self.blocklist
        )

    def check_allowindb(self, url: str) -> bool:
        path = urlparse(url).path.rstrip("/")

        for allowed in self.allowindb:
            allowed = allowed.rstrip("/")

            if path == allowed or path.startswith(allowed + "/"):
                return True

        return False