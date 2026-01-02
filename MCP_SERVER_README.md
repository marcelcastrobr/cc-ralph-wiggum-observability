# MCP Server for Todo REST API

This MCP (Model Context Protocol) server provides a seamless interface for interacting with the Todo REST API through standardized tools that can be used by AI assistants and automation systems.

## Features

- **Complete CRUD Operations**: All Create, Read, Update, and Delete operations for todos
- **Robust Error Handling**: Comprehensive error handling with detailed error types and messages
- **Connection Management**: Automatic retry and timeout handling for API requests
- **Validation**: Input validation to ensure data integrity before API calls
- **Convenience Methods**: Additional helper methods for common operations

## Prerequisites

- Python 3.8 or higher
- Running Todo REST API on http://localhost:8000
- Required Python packages:
  - `mcp>=1.0.0`
  - `httpx>=0.24.0`

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements-mcp.txt
```

2. Ensure the Todo REST API is running:
```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000

# Or using the main.py script
python main.py
```

3. Verify the API is accessible:
```bash
curl http://localhost:8000/
```

## Running the MCP Server

### Standalone Mode

Run the MCP server directly:
```bash
python mcp_server.py
```

The server will connect to the REST API at http://localhost:8000 and expose MCP tools via stdio.

### Integration with MCP Clients

The server can be integrated with any MCP-compatible client. Configuration example:

```json
{
  "name": "todo-mcp-server",
  "command": "python",
  "args": ["mcp_server.py"]
}
```

## Available Tools

### 1. create_todo
Create a new todo item.

**Parameters:**
- `title` (string, required): Title of the todo (1-200 characters)
- `description` (string, optional): Description of the todo (max 1000 characters)
- `completed` (boolean, optional): Whether the todo is completed (default: false)
- `favorite` (boolean, optional): Whether the todo is favorited (default: false)

**Example Response:**
```json
{
  "success": true,
  "message": "Todo created successfully with ID 1",
  "todo": {
    "id": 1,
    "title": "Example Todo",
    "description": "This is an example",
    "completed": false,
    "favorite": false,
    "created_at": "2026-01-02T15:30:00.000000",
    "updated_at": "2026-01-02T15:30:00.000000"
  }
}
```

### 2. list_todos
List todos with optional filtering and pagination.

**Parameters:**
- `completed` (boolean, optional): Filter by completion status
- `skip` (integer, optional): Number of items to skip (default: 0)
- `limit` (integer, optional): Maximum number of items to return (default: 100)

**Example Response:**
```json
{
  "success": true,
  "summary": "Found 5 todo(s) (pending)",
  "count": 5,
  "todos": [...]
}
```

### 3. get_todo
Get a specific todo by ID.

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to retrieve

**Example Response:**
```json
{
  "success": true,
  "todo": {
    "id": 1,
    "title": "Example Todo",
    "description": "This is an example",
    "completed": false,
    "favorite": false,
    "created_at": "2026-01-02T15:30:00.000000",
    "updated_at": "2026-01-02T15:30:00.000000"
  }
}
```

### 4. update_todo
Update a todo item (supports partial updates).

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to update
- `title` (string, optional): New title (1-200 characters)
- `description` (string, optional): New description (max 1000 characters)
- `completed` (boolean, optional): New completion status
- `favorite` (boolean, optional): New favorite status

**Example Response:**
```json
{
  "success": true,
  "message": "Todo 1 updated successfully",
  "updated_fields": ["title", "completed"],
  "todo": {...}
}
```

### 5. delete_todo
Delete a todo item.

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to delete

**Example Response:**
```json
{
  "success": true,
  "message": "Todo 1 deleted successfully"
}
```

### 6. mark_todo_complete
Convenience method to mark a todo as completed.

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to mark as complete

### 7. mark_todo_incomplete
Convenience method to mark a todo as incomplete.

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to mark as incomplete

## Error Handling

The MCP server provides detailed error information with specific error types:

### Error Types

- **validation_error**: Input validation failed (e.g., empty title, title too long)
- **not_found**: The requested todo was not found
- **api_error**: The REST API returned an unexpected status code
- **timeout_error**: The request to the API timed out
- **connection_error**: Could not connect to the REST API
- **internal_error**: An unexpected internal error occurred
- **execution_error**: Error during tool execution
- **invalid_tool**: Unknown tool name requested

### Example Error Response
```json
{
  "error": "Todo with ID 999 not found",
  "type": "not_found"
}
```

## Testing

### Unit Testing
Run the test suite to verify all operations:

```bash
python test_mcp_server.py
```

### Simple Integration Test
Test direct method calls:

```bash
python simple_test_mcp.py
```

### Manual Testing with curl
Test the underlying REST API:

```bash
# Create a todo
curl -X POST http://localhost:8000/todos \
  -H "Content-Type: application/json" \
  -d '{"title": "Test", "description": "Test todo", "completed": false}'

# List todos
curl http://localhost:8000/todos

# Get specific todo
curl http://localhost:8000/todos/1

# Update todo
curl -X PUT http://localhost:8000/todos/1 \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete todo
curl -X DELETE http://localhost:8000/todos/1
```

## Configuration

### API Endpoint
The MCP server connects to the REST API at `http://localhost:8000` by default. To change this, modify the `API_BASE_URL` constant in `mcp_server.py`:

```python
API_BASE_URL = "http://localhost:8000"  # Change to your API URL
```

### Timeout Settings
The default timeout is 30 seconds. To adjust, modify the `TIMEOUT` constant:

```python
TIMEOUT = 30.0  # seconds
```

## Architecture

The MCP server follows a clean architecture pattern:

1. **Server Class (`TodoMCPServer`)**: Main server class that manages the MCP protocol
2. **Handler Methods**: Override MCP server methods for tool listing and execution
3. **Tool Implementation Methods**: Individual methods for each CRUD operation
4. **Error Handling**: Comprehensive try-catch blocks with specific error types
5. **HTTP Client**: Uses `httpx` for async HTTP requests with proper timeout handling

## Troubleshooting

### API Connection Issues
If you see connection errors:
1. Verify the REST API is running: `curl http://localhost:8000/`
2. Check the API logs for any errors
3. Ensure no firewall is blocking port 8000

### Validation Errors
If validation fails:
1. Ensure title is not empty and not longer than 200 characters
2. Ensure description is not longer than 1000 characters
3. Check that boolean values are properly formatted

### MCP Protocol Issues
If the MCP server doesn't start:
1. Verify MCP package is installed: `pip show mcp`
2. Check Python version is 3.8 or higher
3. Review server logs for initialization errors

## Development

### Adding New Tools
To add a new tool:

1. Add the tool definition in `_list_tools()` method
2. Add a handler case in `_call_tool()` method
3. Implement the tool method (e.g., `_new_tool()`)
4. Add appropriate error handling
5. Update documentation

### Logging
The server uses Python's logging module. To increase verbosity:

```python
logging.basicConfig(level=logging.DEBUG)
```

## License

This MCP server is provided as-is for use with the Todo REST API project.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the test output for specific errors
3. Examine API and MCP server logs
4. Verify all dependencies are correctly installed