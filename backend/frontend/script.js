/**
 * Task Management Frontend Application
 * Handles authentication and task CRUD operations
 */

// ========================================
// Configuration
// ========================================
const API_BASE_URL = 'http://localhost:5000/api/v1';

// ========================================
// State Management
// ========================================
let currentUser = null;
let currentPage = 1;
let itemsPerPage = 10;
let taskToDelete = null;

// ========================================
// Utility Functions
// ========================================

/**
 * Get stored JWT token
 */
function getToken() {
    return localStorage.getItem('token');
}

/**
 * Store JWT token
 */
function setToken(token) {
    localStorage.setItem('token', token);
}

/**
 * Remove stored token
 */
function removeToken() {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
}

/**
 * Store user data
 */
function setUser(user) {
    localStorage.setItem('user', JSON.stringify(user));
    currentUser = user;
}

/**
 * Get stored user data
 */
function getUser() {
    const user = localStorage.getItem('user');
    return user ? JSON.parse(user) : null;
}

/**
 * Check if user is authenticated
 */
function isAuthenticated() {
    return !!getToken();
}

/**
 * Make authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const defaultHeaders = {
        'Content-Type': 'application/json'
    };
    
    const token = getToken();
    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }
    
    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };
    
    try {
        const response = await fetch(url, config);
        const data = await response.json();
        
        // Handle expired or invalid token
        if (response.status === 401 && token) {
            removeToken();
            window.location.href = 'index.html';
            return null;
        }
        
        return {
            ok: response.ok,
            status: response.status,
            data: data
        };
    } catch (error) {
        console.error('API Request Error:', error);
        return {
            ok: false,
            status: 0,
            data: { error: 'Network error. Please try again.' }
        };
    }
}

/**
 * Display message to user
 */
function showMessage(message, type = 'info') {
    const messageEl = document.getElementById('message');
    if (!messageEl) return;
    
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 5000);
}

/**
 * Format date for display
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// ========================================
// Authentication Functions
// ========================================

/**
 * Handle user registration
 */
async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('register-name').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const password = document.getElementById('register-password').value;
    const role = document.getElementById('register-role').value;
    
    if (!name || !email || !password) {
        showMessage('Please fill in all fields', 'error');
        return;
    }
    
    const response = await apiRequest('/auth/register', {
        method: 'POST',
        body: JSON.stringify({ name, email, password, role })
    });
    
    if (response.ok) {
        showMessage('Registration successful! Please login.', 'success');
        // Switch to login tab
        document.querySelector('[data-tab="login"]').click();
        // Clear form
        document.getElementById('register-form').reset();
    } else {
        showMessage(response.data.error || 'Registration failed', 'error');
    }
}

/**
 * Handle user login
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value;
    
    if (!email || !password) {
        showMessage('Please enter email and password', 'error');
        return;
    }
    
    const response = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
    });
    
    if (response.ok) {
        setToken(response.data.data.token);
        setUser(response.data.data.user);
        showMessage('Login successful!', 'success');
        
        // Redirect to dashboard
        setTimeout(() => {
            window.location.href = 'dashboard.html';
        }, 500);
    } else {
        showMessage(response.data.error || 'Login failed', 'error');
    }
}

/**
 * Handle user logout
 */
async function handleLogout() {
    await apiRequest('/auth/logout', { method: 'POST' });
    removeToken();
    window.location.href = 'index.html';
}

// ========================================
// Task Functions
// ========================================

/**
 * Load and display tasks
 */
async function loadTasks() {
    const container = document.getElementById('tasks-container');
    const statusFilter = document.getElementById('filter-status').value;
    const showAll = document.getElementById('show-all-tasks')?.checked || false;
    
    container.innerHTML = '<p class="loading">Loading tasks...</p>';
    
    let endpoint = `/tasks?page=${currentPage}&limit=${itemsPerPage}`;
    
    if (statusFilter) {
        endpoint += `&status=${statusFilter}`;
    }
    
    if (showAll && currentUser?.role === 'admin') {
        endpoint += '&all=true';
    }
    
    const response = await apiRequest(endpoint);
    
    if (response.ok) {
        const { tasks, pagination } = response.data.data;
        
        if (tasks.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>No tasks found</h3>
                    <p>Create your first task using the form above.</p>
                </div>
            `;
        } else {
            container.innerHTML = tasks.map(task => createTaskCard(task)).join('');
            
            // Add event listeners to task buttons
            attachTaskEventListeners();
        }
        
        // Update pagination
        updatePagination(pagination);
    } else {
        container.innerHTML = '<p class="error">Failed to load tasks</p>';
        showMessage(response.data.error || 'Failed to load tasks', 'error');
    }
}

/**
 * Create HTML for a task card
 */
function createTaskCard(task) {
    const isOwner = task.user_id === currentUser?.id;
    const canEdit = isOwner;
    const canDelete = isOwner || currentUser?.role === 'admin';
    
    return `
        <div class="task-card ${task.status}" data-task-id="${task.id}">
            <div class="task-info">
                <div class="task-title">${escapeHtml(task.title)}</div>
                ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ''}
                <div class="task-meta">
                    <span class="status-badge ${task.status}">${formatStatus(task.status)}</span>
                    <span>Created: ${formatDate(task.created_at)}</span>
                    ${currentUser?.role === 'admin' ? `<span>User ID: ${task.user_id}</span>` : ''}
                </div>
            </div>
            <div class="task-actions">
                ${canEdit ? `<button class="btn btn-sm btn-primary edit-task-btn" data-task-id="${task.id}">Edit</button>` : ''}
                ${canDelete ? `<button class="btn btn-sm btn-danger delete-task-btn" data-task-id="${task.id}">Delete</button>` : ''}
            </div>
        </div>
    `;
}

/**
 * Format status for display
 */
function formatStatus(status) {
    return status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Attach event listeners to task buttons
 */
function attachTaskEventListeners() {
    // Edit buttons
    document.querySelectorAll('.edit-task-btn').forEach(btn => {
        btn.addEventListener('click', () => editTask(btn.dataset.taskId));
    });
    
    // Delete buttons
    document.querySelectorAll('.delete-task-btn').forEach(btn => {
        btn.addEventListener('click', () => confirmDeleteTask(btn.dataset.taskId));
    });
}

/**
 * Update pagination controls
 */
function updatePagination(pagination) {
    const paginationEl = document.getElementById('pagination');
    const prevBtn = document.getElementById('prev-page');
    const nextBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    if (pagination.pages <= 1) {
        paginationEl.classList.add('hidden');
        return;
    }
    
    paginationEl.classList.remove('hidden');
    pageInfo.textContent = `Page ${pagination.page} of ${pagination.pages}`;
    
    prevBtn.disabled = pagination.page <= 1;
    nextBtn.disabled = pagination.page >= pagination.pages;
}

/**
 * Handle task form submission
 */
async function handleTaskSubmit(event) {
    event.preventDefault();
    
    const taskId = document.getElementById('task-id').value;
    const title = document.getElementById('task-title').value.trim();
    const description = document.getElementById('task-description').value.trim();
    const status = document.getElementById('task-status').value;
    
    if (!title) {
        showMessage('Task title is required', 'error');
        return;
    }
    
    const taskData = { title, description, status };
    
    let response;
    
    if (taskId) {
        // Update existing task
        response = await apiRequest(`/tasks/${taskId}`, {
            method: 'PUT',
            body: JSON.stringify(taskData)
        });
    } else {
        // Create new task
        response = await apiRequest('/tasks', {
            method: 'POST',
            body: JSON.stringify(taskData)
        });
    }
    
    if (response.ok) {
        showMessage(taskId ? 'Task updated successfully' : 'Task created successfully', 'success');
        resetTaskForm();
        loadTasks();
    } else {
        showMessage(response.data.error || 'Operation failed', 'error');
    }
}

/**
 * Load task for editing
 */
async function editTask(taskId) {
    const response = await apiRequest(`/tasks/${taskId}`);
    
    if (response.ok) {
        const task = response.data.data;
        
        document.getElementById('task-id').value = task.id;
        document.getElementById('task-title').value = task.title;
        document.getElementById('task-description').value = task.description || '';
        document.getElementById('task-status').value = task.status;
        
        document.getElementById('form-title').textContent = 'Edit Task';
        document.getElementById('submit-btn').textContent = 'Update Task';
        document.getElementById('cancel-btn').classList.remove('hidden');
        
        // Scroll to form
        document.getElementById('task-form').scrollIntoView({ behavior: 'smooth' });
    } else {
        showMessage(response.data.error || 'Failed to load task', 'error');
    }
}

/**
 * Reset task form to create mode
 */
function resetTaskForm() {
    document.getElementById('task-form').reset();
    document.getElementById('task-id').value = '';
    document.getElementById('form-title').textContent = 'Create New Task';
    document.getElementById('submit-btn').textContent = 'Create Task';
    document.getElementById('cancel-btn').classList.add('hidden');
}

/**
 * Show delete confirmation modal
 */
function confirmDeleteTask(taskId) {
    taskToDelete = taskId;
    document.getElementById('delete-modal').classList.remove('hidden');
}

/**
 * Hide delete confirmation modal
 */
function hideDeleteModal() {
    taskToDelete = null;
    document.getElementById('delete-modal').classList.add('hidden');
}

/**
 * Delete a task
 */
async function deleteTask() {
    if (!taskToDelete) return;
    
    const isAdmin = currentUser?.role === 'admin';
    const endpoint = isAdmin ? `/tasks/admin/${taskToDelete}` : `/tasks/${taskToDelete}`;
    
    const response = await apiRequest(endpoint, { method: 'DELETE' });
    
    if (response.ok) {
        showMessage('Task deleted successfully', 'success');
        loadTasks();
    } else {
        showMessage(response.data.error || 'Failed to delete task', 'error');
    }
    
    hideDeleteModal();
}

// ========================================
// Admin Functions
// ========================================

/**
 * Load admin dashboard data
 */
async function loadAdminData() {
    if (currentUser?.role !== 'admin') return;
    
    // Show admin section
    document.getElementById('admin-section').classList.remove('hidden');
    document.getElementById('admin-filter').classList.remove('hidden');
    
    // Load users
    const usersResponse = await apiRequest('/auth/users');
    
    if (usersResponse.ok) {
        const users = usersResponse.data.data.users;
        document.getElementById('total-users').textContent = users.length;
        
        const usersList = document.getElementById('users-list');
        usersList.innerHTML = users.map(user => `
            <div class="user-card">
                <div class="user-details">
                    <span class="user-email">${escapeHtml(user.email)}</span>
                    <span class="user-name">${escapeHtml(user.name)}</span>
                </div>
                <span class="role-badge ${user.role}">${user.role}</span>
            </div>
        `).join('');
    }
    
    // Load all tasks count
    const tasksResponse = await apiRequest('/tasks/admin/all');
    
    if (tasksResponse.ok) {
        document.getElementById('total-tasks').textContent = tasksResponse.data.data.total;
    }
}

// ========================================
// Dashboard Initialization
// ========================================

/**
 * Initialize dashboard page
 */
async function initDashboard() {
    // Check authentication
    if (!isAuthenticated()) {
        window.location.href = 'index.html';
        return;
    }
    
    // Get user info
    currentUser = getUser();
    
    if (!currentUser) {
        // Fetch user info from API
        const response = await apiRequest('/auth/me');
        
        if (response.ok) {
            currentUser = response.data.data;
            setUser(currentUser);
        } else {
            removeToken();
            window.location.href = 'index.html';
            return;
        }
    }
    
    // Display user info
    document.getElementById('user-name').textContent = currentUser.name;
    const roleEl = document.getElementById('user-role');
    roleEl.textContent = currentUser.role;
    roleEl.classList.add(currentUser.role);
    
    // Load tasks
    await loadTasks();
    
    // Load admin data if admin
    if (currentUser.role === 'admin') {
        await loadAdminData();
    }
    
    // Set up event listeners
    setupDashboardEventListeners();
}

/**
 * Set up dashboard event listeners
 */
function setupDashboardEventListeners() {
    // Logout button
    document.getElementById('logout-btn').addEventListener('click', handleLogout);
    
    // Task form
    document.getElementById('task-form').addEventListener('submit', handleTaskSubmit);
    
    // Cancel edit button
    document.getElementById('cancel-btn').addEventListener('click', resetTaskForm);
    
    // Filter change
    document.getElementById('filter-status').addEventListener('change', () => {
        currentPage = 1;
        loadTasks();
    });
    
    // Show all tasks checkbox (admin)
    const showAllCheckbox = document.getElementById('show-all-tasks');
    if (showAllCheckbox) {
        showAllCheckbox.addEventListener('change', () => {
            currentPage = 1;
            loadTasks();
        });
    }
    
    // Refresh button
    document.getElementById('refresh-btn').addEventListener('click', loadTasks);
    
    // Pagination buttons
    document.getElementById('prev-page').addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            loadTasks();
        }
    });
    
    document.getElementById('next-page').addEventListener('click', () => {
        currentPage++;
        loadTasks();
    });
    
    // Delete modal
    document.getElementById('confirm-delete').addEventListener('click', deleteTask);
    document.getElementById('cancel-delete').addEventListener('click', hideDeleteModal);
}

// ========================================
// Login Page Initialization
// ========================================

/**
 * Initialize login page
 */
function initLoginPage() {
    // If already authenticated, redirect to dashboard
    if (isAuthenticated()) {
        window.location.href = 'dashboard.html';
        return;
    }
    
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            // Update active tab button
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Show corresponding tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(`${btn.dataset.tab}-tab`).classList.add('active');
        });
    });
    
    // Form submissions
    document.getElementById('login-form').addEventListener('submit', handleLogin);
    document.getElementById('register-form').addEventListener('submit', handleRegister);
}

// ========================================
// Page Initialization
// ========================================

/**
 * Initialize page based on current location
 */
document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    
    if (path.includes('dashboard.html')) {
        initDashboard();
    } else {
        initLoginPage();
    }
});