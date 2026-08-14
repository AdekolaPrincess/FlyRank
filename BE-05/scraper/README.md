# The Polite Scraper

## Target Classification

- **Site:** https://books.toscrape.com
- **Why this site:** It is a public practice sandbox built specifically for learning web scraping. Its own about page (toscrape.com) states it "desperately wants to be scraped" and is "a safe place for beginners learning web scraping."
- **Scope:** Only the first 3 catalogue pages (60 books total) will be visited. No other site or page range is touched.
- **Data collected:** Book title, price, availability, star rating, description, and page URL publicly displayed catalogue information only.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` once the site returned a 404 Not Found. No robots file exists. This is treated as "no robots file found," not as blanket permission the decision to scrape is instead based on the site's own stated purpose above.
- **Appropriateness:** Since the site explicitly exists for this purpose, scraping its publicly visible catalogue data at a slow, identified low-volume rate is appropriate here.

I will not reuse this code on another site without checking its rules and terms first.

## Setup

1. Clone the repo and navigate into this folder.
2. Create and activate a virtual environment:
`python -m venv venv`
`.\venv\Scripts\Activate.ps1`
3. Install dependencies:
 pip install -r requirements.txt

## Run
`python src\main.py`

This fetches the first 3 catalogue pages of https://books.toscrape.com,
visits all 60 discovered book pages, and writes:

- `output/books.json` — 60 validated book records
- `output/errors.json` — any records that failed validation
- `output/run-report.json` — a summary of the run (counts, timing, failures)

Re-running the script reuses cached pages from `cache/` and produces the
same 60 records — not duplicates.

## Record Schema

Each validated record in `books.json` has this shape:

| Field                | Type            | Notes                                      |
|-----------------------|-----------------|---------------------------------------------|
| `title`               | string          | Book title                                  |
| `product_url`         | string          | Absolute URL, used as the record's identity |
| `price_gbp`           | number          | Cleaned numeric price, e.g. `51.77`         |
| `price_text`          | string          | Original text as shown on the page, e.g. `£51.77` |
| `availability_text`   | string          | Raw stock text, e.g. `In stock (22 available)` |
| `rating_text`         | string          | Star rating as a word, e.g. `Three`         |
| `description`         | string or null  | `null` when the book has no description     |
| `source_page`         | string          | Which catalogue page this book was found on |
| `fetched_at`          | string          | UTC timestamp of when the page was fetched  |

## Politeness Rules

- Every real request sends an identifying user-agent naming this project and a link to this repo.
- Every request has a 10 second timeout — it never waits forever.
- The script waits at least 500ms between real requests to the site. Cached pages are read instantly with no delay, since they never leave this computer.
- The status code is always checked before any content is used. Only `200` is treated as a successful page.
- A `404` or `403` is never retried — the answer will not change, and retrying is how a polite scraper becomes a pest. A timeout or `5xx` server error is retried once, in case it was a temporary issue.
- One broken page never stops the run: it is logged with a reason and the script moves on.

## Sample Run Report

```json
{
  "start_time": "2026-08-14T12:32:21.162436+00:00",
  "duration_seconds": 2.109573,
  "catalogue_pages_fetched": 3,
  "unique_book_urls_discovered": 60,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failed_page_details": []
}
```

## Why This Didn't Need a Browser

The book data (title, price, availability, description) is already present in the plain HTML the server sends back on first request — nothing on these pages is loaded afterward with JavaScript. A browser would only add extra time and memory to render a page whose data was already available in the initial response.

## Ethics Note

This scraper only touches a site built and intended for scraping practice. In real work, I would first check for an official API before scraping anything, since an API is a more stable and explicitly permitted way to get the same data. I would never bypass a login, a paywall, or a block a site puts up on purpose, those are the site explicitly saying no. I only collect the specific data actually needed for the task, not everything a page contains.

## Known Limitation

This scraper is built for one specific site's HTML structure. If Books to Scrape changes its page layout, the CSS selectors used for extraction
would need to be updated, this script does not automatically detect or adapt to structural changes on its own.