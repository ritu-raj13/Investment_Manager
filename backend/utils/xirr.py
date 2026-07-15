"""
XIRR (Extended Internal Rate of Return) calculation utilities
"""
import math
from datetime import datetime, date
from typing import List, Optional, Tuple

MIN_RATE = -0.99
MAX_RATE = 10.0


def _discount_factor(rate: float, years: float) -> float:
    """Safely compute (1 + rate) ** years without floating-point overflow."""
    if years == 0:
        return 1.0
    if rate <= -1.0:
        return float('inf') if years > 0 else 0.0
    try:
        log_df = years * math.log1p(rate)
        if log_df > 700:
            return float('inf')
        if log_df < -700:
            return 0.0
        return math.exp(log_df)
    except (OverflowError, ValueError):
        return float('inf') if rate > 0 else 0.0


def _npv(rate: float, normalized_flows: List[Tuple[float, float]]) -> float:
    total = 0.0
    for days, amount in normalized_flows:
        years = days / 365.0
        df = _discount_factor(rate, years)
        if math.isinf(df):
            continue
        if df == 0.0:
            return float('nan')
        total += amount / df
    return total


def _npv_and_derivative(rate: float, normalized_flows: List[Tuple[float, float]]) -> Tuple[float, float]:
    npv = 0.0
    dnpv = 0.0
    for days, amount in normalized_flows:
        years = days / 365.0
        df = _discount_factor(rate, years)
        if math.isinf(df) or df == 0.0:
            continue
        npv += amount / df
        dnpv += -years * amount / (df * (1 + rate))
    return npv, dnpv


def _find_sign_bracket(
    normalized_flows: List[Tuple[float, float]],
    low: float = MIN_RATE,
    high: float = MAX_RATE,
    steps: int = 200,
) -> Optional[Tuple[float, float]]:
    """Find a rate interval where NPV changes sign."""
    prev_rate = low
    prev_npv = _npv(prev_rate, normalized_flows)
    if math.isnan(prev_npv):
        prev_npv = 0.0

    for i in range(1, steps + 1):
        rate = low + (high - low) * i / steps
        npv = _npv(rate, normalized_flows)
        if math.isnan(npv):
            continue
        if prev_npv * npv < 0:
            return prev_rate, rate
        prev_rate, prev_npv = rate, npv
    return None


def _xirr_bisection(
    normalized_flows: List[Tuple[float, float]],
    low: float,
    high: float,
    tolerance: float = 1e-6,
    max_iterations: int = 100,
) -> Optional[float]:
    npv_low = _npv(low, normalized_flows)
    npv_high = _npv(high, normalized_flows)
    if math.isnan(npv_low) or math.isnan(npv_high) or npv_low * npv_high > 0:
        return None

    for _ in range(max_iterations):
        mid = (low + high) / 2.0
        npv_mid = _npv(mid, normalized_flows)
        if math.isnan(npv_mid):
            return None
        if abs(npv_mid) < tolerance:
            return mid
        if npv_low * npv_mid < 0:
            high = mid
            npv_high = npv_mid
        else:
            low = mid
            npv_low = npv_mid
    return None


def _xirr_newton(
    normalized_flows: List[Tuple[float, float]],
    guess: float,
    max_iterations: int,
    tolerance: float,
) -> Optional[float]:
    rate = max(MIN_RATE, min(MAX_RATE, guess))

    for _ in range(max_iterations):
        try:
            npv, dnpv = _npv_and_derivative(rate, normalized_flows)
        except (OverflowError, ZeroDivisionError):
            return None

        if abs(npv) < tolerance:
            return rate
        if dnpv == 0:
            return None

        new_rate = rate - npv / dnpv
        new_rate = max(MIN_RATE, min(MAX_RATE, new_rate))
        rate = new_rate

    return None


def xirr(cash_flows: List[Tuple[date, float]], guess: float = 0.1, max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculate XIRR (Extended Internal Rate of Return).

    Uses Newton-Raphson with safe discounting, falling back to bisection when
    the solver diverges or overflows.

    Args:
        cash_flows: List of tuples (date, amount) where:
                   - Negative amounts = investments (outflows)
                   - Positive amounts = returns (inflows)
        guess: Initial guess for the rate (default 10%)
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance

    Returns:
        XIRR as a decimal (e.g., 0.15 for 15%)
        Returns None if calculation fails or invalid data
    """
    if not cash_flows or len(cash_flows) < 2:
        return None

    normalized_cash_flows = []
    for cf_date, amount in cash_flows:
        if isinstance(cf_date, datetime):
            cf_date = cf_date.date()
        normalized_cash_flows.append((cf_date, amount))

    cash_flows = sorted(normalized_cash_flows, key=lambda x: x[0])

    signs = [1 if amount > 0 else -1 for _, amount in cash_flows if amount != 0]
    if len(set(signs)) < 2:
        return None

    start_date = cash_flows[0][0]
    normalized_flows = [
        ((cf_date - start_date).days, amount)
        for cf_date, amount in cash_flows
    ]

    for initial_guess in (guess, 0.0, -0.5, 0.5):
        result = _xirr_newton(normalized_flows, initial_guess, max_iterations, tolerance)
        if result is not None:
            return result

    bracket = _find_sign_bracket(normalized_flows)
    if bracket is not None:
        return _xirr_bisection(normalized_flows, bracket[0], bracket[1], tolerance, max_iterations)

    return None


def calculate_portfolio_xirr(transactions: List, current_portfolio_value: float) -> float:
    """
    Calculate XIRR for entire portfolio.

    Args:
        transactions: List of PortfolioTransaction objects
        current_portfolio_value: Current market value of entire portfolio

    Returns:
        XIRR as percentage (e.g., 15.5 for 15.5%)
        Returns None if calculation fails
    """
    if not transactions:
        return None

    cash_flows = []

    for txn in transactions:
        txn_date = txn.transaction_date

        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()

        if txn.transaction_type == 'BUY':
            amount = -(txn.quantity * txn.price)
        elif txn.transaction_type == 'SELL':
            amount = txn.quantity * txn.price
        else:
            continue

        cash_flows.append((txn_date, amount))

    if current_portfolio_value > 0:
        today = datetime.now().date()
        cash_flows.append((today, current_portfolio_value))

    xirr_rate = xirr(cash_flows)

    if xirr_rate is not None:
        return round(xirr_rate * 100, 2)

    return None


def format_xirr(xirr_value: float) -> str:
    """
    Format XIRR value for display.

    Args:
        xirr_value: XIRR percentage (e.g., 15.5)

    Returns:
        Formatted string (e.g., "+15.5%" or "-5.2%")
    """
    if xirr_value is None:
        return "N/A"

    sign = "+" if xirr_value >= 0 else ""
    return f"{sign}{xirr_value:.2f}%"
