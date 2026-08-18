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
Storage
    ↓
Search
    ↓
Results
```

## Current Features

* Crawls and discovers URLs automatically
* Extracts book information from crawled pages
* Stores indexed book data
* Inverted index for faster search
* N-gram indexing for query matching
* Search across the collected book database
* Distributed/local queue-based crawling
* URL deduplication

## Why I built this

I wanted to understand how search engines work beyond simply calling a search API.

So instead of using an external search service, I decided to build the pieces myself:

**Crawling → Parsing → Indexing → Searching**

The project is intentionally being built incrementally, and I'm documenting the process as I go.

## Current Status

The system is currently crawling a small number of sites and can search through the books it has collected.

There is still a lot to improve, particularly around:

* Ranking / relevance
* Crawling scale
* Duplicate detection
* Search quality
* Performance
* Handling more sources

This is an ongoing learning project, so the architecture will probably change quite a bit as I understand the problems better.

## Tech Stack

* **Crawler:** Python
* **Storage:** SQLite / Redis
* **Indexing:** Inverted Index + N-grams
* **Scoring:** BM25

## Status

🚧 **Actively building**

This repository represents the current state of the project rather than a finished search engine.
