Modular ToDo REST API (Rate Limited)

This project is a modern, modular ToDo list backend built with FastAPI and uses SQLite for persistence and Redis for robust Rate Limiting.

The application is structured into three main files: main.py (API endpoints), models.py (Pydantic schemas), and database.py (SQLite operations).

Key Features

FastAPI: Asynchronous performance and automatic interactive API documentation (Swagger UI).

Modular Design: Separation of concerns between API routes, data models, and database logic.

Rate Limiting: Protects the /tasks/ creation endpoint, allowing a maximum of 5 requests every 10 seconds per user via fastapi-limiter and Redis.

Authentication Simulation: Uses a simple dependency (get_current_user_id) for user-specific data isolation.

Full CRUD: Endpoints for creating, reading (single and list with filtering/search), updating, and deleting tasks.

Setup and Installation

Prerequisites

You must have Python installed and a running Redis server instance.

Python: Ensure Python 3.8+ is installed.

Redis: The application is configured to connect to Redis on the non-default port 6380 to avoid conflicts. You must start your Redis server listening on this port.

1. Create and Activate Virtual Environment

python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
# .\venv\Scripts\activate.ps1  # On Windows PowerShell


2. Install Dependencies

This project requires FastAPI, Uvicorn, Pydantic, and the Redis-related packages for rate limiting.

pip install fastapi uvicorn pydantic "pydantic[email]" fastapi-limiter redis-py-cluster python-multipart


Running the Application

1. Start Redis Server

Ensure your Redis server is running and accessible on port 6380.

2. Run the API Server

The application will automatically initialize the todo_app.db SQLite file and the tasks table upon first run.

uvicorn main:app --reload --host 0.0.0.0 --port 8000


You should see output similar to this, including the Redis connection log:

FastAPILimiter initialized, connecting to Redis on localhost:6380.
Application started. Database connection ready (schema managed by Alembic).
Uvicorn running on [http://0.0.0.0:8000](http://0.0.0.0:8000) (Press CTRL+C to quit)


API Documentation and Testing

Once the server is running, you can access the interactive API documentation (Swagger UI) in your browser:

Swagger UI: http://localhost:8000/docs

Redoc: http://localhost:8000/redoc

You can use the Swagger UI to test all the endpoints, including triggering the rate limit on the POST /tasks/ endpoint.
