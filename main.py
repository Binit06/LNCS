import logging
import os

from crawler.controller import CrawlController
from crawler.seeder import Seeder
from index import SearchIndex
from storage.database import Database
from config.site_registry import SITE_REGISTRY
from dotenv_vault import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s "
            "[%(name)s] "
            "%(levelname)s: "
            "%(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("crawler.log", mode="w")
    ]
)

USER_AGENT = "HALOVOID/1.0 (+https://github.com/Binit06)"
IDLE_GRACE_SECOND = 30
POLL_INTERVAL = 2

def build_seeders(controller: CrawlController):
    for domain, config in SITE_REGISTRY.items():
        seeder = Seeder(
            controller=controller,
            user_agent=USER_AGENT,
            **config
        )
        controller.attach(seeder)

def main():
    db = Database("search.db")
    return;
    index = SearchIndex(db)

    controller = CrawlController(
        index=index,
        worker_count=6
    )

    build_seeders(controller)

    controller.start(idle_grace_second=IDLE_GRACE_SECOND, poll_interval=POLL_INTERVAL)

if __name__ == "__main__":
    main()
