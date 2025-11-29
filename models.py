from pydantic import BaseModel, Field
from typing import Optional

# --- Schema for Database Interaction ---

class TaskBase(BaseModel):
    """Base model containing fields common to all Task representations."""
    title: str = Field(..., max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

class TaskCreate(TaskBase):
    """Model used when creating a new task (POST request body)."""
    pass

class TaskUpdate(BaseModel):
    """Model used when updating an existing task (PUT/PATCH request body)."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    is_done: Optional[bool] = None

# --- Schema for API Response ---

class Task(TaskBase):
    """Model for the data returned in responses."""
    id: int
    user_id: str
    is_done: bool = False

    class Config:
        """Pydantic configuration for mapping database rows."""
        from_attributes = True

class DeleteResponse(BaseModel):
    """Simple response schema for a successful deletion."""
    message: str
    task_id: int
