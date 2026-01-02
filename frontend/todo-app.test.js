/**
 * @jest-environment jsdom
 */

const {
    api,
    showError,
    escapeHtml,
    renderTodos,
    loadTodos,
    addTodo,
    toggleComplete,
    toggleFavorite,
    deleteTodo
} = require('./todo-app.js');

// Mock fetch globally
global.fetch = jest.fn();
global.window.API_URL = 'http://localhost:8000';
global.window.confirm = jest.fn();

// Initialize global todos array
global.todos = [];

describe('Todo App', () => {
    beforeEach(() => {
        // Reset DOM for each test
        document.body.innerHTML = `
            <div id="errorMessage"></div>
            <div id="todoList"></div>
            <form id="addTodoForm">
                <input id="todoTitle" />
                <input id="todoDescription" />
            </form>
        `;

        // Clear all mocks before each test
        jest.clearAllMocks();
        // Reset todos
        global.todos = [];
        // Clear error message
        const errorEl = document.getElementById('errorMessage');
        if (errorEl) {
            errorEl.style.display = 'none';
        }
    });

    describe('Utility Functions', () => {
        describe('showError', () => {
            it('should display error message', () => {
                const errorEl = document.getElementById('errorMessage');
                showError('Test error');

                expect(errorEl.textContent).toBe('Test error');
                expect(errorEl.style.display).toBe('block');
            });

            it('should hide error message after 5 seconds', () => {
                jest.useFakeTimers();
                const errorEl = document.getElementById('errorMessage');

                showError('Test error');
                expect(errorEl.style.display).toBe('block');

                jest.advanceTimersByTime(5000);
                expect(errorEl.style.display).toBe('none');

                jest.useRealTimers();
            });

            it('should handle missing error element gracefully', () => {
                const errorEl = document.getElementById('errorMessage');
                errorEl.remove();

                expect(() => showError('Test error')).not.toThrow();
            });
        });

        describe('escapeHtml', () => {
            it('should escape HTML characters', () => {
                expect(escapeHtml('<script>alert("XSS")</script>')).toBe(
                    '&lt;script&gt;alert("XSS")&lt;/script&gt;'
                );
                expect(escapeHtml('Test & "quotes"')).toBe('Test &amp; "quotes"');
            });

            it('should handle empty string', () => {
                expect(escapeHtml('')).toBe('');
            });

            it('should handle plain text', () => {
                expect(escapeHtml('Plain text')).toBe('Plain text');
            });
        });
    });

    describe('API Functions', () => {
        describe('getTodos', () => {
            it('should fetch todos successfully', async () => {
                const mockTodos = [
                    { id: 1, title: 'Test Todo', completed: false }
                ];

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => mockTodos
                });

                const result = await api.getTodos();

                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos');
                expect(result).toEqual(mockTodos);
            });

            it('should handle fetch error', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false
                });

                await expect(api.getTodos()).rejects.toThrow('Failed to fetch todos');
            });

            it('should handle network error', async () => {
                fetch.mockRejectedValueOnce(new Error('Network error'));

                await expect(api.getTodos()).rejects.toThrow('Network error');
            });
        });

        describe('createTodo', () => {
            it('should create todo successfully', async () => {
                const newTodo = { title: 'New Todo', description: 'Test', completed: false };
                const createdTodo = { id: 1, ...newTodo };

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => createdTodo
                });

                const result = await api.createTodo(newTodo);

                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(newTodo)
                });
                expect(result).toEqual(createdTodo);
            });

            it('should handle create error with detail', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false,
                    json: async () => ({ detail: 'Validation error' })
                });

                await expect(api.createTodo({ title: '' })).rejects.toThrow('Validation error');
            });

            it('should handle create error without detail', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false,
                    json: async () => ({})
                });

                await expect(api.createTodo({ title: 'Test' })).rejects.toThrow('Failed to create todo');
            });
        });

        describe('updateTodo', () => {
            it('should update todo successfully', async () => {
                const updates = { completed: true };
                const updatedTodo = { id: 1, title: 'Test', completed: true };

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => updatedTodo
                });

                const result = await api.updateTodo(1, updates);

                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos/1', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(updates)
                });
                expect(result).toEqual(updatedTodo);
            });

            it('should handle update error', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false,
                    json: async () => ({ detail: 'Todo not found' })
                });

                await expect(api.updateTodo(999, {})).rejects.toThrow('Todo not found');
            });
        });

        describe('deleteTodo', () => {
            it('should delete todo successfully', async () => {
                fetch.mockResolvedValueOnce({
                    ok: true
                });

                await api.deleteTodo(1);

                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos/1', {
                    method: 'DELETE'
                });
            });

            it('should handle delete error', async () => {
                fetch.mockResolvedValueOnce({
                    ok: false,
                    json: async () => ({ detail: 'Todo not found' })
                });

                await expect(api.deleteTodo(999)).rejects.toThrow('Todo not found');
            });
        });
    });

    describe('UI Functions', () => {
        describe('renderTodos', () => {
            it('should render empty state when no todos', () => {
                const todoListEl = document.getElementById('todoList');
                global.todos = [];

                renderTodos();

                expect(todoListEl.innerHTML).toContain('No tasks yet');
            });

            it('should render todos correctly', () => {
                const todoListEl = document.getElementById('todoList');
                global.todos = [
                    {
                        id: 1,
                        title: 'Test Todo',
                        description: 'Test Description',
                        completed: false,
                        favorite: false,
                        created_at: '2024-01-01T00:00:00'
                    },
                    {
                        id: 2,
                        title: 'Favorite Todo',
                        description: null,
                        completed: true,
                        favorite: true,
                        created_at: '2024-01-02T00:00:00'
                    }
                ];

                renderTodos();

                const html = todoListEl.innerHTML;
                expect(html).toContain('Test Todo');
                expect(html).toContain('Test Description');
                expect(html).toContain('Favorite Todo');
                expect(html).toContain('⭐');
                expect(html).toContain('☆');
                expect(html).toContain('completed');
            });

            it('should sort todos with favorites first', () => {
                global.todos = [
                    {
                        id: 1,
                        title: 'Regular Todo',
                        favorite: false,
                        created_at: '2024-01-02T00:00:00'
                    },
                    {
                        id: 2,
                        title: 'Favorite Todo',
                        favorite: true,
                        created_at: '2024-01-01T00:00:00'
                    }
                ];

                renderTodos();

                const todoItems = document.querySelectorAll('.todo-item');
                expect(todoItems[0].getAttribute('data-id')).toBe('2');
                expect(todoItems[1].getAttribute('data-id')).toBe('1');
            });

            it('should escape HTML in todo titles and descriptions', () => {
                global.todos = [
                    {
                        id: 1,
                        title: '<script>alert("XSS")</script>',
                        description: '<img src=x onerror=alert("XSS")>',
                        completed: false,
                        favorite: false,
                        created_at: '2024-01-01T00:00:00'
                    }
                ];

                renderTodos();

                const html = document.getElementById('todoList').innerHTML;
                expect(html).not.toContain('<script>');
                expect(html).not.toContain('<img');
                expect(html).toContain('&lt;script&gt;');
                expect(html).toContain('&lt;img');
            });

            it('should handle missing todoList element', () => {
                document.getElementById('todoList').remove();
                global.todos = [{ id: 1, title: 'Test' }];

                expect(() => renderTodos()).not.toThrow();
            });
        });

        describe('loadTodos', () => {
            it('should load and render todos', async () => {
                const mockTodos = [
                    { id: 1, title: 'Test Todo', completed: false }
                ];

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => mockTodos
                });

                await loadTodos();

                expect(global.todos).toEqual(mockTodos);
                expect(document.getElementById('todoList').innerHTML).toContain('Test Todo');
            });

            it('should handle load error gracefully', async () => {
                fetch.mockRejectedValueOnce(new Error('Network error'));

                await loadTodos();

                expect(global.todos).toEqual([]);
            });
        });

        describe('addTodo', () => {
            it('should add todo successfully', async () => {
                const titleInput = document.getElementById('todoTitle');
                const descriptionInput = document.getElementById('todoDescription');

                titleInput.value = '  New Todo  ';
                descriptionInput.value = '  Description  ';

                const createdTodo = {
                    id: 1,
                    title: 'New Todo',
                    description: 'Description',
                    completed: false,
                    favorite: false
                };

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => createdTodo
                });

                const event = { preventDefault: jest.fn() };
                await addTodo(event);

                expect(event.preventDefault).toHaveBeenCalled();
                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        title: 'New Todo',
                        description: 'Description',
                        completed: false,
                        favorite: false
                    })
                });

                expect(global.todos).toContainEqual(createdTodo);
                expect(titleInput.value).toBe('');
                expect(descriptionInput.value).toBe('');
            });

            it('should handle empty title', async () => {
                const titleInput = document.getElementById('todoTitle');
                titleInput.value = '   ';

                const event = { preventDefault: jest.fn() };
                await addTodo(event);

                expect(fetch).not.toHaveBeenCalled();
                expect(document.getElementById('errorMessage').textContent).toBe('Please enter a title');
            });

            it('should handle missing inputs gracefully', async () => {
                document.getElementById('todoTitle').remove();

                await addTodo();

                expect(fetch).not.toHaveBeenCalled();
            });

            it('should handle API error', async () => {
                const titleInput = document.getElementById('todoTitle');
                titleInput.value = 'Test';

                fetch.mockRejectedValueOnce(new Error('API Error'));

                await addTodo();

                expect(global.todos).toEqual([]);
            });

            it('should handle empty description as null', async () => {
                const titleInput = document.getElementById('todoTitle');
                const descriptionInput = document.getElementById('todoDescription');

                titleInput.value = 'Test';
                descriptionInput.value = '   ';

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => ({ id: 1, title: 'Test', description: null })
                });

                await addTodo();

                const call = fetch.mock.calls[0];
                const body = JSON.parse(call[1].body);
                expect(body.description).toBeNull();
            });
        });

        describe('toggleComplete', () => {
            it('should toggle todo completion', async () => {
                global.todos = [
                    { id: 1, title: 'Test', completed: false }
                ];

                const updatedTodo = { id: 1, title: 'Test', completed: true };

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => updatedTodo
                });

                await toggleComplete(1);

                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos/1', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ completed: true })
                });

                expect(global.todos[0].completed).toBe(true);
            });

            it('should handle non-existent todo', async () => {
                global.todos = [];

                await toggleComplete(999);

                expect(fetch).not.toHaveBeenCalled();
            });

            it('should revert on error', async () => {
                global.todos = [
                    { id: 1, title: 'Test', completed: false }
                ];

                fetch.mockRejectedValueOnce(new Error('API Error'));

                await toggleComplete(1);

                expect(global.todos[0].completed).toBe(false);
            });
        });

        describe('toggleFavorite', () => {
            it('should toggle todo favorite status', async () => {
                global.todos = [
                    { id: 1, title: 'Test', favorite: false }
                ];

                const updatedTodo = { id: 1, title: 'Test', favorite: true };

                fetch.mockResolvedValueOnce({
                    ok: true,
                    json: async () => updatedTodo
                });

                await toggleFavorite(1);

                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos/1', {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ favorite: true })
                });

                expect(global.todos[0].favorite).toBe(true);
            });

            it('should handle non-existent todo', async () => {
                global.todos = [];

                await toggleFavorite(999);

                expect(fetch).not.toHaveBeenCalled();
            });

            it('should handle API error', async () => {
                global.todos = [
                    { id: 1, title: 'Test', favorite: false }
                ];

                fetch.mockRejectedValueOnce(new Error('API Error'));

                await toggleFavorite(1);

                expect(global.todos[0].favorite).toBe(false);
            });
        });

        describe('deleteTodo', () => {
            it('should delete todo after confirmation', async () => {
                global.todos = [
                    { id: 1, title: 'Test' },
                    { id: 2, title: 'Keep' }
                ];

                window.confirm.mockReturnValueOnce(true);

                fetch.mockResolvedValueOnce({ ok: true });

                await deleteTodo(1);

                expect(window.confirm).toHaveBeenCalledWith('Are you sure you want to delete this task?');
                expect(fetch).toHaveBeenCalledWith('http://localhost:8000/todos/1', {
                    method: 'DELETE'
                });

                expect(global.todos).toEqual([
                    { id: 2, title: 'Keep' }
                ]);
            });

            it('should not delete if cancelled', async () => {
                global.todos = [
                    { id: 1, title: 'Test' }
                ];

                window.confirm.mockReturnValueOnce(false);

                await deleteTodo(1);

                expect(fetch).not.toHaveBeenCalled();
                expect(global.todos).toHaveLength(1);
            });

            it('should handle missing confirm function', async () => {
                global.todos = [
                    { id: 1, title: 'Test' }
                ];

                delete window.confirm;

                await deleteTodo(1);

                expect(fetch).not.toHaveBeenCalled();
                expect(global.todos).toHaveLength(1);
            });

            it('should handle API error', async () => {
                global.todos = [
                    { id: 1, title: 'Test' }
                ];

                window.confirm = jest.fn().mockReturnValueOnce(true);
                fetch.mockRejectedValueOnce(new Error('API Error'));

                await deleteTodo(1);

                expect(global.todos).toHaveLength(1);
            });
        });
    });

    describe('Global Exports', () => {
        it('should expose functions globally', () => {
            expect(window.toggleComplete).toBe(toggleComplete);
            expect(window.toggleFavorite).toBe(toggleFavorite);
            expect(window.deleteTodo).toBe(deleteTodo);

            // Check if todoApp is defined after module loads
            if (window.todoApp) {
                expect(window.todoApp).toBeDefined();
                expect(window.todoApp.api).toBe(api);
            }
        });
    });
});