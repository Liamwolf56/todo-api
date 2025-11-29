import sqlite3
from typing import Optional, Dict, List, Any

# Define the database file name
DATABASE_NAME = "todo.db"

def get_db_connection() -> sqlite3.Connection:
    """
    Creates and returns a new SQLite database connection.
    Sets row_factory to sqlite3.Row for dictionary-like access.
    """
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_task_by_id(db: sqlite3.Connection, task_id: int, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a single task by ID and user_id."""
    cursor = db.execute(
        "SELECT id, user_id, title, description, is_done FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    task = cursor.fetchone()
    return dict(task) if task else None

def get_all_tasks(db: sqlite3.Connection, user_id: str, is_done: Optional[bool] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves all tasks for a user, with optional filtering and search."""
    query = "SELECT id, user_id, title, description, is_done FROM tasks WHERE user_id = ?"
    params: List[Any] = [user_id]
    
    # Filter by completion status
    if is_done is not None:
        query += " AND is_done = ?"
        params.append(is_done)
        
    # Filter by search term in title or description
    if search:
        search_term = f"%{search}%"
        query += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([search_term, search_term])
        
    query += " ORDER BY id DESC"
    
    cursor = db.execute(query, tuple(params))
    return [dict(row) for row in cursor.fetchall()]

def create_task(db: sqlite3.Connection, user_id: str, title: str, description: Optional[str]) -> int:
    """Creates a new task and returns its ID."""
    cursor = db.execute(
        "INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
        (user_id, title, description)
    )
    db.commit()
    return cursor.lastrowid # type: ignore

def update_task(db: sqlite3.Connection, task_id: int, user_id: str, updates: Dict[str, Any]) -> bool:
    """Updates one or more fields of an existing task."""
    set_clauses = []
    params = []
    
    for key, value in updates.items():
        if key in ['title', 'description', 'is_done']:
            set_clauses.append(f"{key} = ?")
            params.append(value)
            
    if not set_clauses:
        return False
        
    query = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ? AND user_id = ?"
    params.extend([task_id, user_id])
    
    cursor = db.execute(query, tuple(params))
    db.commit()
    return cursor.rowcount > 0

def delete_task(db: sqlite3.Connection, task_id: int, user_id: str) -> bool:
    """Deletes a task by ID and user_id."""
    cursor = db.execute(
        "DELETE FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id)
    )
    db.commit()
    return cursor.rowcount > 0

def delete_test_db():
    """Utility function for main.py cleanup during development."""
    import os
    if os.path.exists(DATABASE_NAME):
        os.remove(DATABASE_NAME)
        print(f"Removed database file: {DATABASE_NAME}")
