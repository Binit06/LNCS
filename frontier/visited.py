import hashlib
from datetime import date
from config.settings import REDIS_KEY_VISITED_URLS


class VisitedURLs:
    def __init__(self, redis_client, namespace: str) -> None:
        self.redis = redis_client
        self.namespace = namespace
        # In-memory fallback if Redis is not present/configured
        self._local_visited = set()

    def _key(self) -> str:
        return REDIS_KEY_VISITED_URLS.format(
            namespace=self.namespace,
            date_str=date.today().isoformat()
        )

    def normalize(self, url: str) -> str:
        return url.split("#")[0].rstrip("/")

    def _hash(self, url: str) -> str:
        return hashlib.sha1(self.normalize(url).encode()).hexdigest()

    def mark_visited(self, url: str) -> bool:
        url_hash = self._hash(url)
        if self.redis is None:
            if url_hash in self._local_visited:
                return False
            self._local_visited.add(url_hash)
            return True

        key = self._key()
        added = bool(self.redis.sadd(key, url_hash))
        self.redis.expire(key, 172800) # today's storage expires in 2 days
        return added
