import os
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
import sqlite3
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL =  os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

class AuthCredentials(BaseModel):
    email: str
    password: str

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

@app.get("/public/info", summary = "Public info")
def public_info():
    """Open to everyone, no login required"""
    return {"message": "Welcome stranger! This info is piblic."}

@app.post("/auth/signup", status_code = 201, summary = "Create a new user account")
def signup(credentials: AuthCredentials):
    """Registers a new user with Supabase Auth"""
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(status_code = 400, detail = "Email and password are required")
    try:
        result = supabase.auth.sign_up({
            "email": credentials.email,
            "password": credentials.password
        })
    except Exception as e:
        raise HTTPException(status_code = 400, detail = str(e))
    return {"user": result.user}

@app.post("/auth/login", summary = "Log in and receive JWT")
def login(credentials: AuthCredentials):
    """Authenticates a user with Supabase Auth and return access + refresh tokens."""
    if not credentials.email.strip() or not credentials.password.strip():
        raise HTTPException(status_code = 400, detail = "Email and password are required")
    try:
        result = supabase.auth.sign_in_with_password({
            "email" : credentials.email,
            "password" : credentials.password
        })
    except Exception as e:
        raise HTTPException( status_code= 401, detail = "Invalid login credentials")
    return{
        "access_token": result.session.access_token,
        "refresh_token" : result.session.refresh_token
    }

@app.get("/protected/profile", summary = "Get logged-in user's profile")
def get_profile(request: Request):
    """Requires a bearer token to be present (not verified)."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code= 401, detail = "Access token required")
    token = auth_header.split(" ")[1]
    return {"message": "Token received (not yet verified)", "token_preview": token[:10]}

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
    conn = get_db_connection()
    cursor = conn.execute("INSERT INTO tasks (title, done) VALUES (?, ?)", (new_task.title, 0))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "title": new_task.title, "done": False}

@app.put("/tasks/{task_id}", summary = "Update a task")
def update_task(task_id: int, updates: TaskUpdate):
    """Updates a task's title and/or done status. Either field is optional."""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail = f" Task {task_id} not found")
    new_title = row["title"]
    new_done = row["done"]

    if updates.title is not None:
        if not updates.title.strip():
            conn.close()
            raise HTTPException(status_code= 400, detail= "Title cannot be empty")
        new_title = updates.title
    if updates.done is not None:
        new_done = int(updates.done)
    conn.execute("UPDATE tasks SET title = ?, done = ? WHERE id = ?", (new_title, new_done, task_id))
    conn.commit()
    conn.close()
    return{"id": task_id, "title": new_title, "done": bool(new_done)}

@app.delete("/tasks/{task_id}", status_code = 204, summary = "Delete a task")
def delete_task(task_id: int):
    """Deletes a task by id. Returns no content on success"""
    conn = get_db_connection()
    row = conn.execute("SELECT * FROM tasks where id = ?", (task_id,)).fetchone()

    if row is None:
        conn.close()
        raise HTTPException(status_code= 404, detail = f"Task {task_id} not found")
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()