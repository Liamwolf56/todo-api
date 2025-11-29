import pytest
import httpx
from fastapi.testclient import TestClient
import os
import sys

# Add the current directory to the path to import main and database
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from main import app, get_current_user_id # Import the app and the dependency
import database

# Use a specific, temporary file name for the test database
TEST_DATABASE_FILE = "test_isolated_todo.db"
database.DATABASE_FILE = TEST_DATABASE_FILE

# Define test user IDs
USER_A = "test-user-A-123"
USER_B = "test-user-B-456"

# Override the main dependency to use a specific user ID for testing
def override_get_current_user_A():
    return USER_A

def override_get_current_user_B():
    return USER_B

# Apply the override only for tests that need User A's context
client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_teardown_db():
    """
    1. Sets up the test database before the tests run.
    2. Deletes the test database after the tests run.
    """
    print(f"\n--- Setting up isolated test database: {TEST_DATABASE_FILE} ---")
    conn = database.get_db_connection()
    database.create_tasks_table(conn)
    conn.close()
    
    yield
    
    print(f"\n--- Tearing down test database: {TEST_DATABASE_FILE} ---")
    database.delete_test_db(TEST_DATABASE_FILE)


# --- 1. Isolation Tests (CRUD for User A) ---

def test_01_create_task_user_A():
    """Create a task as User A."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    response = client.post(
        "/tasks/",
        json={"title": "A's Task 1: Unfinished", "description": "Need to finish this for user A"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == USER_A
    pytest.task_id_A = data["id"]
    
def test_02_read_task_user_A():
    """Read A's task as User A."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    response = client.get(f"/tasks/{pytest.task_id_A}")
    assert response.status_code == 200
    assert response.json()["user_id"] == USER_A

def test_03_create_task_user_B():
    """Create a separate task as User B."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_B
    response = client.post(
        "/tasks/",
        json={"title": "B's Task 1: For Isolation Check", "description": "This task should be invisible to A"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == USER_B
    pytest.task_id_B = data["id"] # Store B's ID

def test_04_isolation_read_A_as_B_fails():
    """Verify isolation: User B tries to read User A's task."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_B
    response = client.get(f"/tasks/{pytest.task_id_A}")
    assert response.status_code == 404 # Should fail because it doesn't belong to B

def test_05_isolation_update_A_as_B_fails():
    """Verify isolation: User B tries to update User A's task."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_B
    response = client.put(f"/tasks/{pytest.task_id_A}", json={"is_done": True})
    assert response.status_code == 404 # Should fail

# --- 2. Filtering Tests (for User A) ---

def test_06_create_second_task_user_A_and_mark_done():
    """Create a second task for User A and mark it as done."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    
    # Create the task
    response_create = client.post(
        "/tasks/",
        json={"title": "A's Task 2: Finished"}
    )
    assert response_create.status_code == 201
    pytest.task_id_A_done = response_create.json()["id"]

    # Mark as done
    response_update = client.put(
        f"/tasks/{pytest.task_id_A_done}", 
        json={"is_done": True}
    )
    assert response_update.status_code == 200
    assert response_update.json()["is_done"] == True


def test_07_read_all_tasks_no_filter():
    """Read all tasks for User A (should be 2 tasks)."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    response = client.get("/tasks/")
    assert response.status_code == 200
    data = response.json()
    # User A has 2 tasks (A's Task 1 and A's Task 2). User B's task is filtered out.
    assert len(data) == 2 
    assert all(task["user_id"] == USER_A for task in data)


def test_08_read_filtered_tasks_done():
    """Filter tasks by is_done=true for User A (should be 1 task)."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    response = client.get("/tasks/?is_done=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "A's Task 2: Finished"
    assert data[0]["is_done"] == True
    
def test_09_read_filtered_tasks_not_done():
    """Filter tasks by is_done=false for User A (should be 1 task)."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    response = client.get("/tasks/?is_done=false")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "A's Task 1: Unfinished"
    assert data[0]["is_done"] == False


# --- 3. Final Deletion ---

def test_10_delete_user_A_task():
    """Delete one of User A's tasks."""
    app.dependency_overrides[get_current_user_id] = override_get_current_user_A
    response = client.delete(f"/tasks/{pytest.task_id_A}")
    assert response.status_code == 200
    
def test_11_cleanup_overrides():
    """Ensure the dependency override is removed after tests."""
    app.dependency_overrides.clear()
