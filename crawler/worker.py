from __future__ import annotations

import logging
import requests

from typing import TYPE_CHECKING
from frontier.task import Task

if TYPE_CHECKING:
    from crawler.controller import CrawlController

class FetcherWorker:
    def __init__(self, worker_id: int, controller: "CrawlController") -> None:
        self.worker_id = worker_id
        self.controller = controller

        self.logger = logging.getLogger(f"worker.{worker_id}")

    def run(self):
        self.logger.info(f"Started, waiting for url's")
        while True:
            task = self.controller.queue.get()

            if not task:
                continue

            self.logger.info(f"Fetching: {task.url}")
            self.controller.stats.request_started()
            self.controller.rate_limitter.wait(task.site, task.rate_limit)

            try:
                response = requests.get(task.url, headers=task.headers, timeout=3)
                if response.status_code == 200:
                    self.controller.stats.request_success()
                    self.controller.stats.page_crawled()

                    seeder = self.controller.get_seeder(task.site)

                    if seeder:
                        seeder.process(
                            task,
                            response.text
                        )
                    else:
                        self.logger.error(f"No seeder found for {task.site}")
                else:
                    self.controller.stats.request_failed()
                    self.logger.warning(
                        f"{task.url} returned "
                        f"{response.status_code}"
                    )
                    self.handle_failure(task)
            except Exception as e:
                self.controller.stats.request_failed()
                self.logger.exception(f"Error fetching {task.url}")
                self.handle_failure(task)

    def handle_failure(self, task: Task):
        task.retry_count += 1

        if task.retry_count <= task.max_retries:
            self.logger.info(
                f"Retrying {task.url} "
                f"(attempt {task.retry_count}/{task.max_retries})"
            )
            self.controller.add_task(task)
        else:
            self.logger.warning(
                f"Giving up on {task.url} "
                f"after {task.max_retries} retries"
            )
            self.controller.queue.dead_letter(task)