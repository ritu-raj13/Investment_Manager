"""
XIRR (Extended Internal Rate of Return) calculation utilities
"""
from datetime import datetime, date
from typing import List, Tuple


def xirr(cash_flows: List[Tuple[date, float]], guess: float = 0.1, max_iterations: int = 100, tolerance: float = 1e-6) -> float:
    """
    Calculate XIRR (Extended Internal Rate of Return) using Newton-Raphson method.
    
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
    
    # Normalize all dates to date objects (handle both date and datetime)
    normalized_cash_flows = []
    for cf_date, amount in cash_flows:
        if isinstance(cf_date, datetime):
            cf_date = cf_date.date()
        normalized_cash_flows.append((cf_date, amount))
    
    # Sort by date
    cash_flows = sorted(normalized_cash_flows, key=lambda x: x[0])
    
    # Check if all cash flows have the same sign (invalid for XIRR)
    signs = [1 if amount > 0 else -1 for _, amount in cash_flows if amount != 0]
    if len(set(signs)) < 2:
        return None  # Need both positive and negative cash flows
    
    # Use first date as reference (t=0)
    start_date = cash_flows[0][0]
    
    # Convert to (days_from_start, amount) pairs
    normalized_flows = []
    for cf_date, amount in cash_flows:
        days = (cf_date - start_date).days
        normalized_flows.append((days, amount))
    
    rate = guess
    
    for iteration in range(max_iterations):
        # Calculate NPV (Net Present Value) and its derivative
        npv = 0
        dnpv = 0
        
        for days, amount in normalized_flows:
            years = days / 365.0
            
            # NPV = Σ(cash_flow / (1 + rate)^years)
            discount_factor = (1 + rate) ** years
            npv += amount / discount_factor
            
            # Derivative of NPV with respect to rate
            # d(NPV)/d(rate) = Σ(-years * cash_flow / (1 + rate)^(years+1))
            dnpv += -years * amount / ((1 + rate) ** (years + 1))
        
        # Check convergence
        if abs(npv) < tolerance:
            return rate
        
        # Newton-Raphson: new_rate = old_rate - f(rate) / f'(rate)
        if dnpv == 0:
            return None  # Avoid division by zero
        
        new_rate = rate - npv / dnpv
        
        # Prevent rate from going too negative (< -99%)
        if new_rate <= -0.99:
            new_rate = -0.99
        
        rate = new_rate
    
    # If we didn't converge, return None
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
    
    # Add all transactions
    for txn in transactions:
        txn_date = txn.transaction_date
        
        # Normalize to date object (handle both date and datetime)
        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()
        
        if txn.transaction_type == 'BUY':
            # Money out (negative)
            amount = -(txn.quantity * txn.price)
        elif txn.transaction_type == 'SELL':
            # Money in (positive)
            amount = txn.quantity * txn.price
        else:
            continue
        
        cash_flows.append((txn_date, amount))
    
    # Add current portfolio value as final inflow (today)
    if current_portfolio_value > 0:
        today = datetime.now().date()
        cash_flows.append((today, current_portfolio_value))
    
    # Calculate XIRR
    xirr_rate = xirr(cash_flows)
    
    if xirr_rate is not None:
        return round(xirr_rate * 100, 2)  # Convert to percentage
    
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

