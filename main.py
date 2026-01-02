from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import uvicorn

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
app = FastAPI(title="Todo API", version="1.0.0", description="REST API for managing todos")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD Operations

@app.post("/todos", response_model=TodoResponse, status_code=201)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db)):
    """Create a new todo item with validation"""
    db_todo = TodoDB(
        title=todo.title,
        description=todo.description,
        completed=todo.completed,
        favorite=todo.favorite
    )
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

@app.get("/todos", response_model=List[TodoResponse])
def get_all_todos(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """Get all todos with optional filtering and pagination"""
    query = db.query(TodoDB)
    if completed is not None:
        query = query.filter(TodoDB.completed == completed)
    todos = query.offset(skip).limit(limit).all()
    return todos

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    """Get a specific todo by ID"""
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")
    return todo

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo(todo_id: int, todo_update: TodoUpdate, db: Session = Depends(get_db)):
    """Update a todo item with validation"""
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
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
    return todo

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    """Delete a todo item"""
    todo = db.query(TodoDB).filter(TodoDB.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail=f"Todo with id {todo_id} not found")

    db.delete(todo)
    db.commit()
    return None

@app.get("/")
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
            "DELETE /todos/{id}": "Delete a todo"
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)