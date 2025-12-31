"""
Input Validation Utilities
Handles input sanitization and validation
"""

import re
import html


def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email string to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not email:
        return False
    
    # Simple but effective email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    return bool(re.match(pattern, email))


def validate_password(password):
    """
    Validate password strength
    
    Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
    
    Args:
        password: Password string to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    return True, "Password is valid"


def sanitize_input(value):
    """
    Sanitize user input to prevent XSS and injection
    
    Args:
        value: Input string to sanitize
    
    Returns:
        Sanitized string
    """
    if value is None:
        return ''
    
    if not isinstance(value, str):
        value = str(value)
    
    # Strip leading/trailing whitespace
    value = value.strip()
    
    # Escape HTML entities
    value = html.escape(value)
    
    return value


def validate_task_status(status):
    """
    Validate task status value
    
    Args:
        status: Status string to validate
    
    Returns:
        True if valid, False otherwise
    """
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    
    return status in valid_statuses


def validate_string_length(value, min_length=1, max_length=255):
    """
    Validate string length
    
    Args:
        value: String to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not value:
        return False, f"Value must be at least {min_length} characters"
    
    if len(value) < min_length:
        return False, f"Value must be at least {min_length} characters"
    
    if len(value) > max_length:
        return False, f"Value must not exceed {max_length} characters"
    
    return True, "Valid"