# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Todo REST API application built with FastAPI (Python backend) and vanilla JavaScript (frontend). The project uses SQLite for persistence and includes comprehensive test suites for both backend and frontend.

## Essential Commands

### Backend Commands

```bash
# Install dependencies (use one of these):
pip install -e .                    # Install from pyproject.toml (recommended)
pip install -r requirements.txt      # Install minimal dependencies (boto3/botocore only)

# Run the backend server
python main.py                       # Starts FastAPI server on http://localhost:8000

# Run backend tests
python -m pytest test_main.py -v                                    # Run all tests
python -m pytest test_main.py --cov=main --cov-report=term-missing  # With coverage
python -m pytest test_main.py::test_create_todo -v                  # Run specific test
```

### Frontend Commands

```bash
# Navigate to frontend directory first
cd frontend

# Install Node.js dependencies (for testing only)
npm install

# Run frontend tests
npm test                             # Run all tests with coverage
npm run test:watch                   # Run tests in watch mode

# Serve frontend (from project root)
python3 -m http.server 8080          # Serves on http://localhost:8080
```

## Architecture Overview

### Backend Structure (FastAPI)

The backend (`main.py`) implements a REST API with the following key components:

1. **Database Layer**: SQLAlchemy ORM with SQLite
   - `TodoDB` model defines the database schema
   - Auto-creates `todos.db` on first run
   - Handles timestamps automatically (created_at, updated_at)

2. **Validation Layer**: Pydantic models
   - `TodoBase`, `TodoCreate`, `TodoUpdate`, `TodoResponse` models
   - Automatic validation and trimming of text fields
   - Title: required, 1-200 chars, cannot be empty/whitespace
   - Description: optional, max 1000 chars

3. **API Endpoints**:
   - `POST /todos` - Create todo (returns 201)
   - `GET /todos` - List todos with optional filtering by `completed` status
   - `GET /todos/{id}` - Get specific todo
   - `PUT /todos/{id}` - Update todo (partial updates supported)
   - `DELETE /todos/{id}` - Delete todo (returns 204)

4. **CORS Configuration**: Enabled for all origins (development mode)

### Frontend Structure

Located in `/frontend/` directory:
- `index.html` - Main UI (can be opened directly or served)
- `todo-app.js` - JavaScript logic for API interaction
- `todo-app.test.js` - Jest test suite with 80% coverage requirement

### Database

- SQLite database: `todos.db` (production), `test_todos.db` (testing)
- Schema includes: id, title, description, completed, favorite, created_at, updated_at
- To reset: `rm todos.db` and restart server

## Development Workflow

### Running Both Services

1. **Terminal 1**: Start backend
   ```bash
   python main.py
   ```

2. **Terminal 2**: Serve frontend (optional)
   ```bash
   python3 -m http.server 8080
   ```
   Or open `frontend/index.html` directly in browser

3. Access:
   - Frontend: http://localhost:8080 or open index.html
   - API Docs: http://localhost:8000/docs (Swagger UI)
   - API: http://localhost:8000

### Testing Guidelines

- Backend tests use pytest with test database isolation
- Frontend tests require `npm install` in frontend directory first
- Both test suites include validation, error handling, and edge cases
- Frontend has 80% coverage requirement configured in package.json

## Claude Code Ralph Wiggum Plugin Context

This repository appears to be testing the Claude Code Ralph Wiggum plugin with observability features. The `HOW-CLAUDECODE-BUIL-IT.md` file indicates this is specifically for testing loop functionality in Claude Code.

## Important Notes

- The `requirements.txt` only contains boto3/botocore, but the actual dependencies are in `pyproject.toml`
- Backend auto-reloads in development mode (reload=True in main.py)
- All text fields are automatically trimmed of whitespace
- CORS is configured for all origins (development setup)
- Frontend is vanilla JavaScript with no build process required