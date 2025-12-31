"""
Password Utilities
Handles password hashing and verification using bcrypt
"""

import bcrypt


def hash_password(password):
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password string
    """
    # Convert password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string for database storage
    return hashed.decode('utf-8')


def verify_password(password, password_hash):
    """
    Verify a password against its hash
    
    Args:
        password: Plain text password to verify
        password_hash: Stored hash to compare against
    
    Returns:
        True if password matches, False otherwise
    """
    try:
        # Convert to bytes
        password_bytes = password.encode('utf-8')
        hash_bytes = password_hash.encode('utf-8')
        
        # Check password
        return bcrypt.checkpw(password_bytes, hash_bytes)
    except Exception:
        return False