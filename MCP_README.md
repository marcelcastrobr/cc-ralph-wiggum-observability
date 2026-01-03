# Todo MCP Server

This document describes the MCP (Model Context Protocol) server implementation for the Todo REST API, enabling AI agents to interact with the todo management system.

## Overview

The MCP server is built using [FastAPI-MCP](https://github.com/tadata-org/fastapi_mcp), which exposes the FastAPI REST API endpoints as MCP tools. This allows AI agents (like Claude Desktop, Cursor, or other MCP-compatible clients) to programmatically create, read, update, and delete todo items.

## Installation

Ensure you have the required dependencies installed:

```bash
pip install fastapi-mcp
# or
pip install -e .  # If using pyproject.toml
```

## Starting the Server

Start the server with:

```bash
python main.py
```

The server will be available at:
- **REST API**: `http://localhost:8000`
- **MCP Server**: `http://localhost:8000/mcp`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)

## Available MCP Tools

The following CRUD operations are exposed as MCP tools:

### 1. `create_todo`

Create a new todo item.

**Parameters:**
- `title` (string, required): Title of the todo (1-200 characters)
- `description` (string, optional): Description of the todo (max 1000 characters)
- `completed` (boolean, optional): Completion status (default: false)
- `favorite` (boolean, optional): Favorite status (default: false)

**Returns:** The created todo object with id, timestamps, and all fields.

**Example:**
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "favorite": true
}
```

### 2. `list_todos`

List all todos with optional filtering and pagination.

**Parameters:**
- `skip` (integer, optional): Number of items to skip (default: 0)
- `limit` (integer, optional): Maximum number of items to return (default: 100)
- `completed` (boolean, optional): Filter by completion status

**Returns:** Array of todo objects.

**Example:** Get incomplete todos: `completed=false`

### 3. `get_todo`

Get a specific todo by its ID.

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to retrieve

**Returns:** The todo object if found, or a 404 error if not found.

### 4. `update_todo`

Update an existing todo item (partial updates supported).

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to update
- `title` (string, optional): New title (1-200 characters)
- `description` (string, optional): New description (max 1000 characters)
- `completed` (boolean, optional): New completion status
- `favorite` (boolean, optional): New favorite status

**Returns:** The updated todo object.

**Example:** Mark a todo as completed:
```json
{
  "completed": true
}
```

### 5. `delete_todo`

Delete a todo item by its ID.

**Parameters:**
- `todo_id` (integer, required): The ID of the todo to delete

**Returns:** No content (204 status) on success, or 404 if not found.

## Connecting MCP Clients

### Claude Code

Add the MCP server to Claude Code using the CLI:

```bash
claude mcp add todo-api http://localhost:8000/mcp --transport http
```

Or add it manually to your Claude Code settings file (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "todo-api": {
      "type": "http",
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

After adding, restart Claude Code or run `/mcp` to verify the server is connected. You should see the 5 todo tools available (create_todo, list_todos, get_todo, update_todo, delete_todo).

### Claude Desktop

Add to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "todo-api": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "todo-api": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### Using mcp-remote (for clients without SSE support)

If your MCP client doesn't support Server-Sent Events (SSE), use `mcp-remote` as a bridge:

```bash
npx mcp-remote http://localhost:8000/mcp
```

## Error Handling

The MCP server inherits the error handling from the REST API:

- **400 Bad Request**: Invalid input data (e.g., empty title, title too long)
- **404 Not Found**: Todo with specified ID doesn't exist
- **422 Unprocessable Entity**: Validation errors (returned with detailed messages)
- **500 Internal Server Error**: Unexpected server errors (logged with request ID)

All errors include descriptive messages to help diagnose issues.

## Example Workflow

Here's an example workflow using the MCP tools:

1. **Create a todo:**
   ```
   create_todo(title="Review PR #123", description="Check tests and code quality", favorite=true)
   ```

2. **List all incomplete todos:**
   ```
   list_todos(completed=false)
   ```

3. **Mark as complete:**
   ```
   update_todo(todo_id=1, completed=true)
   ```

4. **Delete when done:**
   ```
   delete_todo(todo_id=1)
   ```

## Architecture

The MCP server is implemented using FastAPI-MCP, which:
- Uses FastAPI's native ASGI interface for efficient communication
- Preserves request/response schemas from the original endpoints
- Maintains endpoint documentation from the Swagger specification
- Supports HTTP transport (recommended) for broad compatibility

## Observability

The MCP server shares the same observability features as the REST API:
- Structured JSON logging
- Request metrics and timing
- Health check endpoint at `/health`
- Metrics endpoint at `/metrics`

## Development

To add new MCP tools, add new FastAPI endpoints with `operation_id` parameters and include them in the `include_operations` list when initializing `FastApiMCP`.

Example:
```python
@app.post("/todos/bulk", operation_id="bulk_create_todos")
def bulk_create_todos(...):
    ...

mcp = FastApiMCP(
    app,
    include_operations=[..., "bulk_create_todos"]
)
```
