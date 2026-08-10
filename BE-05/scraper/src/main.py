import requests
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/AdekolaPrincess/FlyRank)"
TIMEOUT_SECONDS = 10

def fetch_page(url, cache_path):
    if os.path.exists(cache_path):
        print(f"CACHE HIT: {cache_path}")
        with open(cache_path, "r", encoding = "utf-8") as f:
            return f.read()

    print(f"FETCH: {url}")
    headers = {"User-Agent": USER_AGENT}
    response = requests.get(url, headers = headers, timeout = TIMEOUT_SECONDS)
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
        book_links.append(absolute_url)
    return book_links

def find_next_page_url(html, page_url):
    soup = BeautifulSoup(html, "html.parser")
    next_link = soup.select_one("li.next a")
    if next_link is None:
        return None
    href = next_link["href"]
    return urljoin(page_url, href)

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

    unique_links = list(set(all_links))

    print(f"catalogue_pages={page_number - 1}")
    print(f"discovered={len(all_links)}")
    print(f"unique_urls={len(unique_links)}")