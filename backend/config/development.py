"""
Development configuration for Investment Manager
Uses SQLite database and relaxed security settings
"""
from .base import Config


class DevelopmentConfig(Config):
    """Development-specific configuration"""
    
    # Enable debug mode
    DEBUG = True
    
    # SQLite for local development - use instance folder
    # Flask automatically creates instance folder for app data
    import os
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "instance", "investment_manager.db")}'
    
    # Don't require HTTPS for cookies in development
    SESSION_COOKIE_SECURE = False
    
    # CORS for local React development server
    CORS_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000"
    ]

