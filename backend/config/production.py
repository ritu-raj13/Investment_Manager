"""
Production configuration for Investment Manager
Uses PostgreSQL database and strict security settings
"""
import os
from .base import Config


class ProductionConfig(Config):
    """Production-specific configuration"""
    
    # Disable debug mode in production
    DEBUG = False
    
    # PostgreSQL database URL from environment
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Fix Heroku/Railway postgres:// to postgresql://
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Require HTTPS for secure cookies
    SESSION_COOKIE_SECURE = True
    
    # CORS for production frontend
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'https://your-app.railway.app')
    CORS_ORIGINS = [FRONTEND_URL]
    
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    
    # Stricter rate limiting in production (if using Redis)
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

