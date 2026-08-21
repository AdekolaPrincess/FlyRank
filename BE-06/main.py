import os
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
from enum import Enum
from dotenv import load_dotenv
from supabase import create_client, Client
from src.llm.triage import run_triage


security = HTTPBearer()
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
init_db()

class TaskCreate(BaseModel):
    title: str

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

class AuthCredentials(BaseModel):
    email: str
    password: str

class TriageInput(BaseModel):
    text: str = Field(..., min_length = 1, max_length = 2000)

class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    account = "account"
    shipping = "shipping"
    enquiring = "enquiry"
    other = "other"

class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"

class Team(str, Enum):
    billing_team = "billing_team"
    tech_team = "tech_team"
    account_team = "account_team"
    shipping_team = "shipping_team"
    support_team = "support_team"

class TriageOutput(BaseModel):
    category: Category
    urgency: Urgency
    suggested_team: Team
    confidence: float = Field(..., ge = 0.0, le = 1.0)
    reason: str

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Reusable guard: extracts and verifies the bearer token, returns the user."""
    token = credentials.credentials
    try:
        user_response = supabase.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code= 401, detail= "Invalid or expired token")
    return user_response.user

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    first_error = errors[0]
    field = first_error["loc"][-1]  
    return JSONResponse(
        status_code=400,
        content={"detail": f"Invalid or missing field: {field}"}
    )

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
def get_profile(user = Depends(get_current_user)):
    """Returns the logged-in user's profile protected by get_current_user."""
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at
    }

@app.get("/protected/dashboard", summary = "Protected route example")
def get_dashboard(user = Depends(get_current_user)):
    """Another protected route using the same middleware, no new auth code"""
    return {"message": f"Welcome to your dashboard, {user.email}!"}

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

@app.post("/auth/logout", status_code= 204, summary= "Log out the current user")
def logout(user = Depends(get_current_user)):
    """Ends the user's session and it requires a valid token"""
    supabase.auth.sign_out()
    return None

def load_prompt(filename: str) -> str:
    """Reads a prompt file from the prompts/ folder and returns its text."""
    with open(f"prompts/{filename}", "r", encoding="utf-8") as f:
        return f.read()

TRIAGE_PROMPT = load_prompt("triage-v1.md")

@app.post("/triage", summary="Classify a support message")
def triage_message(input: TriageInput) -> TriageOutput:
    """Takes a support message and returns a category, urgency, and suggested team."""
    if os.getenv("LLM_STUB") == "1":
        return TriageOutput(
            category=Category.other,
            urgency=Urgency.low,
            suggested_team=Team.support_team,
            confidence=0.42,
            reason="stub mode - no model call made"
        )

    # Real AI call
    raw_reply = run_triage(input.text)
    print("RAW MODEL REPLY:", raw_reply)  

   
    return TriageOutput(
        category=Category.other,
        urgency=Urgency.low,
        suggested_team=Team.support_team,
        confidence=0.0,
        reason="AI not wired yet"
    )
