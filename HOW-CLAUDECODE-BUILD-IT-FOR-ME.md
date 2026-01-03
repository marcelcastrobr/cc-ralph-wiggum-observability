# Using Loops in Claude Code

This week I came accross the concet of "**claude code loop**" which I was not aware of.  

Basically it is a term coined from [Geoffrey Huntley](https://ghuntley.com/) which describe it as a **"Ralph is a Bash loop" - a development methodology based on continuous AI agents loops** . 

Ralph in this case is named after [Ralph Wiggum from The Simpsons](https://en.wikipedia.org/wiki/Ralph_Wiggum), which represents the philosophy of **persistent interactions despite setbacks**.



![Ralph Wiggum by Gemini](./assets/image-20260102182926268.png)



## Ralph Wiggum Plugin

**Claude code loop** is implement as a plugin named  "Ralph Wiggum Plugin"  at https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum.

In my case, I use the pluging to create an MCP server for my simple [REST API for managing TODO items](https://github.com/marcelcastrobr/cc-ralph-wiggum-observability) build with FastAPI and SQLAlchemy.

But before check the results, lets look at how to install and use the Claude Code [Ralph Wiggum Plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum)

#### How to install the plugin

```markdown
**Install ralph-wiggum plugin:**
 /plugin install claude-plugins-official/ralph-wiggum
 
 **Remove ralph-wiggum plugin:**	
 /plugin remove ralph-wiggum
 
**Alternative installation method:**
 You can also use the interactive installer which will show available plugins:
  /plugin install
```



#### How to use Ralph Wiggum Plugin

The basic concepts are:

```bash
# You run ONCE:
/ralph-loop "Your task description" --completion-promise "DONE"

# Then Claude Code automatically:
# 1. Works on the task
# 2. Tries to exit
# 3. Stop hook blocks exit
# 4. Stop hook feeds the SAME prompt back
# 5. Repeat until completion
```

I used it to add an MCP Server using the following instructions.

```bash
/ralph-loop "Build a MCP server for my REST API for todos. MCP server using FASTAPI is prefered.

When complete:
- All CRUD operations as tools.
- MCP server will be used to interact with REST API to create/delete/show/update TODOs.
- Make sure error handlinhg is done properly.
- Output: <promise>COMPLETE</promise>" --completion-promise "COMPLETE" --max-iterations 20
```

After $8.88 , I got the following output from claude code.

```markdown
Perfect! I have successfully completed the MCP server for your REST API for todos. Here's a summary of what has been accomplished:

  ✅ Completed Tasks

  1. MCP Server Implementation (mcp_server.py)
    - Built using FastAPI-compatible architecture as requested
    - Interfaces with your existing REST API at http://localhost:8000
    - Implements proper async/await patterns for efficient operation
  2. All CRUD Operations as Tools
    - create_todo - Create new todos with validation
    - list_todos - List todos with filtering and pagination
    - get_todo - Retrieve specific todo by ID
    - update_todo - Update todos with partial update support
    - delete_todo - Delete todos
    - mark_todo_complete - Convenience method to mark as complete
    - mark_todo_incomplete - Convenience method to mark as incomplete
  3. Comprehensive Error Handling
    - Validation errors for input constraints
    - Not found errors for missing todos
    - Connection and timeout errors for API issues
    - Detailed error types and messages for debugging
    - Graceful error recovery and reporting
  4. Configuration Files
    - mcp.json - MCP server configuration
    - requirements-mcp.txt - Python dependencies
  5. Testing Suite
    - test_mcp_server.py - Comprehensive test suite
    - simple_test_mcp.py - Simple integration test
    - Successfully tested all CRUD operations
  6. Documentation
    - MCP_SERVER_README.md - Complete documentation with:
        - Installation instructions
      - Usage examples for all tools
      - Error handling guide
      - Troubleshooting section
      - Architecture overview

  The MCP server is fully functional and ready to use. It successfully:
  - Connects to your REST API
  - Performs all CRUD operations
  - Handles errors gracefully
  - Provides detailed responses
  - Validates input data

  COMPLETE
```



And here a detailed information on cost.

```
/cost 
  ⎿  Total cost:            $8.88
     Total duration (API):  22m 18s
     Total duration (wall): 4h 49m 58s
     Total code changes:    1941 lines added, 447 lines removed
     Usage by model:
             claude-haiku:  24.0k input, 926 output, 0 cache read, 0 cache write ($0.0287)
         claude-3-5-haiku:  4 input, 362 output, 2.1k cache read, 0 cache write ($0.0016)
          claude-opus-4-1:  66 input, 28.2k output, 2.8m cache read, 135.9k cache write ($8.85)

```



## 

### Using MCP to interact with my TODO List

In order to use the MCP server in claude code, we need to add the following configuration in the .claude/settings.json file.

```json
{
    "mcpServers": {
      "todo-mcp-server": {
        "name": "todo-mcp-server",
        "command": "python",
        "args": ["/Documents/claudecode/cc-ralph-wiggum-observability/mcp_server.py"],
        "cwd": "/Documents/claudecode/cc-ralph-wiggum-observability",
        "env": {
          "PYTHONUNBUFFERED": "1"
        }
      }
    }
  }

```

Once installed, we can use the MCP tools in our Claude Code conversations:

 \- "Use the todo MCP server to create a new todo called 'Test MCP Integration'"

 \- "List all pending todos using the MCP server"

 \- "Mark todo ID 1 as complete"

 \- "Delete todo ID 2"





## Claude Code Transcripts

I am new user of claude code using CLI (command line). Sometimes I find useful to check what the agent has done as a way to learn from the agent during task execution. In special, when using  **/ralp-loop** where the idea is to have claude code to develop the whole task in a loop with minimum interuption.

In order to o it I came accross the [claude-code-transcripts](https://simonwillison.net/2025/Dec/25/claude-code-transcripts/) from Simon Willison, which is a python CLI tool that converts the claude code transcripts to HTML pages that can be shared through Github Gists.

You can run using:

```bash
uvx claude-code-transcripts
```

To generate Github gist, make sure you have the gh authentication and run the command:

```bash
uvx claude-code-transcripts --gist

# Or if you have installed it through "uv tool install claude-code-transcripts"
claude-code-transcripts --gist
```



The result is the converted claude code session files to clean HTML pages with pagination. Thanks to [Simon Willison](https://simonwillison.net/).

![image-20260102182355101](./assets/image-20260102182355101.png)

Check the complete Claude Code session at https://gisthost.github.io/?b3539b30c87b796fb924d791c6ec5126/page-002.html



## References

- [Ralph Wiggum Plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum)
- [claude-code-transcripts by Simon Willison](https://simonwillison.net/2025/Dec/25/claude-code-transcripts/)