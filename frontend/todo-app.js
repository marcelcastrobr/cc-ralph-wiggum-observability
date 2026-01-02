// API Configuration
const API_URL = window.API_URL || 'http://localhost:8000';

// State management
let todos = [];

// Utility functions
const showError = (message) => {
    const errorEl = document.getElementById('errorMessage');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
        setTimeout(() => {
            errorEl.style.display = 'none';
        }, 5000);
    }
};

const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
};

// API functions
const api = {
    async getTodos() {
        try {
            const response = await fetch(`${API_URL}/todos`);
            if (!response.ok) throw new Error('Failed to fetch todos');
            return await response.json();
        } catch (error) {
            showError('Failed to load todos. Please check if the API is running.');
            throw error;
        }
    },

    async createTodo(todo) {
        try {
            const response = await fetch(`${API_URL}/todos`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(todo)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create todo');
            }
            return await response.json();
        } catch (error) {
            showError(error.message || 'Failed to create todo');
            throw error;
        }
    },

    async updateTodo(id, updates) {
        try {
            const response = await fetch(`${API_URL}/todos/${id}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updates)
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to update todo');
            }
            return await response.json();
        } catch (error) {
            showError(error.message || 'Failed to update todo');
            throw error;
        }
    },

    async deleteTodo(id) {
        try {
            const response = await fetch(`${API_URL}/todos/${id}`, {
                method: 'DELETE'
            });
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to delete todo');
            }
        } catch (error) {
            showError(error.message || 'Failed to delete todo');
            throw error;
        }
    }
};

// UI functions
const renderTodos = () => {
    const todoListEl = document.getElementById('todoList');
    if (!todoListEl) return;

    if (todos.length === 0) {
        todoListEl.innerHTML = `
            <div class="empty-state">
                <p>No tasks yet. Add your first task above!</p>
            </div>
        `;
        return;
    }

    // Sort todos: favorites first, then by created date
    const sortedTodos = [...todos].sort((a, b) => {
        if (a.favorite && !b.favorite) return -1;
        if (!a.favorite && b.favorite) return 1;
        return new Date(b.created_at) - new Date(a.created_at);
    });

    todoListEl.innerHTML = sortedTodos.map(todo => `
        <div class="todo-item ${todo.completed ? 'completed' : ''}" data-id="${todo.id}">
            <input
                type="checkbox"
                class="todo-checkbox"
                ${todo.completed ? 'checked' : ''}
                onchange="toggleComplete(${todo.id})"
            >
            <div class="todo-content">
                <div class="todo-text">${escapeHtml(todo.title)}</div>
                ${todo.description ? `<div class="todo-description">${escapeHtml(todo.description)}</div>` : ''}
            </div>
            <div class="todo-actions">
                <button
                    class="btn-star ${todo.favorite ? 'active' : ''}"
                    onclick="toggleFavorite(${todo.id})"
                    title="${todo.favorite ? 'Remove from favorites' : 'Add to favorites'}"
                >
                    ${todo.favorite ? '⭐' : '☆'}
                </button>
                <button
                    class="btn-delete"
                    onclick="deleteTodo(${todo.id})"
                    title="Delete todo"
                >
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
};

// Event handlers
const loadTodos = async () => {
    try {
        todos = await api.getTodos();
        renderTodos();
    } catch (error) {
        console.error('Failed to load todos:', error);
    }
};

const addTodo = async (event) => {
    if (event) event.preventDefault();

    const titleInput = document.getElementById('todoTitle');
    const descriptionInput = document.getElementById('todoDescription');

    if (!titleInput) return;

    const title = titleInput.value.trim();
    const description = descriptionInput ? descriptionInput.value.trim() : '';

    if (!title) {
        showError('Please enter a title');
        return;
    }

    try {
        const newTodo = await api.createTodo({
            title,
            description: description || null,
            completed: false,
            favorite: false
        });

        todos.push(newTodo);
        renderTodos();

        // Clear form
        titleInput.value = '';
        if (descriptionInput) descriptionInput.value = '';
        titleInput.focus();
    } catch (error) {
        console.error('Failed to add todo:', error);
    }
};

const toggleComplete = async (id) => {
    const todo = todos.find(t => t.id === id);
    if (!todo) return;

    try {
        const updated = await api.updateTodo(id, {
            completed: !todo.completed
        });

        const index = todos.findIndex(t => t.id === id);
        todos[index] = updated;
        renderTodos();
    } catch (error) {
        console.error('Failed to toggle complete:', error);
        renderTodos(); // Re-render to restore original state
    }
};

const toggleFavorite = async (id) => {
    const todo = todos.find(t => t.id === id);
    if (!todo) return;

    try {
        const updated = await api.updateTodo(id, {
            favorite: !todo.favorite
        });

        const index = todos.findIndex(t => t.id === id);
        todos[index] = updated;
        renderTodos();
    } catch (error) {
        console.error('Failed to toggle favorite:', error);
    }
};

const deleteTodo = async (id) => {
    if (!window.confirm || !window.confirm('Are you sure you want to delete this task?')) {
        return;
    }

    try {
        await api.deleteTodo(id);
        todos = todos.filter(t => t.id !== id);
        renderTodos();
    } catch (error) {
        console.error('Failed to delete todo:', error);
    }
};

// Make functions globally available
if (typeof window !== 'undefined') {
    window.toggleComplete = toggleComplete;
    window.toggleFavorite = toggleFavorite;
    window.deleteTodo = deleteTodo;
    window.todoApp = {
        api,
        todos,
        showError,
        escapeHtml,
        renderTodos,
        loadTodos,
        addTodo,
        toggleComplete,
        toggleFavorite,
        deleteTodo
    };
}

// Initialize app
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('addTodoForm');
        if (form) {
            form.addEventListener('submit', addTodo);
        }
        loadTodos();
    });
}

// Export for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        api,
        showError,
        escapeHtml,
        renderTodos,
        loadTodos,
        addTodo,
        toggleComplete,
        toggleFavorite,
        deleteTodo
    };
}