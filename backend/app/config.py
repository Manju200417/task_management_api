"""
Application Configuration
Loads settings from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for Flask application
    All settings are loaded from environment variables
    """
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # JWT settings
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'default-jwt-secret')
    JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', 24))
    
    # Database type (mysql or postgresql)
    DB_TYPE = os.getenv('DB_TYPE', 'mysql').lower()
    
    # MySQL settings
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'task_management')
    
    # PostgreSQL settings
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    POSTGRES_DATABASE = os.getenv('POSTGRES_DATABASE', 'task_management')
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    
    @classmethod
    def get_db_config(cls):
        """
        Returns database configuration based on DB_TYPE
        """
        if cls.DB_TYPE == 'postgresql':
            return {
                'type': 'postgresql',
                'host': cls.POSTGRES_HOST,
                'port': cls.POSTGRES_PORT,
                'user': cls.POSTGRES_USER,
                'password': cls.POSTGRES_PASSWORD,
                'database': cls.POSTGRES_DATABASE
            }
        else:
            return {
                'type': 'mysql',
                'host': cls.MYSQL_HOST,
                'port': cls.MYSQL_PORT,
                'user': cls.MYSQL_USER,
                'password': cls.MYSQL_PASSWORD,
                'database': cls.MYSQL_DATABASE
            }