"""
Mutual Funds Utilities

This module provides FIFO tracking and calculations for mutual funds.
Similar to stock holdings but adapted for units and NAV instead of shares and price.
"""

from collections import deque
from datetime import datetime


def calculate_mf_holdings(transactions):
    """
    Calculate mutual fund holdings using FIFO method
    
    Args:
        transactions: List of MutualFundTransaction objects
        
    Returns:
        dict: Dictionary with scheme_id (or scheme_code as fallback) as key and holding details as value
    """
    if not transactions:
        return {}
    
    holdings = {}
    
    # Sort transactions by date
    sorted_transactions = sorted(transactions, key=lambda t: t.transaction_date)
    
    for transaction in sorted_transactions:
        # Use scheme_id as primary key, fallback to scheme_code
        key = transaction.scheme_id if transaction.scheme_id else transaction.scheme_code
        if not key:
            key = f"unknown_{transaction.scheme_name}"
        
        # Initialize holding if not exists
        if key not in holdings:
            holdings[key] = {
                'scheme_id': transaction.scheme_id,
                'scheme_code': transaction.scheme_code,
                'scheme_name': transaction.scheme_name,
                'units': 0,
                'invested_amount': 0,
                'realized_pnl': 0,
                'lots': deque()  # FIFO queue of purchase lots
            }
        
        holding = holdings[key]
        
        # Always update scheme_name to latest (in case it was changed)
        holding['scheme_name'] = transaction.scheme_name
        
        if transaction.transaction_type == 'BUY':
            # Add new lot
            holding['units'] += transaction.units
            holding['invested_amount'] += transaction.amount
            
            # Store lot details: (units, nav, amount)
            holding['lots'].append({
                'units': transaction.units,
                'nav': transaction.nav,
                'amount': transaction.amount,
                'date': transaction.transaction_date
            })
        
        elif transaction.transaction_type == 'SELL':
            # Reduce units using FIFO
            units_to_sell = transaction.units
            total_cost_basis = 0
            
            while units_to_sell > 0 and holding['lots']:
                lot = holding['lots'][0]
                
                if lot['units'] <= units_to_sell:
                    # Consume entire lot
                    units_to_sell -= lot['units']
                    total_cost_basis += lot['amount']
                    holding['lots'].popleft()
                else:
                    # Partial lot consumption
                    cost_basis = (units_to_sell / lot['units']) * lot['amount']
                    total_cost_basis += cost_basis
                    
                    # Update remaining lot
                    lot['units'] -= units_to_sell
                    lot['amount'] -= cost_basis
                    units_to_sell = 0
            
            # Update holdings
            holding['units'] -= transaction.units
            holding['invested_amount'] -= total_cost_basis
            
            # Calculate realized P&L
            sale_proceeds = transaction.amount
            realized_pnl = sale_proceeds - total_cost_basis
            holding['realized_pnl'] += realized_pnl
        
        elif transaction.transaction_type == 'SWITCH':
            # Handle switch transactions (selling one and buying another)
            # For now, treat as sell - to be enhanced later
            pass
    
    return holdings


def calculate_mf_xirr(transactions):
    """
    Calculate XIRR for mutual fund portfolio
    
    Args:
        transactions: List of MutualFundTransaction objects
        
    Returns:
        float: XIRR percentage (e.g., 12.5 for 12.5% returns)
    """
    from utils.xirr import xirr
    
    if not transactions:
        return None
    
    # Prepare cash flows
    cash_flows = []
    
    for txn in transactions:
        # Convert transaction_date to date if it's datetime
        txn_date = txn.transaction_date
        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()
        
        if txn.transaction_type == 'BUY':
            # Outflow (negative)
            cash_flows.append((txn_date, -txn.amount))
        elif txn.transaction_type == 'SELL':
            # Inflow (positive)
            cash_flows.append((txn_date, txn.amount))
    
    # Add current holdings as final inflow
    holdings = calculate_mf_holdings(transactions)
    from datetime import date
    today = date.today()
    
    for scheme_code, holding in holdings.items():
        if holding['units'] > 0:
            # Get current NAV from transaction (ideally from scheme table)
            # For now, use last transaction NAV as approximation
            last_nav = next((t.nav for t in reversed(transactions) if t.scheme_code == scheme_code), 0)
            current_value = holding['units'] * last_nav
            cash_flows.append((today, current_value))
    
    return xirr(cash_flows)


def get_mf_allocation(holdings, schemes):
    """
    Get mutual fund allocation by category (equity/debt/hybrid)
    
    Args:
        holdings: List of holding dictionaries
        schemes: List of MutualFund objects from database
        
    Returns:
        dict: Allocation breakdown by category
    """
    schemes_map = {scheme.scheme_code: scheme for scheme in schemes}
    
    allocation = {
        'equity': 0,
        'debt': 0,
        'hybrid': 0,
        'other': 0
    }
    
    total_value = 0
    
    for holding in holdings:
        scheme_code = holding.get('scheme_code')
        scheme = schemes_map.get(scheme_code)
        
        if scheme and holding.get('units', 0) > 0 and scheme.current_nav:
            value = holding['units'] * scheme.current_nav
            category = scheme.category or 'other'
            
            if category in allocation:
                allocation[category] += value
            else:
                allocation['other'] += value
            
            total_value += value
    
    # Convert to percentages
    if total_value > 0:
        return {
            category: round((amount / total_value) * 100, 2)
            for category, amount in allocation.items()
        }
    
    return allocation


def calculate_mf_holding_period_days(transactions, scheme_code):
    """
    Calculate FIFO-weighted holding period for a mutual fund scheme
    
    Args:
        transactions: All MutualFundTransaction objects
        scheme_code: Scheme code to calculate for
        
    Returns:
        int: Average holding period in days (FIFO-weighted)
    """
    from datetime import date
    
    # Filter transactions for this scheme
    scheme_transactions = [t for t in transactions if t.scheme_code == scheme_code]
    
    if not scheme_transactions:
        return 0
    
    # Calculate holdings with FIFO
    holdings_dict = calculate_mf_holdings(scheme_transactions)
    holding = holdings_dict.get(scheme_code)
    
    if not holding or holding['units'] <= 0:
        return 0
    
    # Calculate weighted average holding period from remaining lots
    today = date.today()
    total_units = 0
    weighted_days = 0
    
    for lot in holding['lots']:
        lot_date = lot['date']
        if isinstance(lot_date, datetime):
            lot_date = lot_date.date()
        
        days_held = (today - lot_date).days
        weighted_days += days_held * lot['units']
        total_units += lot['units']
    
    if total_units > 0:
        return int(weighted_days / total_units)
    
    return 0

