from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import sqlite3
import sys
import asyncio
from datetime import date, datetime
from report_data import get_report_data
from render_report import build_html, render_pdf

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect("report.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_reports_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        path TEXT,
        created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_reports_table()

@app.get("/health")
def health():
    return{"status": "ok"}

@app.post("/reports", status_code = 201)
async def create_report():
    conn = get_db_connection()

    data = get_report_data()
    html = build_html(data)

    cursor = conn.execute("INSERT INTO reports (path, created_at) VALUES (?, ?)", ("", str(date.today())))
    report_id = cursor.lastrowid

    output_path =  f"reports/{report_id}.pdf"
    await render_pdf(html, output_path)

    conn.execute("UPDATE reports SET path = ? WHERE id = ?", (output_path, report_id))
    conn.commit()
    conn.close()

    return {"id": report_id, "file": f"/reports/{report_id}/file"}

@app.get("/reports/{report_id}")
def get_report(report_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code = 404, detail = "Report not found")
    return {"id": row["id"], "path": row["path"], "created_at": row["created_at"], "file": f"/reports/{row['id']}/file"}

@app.get("/reports/{report_id}/file")
def get_report_file(report_id: int):
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Report not found")

    return FileResponse(path=row["path"], media_type="application/pdf", filename=f"report-{report_id}.pdf")