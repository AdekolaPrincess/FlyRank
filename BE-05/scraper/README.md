# The Polite Scraper

## Target Classification

- **Site:** https://books.toscrape.com
- **Why this site:** It is a public practice sandbox built specifically for learning web scraping. Its own about page (toscrape.com) states it "desperately wants to be scraped" and is "a safe place for beginners learning web scraping."
- **Scope:** Only the first 3 catalogue pages (60 books total) will be visited. No other site or page range is touched.
- **Data collected:** Book title, price, availability, star rating, description, and page URL publicly displayed catalogue information only.
- **robots.txt result:** Requested `https://books.toscrape.com/robots.txt` once the site returned a 404 Not Found. No robots file exists. This is treated as "no robots file found," not as blanket permission the decision to scrape is instead based on the site's own stated purpose above.
- **Appropriateness:** Since the site explicitly exists for this purpose, scraping its publicly visible catalogue data at a slow, identified low-volume rate is appropriate here.

I will not reuse this code on another site without checking its rules and terms first.