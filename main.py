from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_mcp import FastApiMCP
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
import uvicorn
import logging
import json
import time
import traceback
from collections import defaultdict
import sys

# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        return json.dumps(log_obj)

# Set up logger
logger = logging.getLogger("todo_api")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

# Metrics storage
class Metrics:
    def __init__(self):
        self.request_count = 0
        self.error_count = 0
        self.endpoint_counts = defaultdict(int)
        self.endpoint_timings = defaultdict(list)
        self.status_code_counts = defaultdict(int)
        self.recent_errors = []
        self.start_time = datetime.utcnow()

    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        self.request_count += 1
        key = f"{method} {endpoint}"
        self.endpoint_counts[key] += 1
        self.endpoint_timings[key].append(duration)
        self.status_code_counts[status_code] += 1
        if status_code >= 400:
            self.error_count += 1

    def record_error(self, endpoint: str, method: str, error: Exception):
        error_info = {
            'timestamp': datetime.utcnow().isoformat(),
            'endpoint': endpoint,
            'method': method,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        self.recent_errors.append(error_info)
        # Keep only last 100 errors
        if len(self.recent_errors) > 100:
            self.recent_errors.pop(0)

    def get_stats(self) -> Dict[str, Any]:
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

        # Calculate average response times
        avg_timings = {}
        for endpoint, timings in self.endpoint_timings.items():
            if timings:
                avg_timings[endpoint] = {
                    'count': len(timings),
                    'avg_ms': sum(timings) / len(timings),
                    'min_ms': min(timings),
                    'max_ms': max(timings)
                }

        return {
            'uptime_seconds': uptime_seconds,
            'total_requests': self.request_count,
            'total_errors': self.error_count,
            'error_rate': self.error_count / max(self.request_count, 1),
            'endpoint_stats': dict(self.endpoint_counts),
            'response_times': avg_timings,
            'status_codes': dict(self.status_code_counts),
            'recent_errors': self.recent_errors[-10:]  # Last 10 errors
        }

metrics = Metrics()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./todos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class TodoDB(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic Models with Validation
class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Title of the todo")
    description: Optional[str] = Field(None, max_length=1000, description="Description of the todo")
    completed: bool = Field(False, description="Completion status")
    favorite: bool = Field(False, description="Favorite status")

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v or v.strip() == "":
            raise ValueError('Title cannot be empty or just whitespace')
        return v.strip()

    @validator('description')
    def clean_description(cls, v):
        if v:
            return v.strip()
        return v

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    completed: Optional[bool] = None
    favorite: Optional[bool] = None

    @validator('title')
    def title_must_not_be_empty(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('Title cannot be empty or just whitespace')
        return v.strip() if v else v

    @validator('description')
    def clean_description(cls, v):
        if v:
            return v.strip()
        return v

class TodoResponse(TodoBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title="Todo API", version="1.0.0", description="REST API for managing todos with observability")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Middleware for request logging and timing
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Generate request ID
    request_id = f"req_{int(time.time() * 1000000)}"

    # Log request
    logger.info("Request received", extra={'extra_fields': {
        'request_id': request_id,
        'method': request.method,
        'path': request.url.path,
        'client_host': request.client.host if request.client else None
    }})

    try:
        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Record metrics
        metrics.record_request(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration=duration
        )

        # Log response
        logger.info("Request completed", extra={'extra_fields': {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'status_code': response.status_code,
            'duration_ms': duration
        }})

        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.2f}ms"

        return response

    except Exception as e:
        duration = (time.time() - start_time) * 1000

        # Record error
        metrics.record_error(
            endpoint=request.url.path,
            method=request.method,
            error=e
        )

        # Log error
        logger.error("Request failed", extra={'extra_fields': {
            'request_id': request_id,
            'method': request.method,
            'path': request.url.path,
            'error': str(e),
            'error_type': type(e).__name__,
            'duration_ms': duration,
            'traceback': traceback.format_exc()
        }})

        # Return error response
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "request_id": request_id,
                "error": str(e)
            },
            headers={
                "X-Request-ID": request_id,
                "X-Response-Time": f"{duration:.2f}ms"
            }
        )

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check endpoint
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint for monitoring"""
    try:
        # Check database connectivity
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - metrics.start_time).total_seconds(),
        "components": {
            "database": db_status,
            "api": "healthy"
        }
    }

# Metrics endpoint
@app.get("/metrics")
def get_metrics():
    """Get API metrics and statistics"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics.get_stats()
    }

# CRUD Operations

@app.post("/todos", response_model=TodoResponse, status_code=201, operation_id="create_todo")
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item with title, optional description, completed status, and favorite flag"""
    logger.info("Creating todo", extra={'extra_fields': {
        'action': 'create_todo',
        'title': todo.title,
        'completed': todo.completed
    }})

    db_todo = TodoDB(
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        favorite=todo.favorite
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)

    logger.info("Todo created", extra={'extra_fields': {
        'action': 'todo_created',
        'todo_id': db_todo.id,
        'title': db_todo.title
    }})

    return db_todo

@app.get("/todos", response_model=List[TodoResponse], operation_id="list_todos")
def get_all_todos(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all todos with optional filtering by completed status and pagination (skip, limit)"""
    logger.info("Fetching todos", extra={'extra_fields': {
        'action': 'get_todos',
        'skip': skip,
        'limit': limit,
        'completed_filter': completed
    }})

    query = db.query(TodoDB)
    if completed is not None:
        query = query.filter(TodoDB.completed == completed)
    todos = query.offset(skip).limit(limit).all()

    logger.info("Todos fetched", extra={'extra_fields': {
        'action': 'todos_fetched',
        'count': len(todos)
    }})

    return todos

@app.get("/todos/{todo_id}", response_model=TodoResponse, operation_id="get_todo")
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo item by its ID"""
    logger.info("Fetching todo", extra={'extra_fields': {
        'action': 'get_todo',
        'todo_id': todo_id
    }})

    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        logger.warning("Todo not found", extra={'extra_fields': {
            'action': 'todo_not_found',
            'todo_id': todo_id
        }})
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")

    return todo

@app.put("/todos/{todo_id}", response_model=TodoResponse, operation_id="update_todo")
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)):
    """Update an existing todo item - can update title, description, completed status, or favorite flag"""
    logger.info("Updating todo", extra={'extra_fields': {
        'action': 'update_todo',
        'todo_id': todo_id,
        'updates': todo_update.dict(exclude_unset=True)
    }})

    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        logger.warning("Todo not found for update", extra={'extra_fields': {
            'action': 'todo_not_found',
            'todo_id': todo_id
        }})
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")

    # Only update provided fields
    if todo_update.title is not None:
        todo.title = todo_update.title
    if todo_update.description is not None:
        todo.description = todo_update.description
    if todo_update.completed is not None:
        todo.completed = todo_update.completed
    if todo_update.favorite is not None:
        todo.favorite = todo_update.favorite

    todo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(todo)

    logger.info("Todo updated", extra={'extra_fields': {
        'action': 'todo_updated',
        'todo_id': todo_id
    }})

    return todo

@app.delete("/todos/{todo_id}", status_code=204, operation_id="delete_todo")
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item by its ID"""
    logger.info("Deleting todo", extra={'extra_fields': {
        'action': 'delete_todo',
        'todo_id': todo_id
    }})

    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        logger.warning("Todo not found for deletion", extra={'extra_fields': {
            'action': 'todo_not_found',
            'todo_id': todo_id
        }})
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")

    db.delete(todo)
    db.commit()

    logger.info("Todo deleted", extra={'extra_fields': {
        'action': 'todo_deleted',
        'todo_id': todo_id
    }})

    return None

@app.get("/", operation_id="api_info")
def root():
    """Root endpoint with API information"""
    return {
        "message": "Todo REST API",
        "version": "1.0.0",
        "endpoints": {
            "POST /todos": "Create a new todo",
            "GET /todos": "Get all todos",
            "GET /todos/{id}": "Get a specific todo",
            "PUT /todos/{id}": "Update a todo",
            "DELETE /todos/{id}": "Delete a todo",
            "GET /health": "Health check endpoint",
            "GET /metrics": "API metrics and statistics"
        },
        "mcp_server": "/mcp (MCP server for AI agents)"
    }

# Initialize MCP server
# This exposes the FastAPI endpoints as MCP tools for AI agents
mcp = FastApiMCP(
    app,
    name="Todo MCP Server",
    description="MCP server for managing todos - provides tools to create, read, update, and delete todo items",
    # Only include the CRUD operations as MCP tools, not health/metrics/root
    include_operations=["create_todo", "list_todos", "get_todo", "update_todo", "delete_todo"]
)

# Mount the MCP server at /mcp using HTTP transport (recommended)
mcp.mount_http()

if __name__ == "__main__":
    logger.info("Starting Todo API server", extra={'extra_fields': {
        'action': 'server_start',
        'port': 8000
    }})
    # Use string import to allow reload to work properly with MCP routes
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)