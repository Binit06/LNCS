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
from dotenv_vault import load_dotenv

load_dotenv()

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
# Frontend
# --------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(STATIC_DIR, "index.html")


# --------------------------------------------------
# Search API
# --------------------------------------------------

@app.route("/api/search")
def search_api():
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
# Run
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5050,
        debug=True
    )
