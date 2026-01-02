import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, TodoDB
import json

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_todos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def cleanup():
    """Clean up database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

class TestRootEndpoint:
    def test_root_endpoint(self):
        """Test the root endpoint returns API information"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert data["message"] == "Todo REST API"
        assert data["version"] == "1.0.0"

class TestCreateTodo:
    def test_create_todo_success(self):
        """Test creating a todo with valid data"""
        todo_data = {
            "title": "Test Todo",
            "description": "This is a test todo",
            "completed": False
        }
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "This is a test todo"
        assert data["completed"] == False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_todo_minimal(self):
        """Test creating a todo with minimal data"""
        todo_data = {"title": "Minimal Todo"}
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Minimal Todo"
        assert data["description"] is None
        assert data["completed"] == False

    def test_create_todo_empty_title(self):
        """Test validation rejects empty title"""
        todo_data = {"title": "", "description": "Test"}
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_whitespace_title(self):
        """Test validation rejects whitespace-only title"""
        todo_data = {"title": "   ", "description": "Test"}
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_missing_title(self):
        """Test validation rejects missing title"""
        todo_data = {"description": "Test"}
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_title_too_long(self):
        """Test validation rejects title over 200 characters"""
        todo_data = {"title": "x" * 201}
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_description_too_long(self):
        """Test validation rejects description over 1000 characters"""
        todo_data = {"title": "Test", "description": "x" * 1001}
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 422

    def test_create_todo_strips_whitespace(self):
        """Test that title and description whitespace is stripped"""
        todo_data = {
            "title": "  Test Todo  ",
            "description": "  Test Description  "
        }
        response = client.post("/todos", json=todo_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Todo"
        assert data["description"] == "Test Description"

class TestGetTodos:
    def test_get_all_todos_empty(self):
        """Test getting todos when database is empty"""
        response = client.get("/todos")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_todos(self):
        """Test getting all todos"""
        # Create test todos
        client.post("/todos", json={"title": "Todo 1"})
        client.post("/todos", json={"title": "Todo 2"})
        client.post("/todos", json={"title": "Todo 3"})

        response = client.get("/todos")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Todo 1"
        assert data[1]["title"] == "Todo 2"
        assert data[2]["title"] == "Todo 3"

    def test_get_todos_with_pagination(self):
        """Test pagination parameters"""
        # Create 5 todos
        for i in range(5):
            client.post("/todos", json={"title": f"Todo {i+1}"})

        # Test skip
        response = client.get("/todos?skip=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["title"] == "Todo 3"

        # Test limit
        response = client.get("/todos?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        # Test skip and limit
        response = client.get("/todos?skip=1&limit=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["title"] == "Todo 2"
        assert data[1]["title"] == "Todo 3"

    def test_get_todos_filter_completed(self):
        """Test filtering by completion status"""
        # Create mixed todos
        client.post("/todos", json={"title": "Todo 1", "completed": False})
        client.post("/todos", json={"title": "Todo 2", "completed": True})
        client.post("/todos", json={"title": "Todo 3", "completed": False})
        client.post("/todos", json={"title": "Todo 4", "completed": True})

        # Get only completed
        response = client.get("/todos?completed=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(todo["completed"] for todo in data)

        # Get only not completed
        response = client.get("/todos?completed=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(not todo["completed"] for todo in data)

class TestGetTodoById:
    def test_get_todo_by_id(self):
        """Test getting a specific todo by ID"""
        # Create a todo
        create_response = client.post("/todos", json={"title": "Test Todo"})
        todo_id = create_response.json()["id"]

        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == todo_id
        assert data["title"] == "Test Todo"

    def test_get_todo_not_found(self):
        """Test getting a non-existent todo"""
        response = client.get("/todos/999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

class TestUpdateTodo:
    def test_update_todo_all_fields(self):
        """Test updating all fields of a todo"""
        # Create a todo
        create_response = client.post("/todos", json={
            "title": "Original",
            "description": "Original desc",
            "completed": False
        })
        todo_id = create_response.json()["id"]

        # Update all fields
        update_data = {
            "title": "Updated",
            "description": "Updated desc",
            "completed": True
        }
        response = client.put(f"/todos/{todo_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "Updated desc"
        assert data["completed"] == True

    def test_update_todo_partial(self):
        """Test partial update of a todo"""
        # Create a todo
        create_response = client.post("/todos", json={
            "title": "Original",
            "description": "Original desc",
            "completed": False
        })
        todo_id = create_response.json()["id"]

        # Update only title
        response = client.put(f"/todos/{todo_id}", json={"title": "New Title"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "Original desc"
        assert data["completed"] == False

        # Update only completed
        response = client.put(f"/todos/{todo_id}", json={"completed": True})
        assert response.status_code == 200
        data = response.json()
        assert data["completed"] == True
        assert data["title"] == "New Title"

    def test_update_todo_empty_title(self):
        """Test validation rejects empty title on update"""
        create_response = client.post("/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]

        response = client.put(f"/todos/{todo_id}", json={"title": ""})
        assert response.status_code == 422

    def test_update_todo_whitespace_title(self):
        """Test validation rejects whitespace title on update"""
        create_response = client.post("/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]

        response = client.put(f"/todos/{todo_id}", json={"title": "   "})
        assert response.status_code == 422

    def test_update_todo_not_found(self):
        """Test updating a non-existent todo"""
        response = client.put("/todos/999", json={"title": "Test"})
        assert response.status_code == 404

    def test_update_todo_strips_whitespace(self):
        """Test that update strips whitespace"""
        create_response = client.post("/todos", json={"title": "Test"})
        todo_id = create_response.json()["id"]

        response = client.put(f"/todos/{todo_id}", json={
            "title": "  Updated  ",
            "description": "  Desc  "
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["description"] == "Desc"

    def test_update_todo_empty_body(self):
        """Test update with empty body keeps todo unchanged"""
        create_response = client.post("/todos", json={
            "title": "Original",
            "description": "Original desc"
        })
        todo_id = create_response.json()["id"]

        response = client.put(f"/todos/{todo_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Original"
        assert data["description"] == "Original desc"

class TestDeleteTodo:
    def test_delete_todo(self):
        """Test deleting a todo"""
        # Create a todo
        create_response = client.post("/todos", json={"title": "To Delete"})
        todo_id = create_response.json()["id"]

        # Delete it
        response = client.delete(f"/todos/{todo_id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/todos/{todo_id}")
        assert response.status_code == 404

    def test_delete_todo_not_found(self):
        """Test deleting a non-existent todo"""
        response = client.delete("/todos/999")
        assert response.status_code == 404

class TestEdgeCases:
    def test_invalid_json(self):
        """Test handling of invalid JSON"""
        response = client.post("/todos", data="not json")
        assert response.status_code == 422

    def test_wrong_type_fields(self):
        """Test validation of wrong field types"""
        response = client.post("/todos", json={
            "title": 123,  # Should be string
            "completed": "yes"  # Should be boolean
        })
        assert response.status_code == 422

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored"""
        response = client.post("/todos", json={
            "title": "Test",
            "extra_field": "ignored"
        })
        assert response.status_code == 201
        data = response.json()
        assert "extra_field" not in data

    def test_timestamps_behavior(self):
        """Test that timestamps are set correctly"""
        # Create todo
        create_response = client.post("/todos", json={"title": "Test"})
        data = create_response.json()
        todo_id = data["id"]
        created_at = data["created_at"]
        updated_at = data["updated_at"]

        # Initially, created_at and updated_at should be very close (within 1 second)
        from datetime import datetime
        created_dt = datetime.fromisoformat(created_at)
        updated_dt = datetime.fromisoformat(updated_at)
        assert abs((updated_dt - created_dt).total_seconds()) < 1

        # Update todo
        import time
        time.sleep(0.1)  # Small delay to ensure different timestamp
        update_response = client.put(f"/todos/{todo_id}", json={"title": "Updated"})
        updated_data = update_response.json()

        # created_at should remain the same, updated_at should change
        assert updated_data["created_at"] == created_at
        assert updated_data["updated_at"] != updated_at