from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

tasks = [
    {"id": 1, "title": "Buy milk", "done": False},
    {"id": 2, "title": "Walk the dog", "done": False},
    {"id": 3, "title": "Finish assignment", "done": True}
]

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
    result = tasks
    if done is not None:
        result = [task for task in result if task["done"] == done]
    if search is not None:
        result = [task for task in result if search.lower() in task["title"].lower()]
    return result

@app.get("/tasks/{task_id}", summary = "Get a single task")
def get_task(task_id: int):
    """Returns one task by id, or 404 if it doesn't exist."""
    for task in tasks:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code = 404, detail = f"Task {task_id} not found")

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
