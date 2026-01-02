# Todo REST API

A robust REST API for managing todo items built with FastAPI and SQLAlchemy.

## Features

- **CRUD Operations**: Full Create, Read, Update, Delete functionality for todos
- **Data Validation**: Comprehensive input validation using Pydantic models
- **Persistence**: SQLite database with SQLAlchemy ORM
- **Filtering & Pagination**: Query todos by completion status with pagination support
- **Favorites**: Mark todos as favorites for prioritization
- **Timestamps**: Automatic tracking of creation and update times
- **Error Handling**: Proper HTTP status codes and error messages

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Get API information and available endpoints |
| POST | `/todos` | Create a new todo |
| GET | `/todos` | Get all todos (with optional filtering) |
| GET | `/todos/{id}` | Get a specific todo by ID |
| PUT | `/todos/{id}` | Update a todo |
| DELETE | `/todos/{id}` | Delete a todo |

## Data Model

### Todo Schema

```json
{
  "id": 1,
  "title": "string (required, 1-200 chars)",
  "description": "string (optional, max 1000 chars)",
  "completed": false,
  "favorite": false,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

## Installation

### Prerequisites

- Python 3.7+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## Usage Examples

### Create a Todo

```bash
curl -X POST "http://localhost:8000/todos" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",
    "completed": false,
    "favorite": false
  }'
```

### Get All Todos

```bash
# Get all todos
curl "http://localhost:8000/todos"

# Get only completed todos
curl "http://localhost:8000/todos?completed=true"

# Get todos with pagination
curl "http://localhost:8000/todos?skip=10&limit=5"
```

### Update a Todo

```bash
curl -X PUT "http://localhost:8000/todos/1" \
  -H "Content-Type: application/json" \
  -d '{
    "completed": true,
    "favorite": true
  }'
```

### Delete a Todo

```bash
curl -X DELETE "http://localhost:8000/todos/1"
```

## Testing

Run the test suite with coverage:

```bash
pytest test_main.py --cov=main --cov-report=term-missing
```

The test suite includes:
- Unit tests for all CRUD operations
- Validation testing for input data
- Edge case handling
- Error response testing
- Timestamp behavior verification

## Data Validation

The API enforces strict validation rules:

- **Title**: Required, 1-200 characters, cannot be empty or whitespace
- **Description**: Optional, max 1000 characters
- **Completed**: Boolean, defaults to false
- **Favorite**: Boolean, defaults to false

All text fields are automatically trimmed of leading/trailing whitespace.

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK`: Successful GET/PUT requests
- `201 Created`: Successful POST requests
- `204 No Content`: Successful DELETE requests
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation errors

Error responses include detailed messages:
```json
{
  "detail": "Todo with id 999 not found"
}
```

## Database

The API uses SQLite for data persistence. The database file (`todos.db`) is created automatically on first run.

### Database Schema

```sql
CREATE TABLE todos (
    id INTEGER PRIMARY KEY,
    title VARCHAR NOT NULL,
    description VARCHAR,
    completed BOOLEAN DEFAULT FALSE,
    favorite BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Development

### Project Structure

```
rest-api/
├── main.py           # Main API application
├── test_main.py      # Test suite
├── todos.db          # SQLite database (auto-generated)
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### Adding New Features

1. Update the Pydantic models for validation
2. Add new endpoints or modify existing ones
3. Update the database schema if needed
4. Add corresponding tests
5. Update this documentation

## License

This project is open source and available for educational purposes.