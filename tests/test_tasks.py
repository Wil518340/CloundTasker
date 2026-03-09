import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import app, get_firestore
from app.firestore import Task, FirestoreService

client = TestClient(app)

@pytest.fixture
def mock_firestore():
    """Mock FirestoreService and override FastAPI dependency."""
    mock = MagicMock(spec=FirestoreService)
    # Override dependency
    app.dependency_overrides[get_firestore] = lambda: mock
    yield mock
    app.dependency_overrides.clear()  # cleanup after test

def test_create_task_success(mock_firestore):
    mock_firestore.create_task.return_value = Task(
        id="123",
        user_id="user1",
        title="Test Task",
        completed=False,
        created_at=None,
        updated_at=None
    )
    response = client.post("/tasks", json={"title": "Test Task"}, params={"user_id": "user1"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "123"
    assert data["title"] == "Test Task"
    assert data["user_id"] == "user1"

def test_create_task_failure(mock_firestore):
    mock_firestore.create_task.side_effect = Exception("DB error")
    response = client.post("/tasks", json={"title": "Test Task"}, params={"user_id": "user1"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

def test_list_tasks_success(mock_firestore):
    mock_firestore.list_tasks.return_value = [
        Task(id="1", user_id="user1", title="Task 1"),
        Task(id="2", user_id="user1", title="Task 2"),
    ]
    response = client.get("/tasks", params={"user_id": "user1"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "1"

def test_get_task_found(mock_firestore):
    mock_firestore.get_task.return_value = Task(id="1", user_id="user1", title="Task")
    response = client.get("/tasks/1", params={"user_id": "user1"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "1"
    assert data["title"] == "Task"

def test_get_task_not_found(mock_firestore):
    mock_firestore.get_task.return_value = None
    response = client.get("/tasks/999", params={"user_id": "user1"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_toggle_task_success(mock_firestore):
    # Original task
    original_task = Task(id="1", user_id="user1", title="Task", completed=False)
    updated_task = Task(id="1", user_id="user1", title="Task", completed=True)
    mock_firestore.get_task.return_value = original_task
    mock_firestore.update_task.return_value = updated_task

    response = client.put("/tasks/1/toggle", params={"user_id": "user1"})
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True

def test_toggle_task_not_found(mock_firestore):
    mock_firestore.get_task.return_value = None
    response = client.put("/tasks/1/toggle", params={"user_id": "user1"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_delete_task_success(mock_firestore):
    mock_firestore.delete_task.return_value = True
    response = client.delete("/tasks/1", params={"user_id": "user1"})
    assert response.status_code == 204
    assert response.content == b""

def test_delete_task_not_found(mock_firestore):
    mock_firestore.delete_task.return_value = False
    response = client.delete("/tasks/1", params={"user_id": "user1"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"

def test_health_success(mock_firestore):
    mock_firestore.list_tasks.return_value = []
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["firestore"] == "connected"

def test_health_failure(mock_firestore):
    mock_firestore.list_tasks.side_effect = Exception("Firestore down")
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json()["detail"] == "Service unavailable"