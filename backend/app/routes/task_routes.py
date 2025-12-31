"""
Task Routes
CRUD operations for tasks with role-based access
"""

from flask import Blueprint, request, current_app
from app.models.task_model import TaskModel
from app.utils.validators import sanitize_input
from app.utils.responses import success_response, error_response
from app.middleware.auth_middleware import token_required
from app.middleware.role_check import admin_required

task_bp = Blueprint('tasks', __name__)


@task_bp.route('', methods=['POST'])
@token_required
def create_task(current_user):
    """
    Create a new task
    
    Headers:
        - Authorization: Bearer <token>
    
    Request Body:
        - title: Task title (required)
        - description: Task description (optional)
        - status: Task status (optional, defaults to 'pending')
    
    Returns:
        - 201: Task created successfully
        - 400: Validation error
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Request body is required', 400)
        
        title = sanitize_input(data.get('title', ''))
        description = sanitize_input(data.get('description', ''))
        status = sanitize_input(data.get('status', 'pending'))
        
        # Validate title
        if not title:
            return error_response('Task title is required', 400)
        
        if len(title) > 200:
            return error_response('Title must be less than 200 characters', 400)
        
        # Validate status
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            return error_response(
                f'Invalid status. Must be one of: {", ".join(valid_statuses)}', 
                400
            )
        
        # Create task
        task_id = TaskModel.create(
            title=title,
            description=description,
            status=status,
            user_id=current_user['user_id']
        )
        
        current_app.logger.info(
            f'Task created: {task_id} by user {current_user["user_id"]}'
        )
        
        return success_response(
            message='Task created successfully',
            data={'task_id': task_id},
            status_code=201
        )
        
    except Exception as e:
        current_app.logger.error(f'Create task error: {e}')
        return error_response('Failed to create task', 500)


@task_bp.route('', methods=['GET'])
@token_required
def get_tasks(current_user):
    """
    Get tasks for current user
    Admin can see all tasks with ?all=true parameter
    
    Headers:
        - Authorization: Bearer <token>
    
    Query Parameters:
        - all: Show all tasks (admin only)
        - status: Filter by status
        - page: Page number (default: 1)
        - limit: Items per page (default: 10)
    
    Returns:
        - 200: List of tasks
    """
    try:
        # Parse query parameters
        show_all = request.args.get('all', 'false').lower() == 'true'
        status_filter = request.args.get('status', None)
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # Validate pagination
        if page < 1:
            page = 1
        if limit < 1 or limit > 100:
            limit = 10
        
        offset = (page - 1) * limit
        
        # Get tasks based on role
        if show_all and current_user['role'] == 'admin':
            tasks = TaskModel.find_all(
                status=status_filter,
                limit=limit,
                offset=offset
            )
            total = TaskModel.count_all(status=status_filter)
        else:
            tasks = TaskModel.find_by_user(
                user_id=current_user['user_id'],
                status=status_filter,
                limit=limit,
                offset=offset
            )
            total = TaskModel.count_by_user(
                user_id=current_user['user_id'],
                status=status_filter
            )
        
        # Format response
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task['id'],
                'title': task['title'],
                'description': task['description'],
                'status': task['status'],
                'user_id': task['user_id'],
                'created_at': str(task['created_at'])
            })
        
        return success_response(
            message='Tasks retrieved successfully',
            data={
                'tasks': task_list,
                'pagination': {
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'pages': (total + limit - 1) // limit
                }
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Get tasks error: {e}')
        return error_response('Failed to retrieve tasks', 500)


@task_bp.route('/<int:task_id>', methods=['GET'])
@token_required
def get_task(current_user, task_id):
    """
    Get a specific task by ID
    Users can only view their own tasks, admins can view all
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: Task details
        - 403: Forbidden
        - 404: Not found
    """
    try:
        task = TaskModel.find_by_id(task_id)
        
        if not task:
            return error_response('Task not found', 404)
        
        # Check ownership (unless admin)
        if task['user_id'] != current_user['user_id'] and current_user['role'] != 'admin':
            return error_response('You do not have permission to view this task', 403)
        
        return success_response(
            message='Task retrieved successfully',
            data={
                'id': task['id'],
                'title': task['title'],
                'description': task['description'],
                'status': task['status'],
                'user_id': task['user_id'],
                'created_at': str(task['created_at'])
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Get task error: {e}')
        return error_response('Failed to retrieve task', 500)


@task_bp.route('/<int:task_id>', methods=['PUT'])
@token_required
def update_task(current_user, task_id):
    """
    Update a task
    Users can only update their own tasks
    
    Headers:
        - Authorization: Bearer <token>
    
    Request Body:
        - title: Task title (optional)
        - description: Task description (optional)
        - status: Task status (optional)
    
    Returns:
        - 200: Task updated successfully
        - 403: Forbidden
        - 404: Not found
    """
    try:
        task = TaskModel.find_by_id(task_id)
        
        if not task:
            return error_response('Task not found', 404)
        
        # Check ownership (users can only update their own tasks)
        if task['user_id'] != current_user['user_id']:
            return error_response('You do not have permission to update this task', 403)
        
        data = request.get_json()
        
        if not data:
            return error_response('Request body is required', 400)
        
        # Get update fields
        title = sanitize_input(data.get('title', task['title']))
        description = sanitize_input(data.get('description', task['description']))
        status = sanitize_input(data.get('status', task['status']))
        
        # Validate title
        if not title:
            return error_response('Task title cannot be empty', 400)
        
        if len(title) > 200:
            return error_response('Title must be less than 200 characters', 400)
        
        # Validate status
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            return error_response(
                f'Invalid status. Must be one of: {", ".join(valid_statuses)}',
                400
            )
        
        # Update task
        TaskModel.update(
            task_id=task_id,
            title=title,
            description=description,
            status=status
        )
        
        current_app.logger.info(
            f'Task updated: {task_id} by user {current_user["user_id"]}'
        )
        
        return success_response(
            message='Task updated successfully',
            data={
                'id': task_id,
                'title': title,
                'description': description,
                'status': status
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Update task error: {e}')
        return error_response('Failed to update task', 500)


@task_bp.route('/<int:task_id>', methods=['DELETE'])
@token_required
def delete_task(current_user, task_id):
    """
    Delete a task
    Users can delete their own tasks, admins can delete any task
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: Task deleted successfully
        - 403: Forbidden
        - 404: Not found
    """
    try:
        task = TaskModel.find_by_id(task_id)
        
        if not task:
            return error_response('Task not found', 404)
        
        # Check ownership (unless admin)
        if task['user_id'] != current_user['user_id'] and current_user['role'] != 'admin':
            return error_response('You do not have permission to delete this task', 403)
        
        # Delete task
        TaskModel.delete(task_id)
        
        current_app.logger.info(
            f'Task deleted: {task_id} by user {current_user["user_id"]}'
        )
        
        return success_response(message='Task deleted successfully')
        
    except Exception as e:
        current_app.logger.error(f'Delete task error: {e}')
        return error_response('Failed to delete task', 500)


@task_bp.route('/admin/all', methods=['GET'])
@token_required
@admin_required
def admin_get_all_tasks(current_user):
    """
    Get all tasks (Admin only endpoint)
    
    Headers:
        - Authorization: Bearer <token>
    
    Query Parameters:
        - status: Filter by status
        - user_id: Filter by user
    
    Returns:
        - 200: List of all tasks
    """
    try:
        status_filter = request.args.get('status', None)
        user_id_filter = request.args.get('user_id', None)
        
        if user_id_filter:
            user_id_filter = int(user_id_filter)
        
        tasks = TaskModel.find_all(
            status=status_filter,
            user_id=user_id_filter
        )
        
        task_list = []
        for task in tasks:
            task_list.append({
                'id': task['id'],
                'title': task['title'],
                'description': task['description'],
                'status': task['status'],
                'user_id': task['user_id'],
                'created_at': str(task['created_at'])
            })
        
        return success_response(
            message='All tasks retrieved successfully',
            data={'tasks': task_list, 'total': len(task_list)}
        )
        
    except Exception as e:
        current_app.logger.error(f'Admin get tasks error: {e}')
        return error_response('Failed to retrieve tasks', 500)


@task_bp.route('/admin/<int:task_id>', methods=['DELETE'])
@token_required
@admin_required
def admin_delete_task(current_user, task_id):
    """
    Admin delete any task
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: Task deleted successfully
        - 404: Not found
    """
    try:
        task = TaskModel.find_by_id(task_id)
        
        if not task:
            return error_response('Task not found', 404)
        
        TaskModel.delete(task_id)
        
        current_app.logger.info(
            f'Task {task_id} deleted by admin {current_user["user_id"]}'
        )
        
        return success_response(message='Task deleted successfully by admin')
        
    except Exception as e:
        current_app.logger.error(f'Admin delete task error: {e}')
        return error_response('Failed to delete task', 500)