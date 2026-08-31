from __future__ import annotations

import json
from typing import Any

from config.settings import REDIS_KEY_PROD_QUEUE, REDIS_KEY_PROD_DEAD_LETTER
from config.site_registry import SITE_REGISTRY, SiteConfig
from frontier.task import Task


class ProdQueue:
    """Single flat Redis list for user-submitted indexing requests.
    No per-site sharding — the producer just pushes URLs into one key."""

    def __init__(self, redis_client, key=None, dead_letter_key=None) -> None:
        self.redis = redis_client
        self.key = key or REDIS_KEY_PROD_QUEUE
        self.dead_letter_key = dead_letter_key or REDIS_KEY_PROD_DEAD_LETTER

    def _resolve_site(self, url: str) -> SiteConfig | None:
        for cfg in SITE_REGISTRY.values():
            if url.startswith(cfg["base_url"]):
                return cfg
        return None

    def add(self, task: Task) -> None:
        self.redis.lpush(self.key, task.to_json())

    def get(self) -> Task | None:
        data = self.redis.brpop(self.key, timeout=1)
        if data is None:
            return None
        _key, raw = data
        if isinstance(raw, bytes):
            raw = raw.decode()

        # The queue holds two shapes: plain URL strings pushed by external
        # submitters, and full JSON Task payloads re-enqueued by the retry
        # path (add() always serializes via task.to_json()). Handle both.
        # Explicitly widened to dict[str, Any] so the type checker doesn't
        # narrow it to the shape of the {"url": raw} fallback literal.
        payload: dict[str, Any]
        try:
            parsed = json.loads(raw)
            if not isinstance(parsed, dict) or "url" not in parsed:
                raise ValueError("decoded JSON is not a task payload")
            payload = parsed
        except (json.JSONDecodeError, ValueError):
            payload = {"url": raw}

        url = payload["url"]
        cfg = self._resolve_site(url)
        if cfg is None:
            print(f"[ProdQueue] No site matched for {url}, dropping")
            return None

        payload["site"] = cfg["base_url"]

        # Bare-URL submissions (and any retry payload that somehow lost its
        # headers) have no User-Agent, which is what novelfull.com's 403s
        # were actually about - not a routing problem.
        headers: dict[str, Any] = payload.get("headers") or {}
        if not headers.get("User-Agent"):
            headers["User-Agent"] = cfg["user_agent"]
        payload["headers"] = headers

        return Task(**payload)

    def empty(self) -> bool:
        return self.redis.llen(self.key) == 0

    def dead_letter(self, task: Task) -> None:
        self.redis.rpush(self.dead_letter_key, task.to_json())
