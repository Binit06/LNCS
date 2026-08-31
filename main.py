import argparse
import logging
import os
import time

import redis
from dotenv_vault import load_dotenv

from config.site_registry import SITE_REGISTRY
from crawler.controller import CrawlController
from crawler.seeder import Seeder
from frontier.prod_queue import ProdQueue
from index import SearchIndex
from storage.database import Database

# Load environment variables first so they can be used as defaults in argparse
load_dotenv()


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("crawler.log", mode="w")
        ]
    )


def build_seeders(controller: CrawlController, default_user_agent: str):
    for cfg in SITE_REGISTRY.values():
        cfg_copy = dict(cfg)
        # Use the configured user_agent if defined in the site configuration,
        # otherwise fall back to the CLI/environment default.
        ua = cfg_copy.pop("user_agent", default_user_agent)
        controller.attach(Seeder(**cfg_copy, controller=controller, user_agent=ua))


def run_crawl(args):
    db = Database()
    index = SearchIndex(db)

    stats_redis = redis.Redis(
        host=args.redis_host,
        port=args.redis_port,
        decode_responses=True
    )

    controller = CrawlController(index=index, worker_count=args.workers, redis=stats_redis)
    build_seeders(controller, args.user_agent)

    logging.info(
        f"Starting crawler. Workers: {args.workers}, "
        f"Idle grace: {args.idle_grace}s, Poll interval: {args.poll_interval}s"
    )
    controller.start(
        idle_grace_second=args.idle_grace,
        poll_interval=args.poll_interval
    )


def run_index_prod(args):
    if not args.redis_url:
        raise ValueError(
            "REDIS_URL must be set via --redis-url or the REDIS_URL environment variable."
        )

    db = Database()
    index = SearchIndex(db)

    stats_redis = redis.Redis(
        host=args.stats_redis_host,
        port=args.stats_redis_port,
        decode_responses=True
    )

    prod_redis = redis.Redis.from_url(args.redis_url, decode_responses=True)
    prod_queue = ProdQueue(prod_redis)

    controller = CrawlController(
        index=index,
        worker_count=args.workers,
        redis=stats_redis,
        queue=prod_queue
    )
    build_seeders(controller, args.user_agent)

    logging.info(f"Starting production queue indexing. Workers: {args.workers}")
    controller.start_workers(mode="index")
    while controller.running:
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="HaloVoid Search Crawler and Indexer CLI")
    
    # Legacy / top-level flags
    parser.add_argument(
        "--prod",
        action="store_true",
        help="Legacy flag to run in production indexer mode (equivalent to index-prod subcommand)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # crawl subcommand
    crawl_parser = subparsers.add_parser("crawl", help="Run local crawler and indexer")
    crawl_parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("CRAWLER_WORKERS", 3)),
        help="Number of concurrent crawl workers (default: 3)"
    )
    crawl_parser.add_argument(
        "--idle-grace",
        type=int,
        default=int(os.getenv("CRAWLER_IDLE_GRACE", 30)),
        help="Idle grace period in seconds before shutting down (default: 30)"
    )
    crawl_parser.add_argument(
        "--poll-interval",
        type=int,
        default=int(os.getenv("CRAWLER_POLL_INTERVAL", 2)),
        help="Interval in seconds to check queue status (default: 2)"
    )
    crawl_parser.add_argument(
        "--redis-host",
        default=os.getenv("CRAWLER_REDIS_HOST", "localhost"),
        help="Redis host for local frontier queue and stats (default: localhost)"
    )
    crawl_parser.add_argument(
        "--redis-port",
        type=int,
        default=int(os.getenv("CRAWLER_REDIS_PORT", 6379)),
        help="Redis port for local frontier queue and stats (default: 6379)"
    )
    crawl_parser.add_argument(
        "--user-agent",
        default=os.getenv("CRAWLER_USER_AGENT", "HALOVOID/1.0 (+https://github.com/Binit06/LNCS)"),
        help="User-agent string to identify the crawler"
    )

    # index-prod subcommand
    prod_parser = subparsers.add_parser("index-prod", help="Run production queue indexing worker")
    prod_parser.add_argument(
        "--workers",
        type=int,
        default=int(os.getenv("CRAWLER_WORKERS", 3)),
        help="Number of concurrent indexer workers (default: 3)"
    )
    prod_parser.add_argument(
        "--redis-url",
        default=os.getenv("REDIS_URL"),
        help="Redis URL containing credentials for production queue (default: REDIS_URL env var)"
    )
    prod_parser.add_argument(
        "--stats-redis-host",
        default=os.getenv("CRAWLER_REDIS_HOST", "localhost"),
        help="Redis host for local stats & rate limiting (default: localhost)"
    )
    prod_parser.add_argument(
        "--stats-redis-port",
        type=int,
        default=int(os.getenv("CRAWLER_REDIS_PORT", 6379)),
        help="Redis port for local stats & rate limiting (default: 6379)"
    )
    prod_parser.add_argument(
        "--user-agent",
        default=os.getenv("CRAWLER_USER_AGENT", "HALOVOID/1.0 (+https://github.com/Binit06/LNCS)"),
        help="User-agent string to identify the crawler"
    )

    args = parser.parse_args()

    # Route and handle legacy or empty subcommand defaults
    if not args.command:
        if args.prod:
            args.command = "index-prod"
            args.workers = int(os.getenv("CRAWLER_WORKERS", 3))
            args.redis_url = os.getenv("REDIS_URL")
            args.stats_redis_host = os.getenv("CRAWLER_REDIS_HOST", "localhost")
            args.stats_redis_port = int(os.getenv("CRAWLER_REDIS_PORT", 6379))
            args.user_agent = os.getenv("CRAWLER_USER_AGENT", "HALOVOID/1.0 (+https://github.com/Binit06/LNCS)")
        else:
            args.command = "crawl"
            args.workers = int(os.getenv("CRAWLER_WORKERS", 3))
            args.idle_grace = int(os.getenv("CRAWLER_IDLE_GRACE", 30))
            args.poll_interval = int(os.getenv("CRAWLER_POLL_INTERVAL", 2))
            args.redis_host = os.getenv("CRAWLER_REDIS_HOST", "localhost")
            args.redis_port = int(os.getenv("CRAWLER_REDIS_PORT", 6379))
            args.user_agent = os.getenv("CRAWLER_USER_AGENT", "HALOVOID/1.0 (+https://github.com/Binit06/LNCS)")

    setup_logging()

    if args.command == "crawl":
        run_crawl(args)
    elif args.command == "index-prod":
        run_index_prod(args)


if __name__ == "__main__":
    main()

