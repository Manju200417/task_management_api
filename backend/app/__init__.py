"""
Flask Application Factory
Creates and configures the Flask application
"""

import os
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify
from flask_cors import CORS

from app.config import Config
from app.extensions import close_db, init_db
from app.routes.auth_routes import auth_bp
from app.routes.task_routes import task_bp


def create_app(config_class=Config):
    app = Flask(__name__)

    # Load configuration FIRST
    app.config.from_object(config_class)

    CORS(app)

    # Setup logging
    setup_logging(app)

    # Initialize database connection pool
    init_db(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(task_bp, url_prefix='/api/v1/tasks')

    # Register error handlers
    register_error_handlers(app)

    # Health check
    @app.route('/api/v1/health', methods=['GET'])
    def health_check():
        return jsonify({
            'status': 'healthy',
            'message': 'API is running'
        }), 200

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        return jsonify({
            'message': 'Task Management API',
            'version': '1.0'
        }), 200

    # IMPORTANT: return DB connection to pool after request
    app.teardown_appcontext(close_db)

    app.logger.info('Application started successfully')

    return app



def setup_logging(app):
    """
    Configure application logging
    Logs to both file and console
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, 'app.log')
    
    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10240000,  # 10MB
        backupCount=5
    )
    
    # Set log format
    log_format = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    )
    file_handler.setFormatter(log_format)
    
    # Set log level from config
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'DEBUG'))
    file_handler.setLevel(log_level)
    
    # Add handler to app logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    
    # Also log to console in development
    if app.config.get('DEBUG'):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_format)
        console_handler.setLevel(log_level)
        app.logger.addHandler(console_handler)


def register_error_handlers(app):
    """
    Register global error handlers
    """
    @app.errorhandler(400)
    def bad_request(error):
        app.logger.warning(f'Bad request: {error}')
        return jsonify({
            'success': False,
            'error': 'Bad Request',
            'message': str(error.description) if hasattr(error, 'description') else 'Invalid request'
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        app.logger.warning(f'Unauthorized access attempt: {error}')
        return jsonify({
            'success': False,
            'error': 'Unauthorized',
            'message': 'Authentication required'
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        app.logger.warning(f'Forbidden access: {error}')
        return jsonify({
            'success': False,
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        app.logger.info(f'Resource not found: {error}')
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Internal server error: {error}')
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500