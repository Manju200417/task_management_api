"""
Authentication Routes
Handles user registration, login, and token management
"""

from flask import Blueprint, request, current_app
from app.models.user_model import UserModel
from app.utils.password import hash_password, verify_password
from app.utils.validators import validate_email, validate_password, sanitize_input
from app.utils.responses import success_response, error_response
from app.middleware.auth_middleware import generate_token, token_required
from app.middleware.role_check import admin_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    
    Request Body:
        - email: User email address
        - password: User password (min 8 chars)
        - name: User full name
        - role: User role (optional, defaults to 'user')
    
    Returns:
        - 201: User created successfully
        - 400: Validation error
        - 409: Email already exists
    """
    try:
        data = request.get_json()
        
        if not data:
            current_app.logger.warning('Registration attempt with empty body')
            return error_response('Request body is required', 400)
        
        # Extract and sanitize input
        email = sanitize_input(data.get('email', ''))
        password = data.get('password', '')
        name = sanitize_input(data.get('name', ''))
        role = sanitize_input(data.get('role', 'user'))
        
        # Validate required fields
        if not email or not password or not name:
            return error_response('Email, password, and name are required', 400)
        
        # Validate email format
        if not validate_email(email):
            return error_response('Invalid email format', 400)
        
        # Validate password strength
        password_valid, password_msg = validate_password(password)
        if not password_valid:
            return error_response(password_msg, 400)
        
        # Validate role
        if role not in ['user', 'admin']:
            role = 'user'
        
        # Check if user already exists
        existing_user = UserModel.find_by_email(email)
        if existing_user:
            current_app.logger.warning(f'Registration attempt with existing email: {email}')
            return error_response('Email already registered', 409)
        
        # Hash password
        password_hash = hash_password(password)
        
        # Create user
        user_id = UserModel.create(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role
        )
        
        current_app.logger.info(f'New user registered: {email} (ID: {user_id})')
        
        return success_response(
            message='User registered successfully',
            data={'user_id': user_id, 'email': email},
            status_code=201
        )
        
    except Exception as e:
        current_app.logger.error(f'Registration error: {e}')
        return error_response('Registration failed', 500)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and return JWT token
    
    Request Body:
        - email: User email
        - password: User password
    
    Returns:
        - 200: Login successful with JWT token
        - 400: Missing credentials
        - 401: Invalid credentials
    """
    try:
        data = request.get_json()
        
        if not data:
            return error_response('Request body is required', 400)
        
        email = sanitize_input(data.get('email', ''))
        password = data.get('password', '')
        
        if not email or not password:
            return error_response('Email and password are required', 400)
        
        # Find user by email
        user = UserModel.find_by_email(email)
        
        if not user:
            current_app.logger.warning(f'Login attempt with unknown email: {email}')
            return error_response('Invalid email or password', 401)
        
        # Verify password
        if not verify_password(password, user['password_hash']):
            current_app.logger.warning(f'Failed login attempt for: {email}')
            return error_response('Invalid email or password', 401)
        
        # Generate JWT token
        token = generate_token(user['id'], user['role'])
        
        current_app.logger.info(f'User logged in: {email}')
        
        return success_response(
            message='Login successful',
            data={
                'token': token,
                'user': {
                    'id': user['id'],
                    'email': user['email'],
                    'name': user['name'],
                    'role': user['role']
                }
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Login error: {e}')
        return error_response('Login failed', 500)


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_current_user(current_user):
    """
    Get current authenticated user details
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: User details
        - 401: Unauthorized
    """
    try:
        user = UserModel.find_by_id(current_user['user_id'])
        
        if not user:
            return error_response('User not found', 404)
        
        return success_response(
            message='User retrieved successfully',
            data={
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'created_at': str(user['created_at'])
            }
        )
        
    except Exception as e:
        current_app.logger.error(f'Get user error: {e}')
        return error_response('Failed to retrieve user', 500)


@auth_bp.route('/users', methods=['GET'])
@token_required
@admin_required
def get_all_users(current_user):
    """
    Get all users (Admin only)
    
    Headers:
        - Authorization: Bearer <token>
    
    Returns:
        - 200: List of users
        - 401: Unauthorized
        - 403: Forbidden (not admin)
    """
    try:
        users = UserModel.find_all()
        
        # Remove password hashes from response
        user_list = []
        for user in users:
            user_list.append({
                'id': user['id'],
                'email': user['email'],
                'name': user['name'],
                'role': user['role'],
                'created_at': str(user['created_at'])
            })
        
        return success_response(
            message='Users retrieved successfully',
            data={'users': user_list, 'total': len(user_list)}
        )
        
    except Exception as e:
        current_app.logger.error(f'Get users error: {e}')
        return error_response('Failed to retrieve users', 500)


@auth_bp.route('/logout', methods=['POST'])
@token_required
def logout(current_user):
    """
    Logout user (client-side token removal)
    
    Note: JWT tokens are stateless, so actual invalidation
    would require a token blacklist (not implemented for simplicity)
    
    Returns:
        - 200: Logout successful
    """
    current_app.logger.info(f'User logged out: {current_user["user_id"]}')
    
    return success_response(
        message='Logout successful. Please remove token from client.'
    )