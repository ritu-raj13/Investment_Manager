"""
Configuration package for Investment Manager
Provides environment-specific configurations
"""
import os
from .base import Config
from .development import DevelopmentConfig
from .production import ProductionConfig


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """
    Get configuration based on FLASK_ENV environment variable.
    
    Returns:
        Config class appropriate for the current environment
    """
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])


__all__ = [
    'Config',
    'DevelopmentConfig',
    'ProductionConfig',
    'get_config',
]

