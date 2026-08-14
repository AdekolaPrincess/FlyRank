import requests
import os
import time
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from pydantic import BaseModel
from typing import Optional

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/AdekolaPrincess/FlyRank)"
TIMEOUT_SECONDS = 10

class Book(BaseModel):
    title: str
    product_url: str
    price_gbp: float
    price_text: str
    availability_text: str
    rating_text: str
    description: Optional[str]
    source_page: str
    fetched_at: str

def fetch_page(url, cache_path):
    if os.path.exists(cache_path):
        print(f"CACHE HIT: {cache_path}")
        with open(cache_path, "r", encoding = "utf-8") as f:
            return f.read()

    print(f"FETCH: {url}")
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers = headers, timeout = TIMEOUT_SECONDS)
    response.encoding = "utf-8"
    print(f"Status code: {response.status_code}, size: {len(response.text)} bytes")

    if response.status_code != 200:
        raise Exception(f"Failed to fetch {url}: status {response.status_code}")
    with open(cache_path, "w", encoding = "utf-8") as f:
        f.write(response.text)
    time.sleep(0.5)
    return response.text

def extract_book_links(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    book_links = []

    for article in soup.select("article.product_pod"):
        link_tag = article.select_one("h3 a")
        href = link_tag["href"]
        absolute_url = urljoin(page_url, href)
        book_links.append((absolute_url, page_url))

    return book_links

def find_next_page_url(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link is None:
        return None
    href = next_link["href"]
    return urljoin(page_url, href)

def url_to_cache_filename(url):
    slug = url.rstrip("/").split("/")[-2]
    return f"book-{slug}.html"

def extract_book_details(html, product_url, source_page):
    soup = BeautifulSoup(html, "html.parser")

    title = soup.select_one("div.product_main h1").get_text(strip=True)

    price_text = soup.select_one("p.price_color").get_text(strip=True)

    availability_text = soup.select_one("p.availability").get_text(strip=True)

    rating_tag = soup.select_one("p.star-rating")
    rating_text = rating_tag["class"][1]

    description_tag = soup.select_one("#product_description ~ p")
    description = description_tag.get_text(strip=True) if description_tag else None

    return {
        "title": title,
        "product_url": product_url,
        "price_text": price_text,
        "availability_text": availability_text,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }

def parse_price(price_text):
    cleaned = price_text.replace("£", "").strip()
    return float(cleaned)

if __name__ == "__main__":
    os.makedirs("cache", exist_ok=True)

    all_links = []
    page_number = 1
    current_url = "https://books.toscrape.com/catalogue/page-1.html"

    MAX_PAGES = 3
    while current_url is not None and page_number <= MAX_PAGES:
        cache_path = os.path.join("cache", f"catalogue-page-{page_number}.html")
        html = fetch_page(current_url, cache_path)

        links = extract_book_links(html, current_url)
        all_links.extend(links)

        current_url = find_next_page_url(html, current_url)
        page_number += 1

    seen_urls = set()
    unique_links = []
    for url, source_page in all_links:
        if url not in seen_urls:
            seen_urls.add(url)
            unique_links.append((url, source_page))

    print(f"catalogue_pages={page_number - 1}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")

    all_books = []
    failed_pages = []

    for book_url, source_page in unique_links:
        book_cache_path = os.path.join("cache", url_to_cache_filename(book_url))
        try:
            book_html = fetch_page(book_url, book_cache_path)
            book_details = extract_book_details(book_html, book_url, source_page)
            all_books.append(book_details)
        except Exception as e:
            print(f"FAILED: {book_url} ({e})")
            failed_pages.append({"url": book_url, "reason": str(e)})

    print(f"detail_pages={len(all_books)}")

    valid_books = []
    invalid_records = []

    for raw_record in all_books:
        try:
            price_gbp = parse_price(raw_record["price_text"])
            book = Book(
                title=raw_record["title"],
                product_url=raw_record["product_url"],
                price_gbp=price_gbp,
                price_text=raw_record["price_text"],
                availability_text=raw_record["availability_text"],
                rating_text=raw_record["rating_text"],
                description=raw_record["description"],
                source_page=raw_record["source_page"],
                fetched_at=raw_record["fetched_at"],
            )
            valid_books.append(book.model_dump())
        except Exception as e:
            invalid_records.append({
                "record": raw_record,
                "reason": str(e),
            })

    os.makedirs("output", exist_ok=True)

    with open(os.path.join("output", "books.json"), "w", encoding="utf-8") as f:
        json.dump(valid_books, f, indent=2, ensure_ascii=False)

    with open(os.path.join("output", "errors.json"), "w", encoding="utf-8") as f:
        json.dump(invalid_records, f, indent=2, ensure_ascii=False)

    print(f"valid_records={len(valid_books)}")
    print(f"invalid_records={len(invalid_records)}")