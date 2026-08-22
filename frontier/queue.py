
import redis

from frontier.task import Task


class TaskQueue:
    def __init__(self) -> None:
        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        self.sites_key = "crawler:active_sites"
        self.dead_letter_name = "crawler:dead_letter"
        self.rotaion_key = "crawler:rotation"

    def _queue_name(self, site: str) -> str:
         return f"crawler:queue:{site}"

    def _decode(self, value: bytes | str) -> str:
        return value.decode() if isinstance(value, bytes) else value

    def add(self, task: Task):
        self.redis.rpush(self._queue_name(task.site), task.to_json())
        self.redis.sadd(self.sites_key, task.site)

    def get(self) -> Task | None:
        raw_sites = list(self.redis.smembers(self.sites_key))
        sites = sorted(self._decode(s) for s in raw_sites)
        if not sites:
            return None

        sites.sort()

        offset = self.redis.incr(self.rotaion_key) % len(sites)
        rotated = sites[offset:] + sites[:offset]

        queue_names = [self._queue_name(site) for site in rotated]

        data = self.redis.blpop(queue_names, timeout=1)
        if data is None:
            return None

        _queue_name, task_data = data
        return Task.from_json(task_data)

    def empty(self) -> bool:
        return self.size() == 0

    def size(self) -> int:
        raw_sites = self.redis.smembers(self.sites_key)
        sites = (self._decode(s) for s in raw_sites)
        return sum(self.redis.llen(self._queue_name(site)) for site in sites)

    def dead_letter(self, task: Task):
        """Park permanently-failing tasks for later inspection instead of
        dropping them silently."""
        self.redis.rpush(self.dead_letter_name, task.to_json())
