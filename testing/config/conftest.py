"""
Pytest Configuration and Fixtures
Shared fixtures for all API tests
"""
import pytest
import sys
import os
from datetime import datetime

# Add backend to path for imports
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, backend_path)

from app import app, db


@pytest.fixture(scope='function')
def test_app():
    """
    Create test application with in-memory database
    Fresh database for each test function
    """
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['RATELIMIT_ENABLED'] = False  # Disable rate limiting for tests
    
    # Disable rate limiter for tests
    from app import limiter
    limiter.enabled = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
        limiter.enabled = True  # Re-enable after tests


@pytest.fixture
def client(test_app):
    """Create test client for making requests"""
    return test_app.test_client()


@pytest.fixture
def auth_client(test_app, client):
    """
    Create authenticated test client
    Logs in with default admin credentials
    """
    # Note: Rate limiting is disabled for tests (see test_app fixture)
    # RATELIMIT_ENABLED = False ensures no 429 errors
    
    response = client.post('/api/auth/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    
    assert response.status_code == 200, f"Failed to authenticate: {response.status_code} - {response.data}"
    
    return client


@pytest.fixture
def sample_stock_data():
    """Sample stock data for tests"""
    return {
        'symbol': 'TEST.NS',
        'name': 'Test Stock',
        'sector': 'Technology',
        'market_cap': 'Large',
        'current_price': 1000.0,
        'buy_zone_price': '900-950',
        'sell_zone_price': '1100-1200',
        'status': 'HOLD'
    }


@pytest.fixture
def sample_transaction_data():
    """Sample transaction data for tests"""
    return {
        'symbol': 'TEST.NS',
        'transaction_type': 'BUY',
        'quantity': 10,
        'price': 1000.0,
        'transaction_date': datetime.now().strftime('%Y-%m-%d'),
        'reason': 'Test purchase'
    }


@pytest.fixture
def sample_mf_data():
    """Sample mutual fund scheme data for tests"""
    return {
        'scheme_code': 'TEST001',
        'scheme_name': 'Test Mutual Fund',
        'fund_house': 'Test AMC',
        'category': 'equity',
        'sub_category': 'large_cap',
        'current_nav': 100.0
    }


@pytest.fixture
def sample_income_data():
    """Sample income transaction data for tests"""
    return {
        'category': 'Salary',
        'amount': 100000.0,
        'transaction_date': datetime.now().strftime('%Y-%m-%d'),
        'description': 'Monthly salary',
        'source': 'Employer'
    }


@pytest.fixture
def sample_expense_data():
    """Sample expense transaction data for tests"""
    return {
        'category': 'Food',
        'amount': 5000.0,
        'transaction_date': datetime.now().strftime('%Y-%m-%d'),
        'description': 'Groceries',
        'payment_method': 'Cash'
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "auth: Authentication tests")
    config.addinivalue_line("markers", "stock: Stock API tests")
    config.addinivalue_line("markers", "portfolio: Portfolio API tests")
    config.addinivalue_line("markers", "mutualfund: Mutual Fund API tests")
    config.addinivalue_line("markers", "fixedincome: Fixed Income API tests")
    config.addinivalue_line("markers", "savings: Savings API tests")
    config.addinivalue_line("markers", "income: Income API tests")
    config.addinivalue_line("markers", "expense: Expense API tests")
    config.addinivalue_line("markers", "budget: Budget API tests")
    config.addinivalue_line("markers", "dashboard: Dashboard API tests")
    config.addinivalue_line("markers", "health: Health API tests")
    config.addinivalue_line("markers", "settings: Settings API tests")
    config.addinivalue_line("markers", "slow: Slow running tests")

