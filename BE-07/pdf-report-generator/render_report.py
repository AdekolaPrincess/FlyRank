from datetime import date
from report_data import get_report_data
import asyncio
from playwright.async_api import async_playwright


def build_html(data):
    today = date.today().strftime("%B %d, %Y")

    top_5_rows = ""
    for title, price in data["top_5_expensive"]:
        top_5_rows += f"<tr><td>{title}</td><td>£{price}</td></tr>"

    rating_rows = ""
    for rating, count in data["books_per_rating"]:
        rating_rows += f"<tr><td>{rating} stars</td><td>{count} books</td></tr>"

    all_books_rows = ""
    for title, price, rating, url in data["all_books"]:
        all_books_rows += f"<tr><td>{title}</td><td>£{price}</td><td>{rating}</td></tr>"

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; }}
            th, td {{ border: 1px solid #ccc; padding: 6px 10px; text-align: left; }}
        </style>
    </head>
    <body>
        <h1>Book Report : {today}</h1>
        <p><strong>Total books:</strong> {data['total_books']}</p>
        <p><strong>Average price:</strong> £{data['average_price']}</p>

        <h2>Top 5 Most Expensive Books</h2>
        <table>
            <thead><tr><th>Title</th><th>Price</th></tr></thead>
            <tbody>{top_5_rows}</tbody>
        </table>

        <h2>Books Per Rating</h2>
        <table>
            <thead><tr><th>Rating</th><th>Count</th></tr></thead>
            <tbody>{rating_rows}</tbody>
        </table>

        <h2>All Books</h2>
        <table>
            <thead><tr><th>Title</th><th>Price</th><th>Rating</th></tr></thead>
            <tbody>{all_books_rows}</tbody>
        </table>
    </body>
    </html>
    """
    return html

async def render_pdf(htm, output_path):
    async with async_playwright() as p:
        browser =  await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        await page.pdf(path=output_path, 
                       format="A4", 
                       print_background=True,
                       margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}
        )
        await browser.close()

if __name__ == "__main__":
    data = get_report_data()
    html = build_html(data)
    asyncio.run(render_pdf(html, "reports/test.pdf"))
    print("PDF saved to reports/test.pdf")