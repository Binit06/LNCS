# config/settings.py

# Global crawler defaults
DEFAULT_USER_AGENT = "HALOVOID/1.0 (+https://github.com/Binit06/LNCS)"
RECRAWL_INTERVAL_DAYS = 3
IDLE_GRACE_SECOND = 30
POLL_INTERVAL = 2

# Redis keys templates and namespaces
REDIS_KEY_CRAWL_STATS = "crawl:{metric}"
REDIS_KEY_VISITED_URLS = "crawler:visited:{namespace}:{date_str}"
REDIS_KEY_RATE_LIMIT = "crawler:ratelimit:{site}"

# Local queue Redis keys
REDIS_KEY_ACTIVE_SITES = "crawler:active_sites"
REDIS_KEY_DEAD_LETTER = "crawler:dead_letter"
REDIS_KEY_ROTATION = "crawler:rotation"
REDIS_KEY_SEQ = "crawler:seq"
REDIS_KEY_QUEUE_TEMPLATE = "crawler:queue:{site}"

# Production queue Redis keys
REDIS_KEY_PROD_QUEUE = "index:queue"
REDIS_KEY_PROD_DEAD_LETTER = "index:dead_letter"
