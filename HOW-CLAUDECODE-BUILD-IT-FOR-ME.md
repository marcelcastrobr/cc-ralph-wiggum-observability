# Using Loops in Claude Code  Ralph Wiggum Plugin with Observability



During the break I came accross the concet of "**claude code loop**" which I was not aware of.  

Basically it is a term coined from [Geoffrey Huntley](https://ghuntley.com/) which describe it as a **"Ralph is a Bash loop" - a development methodology based on continuous AI agents loops** . 

Ralph in this case is named after [Ralph Wiggum from The Simpsons](https://en.wikipedia.org/wiki/Ralph_Wiggum), which represents a persistent interactions despite setbacks.



## Ralph Wiggum Plugin

Claude code loop is implement as a plugin named  "Ralph Wiggum Plugin"  at https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum.



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



I use the following instruction to create observability in my demo TODO API using **/ralp-loop**

```
prompt: |
  Add comprehensive observability to the Todo API including:

    1. Structured JSON logging for all endpoints with request/response details
    2. Request timing metrics
    3. Error tracking with stack traces
    4. Health check endpoint at /health
    5. Metrics endpoint at /metrics showing API usage stats

  All features must have tests passing.
  Output <promise>OBSERVABILITY COMPLETE</promise> when all tests pass.

completion_promise: "OBSERVABILITY COMPLETE"
max_iterations: 15
current_iteration: 1
started_at: 2026-01-02T11:38:00Z
```



Now I used it to add an MCP Server using the following instructions.

```
/ralph-loop "Build a MCP server for my REST API for todos. MCP server using FASTAPI is prefered.

When complete:
- All CRUD operations as tools.
- MCP server will be used to interact with REST API to create/delete/show/update TODOs.
- Make sure error handlinhg is done properly.
- Output: <promise>COMPLETE</promise>" --completion-promise "COMPLETE" --max-iterations 20
```



## Claude Code Transcripts

I am new user of claude code using CLI (command line). Sometimes I find useful to check what the agent has done as a way to learn from the agent during task execution. In special, when using  **/ralp-loop** where the idea is to have claude code to develop the whole task in a loop with minimum interuption.

In order to o it I came accross the [claude-code-transcripts](https://simonwillison.net/2025/Dec/25/claude-code-transcripts/) from Simon Willison, which is a python CLI tool that converts the claude code transcripts to HTML pages that can be shared through Github Gists.

You can run using:

```bash
uvx claude-code-transcripts
```







## References

- [Ralph Wiggum Plugin](https://github.com/anthropics/claude-plugins-official/tree/main/plugins/ralph-wiggum)
- [claude-code-transcripts by Simon Willison](https://simonwillison.net/2025/Dec/25/claude-code-transcripts/)