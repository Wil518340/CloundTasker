import pytest
from unittest.mock import MagicMock#, patch
from fastapi.testclient import TestClient
from app.main import app, get_firestore
from app.firestore import FirestoreService, Task

client = TestClient(app)

@pytest.fixture
def mock_firestore():
    """Mock FirestoreService and override dependency."""
    mock = MagicMock(spec=FirestoreService)
    # Override the dependency with the mock
    app.dependency_overrides[get_firestore] = lambda: mock
    yield mock
    # Clean up after test
    app.dependency_overrides.clear()

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
    assert data["title"] == "Test Task"
    assert data["user_id"] == "user1"

def test_create_task_failure(mock_firestore):
    mock_firestore.create_task.side_effect = Exception("DB error")
    response = client.post("/tasks", json={"title": "Test"}, params={"user_id": "user1"})
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"

def test_list_tasks_success(mock_firestore):
    mock_firestore.list_tasks.return_value = [
        Task(id="1", user_id="user1", title="Task 1"),
        Task(id="2", user_id="user1", title="Task 2"),
    ]
    response = client.get("/tasks", params={"user_id": "user1"})
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_get_task_found(mock_firestore):
    task = Task(id="1", user_id="user1", title="Task")
    mock_firestore.get_task.return_value = task
    response = client.get("/tasks/1", params={"user_id": "user1"})
    assert response.status_code == 200
    assert response.json()["id"] == "1"

def test_get_task_not_found(mock_firestore):
    mock_firestore.get_task.return_value = None
    response = client.get("/tasks/999", params={"user_id": "user1"})
    assert response.status_code == 404

def test_toggle_task_success(mock_firestore):
    original_task = Task(id="1", user_id="user1", title="Task", completed=False)
    updated_task = Task(id="1", user_id="user1", title="Task", completed=True)
    mock_firestore.get_task.return_value = original_task
    mock_firestore.update_task.return_value = updated_task
    response = client.put("/tasks/1/toggle", params={"user_id": "user1"})
    assert response.status_code == 200
    assert response.json()["completed"] is True

def test_toggle_task_not_found(mock_firestore):
    mock_firestore.get_task.return_value = None
    response = client.put("/tasks/1/toggle", params={"user_id": "user1"})
    assert response.status_code == 404

def test_delete_task_success(mock_firestore):
    mock_firestore.delete_task.return_value = True
    response = client.delete("/tasks/1", params={"user_id": "user1"})
    assert response.status_code == 204
    assert response.content == b""

def test_delete_task_not_found(mock_firestore):
    mock_firestore.delete_task.return_value = False
    response = client.delete("/tasks/1", params={"user_id": "user1"})
    assert response.status_code == 404

def test_health_success(mock_firestore):
    mock_firestore.list_tasks.return_value = []
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_health_failure(mock_firestore):
    mock_firestore.list_tasks.side_effect = Exception("Firestore down")
    response = client.get("/health")
    assert response.status_code == 503