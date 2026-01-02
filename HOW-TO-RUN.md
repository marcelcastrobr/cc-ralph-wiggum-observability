# How to Run - Todo REST API with Frontend

This guide provides step-by-step instructions for setting up and running both the backend REST API and the frontend application.

## Prerequisites

- Python 3.7 or higher
- Node.js 14 or higher (for frontend testing)
- pip (Python package manager)
- npm (Node package manager)

## Quick Start

### 1. Backend Setup (REST API)

#### Install Python Dependencies

```bash
# Install from pyproject.toml (recommended)
pip install -e .

# OR install from requirements.txt
pip install -r requirements.txt

# OR install packages individually
pip install fastapi uvicorn[standard] sqlalchemy pydantic
```

#### Run the Backend Server

```bash
# Start the FastAPI server
python main.py
```

The backend API will be available at:
- API Base URL: `http://localhost:8000`
- Interactive API Docs (Swagger): `http://localhost:8000/docs`
- Alternative API Docs (ReDoc): `http://localhost:8000/redoc`

### 2. Frontend Setup

#### Option A: Using Python's Built-in Server (Simple)

```bash
# From the project root directory
python3 -m http.server 8080
```

Then open your browser and navigate to: `http://localhost:8080`

#### Option B: Direct File Access

Simply open the `index.html` file directly in your browser:
```bash
# From the project root
open index.html  # macOS
xdg-open index.html  # Linux
start index.html  # Windows
```

#### Install Frontend Dependencies (for testing only)

```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

## Running Both Services Together

### Step-by-Step Instructions

1. **Terminal 1 - Start Backend:**
   ```bash
   # From project root
   python main.py
   ```
   You should see:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
   ```

2. **Terminal 2 - Start Frontend (if using Python server):**
   ```bash
   # From project root
   python3 -m http.server 8080
   ```
   You should see:
   ```
   Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
   ```

3. **Access the Application:**
   - Frontend UI: `http://localhost:8080` (if using Python server) or open `index.html` directly
   - Backend API: `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`

## Testing

### Backend Tests

```bash
# Run all backend tests
python -m pytest test_main.py -v

# Run with coverage report
python -m pytest test_main.py --cov=main --cov-report=term-missing

# Run specific test
python -m pytest test_main.py::test_create_todo -v
```

### Frontend Tests

```bash
cd frontend

# Run all frontend tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run tests in watch mode (for development)
npm run test:watch
```

## Debugging with Claude Code Transcripts

You can use the `claude-code-transcripts` tool to debug and analyze Claude Code sessions. This tool helps you review and understand the interactions between Claude and your codebase.

### Installation and Usage

```bash
# Run directly using uvx (no installation needed)
uvx claude-code-transcripts

# Or with a specific Claude Code session file
uvx claude-code-transcripts path/to/session.json
```

### What It Does

The `claude-code-transcripts` tool:
- Extracts and formats Claude Code conversation transcripts
- Shows the full conversation history including tool usage
- Helps debug issues by reviewing what commands were executed
- Provides insights into how Claude approached solving problems

### Example Usage for Debugging

```bash
# View the current session transcript
uvx claude-code-transcripts

# Save transcript to a file for analysis
uvx claude-code-transcripts > debug-transcript.md

# Search for specific operations in the transcript
uvx claude-code-transcripts | grep "Edit\|Write"
```

### When to Use

Use this tool when:
- You need to review what changes Claude made to your code
- Debugging unexpected behavior after Claude modifications
- Understanding the sequence of operations performed
- Sharing session details for troubleshooting
- Learning from Claude's problem-solving approach

For more information, see: https://simonwillison.net/2025/Dec/25/claude-code-transcripts/

## Development Mode

### Backend Development

For auto-reload during development:
```bash
# The main.py already includes reload=True when run directly
python main.py
```

### Frontend Development

The frontend is vanilla JavaScript, so changes are reflected immediately upon page refresh.

## Database

The application uses SQLite for data persistence:
- Database file: `todos.db` (created automatically on first run)
- Test database: `test_todos.db` (created during testing)

### Reset Database

To start with a fresh database:
```bash
# Remove the existing database
rm todos.db

# The database will be recreated when you restart the server
python main.py
```

## Troubleshooting

### Port Already in Use

If you see "Address already in use" error:

**Backend (port 8000):**
```bash
# Find and kill the process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

**Frontend (port 8080):**
```bash
# Find and kill the process using port 8080
lsof -i :8080
kill -9 <PID>

# Or use a different port
python3 -m http.server 8081
```

### CORS Issues

If the frontend cannot connect to the backend:
1. Ensure the backend is running on `http://localhost:8000`
2. Check that CORS is properly configured in `main.py`
3. Verify the frontend is making requests to the correct URL

### Missing Dependencies

**Python:**
```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

**Node.js:**
```bash
cd frontend
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Database Lock Issues

If you encounter "database is locked" errors:
1. Ensure only one instance of the application is running
2. Close any database management tools that might be accessing `todos.db`
3. Restart the backend server

## Project Structure

```
rest-api/
├── main.py              # Backend FastAPI application
├── test_main.py         # Backend test suite
├── todos.db             # SQLite database (auto-generated)
├── requirements.txt     # Python dependencies (minimal)
├── pyproject.toml       # Python project configuration
├── index.html           # Frontend HTML file
├── frontend/
│   ├── todo-app.js      # Frontend JavaScript logic
│   ├── todo-app.test.js # Frontend test suite
│   ├── package.json     # Node.js dependencies
│   └── README.md        # Frontend documentation
├── README.md            # Project documentation
└── HOW-TO-RUN.md        # This file
```

## Environment Variables

The application works with default settings, but you can customize:

```bash
# Backend
export UVICORN_HOST=0.0.0.0  # Listen on all interfaces
export UVICORN_PORT=8001     # Use different port

# Then run
python main.py
```

## API Endpoints Quick Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info and endpoints |
| POST | `/todos` | Create new todo |
| GET | `/todos` | Get all todos |
| GET | `/todos/{id}` | Get specific todo |
| PUT | `/todos/{id}` | Update todo |
| DELETE | `/todos/{id}` | Delete todo |

### Query Parameters for GET /todos

- `completed`: Filter by completion status (true/false)
- `skip`: Number of items to skip (pagination)
- `limit`: Maximum items to return (default: 100)

Example: `GET /todos?completed=true&skip=0&limit=10`

## Additional Notes

- The backend automatically creates the SQLite database on first run
- Frontend uses vanilla JavaScript with no build process required
- All API responses include appropriate HTTP status codes
- Text fields are automatically trimmed of whitespace
- Timestamps are automatically managed for creation and updates
- The application includes comprehensive error handling
- Test coverage requirements are set at 80% for the frontend

## Support

For issues or questions:
1. Check the main README.md for detailed API documentation
2. Review test files for usage examples
3. Check API documentation at `http://localhost:8000/docs` when server is running