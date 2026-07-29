from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3


tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Finish assignment", "done": True}
]

DB_FILE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done INTEGER NOT NULL DEFAULT 0
        )
""")

    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Buy milk", 0))
        conn.execute("INSERT INTO tasks (title, done) VALUES(?, ?)", ("Walk the dog", 0))
        conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", ("Finish assignment", 1))
    conn.commit()
    conn.close()

app = FastAPI()
init_db()

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

@app.get("/", summary = "API info")
def read_root():
    """Returns basic info about this API."""
    return {"name": "Task API",
            "version": "1.0",
            "endpoints": ["/tasks"]
             }

@app.get("/health", summary = "Health check")
def health_check():
    """Simple check to confirm the server is alive."""
    return {"status": "ok"}

@app.get("/tasks", summary = "List all tasks")
def get_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    """Returns tasks, optionally filtered by done status and/or a search term in the title."""
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    result = [dict(row) for row in rows]
    if done is not None:
        result = [task for task in result if bool(task["done"]) == done]
    if search is not None:
        result = [task for task in result if search.lower() in task["title"].lower()]
    return result

@app.get("/tasks/{task_id}", summary = "Get a single task")
def get_task(task_id: int):
    """Returns one task by id, or 404 if it doesn't exist."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code = 404, detail = f"Task {task_id} not found")
    return dict(row)

@app.post("/tasks", status_code = 201, summary = "Create a task")
def create_task(new_task: TaskCreate):
    """Creates a new task with the given title. Title cannot be empty."""
    if not new_task.title.strip():
        raise HTTPException(status_code = 400, detail = "Title cannot be empty")
    next_id = max((task["id"] for task in tasks), default = 0) + 1
    task = {"id": next_id, "title": new_task.title, "done": False}
    tasks.append(task)
    return task

@app.put("/tasks/{task_id}", summary = "Update a task")
def update_task(task_id: int, updates: TaskUpdate):
    """Updates a task's title and/or done status. Either field is optional."""
    for task in tasks:
        if task["id"] == task_id:
            if updates.title is not None:
                if not updates.title.strip():
                    raise HTTPException(status_code = 400, detail = "Title cannot be empty")
                task["title"] = updates.title
            if updates.done is not None:
                task["done"] = updates.done
            return task
    raise HTTPException(status_code = 404, detail = f"Task {task_id} not found")

@app.delete("/tasks/{task_id}", status_code = 204, summary = "Delete a task")
def delete_task(task_id: int):
    """Deletes a task by id. Returns no content on success"""
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return
    raise HTTPException(status_code = 404, detail = f"Task {task_id} not found")
