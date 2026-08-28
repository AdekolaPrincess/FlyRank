import sqlite3
import json

conn = sqlite3.connect("report.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        price REAL,
        rating INTEGER,
        url TEXT
    )
""")

cursor.execute("DELETE FROM books") # Wipe existing rowsso re-running this script doesn't duplicate data

#Map word-ratings to numbers
rating_words = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5
}

json_path =  r"C:\Users\Princess\Documents\FlyRank Internship\BE-05\scraper\output\books.json"

with open(json_path, "r", encoding = "utf-8") as f:
    books = json.load(f)

for book in books:
    title = book["title"]
    price = book["price_gbp"]
    rating_word = book["rating_text"]
    rating = rating_words.get(rating_word, 0) # 0 if the word id not recognized
    url = book["product_url"]

    cursor.execute(
        "INSERT INTO books (title, price, rating, url) VALUES (?, ?, ?, ?)", (title, price, rating, url)
    )

conn.commit()
conn.close()
print(f"Inserted {len(books)} books.")