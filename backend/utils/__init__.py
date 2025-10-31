"""
Backend utilities package for Investment Manager
"""
from .auth import User, init_auth, api_login_required, verify_credentials
from .validation import validate_transaction_data
from .zones import parse_zone, is_in_zone
from .holdings import calculate_holdings
from .helpers import format_refresh_response, clean_symbol
from .xirr import calculate_portfolio_xirr
from .portfolio_health import (
    calculate_concentration_risk,
    calculate_diversification_score,
    calculate_allocation_health,
    calculate_overall_health_score
)
from .rebalancing import get_rebalancing_suggestions

__all__ = [
    'User',
    'init_auth',
    'api_login_required',
    'verify_credentials',
    'validate_transaction_data',
    'parse_zone',
    'is_in_zone',
    'calculate_holdings',
    'format_refresh_response',
    'clean_symbol',
    'calculate_portfolio_xirr',
    'calculate_concentration_risk',
    'calculate_diversification_score',
    'calculate_allocation_health',
    'calculate_overall_health_score',
    'get_rebalancing_suggestions',
]

