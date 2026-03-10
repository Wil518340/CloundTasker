import logging
from datetime import datetime
from typing import List, Optional
from google.cloud import firestore
#from google.cloud.firestore import ArrayRemove, ArrayUnion
from pydantic import BaseModel
from app.config import settings

logger = logging.getLogger(__name__)

class Task(BaseModel):
    id: str
    user_id: str
    title: str
    completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_firestore(cls, data: dict) -> "Task":
        # Convert Firestore timestamp to datetime if present
        if "created_at" in data and hasattr(data["created_at"], "timestamp"):
            data["created_at"] = data["created_at"].datetime
        if "updated_at" in data and hasattr(data["updated_at"], "timestamp"):
            data["updated_at"] = data["updated_at"].datetime
        return cls(**data)

class FirestoreService:
    def __init__(self):
        self.client = firestore.Client(project=settings.gcp_project_id)
        self.collection = self.client.collection("tasks")

    def create_task(self, user_id: str, title: str) -> Task:
        """Create a new task and return it with server timestamps."""
        try:
            doc_ref = self.collection.document()
            task_id = doc_ref.id
            task_data = {
                "id": task_id,
                "user_id": user_id,
                "title": title,
                "completed": False,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
            doc_ref.set(task_data)
            # Read back to get actual timestamps
            new_doc = doc_ref.get()
            if not new_doc.exists:
                raise RuntimeError("Task creation failed")
            return Task.from_firestore(new_doc.to_dict())
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise

    def list_tasks(self, user_id: str) -> List[Task]:
        """Return all tasks for a user."""
        try:
            docs = self.collection.where("user_id", "==", user_id).stream()
            return [Task.from_firestore(doc.to_dict()) for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            raise

    def get_task(self, user_id: str, task_id: str) -> Optional[Task]:
        """Retrieve a task by ID if it belongs to the user."""
        try:
            doc = self.collection.document(task_id).get()
            if doc.exists:
                data = doc.to_dict()
                if data.get("user_id") == user_id:
                    return Task.from_firestore(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise

    def update_task(self, user_id: str, task_id: str, completed: bool) -> Optional[Task]:
        """Update task completion status and return updated task or None if not found."""
        try:
            doc_ref = self.collection.document(task_id)
            doc = doc_ref.get()
            if not doc.exists or doc.to_dict().get("user_id") != user_id:
                return None
            doc_ref.update({
                "completed": completed,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            # Return updated task
            updated_doc = doc_ref.get()
            return Task.from_firestore(updated_doc.to_dict())
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise

    def delete_task(self, user_id: str, task_id: str) -> bool:
        """Delete a task if it belongs to the user."""
        try:
            doc_ref = self.collection.document(task_id)
            doc = doc_ref.get()
            if not doc.exists or doc.to_dict().get("user_id") != user_id:
                return False
            doc_ref.delete()
            return True
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise