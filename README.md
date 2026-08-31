# LNCS

> A small-scale search engine for books, built from scratch to understand how search systems work under the hood.

**Build philosophy:** The core system was designed and implemented by me. I used AI as an engineering tool during development, mainly for refactoring, restructuring the codebase, and improving parts of the crawler. The search architecture, indexing approach, and overall system design are my own work.

## What is LNCS?

LNCS is an experimental search engine focused on a limited set of book sources.

The goal isn't to compete with Google. It's to understand what actually happens behind a search box — from crawling and extracting content to indexing and retrieving relevant results.

### Current pipeline

```text
Seed URLs
    ↓
URL Frontier
    ↓
Crawler
    ↓
Page Parser
    ↓
Book Extraction
    ↓
Inverted Index + N-gram Index
    ↓
Storage (PostgreSQL)
    ↓
Search
    ↓
Results
```

---

## Getting Started

### Prerequisites

- **Python**: Version 3.10+
- **PostgreSQL**: Used as the primary relational and inverted index database.
- **Redis** *(Optional)*: Used for distributed URL frontier queues, rate limiting, and crawl stats tracking.

### Installation

1. Clone the repository and navigate to the project directory:
   ```bash
   git clone <repo-url>
   cd Search
   ```

2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure your environment variables. Copy `.env.sample` to `.env` and fill in the values:
   ```bash
   cp .env.sample .env
   ```

---

## CLI Commands & Usage

The project features a unified CLI interface powered by `main.py` with subcommand routing, custom flags, and automatic environment variable fallbacks.

### 1. Local Crawling (`crawl`)

Run the standard dev/local crawler and indexer. It starts by seeding configured entrypoints and recursively discovering and indexing novel detail pages.

```bash
python main.py crawl [options]
```

#### Options:
- `--workers <int>`: Number of concurrent crawler threads (default: `3`, env: `CRAWLER_WORKERS`).
- `--idle-grace <seconds>`: Grace period in seconds to wait when the queue is empty before shutting down (default: `30`, env: `CRAWLER_IDLE_GRACE`).
- `--poll-interval <seconds>`: Interval to poll queue status in seconds (default: `2`, env: `CRAWLER_POLL_INTERVAL`).
- `--redis-host <host>`: Redis host for local frontier queues and stats (default: `localhost`, env: `CRAWLER_REDIS_HOST`).
- `--redis-port <port>`: Redis port for local frontier queues and stats (default: `6379`, env: `CRAWLER_REDIS_PORT`).
- `--user-agent <string>`: User-Agent string to identify the crawler (default: `HALOVOID/1.0 (+https://github.com/Binit06/LNCS)`, env: `CRAWLER_USER_AGENT`).

### 2. Production Indexing (`index-prod`)

Runs a continuous consumer worker that reads task URLs directly from a centralized production Redis list (`index:queue`) instead of crawling sites recursively. It fetches those URLs and indexes them into the database.

```bash
python main.py index-prod [options]
```

#### Options:
- `--workers <int>`: Number of concurrent indexer threads (default: `3`, env: `CRAWLER_WORKERS`).
- `--redis-url <url>`: Redis connection URL containing credentials for the production queue (default: read from `REDIS_URL` environment variable).
- `--stats-redis-host <host>`: Redis host for local stats & rate limiting (default: `localhost`, env: `CRAWLER_REDIS_HOST`).
- `--stats-redis-port <port>`: Redis port for local stats & rate limiting (default: `6379`, env: `CRAWLER_REDIS_PORT`).
- `--user-agent <string>`: User-Agent string to identify the crawler (default: `HALOVOID/1.0 (+https://github.com/Binit06/LNCS)`, env: `CRAWLER_USER_AGENT`).

#### Legacy / Top-level Flags
For backward compatibility with legacy scripts, the `--prod` flag is supported at the root:
```bash
python main.py --prod
```
This is fully equivalent to running the default `python main.py index-prod` command.

---

## Architectural & Codebase Structure

The project is structured logically to maintain a clean separation of concerns:

- **`config/settings.py`**: Central settings file containing crawl defaults and Redis key namespace templates.
- **`config/site_registry.py`**: Declares target websites, seed URLs, HTML selectors for parsing (title, description, cover images), and site-specific rate limits.
- **`crawler/controller.py`**: Coordinates crawl execution, worker thread spawns, rate limits, and robots.txt validation.
- **`crawler/worker.py`**: Fetcher worker implementation running on daemon threads.
- **`crawler/seeder.py`**: Populates the frontier queue with the initial seed list.
- **`crawler/stats.py`**: Tallies request success, fail, and discovery counts.
- **`frontier/`**: Manages URL queues and rate limiters.
  - `queue.py`: Standard local task queue with round-robin site prioritization.
  - `prod_queue.py`: Flat list-based production queue.
  - `rate_limiter.py`: Implements sliding-window sleep delays using Lua scripts on Redis.
  - `visited.py`: Manages deduplication by hashing URLs and tracking visited states.
- **`index/`**: Tokenizer, N-gram builders, and SQL schema mappings for inverted index generation.
- **`storage/`**: Thread-safe PostgreSQL client wrapper with automatic retry-on-connection-loss.
- **`monitoring/`**: Live ASCII crawler dashboard showing current activity and requests metrics.

### Graceful Fallback Mode (Redis-Free)

The crawling components (`VisitedURLs`, `RateLimiter`, and `CrawlStats`) support **graceful fallback**. If local Redis is not installed or unreachable, they automatically degrade to using thread-safe, in-memory python structures (`set`, `dict`, and thread sleeps). This allows local development and debugging without any infrastructure overhead.

---

## Tech Stack

* **Crawler:** Python
* **Storage:** PostgreSQL / Redis
* **Indexing:** Inverted Index + N-grams
* **Scoring:** BM25 + TF-IDF

## Status

🚧 **Actively building**

This repository represents the current state of the project rather than a finished search engine.
