#!/usr/bin/env python3
"""
Simple test to verify MCP server works by calling tool methods directly
"""

import asyncio
import json

async def test_direct():
    from mcp_server import TodoMCPServer

    server = TodoMCPServer()

    # Test create directly
    result = await server._create_todo({
        "title": "Test Todo",
        "description": "Test description",
        "completed": False,
        "favorite": False
    })

    print("Create result:")
    if result:
        text = result[0].text
        data = json.loads(text)
        print(json.dumps(data, indent=2))

        if "todo" in data:
            todo_id = data["todo"]["id"]

            # Test list
            result = await server._list_todos({})
            print("\nList result:")
            text = result[0].text
            data = json.loads(text)
            print(json.dumps(data, indent=2))

            # Test delete
            result = await server._delete_todo({"todo_id": todo_id})
            print("\nDelete result:")
            text = result[0].text
            data = json.loads(text)
            print(json.dumps(data, indent=2))

    await server.cleanup()

if __name__ == "__main__":
    asyncio.run(test_direct())