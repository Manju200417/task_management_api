"""
User Model
Database operations for users table
"""

from app.extensions import execute_query
from flask import current_app


class UserModel:
    """
    User model for database operations
    Uses raw SQL queries
    """
    
    @staticmethod
    def create(email, password_hash, name, role='user'):
        """
        Create a new user in the database
        
        Args:
            email: User's email address
            password_hash: Hashed password
            name: User's full name
            role: User role (default: 'user')
        
        Returns:
            ID of the created user
        """
        query = """
            INSERT INTO users (email, password_hash, name, role)
            VALUES (%s, %s, %s, %s)
        """
        params = (email, password_hash, name, role)
        
        user_id = execute_query(query, params, commit=True)
        
        return user_id
    
    @staticmethod
    def find_by_email(email):
        """
        Find user by email address
        
        Args:
            email: User's email address
        
        Returns:
            User dict or None
        """
        query = """
            SELECT id, email, password_hash, name, role, created_at
            FROM users
            WHERE email = %s
        """
        params = (email,)
        
        user = execute_query(query, params, fetch_one=True)
        
        return user
    
    @staticmethod
    def find_by_id(user_id):
        """
        Find user by ID
        
        Args:
            user_id: User's database ID
        
        Returns:
            User dict or None
        """
        query = """
            SELECT id, email, password_hash, name, role, created_at
            FROM users
            WHERE id = %s
        """
        params = (user_id,)
        
        user = execute_query(query, params, fetch_one=True)
        
        return user
    
    @staticmethod
    def find_all():
        """
        Get all users
        
        Returns:
            List of user dicts
        """
        query = """
            SELECT id, email, password_hash, name, role, created_at
            FROM users
            ORDER BY created_at DESC
        """
        
        users = execute_query(query, fetch_all=True)
        
        return users if users else []
    
    @staticmethod
    def update(user_id, name=None, role=None):
        """
        Update user details
        
        Args:
            user_id: User's database ID
            name: New name (optional)
            role: New role (optional)
        
        Returns:
            True if updated
        """
        updates = []
        params = []
        
        if name:
            updates.append("name = %s")
            params.append(name)
        
        if role:
            updates.append("role = %s")
            params.append(role)
        
        if not updates:
            return False
        
        params.append(user_id)
        
        query = f"""
            UPDATE users
            SET {', '.join(updates)}
            WHERE id = %s
        """
        
        execute_query(query, tuple(params), commit=True)
        
        return True
    
    @staticmethod
    def delete(user_id):
        """
        Delete a user
        
        Args:
            user_id: User's database ID
        
        Returns:
            True if deleted
        """
        query = "DELETE FROM users WHERE id = %s"
        params = (user_id,)
        
        execute_query(query, params, commit=True)
        
        return True
    
    @staticmethod
    def update_password(user_id, password_hash):
        """
        Update user's password
        
        Args:
            user_id: User's database ID
            password_hash: New hashed password
        
        Returns:
            True if updated
        """
        query = """
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
        """
        params = (password_hash, user_id)
        
        execute_query(query, params, commit=True)
        
        return True