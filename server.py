"""
Local search server for testing the crawler + search index.

Run with:
    python server.py

Then open:
    http://localhost:5050
"""

import logging
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from storage.database import Database
from index import SearchIndex

try:
    import redis
except ImportError:
    redis = None


# --------------------------------------------------
# Setup
# --------------------------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("search-console")

app = Flask(__name__, static_folder=None)

db = Database("search.db")
index = SearchIndex(db)

STATIC_DIR = Path(__file__).parent / "search_ui"


# --------------------------------------------------
# Redis
# --------------------------------------------------

redis_client = None

if redis:
    try:
        redis_client = redis.Redis(
            host="localhost",
            port=6379,
            decode_responses=True
        )

        redis_client.ping()

        logger.info("Redis connected")

    except Exception:
        logger.warning(
            "Redis not reachable -- live crawl stats will be disabled"
        )

        redis_client = None


# --------------------------------------------------
# Frontend
# --------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")


# --------------------------------------------------
# Search API
# --------------------------------------------------

@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip()

    # Empty query
    if not query:
        return jsonify({
            "query": "",
            "results": {}
        })

    try:
        results = index.search(query)

        return jsonify({
            "query": query,
            "results": results
        })

    except Exception:
        logger.exception("Search failed")

        return jsonify({
            "query": query,
            "results": {},
            "error": "Search failed"
        }), 500


# --------------------------------------------------
# Crawl / index statistics
# --------------------------------------------------

@app.route("/api/stats")
def stats():
    try:
        doc_count = db.query(
            "SELECT COUNT(*) FROM documents"
        )[0][0]

        crawl_stats = {}

        if redis_client:
            try:
                keys = {
                    "requests": "crawl:request_started",
                    "successful": "crawl:request_success",
                    "failed": "crawl:request_failed",
                    "pages_crawled": "crawl:page_crawled",
                    "urls_discovered": "crawl:url_discovered",
                }

                for label, redis_key in keys.items():
                    value = redis_client.get(redis_key)
                    crawl_stats[label] = int(value) if value else 0

            except Exception as e:
                logger.warning(
                    f"Failed to read crawl stats: {e}"
                )

        return jsonify({
            "indexed_documents": doc_count,
            "crawl": crawl_stats,
            "redis_connected": redis_client is not None
        })

    except Exception:
        logger.exception("Failed to fetch stats")

        return jsonify({
            "indexed_documents": 0,
            "crawl": {},
            "redis_connected": False,
            "error": "Failed to fetch stats"
        }), 500


# --------------------------------------------------
# Run
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5050,
        debug=True
    )