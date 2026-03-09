import logging
from typing import List
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.firestore import FirestoreService, Task
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CloudTasker API",
    description="A simple task manager using Firestore",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_firestore() -> FirestoreService:
    return FirestoreService()

class TaskCreate(BaseModel):
    title: str

@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate,
    user_id: str,
    firestore: FirestoreService = Depends(get_firestore)
):
    """Create a new task."""
    try:
        return firestore.create_task(user_id, task.title)
    except Exception as e:
        logger.exception("Create task failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tasks", response_model=List[Task])
async def list_tasks(
    user_id: str,
    firestore: FirestoreService = Depends(get_firestore)
):
    """List all tasks for a user."""
    try:
        return firestore.list_tasks(user_id)
    except Exception as e:
        logger.exception("List tasks failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/tasks/{task_id}", response_model=Task)
async def get_task(
    task_id: str,
    user_id: str,
    firestore: FirestoreService = Depends(get_firestore)
):
    """Get a specific task."""
    try:
        task = firestore.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get task failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.put("/tasks/{task_id}/toggle", response_model=Task)
async def toggle_task_completion(
    task_id: str,
    user_id: str,
    firestore: FirestoreService = Depends(get_firestore)
):
    """Toggle the completion status of a task."""
    try:
        # First get current task
        task = firestore.get_task(user_id, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        # Update with opposite completion
        updated = firestore.update_task(user_id, task_id, not task.completed)
        if not updated:
            raise HTTPException(status_code=404, detail="Task not found after update")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Toggle task failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    user_id: str,
    firestore: FirestoreService = Depends(get_firestore)
):
    """Delete a task."""
    try:
        deleted = firestore.delete_task(user_id, task_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found")
        return None  # 204 No Content
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Delete task failed")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
async def health(firestore: FirestoreService = Depends(get_firestore)):
    """Health check endpoint."""
    try:
        # Try to list first task to verify Firestore connectivity
        list(firestore.list_tasks("health-check-user"))
        return {"status": "healthy", "firestore": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")