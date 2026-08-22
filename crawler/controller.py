import logging
import threading
import time

import redis

from crawler.robots import RobotsChecker
from crawler.seeder import Seeder
from crawler.stats import CrawlStats
from crawler.worker import FetcherWorker
from frontier.queue import TaskQueue
from frontier.rate_limitter import RateLimiter
from frontier.task import Task
from index import SearchIndex


class CrawlController:
    def __init__(self, index: SearchIndex, worker_count=3) -> None:
        self.logger = logging.getLogger("controller")

        self.queue = TaskQueue()
        self.index = index

        self.redis = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        self.stats = CrawlStats(self.redis)
        self.rate_limitter = RateLimiter(self.redis)
        self.robots = RobotsChecker(user_agent="HALOVOID/1.0 (+https://github.com/Binit06)")

        self.seeders: dict[str, Seeder] = {}
        self.workers = []

        self.worker_count = worker_count

        self.running = False

    def attach(self, seeder):
        self.seeders[seeder.base_url] = seeder
        self.logger.info(f"Attached Seeder: {seeder.base_url}")

    def detach(self, base_url):
        seeder = self.seeders.pop(base_url, None)
        if seeder:
            self.logger.info(f"Detached seeder: {base_url}")

    def get_seeder(self, site) -> Seeder | None:
        return self.seeders.get(site)

    def create_task(
            self,
            url,
            site,
            rate_limit=1.0,
            priority=1,
            headers=None
    ):
        return Task(
            url=url,
            site=site,
            rate_limit=rate_limit,
            priority=priority,
            headers=headers or {}
        )
    
    def add_task(self, task: Task):
        self.queue.add(task)

    def start_workers(self):
        self.running = True

        for i in range(self.worker_count):
            worker = FetcherWorker(
                worker_id=i + 1,
                controller = self
            )

            thread = threading.Thread(
                target=worker.run,
                daemon=True
            )

            thread.start()
            self.workers.append(thread)
        self.logger.info(f"Started {self.worker_count} Workers")

    def start_seeders(self):
        for seeder in self.seeders.values():
            seeder.seed()
    

    def start(self, idle_grace_second: int, poll_interval: int):
        self.start_workers()
        self.start_seeders()

        idle_since = None
        while True:
            if self.queue.empty():
                idle_since = idle_since or time.time()
                if time.time() - idle_since > idle_grace_second:
                    logging.info("Queue drained: Crawl is done")  # noqa: LOG015
                    break
            else:
                idle_since = None
            time.sleep(poll_interval)
