import sqlite3

def get_report_data():
    conn = sqlite3.connect("report.db")
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM books")
    total_books = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(price) FROM books")
    average_price = cursor.fetchone()[0]

    cursor.execute("SELECT title, price FROM books ORDER BY price DESC LIMIT 5")
    top_5_expensive = cursor.fetchall()

    cursor.execute("SELECT rating, COUNT(*) FROM books GROUP BY rating")
    books_per_rating = cursor.fetchall()

    cursor.execute("SELECT title, price, rating, url FROM books")
    all_books = cursor.fetchall()

    conn.close()

    return{
        "total_books": total_books,
        "average_price": round(average_price, 2),
        "top_5_expensive": top_5_expensive,
        "books_per_rating": books_per_rating,
        "all_books": all_books
    }