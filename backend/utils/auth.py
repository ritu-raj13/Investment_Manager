"""
Authentication module for single-user Investment Manager
Uses Flask-Login for session management
"""
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import jsonify


# Single user model (no database needed for just one user)
class User(UserMixin):
    def __init__(self, username):
        self.id = username
        self.username = username


def init_auth(app):
    """Initialize authentication for the app"""
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    # Get admin credentials from config
    admin_username = app.config['ADMIN_USERNAME']
    admin_password_hash = generate_password_hash(app.config['ADMIN_PASSWORD'])
    
    @login_manager.user_loader
    def load_user(user_id):
        """Load user by ID"""
        if user_id == admin_username:
            return User(admin_username)
        return None
    
    @login_manager.unauthorized_handler
    def unauthorized():
        """Handle unauthorized access"""
        return jsonify({'error': 'Authentication required'}), 401
    
    return login_manager, admin_username, admin_password_hash


def api_login_required(f):
    """
    Custom decorator for API routes that need authentication.
    Returns JSON error instead of redirect.
    """
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def verify_credentials(username, password, admin_username, admin_password_hash):
    """
    Verify username and password against admin credentials.
    
    Args:
        username: Provided username
        password: Provided password
        admin_username: Configured admin username
        admin_password_hash: Hashed admin password
    
    Returns:
        bool: True if credentials are valid
    """
    if username != admin_username:
        return False
    
    return check_password_hash(admin_password_hash, password)

