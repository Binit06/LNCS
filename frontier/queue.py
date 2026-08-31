import redis

from config.settings import (
    REDIS_KEY_ACTIVE_SITES,
    REDIS_KEY_DEAD_LETTER,
    REDIS_KEY_ROTATION,
    REDIS_KEY_SEQ,
    REDIS_KEY_QUEUE_TEMPLATE,
)
from frontier.task import Task


class TaskQueue:
    def __init__(self, redis_client=None, key_prefix="crawler") -> None:
        self.redis = redis_client or redis.Redis(host="localhost", port=6379, decode_responses=True)

        self.key_prefix = key_prefix

        self.sites_key = REDIS_KEY_ACTIVE_SITES
        self.dead_letter_name = REDIS_KEY_DEAD_LETTER
        self.rotation_key = REDIS_KEY_ROTATION
        self.seq_key = REDIS_KEY_SEQ

    def _queue_name(self, site: str) -> str:
        if self.key_prefix != "crawler":
            return f"{self.key_prefix}:queue:{site}"
        return REDIS_KEY_QUEUE_TEMPLATE.format(site=site)

    def _decode(self, value: bytes | str) -> str:
        return value.decode() if isinstance(value, bytes) else value

    def add(self, task: Task):
        seq = self.redis.incr(self.seq_key)
        score = task.priority * 1_000_000_000 + seq
        self.redis.zadd(self._queue_name(task.site), {task.to_json(): score})
        self.redis.sadd(self.sites_key, task.site)

    def get(self) -> Task | None:
        raw_sites = list(self.redis.smembers(self.sites_key))
        sites = sorted(self._decode(s) for s in raw_sites)
        if not sites:
            return None

        sites.sort()

        offset = self.redis.incr(self.rotation_key) % len(sites)
        rotated = sites[offset:] + sites[:offset]
        queue_names = [self._queue_name(site) for site in rotated]

        data = self.redis.bzpopmin(queue_names, timeout=1)
        if data is None:
            return None

        _queue_name, task_data, _score = data
        return Task.from_json(task_data)

    def empty(self) -> bool:
        return self.size() == 0

    def size(self) -> int:
        raw_sites = self.redis.smembers(self.sites_key)
        sites = (self._decode(s) for s in raw_sites)
        return sum(self.redis.zcard(self._queue_name(site)) for site in sites)

    def dead_letter(self, task: Task):
        self.redis.rpush(self.dead_letter_name, task.to_json())
