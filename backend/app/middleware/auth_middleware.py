"""
Authentication Middleware
JWT token generation and verification
"""

import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, current_app
from app.utils.responses import error_response


def generate_token(user_id, role):
    """
    Generate JWT token for authenticated user
    
    Args:
        user_id: User's database ID
        role: User's role (user/admin)
    
    Returns:
        JWT token string
    """
    secret_key = current_app.config.get('JWT_SECRET_KEY')
    expiry_hours = current_app.config.get('JWT_EXPIRY_HOURS', 24)
    
    payload = {
        'user_id': user_id,
        'role': role,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expiry_hours)
    }
    
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    
    return token


def decode_token(token):
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded payload or None if invalid
    """
    secret_key = current_app.config.get('JWT_SECRET_KEY')
    
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        current_app.logger.warning('Token expired')
        return None
    except jwt.InvalidTokenError as e:
        current_app.logger.warning(f'Invalid token: {e}')
        return None


def token_required(f):
    """
    Decorator for routes that require authentication
    Extracts and validates JWT from Authorization header
    
    Usage:
        @app.route('/protected')
        @token_required
        def protected_route(current_user):
            # current_user contains user_id and role
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            # Expected format: "Bearer <token>"
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        
        if not token:
            current_app.logger.warning('Request without token')
            return error_response('Authentication token is required', 401)
        
        # Decode and validate token
        payload = decode_token(token)
        
        if not payload:
            return error_response('Invalid or expired token', 401)
        
        # Create current_user dict from payload
        current_user = {
            'user_id': payload.get('user_id'),
            'role': payload.get('role')
        }
        
        # Pass current_user to the wrapped function
        return f(current_user, *args, **kwargs)
    
    return decorated