# Task API

A simple CRUD API for managing a to-do list, built with FastAPI as part of the FlyRank Backend Internship (Week 2).

Tasks are stored in memory only, restarting the server resets the list back to the 3 example tasks. There is no database yet.

## How to run it

1. Clone this repo and navigate to this folder:
```
   cd BE-02/CRUD API
```
2. Create and activate a virtual environment:
```
   python -m venv venv
   venv\Scripts\activate
```
3. Install dependencies:
```
   pip install -r requirements.txt
```
4. Start the server:
```
   uvicorn main:app --reload
```
5. Visit `http://localhost:8000` in your browser, or `http://localhost:8000/docs` for the interactive Swagger UI.

## Endpoints

| Method | Path            | Description                          |
|--------|-----------------|---------------------------------------|
| GET    | `/`             | API info                              |
| GET    | `/health`       | Health check                          |
| GET    | `/tasks`        | List all tasks (supports `?done=` and `?search=` filters) |
| GET    | `/tasks/{id}`   | Get a single task by id               |
| POST   | `/tasks`        | Create a new task                     |
| PUT    | `/tasks/{id}`   | Update a task's title and/or done status |
| DELETE | `/tasks/{id}`   | Delete a task                         |

## Example request

## Example request

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/tasks/1" -Method GET
OR
curl -i http://localhost:8000/tasks/1
```

Response:
```
id title    done
-- -----    ----
 1 Buy milk False
```

## Swagger UI

![Swagger UI screenshot](swagger-screenshot.png)

## AI vs me

### My prompt

Hii, you are a backend engineer and i need you to buid a CRUD API
I need you to use python, therefore, using fastapi, and the endpoints i need you to use are:
GET	/	API info
GET	/health	Health check
GET	/tasks	List all tasks 
GET	/tasks/1	Get a single task by id 
POST	/tasks	Create a new task
PUT	/tasks/1	Update a task's title and/or done status 
DELETE	/tasks/1	Delete a task
for status code, use 200 for ok, 201 for created, 204 for no content, 400 for bad request and 404 for not found
Ensure that empty title is not accepted
The data should be stored in a memory, not database, like 3 tasks should be stored in the list, having keys of the id, title, and done which is a boolean and then finally. it should have swagger ui

### What the AI did better

It used FastAPI's `Field(...)` with `min_length=1` directly inside the Pydantic model to make a task's title required and enforce a minimum length, a cleaner, more declarative way to validate input than my manual `if not title.strip()` check, since it's enforced automatically before the function body even runs.

### What it got wrong or ignored

Nothing major, both versions correctly returned 200 for `/health` and `/tasks`. I initially thought the AI had used a different status code because its health check message said `"healthy"` instead of `"ok"`, but that turned out to just be different wording in the response body, not a different HTTP status code. A good reminder to check the actual status code rather than assume from a field's content.

### What my prompt forgot to specify

I never told it exactly which status code each specific endpoint should use, I only listed the four codes in general (200, 201, 400, 404), without saying "use 200 here, 201 there," etc. The AI figured out the correct mapping on its own anyway, matching what I'd built by hand.