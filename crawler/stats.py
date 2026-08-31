from config.settings import REDIS_KEY_CRAWL_STATS


class CrawlStats:
    def __init__(self, redis) -> None:
        self.redis = redis
        self._local_stats = {}

    def _incr(self, metric: str):
        if self.redis is None:
            self._local_stats[metric] = self._local_stats.get(metric, 0) + 1
            return
        key = REDIS_KEY_CRAWL_STATS.format(metric=metric)
        self.redis.incr(key)

    def request_started(self):
        self._incr("request_started")

    def request_success(self):
        self._incr("request_success")

    def request_failed(self):
        self._incr("request_failed")

    def page_crawled(self):
        self._incr("page_crawled")

    def url_discovered(self):
        self._incr("url_discovered")