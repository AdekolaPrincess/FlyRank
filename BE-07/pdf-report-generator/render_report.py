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
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #2d2d2d;
                margin: 0;
                padding: 0;
            }}
            h1 {{
                color: #6c3ce9;
                font-size: 26px;
                margin-bottom: 4px;
            }}
            h1 + p {{
                color: #888;
                margin-top: 0;
                margin-bottom: 24px;
            }}
            h2 {{
                color: #2d2d2d;
                font-size: 18px;
                border-bottom: 3px solid #6c3ce9;
                display: inline-block;
                padding-bottom: 4px;
                margin-top: 30px;
            }}
            .stats {{
                display: flex;
                gap: 16px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                flex: 1;
                background: #f4f0fd;
                border-left: 5px solid #6c3ce9;
                border-radius: 6px;
                padding: 14px 18px;
            }}
            .stat-card .label {{
                font-size: 13px;
                color: #666;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .stat-card .value {{
                font-size: 24px;
                font-weight: bold;
                color: #6c3ce9;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 20px;
            }}
            th {{
                background: #6c3ce9;
                color: white;
                text-align: left;
                padding: 8px 10px;
                font-size: 13px;
            }}
            td {{
                padding: 7px 10px;
                font-size: 13px;
                border-bottom: 1px solid #eee;
            }}
            tbody tr:nth-child(even) {{
                background: #f7f5fc;
            }}
            tr {{ break-inside: avoid; }}
        </style>
    </head>
        <body>
        <h1>Book Report</h1>
        <p>{today}</p>

        <div class="stats">
            <div class="stat-card">
                <div class="label">Total Books</div>
                <div class="value">{data['total_books']}</div>
            </div>
            <div class="stat-card">
                <div class="label">Average Price</div>
                <div class="value">£{data['average_price']}</div>
            </div>
        </div>

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

async def render_pdf(html, output_path):
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