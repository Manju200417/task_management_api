"""
Role-based Access Control Middleware
Checks user roles for protected routes
"""

from functools import wraps
from flask import current_app
from app.utils.responses import error_response


def admin_required(f):
    """
    Decorator for routes that require admin role
    Must be used after @token_required
    
    Usage:
        @app.route('/admin-only')
        @token_required
        @admin_required
        def admin_route(current_user):
            pass
    """
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.get('role') != 'admin':
            current_app.logger.warning(
                f'Non-admin user {current_user.get("user_id")} '
                f'attempted to access admin route'
            )
            return error_response(
                'Admin privileges required for this action', 
                403
            )
        
        return f(current_user, *args, **kwargs)
    
    return decorated


def role_required(*allowed_roles):
    """
    Decorator for routes that require specific roles
    Must be used after @token_required
    
    Usage:
        @app.route('/special')
        @token_required
        @role_required('admin', 'manager')
        def special_route(current_user):
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            user_role = current_user.get('role')
            
            if user_role not in allowed_roles:
                current_app.logger.warning(
                    f'User {current_user.get("user_id")} with role {user_role} '
                    f'denied access to route requiring {allowed_roles}'
                )
                return error_response(
                    f'Required role: {", ".join(allowed_roles)}',
                    403
                )
            
            return f(current_user, *args, **kwargs)
        
        return decorated
    
    return decorator