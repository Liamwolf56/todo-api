from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from typing import List, Optional
import sqlite3
import uvicorn
import sys

# New Imports for Rate Limiting
from redis.asyncio import Redis
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

# Import models and database functions
import models
import database

# --- Dependency: Simulated Authentication ---
def get_current_user_id() -> str:
    """
    Simulates getting the ID of the currently authenticated user.
    """
    # Hardcoded user ID for demonstration
    return "user-A-123"

# --- Rate Limiter Key Function (FIXED to use User ID) ---
async def rate_limit_key_generator(request: Request) -> str:
    """
    FIXED: Uses the constant user ID as the key to guarantee the limit is hit,
    bypassing unreliable client IP detection in the testing environment.
    """
    # We use the hardcoded user ID used by the authentication dependency
    return "user-A-123"

# --- Lifespan Context Manager (Initialization for Rate Limiter) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events, including Redis and Rate Limiter setup."""

    # 1. Initialize Redis connection
    try:
        # !!! PORT CHANGED TO 6380 TO AVOID CONFLICT WITH SYSTEM REDIS SERVICE !!!
        redis_conn = Redis(host="localhost", port=6380, db=0)

        # 2. Initialize the Rate Limiter using the Redis connection
        await FastAPILimiter.init(
            redis_conn,
            identifier=rate_limit_key_generator
        )
        print("FastAPILimiter initialized, connecting to Redis on localhost:6380.")

    except Exception as e:
        # This will be logged if Redis is not running or unreachable
        print(f"WARNING: Could not connect to Redis for Rate Limiter (port 6380). Rate limiting disabled. Error: {e}")

    print("Application started. Database connection ready (schema managed by Alembic).")

    yield

    print("Application shutting down.")

# Initialize the FastAPI application using the lifespan handler
app = FastAPI(
    title="WSL ToDo REST API (Rate Limited)",
    description="A ToDo list backend with FastAPI, SQLite/Alembic, and Rate Limiting via Redis.",
    version="4.0.0",
    lifespan=lifespan
)

# Dependency to get the database connection
def get_db():
    """Provides a fresh database connection and ensures it is closed after use."""
    conn = database.get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

# --- Custom Exception Handler ---

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """Custom handler for Pydantic validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Validation Error", "errors": exc.errors()},
    )

# --- CRUD Endpoints ---

# CREATE - RATE LIMITED
@app.post(
    "/tasks/",
    response_model=models.Task,
    status_code=status.HTTP_201_CREATED,
    tags=["Tasks"],
    # Apply rate limit: 5 requests every 10 seconds per user
    dependencies=[Depends(RateLimiter(times=5, seconds=10, identifier=rate_limit_key_generator))]
)
def create_new_task(
    task_data: models.TaskCreate,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db)
):
    """
    Creates a new task. This endpoint is limited to 5 requests every 10 seconds per user.
    """
    new_id = database.create_task(db, user_id, task_data.title, task_data.description)
    created_task = database.get_task_by_id(db, new_id, user_id)
    return models.Task(**created_task)

# READ All (with Filtering and Search)
@app.get("/tasks/", response_model=List[models.Task], tags=["Tasks"])
def read_all_tasks(
    is_done: Optional[bool] = Query(None, description="Filter tasks by completion status (true/false)"),
    search: Optional[str] = Query(None, description="Search term to filter by title or description (case-insensitive)"),
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db)
):
    """Retrieves a list of all tasks for the current user."""
    tasks = database.get_all_tasks(db, user_id, is_done, search)
    return tasks

# READ One
@app.get("/tasks/{task_id}", response_model=models.Task, tags=["Tasks"])
def read_single_task(
    task_id: int,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db)
):
    """Retrieves a single task by its ID, only if it belongs to the current user."""
    task = database.get_task_by_id(db, task_id, user_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found for user {user_id}")

    return models.Task(**task)

# UPDATE
@app.put("/tasks/{task_id}", response_model=models.Task, tags=["Tasks"])
def update_existing_task(
    task_id: int,
    task_data: models.TaskUpdate,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db)
):
    """Updates an existing task, only if it belongs to the current user."""
    updates = task_data.model_dump(exclude_none=True)

    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields provided for update.")

    success = database.update_task(db, task_id, user_id, updates)

    if not success:
        if database.get_task_by_id(db, task_id, user_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found for user {user_id}")

        updated_task = database.get_task_by_id(db, task_id, user_id)
        return models.Task(**updated_task)


    updated_task = database.get_task_by_id(db, task_id, user_id)
    return models.Task(**updated_task)

# DELETE
@app.delete("/tasks/{task_id}", response_model=models.DeleteResponse, tags=["Tasks"])
def delete_task_by_id(
    task_id: int,
    user_id: str = Depends(get_current_user_id),
    db: sqlite3.Connection = Depends(get_db)
):
    """Deletes a task by its ID, only if it belongs to the current user."""
    success = database.delete_task(db, task_id, user_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task with ID {task_id} not found for user {user_id}")

    return models.DeleteResponse(message=f"Task {task_id} deleted successfully.", task_id=task_id)

# Optional: Run the app directly from this file (useful for testing)
if __name__ == "__main__":
    # Command to run the Uvicorn server (host and port can be adjusted)
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
