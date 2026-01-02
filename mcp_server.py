#!/usr/bin/env python3
"""
MCP Server for Todo REST API
Provides tools for CRUD operations on todos via MCP protocol
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    CallToolResult,
    INVALID_PARAMS,
    INTERNAL_ERROR
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0  # seconds

class TodoMCPServer:
    """MCP Server for Todo REST API interactions"""

    def __init__(self):
        self.server = Server("todo-mcp-server")
        self.client = httpx.AsyncClient(timeout=TIMEOUT)
        self._setup_handlers()

    def _setup_handlers(self):
        """Set up request handlers for the MCP server"""

        # Override list_tools method
        self.server.list_tools = self._list_tools

        # Override call_tool method
        self.server.call_tool = self._call_tool

    async def _list_tools(self) -> List[Tool]:
        """Return list of available tools"""
        return [
            Tool(
                    name="create_todo",
                    description="Create a new todo item",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Title of the todo (required, 1-200 chars)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Description of the todo (optional, max 1000 chars)"
                            },
                            "completed": {
                                "type": "boolean",
                                "description": "Whether the todo is completed",
                                "default": False
                            },
                            "favorite": {
                                "type": "boolean",
                                "description": "Whether the todo is favorited",
                                "default": False
                            }
                        },
                        "required": ["title"]
                    }
                ),
                Tool(
                    name="list_todos",
                    description="List todos with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "completed": {
                                "type": "boolean",
                                "description": "Filter by completion status"
                            },
                            "skip": {
                                "type": "integer",
                                "description": "Number of items to skip for pagination",
                                "default": 0
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of items to return",
                                "default": 100
                            }
                        }
                    }
                ),
                Tool(
                    name="get_todo",
                    description="Get a specific todo by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "The ID of the todo to retrieve"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="update_todo",
                    description="Update a todo item (partial update supported)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "The ID of the todo to update"
                            },
                            "title": {
                                "type": "string",
                                "description": "New title (1-200 chars)"
                            },
                            "description": {
                                "type": "string",
                                "description": "New description (max 1000 chars)"
                            },
                            "completed": {
                                "type": "boolean",
                                "description": "New completion status"
                            },
                            "favorite": {
                                "type": "boolean",
                                "description": "New favorite status"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="delete_todo",
                    description="Delete a todo item",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "The ID of the todo to delete"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="mark_todo_complete",
                    description="Mark a todo as completed (convenience method)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "The ID of the todo to mark as complete"
                            }
                        },
                        "required": ["todo_id"]
                    }
                ),
                Tool(
                    name="mark_todo_incomplete",
                    description="Mark a todo as incomplete (convenience method)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "todo_id": {
                                "type": "integer",
                                "description": "The ID of the todo to mark as incomplete"
                            }
                        },
                        "required": ["todo_id"]
                    }
                )
            ]

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls"""

        try:
            if tool_name == "create_todo":
                return await self._create_todo(arguments)
            elif tool_name == "list_todos":
                return await self._list_todos(arguments)
            elif tool_name == "get_todo":
                return await self._get_todo(arguments)
            elif tool_name == "update_todo":
                return await self._update_todo(arguments)
            elif tool_name == "delete_todo":
                return await self._delete_todo(arguments)
            elif tool_name == "mark_todo_complete":
                return await self._mark_todo_complete(arguments)
            elif tool_name == "mark_todo_incomplete":
                return await self._mark_todo_incomplete(arguments)
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Unknown tool: {tool_name}",
                        "type": "invalid_tool"
                    }, indent=2)
                )]
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Tool execution error: {str(e)}",
                    "type": "execution_error"
                }, indent=2)
            )]

    async def _create_todo(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Create a new todo item"""
        try:
            # Extract and validate arguments
            title = arguments.get("title", "").strip()
            description = arguments.get("description", "").strip() if arguments.get("description") else None
            completed = arguments.get("completed", False)
            favorite = arguments.get("favorite", False)

            # Validate inputs
            if not title:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Title cannot be empty or just whitespace",
                        "type": "validation_error"
                    }, indent=2)
                )]

            if len(title) > 200:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Title must be 200 characters or less",
                        "type": "validation_error"
                    }, indent=2)
                )]

            if description and len(description) > 1000:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "Description must be 1000 characters or less",
                        "type": "validation_error"
                    }, indent=2)
                )]

            # Prepare request data
            data = {
                "title": title,
                "completed": completed,
                "favorite": favorite
            }
            if description:
                data["description"] = description

            # Make API request
            response = await self.client.post(
                f"{API_BASE_URL}/todos",
                json=data
            )

            # Handle response
            if response.status_code == 201:
                todo = response.json()
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Todo created successfully with ID {todo['id']}",
                        "todo": todo
                    }, indent=2)
                )]
            elif response.status_code == 422:
                error_detail = response.json().get("detail", "Validation error")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Validation error: {error_detail}",
                        "type": "validation_error"
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Failed to create todo. Status: {response.status_code}",
                        "details": response.text,
                        "type": "api_error"
                    }, indent=2)
                )]

        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Request timed out. Please check if the API server is running.",
                    "type": "timeout_error"
                }, indent=2)
            )]
        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Could not connect to API server. Please ensure it's running on http://localhost:8000",
                    "type": "connection_error"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error creating todo: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "type": "internal_error"
                }, indent=2)
            )]

    async def _list_todos(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """List todos with optional filtering"""
        try:
            # Extract arguments
            completed = arguments.get("completed")
            skip = arguments.get("skip", 0)
            limit = arguments.get("limit", 100)

            # Build query parameters
            params = {
                "skip": skip,
                "limit": limit
            }
            if completed is not None:
                params["completed"] = completed

            # Make API request
            response = await self.client.get(
                f"{API_BASE_URL}/todos",
                params=params
            )

            # Handle response
            if response.status_code == 200:
                todos = response.json()

                # Format todos for display
                if todos:
                    summary = f"Found {len(todos)} todo(s)"
                    if completed is not None:
                        summary += f" ({'completed' if completed else 'pending'})"

                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "summary": summary,
                            "count": len(todos),
                            "todos": todos
                        }, indent=2)
                    )]
                else:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "success": True,
                            "message": "No todos found",
                            "todos": []
                        }, indent=2)
                    )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Failed to list todos. Status: {response.status_code}",
                        "details": response.text,
                        "type": "api_error"
                    }, indent=2)
                )]

        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Request timed out. Please check if the API server is running.",
                    "type": "timeout_error"
                }, indent=2)
            )]
        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Could not connect to API server. Please ensure it's running on http://localhost:8000",
                    "type": "connection_error"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error listing todos: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "type": "internal_error"
                }, indent=2)
            )]

    async def _get_todo(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get a specific todo by ID"""
        try:
            todo_id = arguments.get("todo_id")
            if not todo_id:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "todo_id is required",
                        "type": "validation_error"
                    }, indent=2)
                )]

            # Make API request
            response = await self.client.get(f"{API_BASE_URL}/todos/{todo_id}")

            # Handle response
            if response.status_code == 200:
                todo = response.json()
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "todo": todo
                    }, indent=2)
                )]
            elif response.status_code == 404:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Todo with ID {todo_id} not found",
                        "type": "not_found"
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Failed to get todo. Status: {response.status_code}",
                        "details": response.text,
                        "type": "api_error"
                    }, indent=2)
                )]

        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Request timed out. Please check if the API server is running.",
                    "type": "timeout_error"
                }, indent=2)
            )]
        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Could not connect to API server. Please ensure it's running on http://localhost:8000",
                    "type": "connection_error"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error getting todo: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "type": "internal_error"
                }, indent=2)
            )]

    async def _update_todo(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Update a todo item"""
        try:
            todo_id = arguments.get("todo_id")
            if not todo_id:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "todo_id is required",
                        "type": "validation_error"
                    }, indent=2)
                )]

            # Extract update fields
            title = arguments.get("title")
            description = arguments.get("description")
            completed = arguments.get("completed")
            favorite = arguments.get("favorite")

            # Validate inputs
            if title is not None:
                title = title.strip()
                if not title:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Title cannot be empty or just whitespace",
                            "type": "validation_error"
                        }, indent=2)
                    )]
                if len(title) > 200:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Title must be 200 characters or less",
                            "type": "validation_error"
                        }, indent=2)
                    )]

            if description is not None:
                description = description.strip()
                if len(description) > 1000:
                    return [TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Description must be 1000 characters or less",
                            "type": "validation_error"
                        }, indent=2)
                    )]

            # Build update data (only include provided fields)
            data = {}
            if title is not None:
                data["title"] = title
            if description is not None:
                data["description"] = description
            if completed is not None:
                data["completed"] = completed
            if favorite is not None:
                data["favorite"] = favorite

            if not data:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "No fields to update. Please provide at least one field.",
                        "type": "validation_error"
                    }, indent=2)
                )]

            # Make API request
            response = await self.client.put(
                f"{API_BASE_URL}/todos/{todo_id}",
                json=data
            )

            # Handle response
            if response.status_code == 200:
                todo = response.json()
                updated_fields = list(data.keys())
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Todo {todo_id} updated successfully",
                        "updated_fields": updated_fields,
                        "todo": todo
                    }, indent=2)
                )]
            elif response.status_code == 404:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Todo with ID {todo_id} not found",
                        "type": "not_found"
                    }, indent=2)
                )]
            elif response.status_code == 422:
                error_detail = response.json().get("detail", "Validation error")
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Validation error: {error_detail}",
                        "type": "validation_error"
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Failed to update todo. Status: {response.status_code}",
                        "details": response.text,
                        "type": "api_error"
                    }, indent=2)
                )]

        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Request timed out. Please check if the API server is running.",
                    "type": "timeout_error"
                }, indent=2)
            )]
        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Could not connect to API server. Please ensure it's running on http://localhost:8000",
                    "type": "connection_error"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error updating todo: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "type": "internal_error"
                }, indent=2)
            )]

    async def _delete_todo(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Delete a todo item"""
        try:
            todo_id = arguments.get("todo_id")
            if not todo_id:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": "todo_id is required",
                        "type": "validation_error"
                    }, indent=2)
                )]

            # Make API request
            response = await self.client.delete(f"{API_BASE_URL}/todos/{todo_id}")

            # Handle response
            if response.status_code == 204:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Todo {todo_id} deleted successfully"
                    }, indent=2)
                )]
            elif response.status_code == 404:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Todo with ID {todo_id} not found",
                        "type": "not_found"
                    }, indent=2)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Failed to delete todo. Status: {response.status_code}",
                        "details": response.text,
                        "type": "api_error"
                    }, indent=2)
                )]

        except httpx.TimeoutException:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Request timed out. Please check if the API server is running.",
                    "type": "timeout_error"
                }, indent=2)
            )]
        except httpx.ConnectError:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Could not connect to API server. Please ensure it's running on http://localhost:8000",
                    "type": "connection_error"
                }, indent=2)
            )]
        except Exception as e:
            logger.error(f"Error deleting todo: {e}")
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Unexpected error: {str(e)}",
                    "type": "internal_error"
                }, indent=2)
            )]

    async def _mark_todo_complete(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Mark a todo as completed"""
        arguments["completed"] = True
        return await self._update_todo(arguments)

    async def _mark_todo_incomplete(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Mark a todo as incomplete"""
        arguments["completed"] = False
        return await self._update_todo(arguments)

    async def cleanup(self):
        """Clean up resources"""
        await self.client.aclose()

    async def run(self):
        """Run the MCP server"""
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream)
        finally:
            await self.cleanup()

async def main():
    """Main entry point"""
    logger.info("Starting Todo MCP Server")
    logger.info(f"Connecting to API at {API_BASE_URL}")

    server = TodoMCPServer()
    try:
        await server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
    finally:
        logger.info("Todo MCP Server stopped")

if __name__ == "__main__":
    asyncio.run(main())