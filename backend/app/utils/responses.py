"""
Response Utilities
Standardized JSON response formatting
"""

from flask import jsonify


def success_response(message, data=None, status_code=200):
    """
    Create a standardized success response
    
    Args:
        message: Success message
        data: Response data (optional)
        status_code: HTTP status code (default: 200)
    
    Returns:
        Flask JSON response tuple
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def error_response(message, status_code=400, errors=None):
    """
    Create a standardized error response
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        errors: Additional error details (optional)
    
    Returns:
        Flask JSON response tuple
    """
    response = {
        'success': False,
        'error': message
    }
    
    if errors is not None:
        response['errors'] = errors
    
    return jsonify(response), status_code


def paginated_response(message, data, page, limit, total, status_code=200):
    """
    Create a standardized paginated response
    
    Args:
        message: Success message
        data: List of items
        page: Current page number
        limit: Items per page
        total: Total items count
        status_code: HTTP status code (default: 200)
    
    Returns:
        Flask JSON response tuple
    """
    total_pages = (total + limit - 1) // limit if limit > 0 else 0
    
    response = {
        'success': True,
        'message': message,
        'data': data,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_items': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }
    
    return jsonify(response), status_code