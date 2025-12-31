"""
Database Connection Extensions
Handles MySQL and PostgreSQL connections
"""

import mysql.connector
from mysql.connector import pooling
from flask import g, current_app

# Database connection pool
db_pool = None


def init_db(app):
    """
    Initialize database connection pool
    Called during app startup
    """
    global db_pool
    
    config = app.config
    db_type = config.get('DB_TYPE', 'mysql')
    
    try:
        if db_type == 'postgresql':
            # PostgreSQL connection using psycopg2
            import psycopg2
            from psycopg2 import pool
            
            db_pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=config.get('POSTGRES_HOST'),
                port=config.get('POSTGRES_PORT'),
                user=config.get('POSTGRES_USER'),
                password=config.get('POSTGRES_PASSWORD'),
                database=config.get('POSTGRES_DATABASE')
            )
            app.logger.info('PostgreSQL connection pool created')
        else:
            # MySQL connection pool
            db_pool = pooling.MySQLConnectionPool(
                pool_name="app_pool",
                pool_size=10,
                pool_reset_session=True,
                host=config.get('MYSQL_HOST'),
                port=config.get('MYSQL_PORT'),
                user=config.get('MYSQL_USER'),
                password=config.get('MYSQL_PASSWORD'),
                database=config.get('MYSQL_DATABASE')
            )
            app.logger.info('MySQL connection pool created')
            
    except Exception as e:
        app.logger.error(f'Failed to create database pool: {e}')
        raise


def get_db():
    """
    Get database connection from pool
    Connection is stored in Flask's g object for request lifecycle
    """
    if 'db' not in g:
        config = current_app.config
        db_type = config.get('DB_TYPE', 'mysql')
        
        try:
            if db_type == 'postgresql':
                g.db = db_pool.getconn()
            else:
                g.db = db_pool.get_connection()
                
            current_app.logger.debug('Database connection acquired')
        except Exception as e:
            current_app.logger.error(f'Failed to get database connection: {e}')
            raise
            
    return g.db


def close_db(error=None):
    """
    Close database connection at end of request
    """
    db = g.pop('db', None)
    
    if db is not None:
        config = current_app.config
        db_type = config.get('DB_TYPE', 'mysql')
        
        try:
            if db_type == 'postgresql':
                db_pool.putconn(db)
            else:
                db.close()
                
            current_app.logger.debug('Database connection returned to pool')
        except Exception as e:
            current_app.logger.error(f'Error closing database connection: {e}')


def execute_query(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    """
    Execute a database query with proper error handling
    
    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit transaction
        
    Returns:
        Query results or last row id for INSERT
    """
    db = get_db()
    cursor = None
    
    config = current_app.config
    db_type = config.get('DB_TYPE', 'mysql')
    
    try:
        if db_type == 'postgresql':
            from psycopg2.extras import RealDictCursor
            cursor = db.cursor(cursor_factory=RealDictCursor)
        else:
            cursor = db.cursor(dictionary=True)
        
        # Log query for debugging (sanitized)
        current_app.logger.debug(f'Executing query: {query[:100]}...')
        
        cursor.execute(query, params)
        
        result = None
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        elif commit:
            db.commit()
            result = cursor.lastrowid
            
        return result
        
    except Exception as e:
        current_app.logger.error(f'Database query error: {e}')
        if commit:
            db.rollback()
        raise
        
    finally:
        if cursor:
            cursor.close()