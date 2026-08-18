class CrawlStats:
    def __init__(self, redis) -> None:
        self.redis = redis

    def request_started(self):
        self.redis.incr("crawl:request_started")

    def request_success(self):
        self.redis.incr("crawl:request_success")

    def request_failed(self):
        self.redis.incr("crawl:request_failed")

    def page_crawled(self):
        self.redis.incr("crawl:page_crawled")

    def url_discovered(self):
        self.redis.incr("crawl:url_discovered")