"""
Task Model
Database operations for tasks table
"""

from app.extensions import execute_query
from flask import current_app


class TaskModel:
    """
    Task model for database operations
    Uses raw SQL queries
    """
    
    @staticmethod
    def create(title, description, status, user_id):
        """
        Create a new task
        
        Args:
            title: Task title
            description: Task description
            status: Task status
            user_id: Owner's user ID
        
        Returns:
            ID of the created task
        """
        query = """
            INSERT INTO tasks (title, description, status, user_id)
            VALUES (%s, %s, %s, %s)
        """
        params = (title, description, status, user_id)
        
        task_id = execute_query(query, params, commit=True)
        
        return task_id
    
    @staticmethod
    def find_by_id(task_id):
        """
        Find task by ID
        
        Args:
            task_id: Task's database ID
        
        Returns:
            Task dict or None
        """
        query = """
            SELECT id, title, description, status, user_id, created_at
            FROM tasks
            WHERE id = %s
        """
        params = (task_id,)
        
        task = execute_query(query, params, fetch_one=True)
        
        return task
    
    @staticmethod
    def find_by_user(user_id, status=None, limit=10, offset=0):
        """
        Find all tasks belonging to a user
        
        Args:
            user_id: Owner's user ID
            status: Filter by status (optional)
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of task dicts
        """
        if status:
            query = """
                SELECT id, title, description, status, user_id, created_at
                FROM tasks
                WHERE user_id = %s AND status = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (user_id, status, limit, offset)
        else:
            query = """
                SELECT id, title, description, status, user_id, created_at
                FROM tasks
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = (user_id, limit, offset)
        
        tasks = execute_query(query, params, fetch_all=True)
        
        return tasks if tasks else []
    
    @staticmethod
    def find_all(status=None, user_id=None, limit=100, offset=0):
        """
        Find all tasks with optional filters
        
        Args:
            status: Filter by status (optional)
            user_id: Filter by user (optional)
            limit: Max results
            offset: Pagination offset
        
        Returns:
            List of task dicts
        """
        conditions = []
        params = []
        
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)
        
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        query = f"""
            SELECT id, title, description, status, user_id, created_at
            FROM tasks
            {where_clause}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        tasks = execute_query(query, tuple(params), fetch_all=True)
        
        return tasks if tasks else []
    
    @staticmethod
    def count_by_user(user_id, status=None):
        """
        Count tasks for a user
        
        Args:
            user_id: Owner's user ID
            status: Filter by status (optional)
        
        Returns:
            Count of tasks
        """
        if status:
            query = """
                SELECT COUNT(*) as count
                FROM tasks
                WHERE user_id = %s AND status = %s
            """
            params = (user_id, status)
        else:
            query = """
                SELECT COUNT(*) as count
                FROM tasks
                WHERE user_id = %s
            """
            params = (user_id,)
        
        result = execute_query(query, params, fetch_one=True)
        
        return result['count'] if result else 0
    
    @staticmethod
    def count_all(status=None):
        """
        Count all tasks
        
        Args:
            status: Filter by status (optional)
        
        Returns:
            Count of tasks
        """
        if status:
            query = "SELECT COUNT(*) as count FROM tasks WHERE status = %s"
            params = (status,)
        else:
            query = "SELECT COUNT(*) as count FROM tasks"
            params = None
        
        result = execute_query(query, params, fetch_one=True)
        
        return result['count'] if result else 0
    
    @staticmethod
    def update(task_id, title=None, description=None, status=None):
        """
        Update a task
        
        Args:
            task_id: Task's database ID
            title: New title (optional)
            description: New description (optional)
            status: New status (optional)
        
        Returns:
            True if updated
        """
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = %s")
            params.append(title)
        
        if description is not None:
            updates.append("description = %s")
            params.append(description)
        
        if status is not None:
            updates.append("status = %s")
            params.append(status)
        
        if not updates:
            return False
        
        params.append(task_id)
        
        query = f"""
            UPDATE tasks
            SET {', '.join(updates)}
            WHERE id = %s
        """
        
        execute_query(query, tuple(params), commit=True)
        
        return True
    
    @staticmethod
    def delete(task_id):
        """
        Delete a task
        
        Args:
            task_id: Task's database ID
        
        Returns:
            True if deleted
        """
        query = "DELETE FROM tasks WHERE id = %s"
        params = (task_id,)
        
        execute_query(query, params, commit=True)
        
        return True
    
    @staticmethod
    def delete_by_user(user_id):
        """
        Delete all tasks for a user
        
        Args:
            user_id: Owner's user ID
        
        Returns:
            True if deleted
        """
        query = "DELETE FROM tasks WHERE user_id = %s"
        params = (user_id,)
        
        execute_query(query, params, commit=True)
        
        return True