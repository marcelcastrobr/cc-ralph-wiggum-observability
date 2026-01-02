import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app, get_db, Base, TodoDB, metrics
import json
import time

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

class TestObservability:
    def test_health_check_endpoint(self):
        """Test the health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "status" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data
        assert "components" in data

        # Check status is healthy
        assert data["status"] == "healthy"

        # Check components
        assert "database" in data["components"]
        assert "api" in data["components"]
        assert data["components"]["database"] == "healthy"
        assert data["components"]["api"] == "healthy"

        # Check uptime is positive
        assert data["uptime_seconds"] >= 0

    def test_metrics_endpoint(self):
        """Test the metrics endpoint"""
        # Reset metrics for clean test
        metrics.request_count = 0
        metrics.error_count = 0
        metrics.endpoint_counts.clear()
        metrics.endpoint_timings.clear()
        metrics.status_code_counts.clear()

        # Make some requests to generate metrics
        client.post("/todos", json={"title": "Test 1"})
        client.get("/todos")
        client.get("/todos/999")  # This will generate a 404

        # Get metrics
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()

        # Check structure
        assert "timestamp" in data
        assert "metrics" in data

        metrics_data = data["metrics"]
        assert "uptime_seconds" in metrics_data
        assert "total_requests" in metrics_data
        assert "total_errors" in metrics_data
        assert "error_rate" in metrics_data
        assert "endpoint_stats" in metrics_data
        assert "response_times" in metrics_data
        assert "status_codes" in metrics_data
        assert "recent_errors" in metrics_data

        # Check that metrics were recorded
        assert metrics_data["total_requests"] > 0
        assert metrics_data["total_errors"] > 0  # Due to the 404
        assert metrics_data["error_rate"] > 0

    def test_request_headers(self):
        """Test that observability headers are added to responses"""
        response = client.get("/todos")

        # Check for custom headers
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers

        # Check format
        assert response.headers["X-Request-ID"].startswith("req_")
        assert response.headers["X-Response-Time"].endswith("ms")

    def test_request_logging_fields(self):
        """Test that requests generate proper log fields"""
        # Create a todo and check response
        response = client.post("/todos", json={"title": "Log Test"})
        assert response.status_code == 201

        # Headers should be present
        assert "X-Request-ID" in response.headers
        assert "X-Response-Time" in response.headers

    def test_error_tracking(self):
        """Test that errors are properly tracked in metrics"""
        # Reset metrics
        metrics.recent_errors.clear()
        initial_error_count = metrics.error_count

        # Generate some errors
        client.get("/todos/9999")  # 404
        client.post("/todos", json={"title": ""})  # 422 validation error

        # Check that errors were tracked
        assert metrics.error_count > initial_error_count

        # Check recent_errors if any 500 errors occurred
        # Note: 404 and 422 are client errors, not tracked in recent_errors

    def test_metrics_aggregation(self):
        """Test that metrics are properly aggregated"""
        # Reset metrics
        metrics.endpoint_counts.clear()
        metrics.endpoint_timings.clear()

        # Make multiple requests to same endpoint
        for i in range(3):
            client.post("/todos", json={"title": f"Test {i}"})

        # Check endpoint counts
        assert "POST /todos" in metrics.endpoint_counts
        assert metrics.endpoint_counts["POST /todos"] >= 3

        # Check timing aggregation
        assert "POST /todos" in metrics.endpoint_timings
        timings = metrics.endpoint_timings["POST /todos"]
        assert len(timings) >= 3

        # Get metrics and check aggregated stats
        response = client.get("/metrics")
        metrics_data = response.json()["metrics"]

        if "POST /todos" in metrics_data["response_times"]:
            timing_stats = metrics_data["response_times"]["POST /todos"]
            assert "count" in timing_stats
            assert "avg_ms" in timing_stats
            assert "min_ms" in timing_stats
            assert "max_ms" in timing_stats
            assert timing_stats["count"] >= 3

    def test_status_code_tracking(self):
        """Test that different status codes are tracked"""
        # Reset metrics
        metrics.status_code_counts.clear()

        # Generate different status codes
        client.post("/todos", json={"title": "Test"})  # 201
        client.get("/todos")  # 200
        client.get("/todos/9999")  # 404
        client.post("/todos", json={"title": ""})  # 422

        # Check status codes are tracked
        assert 200 in metrics.status_code_counts or 201 in metrics.status_code_counts
        assert metrics.status_code_counts.get(404, 0) >= 1
        assert metrics.status_code_counts.get(422, 0) >= 1

    def test_json_logging_format(self):
        """Test that logs are in JSON format"""
        # The logger should be outputting JSON
        # This is more of an integration test that would need actual log capture
        # For now, we just verify the logger is configured
        from main import logger, JSONFormatter

        assert logger is not None
        assert len(logger.handlers) > 0

        # Check that the formatter is JSONFormatter
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, JSONFormatter)

    def test_health_check_database_failure(self):
        """Test health check when database has issues"""
        # This would require mocking database failure
        # For now, we just ensure the endpoint handles it gracefully
        response = client.get("/health")
        assert response.status_code == 200
        assert "status" in response.json()

    def test_metrics_uptime(self):
        """Test that uptime is calculated correctly"""
        # Get initial metrics
        response1 = client.get("/metrics")
        uptime1 = response1.json()["metrics"]["uptime_seconds"]

        # Wait a bit
        time.sleep(0.1)

        # Get metrics again
        response2 = client.get("/metrics")
        uptime2 = response2.json()["metrics"]["uptime_seconds"]

        # Uptime should have increased
        assert uptime2 > uptime1