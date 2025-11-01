"""
Backend utilities package for Investment Manager
"""
from .auth import User, init_auth, api_login_required, verify_credentials
from .validation import validate_transaction_data
from .zones import parse_zone, is_in_zone
from .holdings import calculate_holdings, calculate_holding_period_days
from .helpers import format_refresh_response, clean_symbol
from .xirr import calculate_portfolio_xirr, xirr
from .portfolio_health import (
    calculate_concentration_risk,
    calculate_diversification_score,
    calculate_allocation_health,
    calculate_overall_health_score
)
from .rebalancing import get_rebalancing_suggestions
from .mutual_funds import (
    calculate_mf_holdings,
    calculate_mf_xirr,
    get_mf_allocation,
    calculate_mf_holding_period_days
)
from .cash_flow import (
    calculate_monthly_cash_flow,
    get_expense_trends,
    calculate_savings_rate,
    get_category_breakdown,
    get_recurring_transactions,
    predict_next_month_expense
)
from .net_worth import (
    calculate_total_net_worth,
    get_asset_allocation,
    calculate_debt_to_income_ratio,
    calculate_emergency_fund_months,
    get_asset_growth_rate,
    calculate_portfolio_diversification_score,
    get_liquidity_analysis,
    calculate_unified_portfolio_xirr  # Phase 3
)
from .backup import DatabaseBackup, create_startup_backup, create_pre_migration_backup

__all__ = [
    'User',
    'init_auth',
    'api_login_required',
    'verify_credentials',
    'validate_transaction_data',
    'parse_zone',
    'is_in_zone',
    'calculate_holdings',
    'calculate_holding_period_days',
    'format_refresh_response',
    'clean_symbol',
    'calculate_portfolio_xirr',
    'xirr',
    'calculate_concentration_risk',
    'calculate_diversification_score',
    'calculate_allocation_health',
    'calculate_overall_health_score',
    'get_rebalancing_suggestions',
    'calculate_mf_holdings',
    'calculate_mf_xirr',
    'get_mf_allocation',
    'calculate_mf_holding_period_days',
    'calculate_monthly_cash_flow',
    'get_expense_trends',
    'calculate_savings_rate',
    'get_category_breakdown',
    'get_recurring_transactions',
    'predict_next_month_expense',
    'calculate_total_net_worth',
    'get_asset_allocation',
    'calculate_debt_to_income_ratio',
    'calculate_emergency_fund_months',
    'get_asset_growth_rate',
    'calculate_portfolio_diversification_score',
    'get_liquidity_analysis',
    'DatabaseBackup',
    'create_startup_backup',
    'create_pre_migration_backup',
]

