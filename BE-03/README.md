# BE-03 — Task API with SQLite

A CRUD (Create, Read, Update, Delete) API for managing a to-do list, built with FastAPI. This is the direct sequel to BE-02: the API's endpoints, request/response shapes, and status codes are unchanged — only the storage layer moved from an in-memory Python list to a real SQLite database, so data now survives a server restart.

## Why SQLite

SQLite was chosen because it needs no separate server to install or run — the entire database is a single file (`tasks.db`) that Python's built-in `sqlite3` module can open directly. For a small project like this, it gives real persistence (data survives restarts) with zero setup cost, which is exactly what this assignment needed to prove: swapping storage layers without touching the API.

## Where the database lives

`tasks.db` is created automatically the first time the app starts — it is **not** committed to git (it's listed in `.gitignore`), so every fresh clone of this repo starts with a clean database. On first run, the app creates the `tasks` table and seeds 3 example tasks, but only if the table is empty — restarting the app never duplicates them.

## How to run it

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload
```

Then visit `http://localhost:8000/docs` for interactive Swagger UI, or `http://localhost:8000/tasks` to see the seeded tasks.

## Endpoints

| Method | Path            | Description                          | Success | Errors |
|--------|-----------------|---------------------------------------|---------|--------|
| GET    | `/`             | API info                              | 200     | —      |
| GET    | `/health`       | Health check                          | 200     | —      |
| GET    | `/tasks`        | List tasks (`?done=`, `?search=`)     | 200     | —      |
| GET    | `/tasks/{id}`   | Get one task                          | 200     | 404    |
| POST   | `/tasks`        | Create a task                         | 201     | 400    |
| PUT    | `/tasks/{id}`   | Update a task                         | 200     | 400, 404 |
| DELETE | `/tasks/{id}`   | Delete a task                         | 204     | 404    |

## Proof the API didn't change

The same endpoints, same request/response shapes, and same status codes from BE-02 (in-memory) still work identically here — only the code *behind* each route changed, from reading/writing a Python list to running SQL queries against `tasks.db`. That identical behavior, before and after, is exactly what proves storage is just an implementation detail: clients calling this API never need to know or care whether their data sits in memory, in SQLite, or in a large production database.

## Exploring the database directly

Opened `tasks.db` in [DB Browser for SQLite](https://sqlitebrowser.org/) and ran SQL by hand in the "Execute SQL" tab:

```sql
UPDATE tasks SET done = 1;
```

This marked every task in the table as done. After clicking "Write Changes," calling `GET /tasks` through the running API immediately showed every task with `done: true` — with no server restart — proving the API and DB Browser read the exact same file as a single source of truth.

![Tasks table in DB Browser for SQLite](swagger-screenshot.png)

## Tech stack

- FastAPI
- Pydantic (request validation)
- Python's built-in `sqlite3` module (no ORM — raw SQL, parameterized queries throughout)
- Uvicorn (dev server)

## Safety note

All queries use parameterized placeholders (`?`) rather than inserting values directly into SQL strings, to avoid SQL injection — user-supplied values (like a task title or id) are always passed separately from the query text, never glued into it.