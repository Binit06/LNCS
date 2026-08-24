from __future__ import annotations

import hashlib
import logging
import re
from collections.abc import Callable
from datetime import date
from typing import TYPE_CHECKING, TypedDict
from urllib.parse import urljoin, urlparse

from crawler.parser import PageParser
from frontier.task import Task

if TYPE_CHECKING:
    from crawler.controller import CrawlController

class PageData(TypedDict):
    title: str
    description: str
    image: str
    slug: str
    links: list[str]

class VisitedURLs:
    def __init__(self, redis_client, namespace: str) -> None:
        self.redis = redis_client
        self.namespace = namespace

    def _key(self) -> str:
        return f"crawler:visited:{self.namespace}:{date.today().isoformat()}" #each day gets a new redis storage  # noqa: DTZ011

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
    def __init__(
            self, 
            base_url: str, 
            seed_url: str, 
            controller: CrawlController, 
            name: str, 
            blocklist: list, 
            user_agent: str, 
            allowindb: list,
            unidirection: bool,
            unidirection_url_struct: str,
            pagination_template: str,
            rate_limit: float = 1.0,
            image_fix: Callable[[str], str] | None = None
        ) -> None:

        self.base_url = base_url
        self.seed_url = seed_url
        self.seeder_name = name
        self.controller = controller

        self.logger = logging.getLogger(f"seeder.{base_url}")

        self.blocklist = blocklist
        self.allowindb = allowindb
        self.unidirection = unidirection
        self.unidirection_url_struct = unidirection_url_struct
        self.pagination_template = pagination_template
        self.image_fix = image_fix
        self.robots = controller.robots

        self.user_agent = user_agent
        self.rate_limit = rate_limit

        self.parser = PageParser()

        self.concurrentvisits = 0
        self.visited = VisitedURLs(self.controller.redis, namespace=base_url)

    def seed(self):
        if self.pagination_template:
            self.logger.info("Seeding 100 paginated listing pages")
            for page_num in range(1, 101):
                url = urljoin(self.base_url, self.pagination_template.format(page=page_num))
                task = self.controller.create_task(
                    url=url,
                    site=self.base_url,
                    rate_limit=self.rate_limit,
                    priority=1,
                    headers={
                        "User-Agent": self.user_agent
                    }
                )
                self.visited.mark_visited(url)
                self.controller.add_task(task)
            return

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

        if self.unidirection and self.check_allowindb(task.url):
            self.logger.info(f"Unidirectional Mode: Skipping link extraction for novel page {task.url}")
            return

        for url in page["links"]:
            nurl = urljoin(task.site, url)
            if self.unidirection:
                is_structure = self.unidirection_url_struct and self.unidirection_url_struct in nurl
                is_allowed = self.check_allowindb(nurl)

                if is_structure or is_allowed:
                    self.handle_url(nurl)
                else:
                    self.logger.debug(f"Unidirectional Mode: Ignoring link {nurl}")
            else:
                self.handle_url(nurl)

    def index_page(self, url: str, page: PageData) -> None:
        if not self.check_allowindb(url):
            return

        title = page["title"]
        description = page["description"]
        image = page["image"]
        slug = page["slug"]

        if image and self.image_fix:
            image = self.image_fix(image)

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
            image_url=image,
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
            priority=0,
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
        path = urlparse(url).path.rstrip('/')
        return any(re.fullmatch(pattern, path) for pattern in self.allowindb)
