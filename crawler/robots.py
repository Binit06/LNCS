# crawler/robots.py
import logging
import threading
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests


class RobotsChecker:
    def __init__(self, user_agent: str) -> None:
        self.user_agent = user_agent
        self._cache: dict[str, RobotFileParser] = {}
        self._disallow_all: set[str] = set()
        self._allow_all: set[str] = set()
        self._unreachable: set[str] = set()
        self._lock = threading.Lock()
        self.logger = logging.getLogger("robots")

    def _get_parser(self, url: str) -> RobotFileParser:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        with self._lock:
            if domain in self._cache:
                return self._cache[domain]

        parser = RobotFileParser()
        parser.set_url(f"{domain}/robots.txt")

        try:
            resp = requests.get(
                f"{domain}/robots.txt",
                headers={"User-Agent": self.user_agent},
                timeout=5,
            )
            if resp.status_code in (401, 403):
                with self._lock:
                    self._disallow_all.add(domain)
            elif 400 <= resp.status_code < 500:
                with self._lock:
                    self._allow_all.add(domain)
            elif resp.status_code >= 500:
                self.logger.warning(f"{domain}/robots.txt returned {resp.status_code}")
                with self._lock:
                    self._unreachable.add(domain)
            else:
                parser.parse(resp.text.splitlines())
        except requests.RequestException as e:
            self.logger.warning(f"Could not fetch robots.txt for {domain}: {e}")
            with self._lock:
                self._unreachable.add(domain)

        with self._lock:
            self._cache[domain] = parser
        return parser

    def can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        parser = self._get_parser(url)

        with self._lock:
            if domain in self._unreachable or domain in self._allow_all:
                return True
            if domain in self._disallow_all:
                return False

        return parser.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        raw = self._get_parser(url).crawl_delay(self.user_agent)
        return float(raw) if raw is not None else None
