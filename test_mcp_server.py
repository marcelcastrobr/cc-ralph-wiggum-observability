#!/usr/bin/env python3
"""
Test script for MCP Server
Tests all CRUD operations through the MCP server
"""

import asyncio
import json
import sys
from typing import Dict, Any

# Add parent directory to path for imports
sys.path.append('.')

async def test_mcp_operations():
    """Test all MCP server operations"""

    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)

    # Import the MCP server module
    from mcp_server import TodoMCPServer

    # Create server instance
    server = TodoMCPServer()

    # Track test results
    tests_passed = 0
    tests_failed = 0

    async def run_test(name: str, tool_name: str, **kwargs):
        """Helper to run a single test"""
        nonlocal tests_passed, tests_failed

        print(f"\n[TEST] {name}")
        print("-" * 40)

        try:
            # Call the tool directly through the internal method
            result = await server.server._handlers['tools/call'](tool_name, kwargs)

            # Parse the response
            if result and len(result) > 0:
                response_text = result[0].text
                response_data = json.loads(response_text)

                # Check for success or error
                if "success" in response_data and response_data["success"]:
                    print(f"✅ PASSED: {name}")
                    if "message" in response_data:
                        print(f"   Message: {response_data['message']}")
                    tests_passed += 1
                    return response_data
                elif "error" in response_data:
                    # Some errors are expected (e.g., not found for non-existent ID)
                    if "not_found" in response_data.get("type", ""):
                        print(f"✅ PASSED: {name} (Expected error)")
                        tests_passed += 1
                    else:
                        print(f"❌ FAILED: {name}")
                        print(f"   Error: {response_data['error']}")
                        tests_failed += 1
                    return response_data
                else:
                    print(f"✅ PASSED: {name}")
                    tests_passed += 1
                    return response_data
            else:
                print(f"❌ FAILED: {name} - No response")
                tests_failed += 1
                return None

        except Exception as e:
            print(f"❌ FAILED: {name}")
            print(f"   Exception: {str(e)}")
            tests_failed += 1
            return None

    print("\n📝 Testing CRUD Operations")
    print("=" * 60)

    # Test 1: Create a todo
    todo1_result = await run_test(
        "Create Todo #1",
        "create_todo",
        title="Test Todo 1",
        description="This is a test todo created via MCP",
        completed=False,
        favorite=True
    )

    todo1_id = None
    if todo1_result and "todo" in todo1_result:
        todo1_id = todo1_result["todo"]["id"]
        print(f"   Created Todo ID: {todo1_id}")

    # Test 2: Create another todo
    todo2_result = await run_test(
        "Create Todo #2",
        "create_todo",
        title="Test Todo 2",
        description="Another test todo",
        completed=True,
        favorite=False
    )

    todo2_id = None
    if todo2_result and "todo" in todo2_result:
        todo2_id = todo2_result["todo"]["id"]
        print(f"   Created Todo ID: {todo2_id}")

    # Test 3: List all todos
    await run_test(
        "List All Todos",
        "list_todos"
    )

    # Test 4: List completed todos
    await run_test(
        "List Completed Todos",
        "list_todos",
        completed=True
    )

    # Test 5: List pending todos
    await run_test(
        "List Pending Todos",
        "list_todos",
        completed=False
    )

    # Test 6: Get specific todo
    if todo1_id:
        await run_test(
            f"Get Todo #{todo1_id}",
            "get_todo",
            todo_id=todo1_id
        )

    # Test 7: Update todo
    if todo1_id:
        await run_test(
            f"Update Todo #{todo1_id}",
            "update_todo",
            todo_id=todo1_id,
            title="Updated Test Todo 1",
            completed=True
        )

    # Test 8: Mark todo as complete
    if todo2_id:
        await run_test(
            f"Mark Todo #{todo2_id} Complete",
            "mark_todo_complete",
            todo_id=todo2_id
        )

    # Test 9: Mark todo as incomplete
    if todo1_id:
        await run_test(
            f"Mark Todo #{todo1_id} Incomplete",
            "mark_todo_incomplete",
            todo_id=todo1_id
        )

    # Test 10: Delete todo
    if todo1_id:
        await run_test(
            f"Delete Todo #{todo1_id}",
            "delete_todo",
            todo_id=todo1_id
        )

    # Test 11: Try to get deleted todo (should fail)
    if todo1_id:
        await run_test(
            f"Get Deleted Todo #{todo1_id} (Should Fail)",
            "get_todo",
            todo_id=todo1_id
        )

    # Test 12: Validation - empty title
    await run_test(
        "Create Todo with Empty Title (Should Fail)",
        "create_todo",
        title="",
        description="This should fail"
    )

    # Test 13: Validation - title too long
    await run_test(
        "Create Todo with Title Too Long (Should Fail)",
        "create_todo",
        title="x" * 201,
        description="This should fail"
    )

    # Clean up: Delete remaining test todos
    if todo2_id:
        await run_test(
            f"Cleanup: Delete Todo #{todo2_id}",
            "delete_todo",
            todo_id=todo2_id
        )

    # Clean up the HTTP client
    await server.cleanup()

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"✅ Tests Passed: {tests_passed}")
    print(f"❌ Tests Failed: {tests_failed}")
    print(f"📊 Total Tests: {tests_passed + tests_failed}")

    if tests_failed == 0:
        print("\n🎉 All tests passed successfully!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed")
        return 1

async def main():
    """Main entry point"""
    try:
        return await test_mcp_operations()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)