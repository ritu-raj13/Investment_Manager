"""
Utility functions for Investment Manager backend
"""
from datetime import datetime
from typing import Optional, Tuple, Dict, List


def parse_zone(zone_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse zone string and return (min, max) tuple.
    
    Args:
        zone_str: Zone string like "250-300" or "250"
    
    Returns:
        Tuple of (min_val, max_val) or (None, None) if invalid
    
    Examples:
        "250-300" -> (250.0, 300.0)
        "250" -> (250.0, 250.0)
        "" -> (None, None)
    """
    if not zone_str:
        return None, None
    
    zone_str = str(zone_str).strip()
    
    if '-' in zone_str:
        parts = zone_str.split('-')
        try:
            return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            return None, None
    else:
        try:
            val = float(zone_str)
            return val, val
        except ValueError:
            return None, None


def calculate_holdings(transactions: List) -> Dict[str, Dict]:
    """
    Calculate current holdings from transaction history.
    
    Args:
        transactions: List of PortfolioTransaction objects
    
    Returns:
        Dict mapping symbol to holding data (quantity, invested_amount)
    """
    holdings = {}
    
    for txn in transactions:
        symbol = txn.stock_symbol
        if symbol not in holdings:
            holdings[symbol] = {
                'symbol': symbol,
                'name': txn.stock_name,
                'quantity': 0,
                'invested_amount': 0,
                'transactions': []
            }
        
        if txn.transaction_type == 'BUY':
            holdings[symbol]['quantity'] += txn.quantity
            holdings[symbol]['invested_amount'] += txn.quantity * txn.price
        elif txn.transaction_type == 'SELL':
            holdings[symbol]['quantity'] -= txn.quantity
            holdings[symbol]['invested_amount'] -= txn.quantity * txn.price
        
        holdings[symbol]['transactions'].append(txn.to_dict())
    
    # Filter out holdings with zero or negative quantity
    return {k: v for k, v in holdings.items() if v['quantity'] > 0}


def validate_transaction_data(data: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate transaction form data.
    
    Args:
        data: Transaction form data dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['stock_symbol', 'stock_name', 'transaction_type', 
                      'quantity', 'price', 'transaction_date']
    
    # Check required fields
    missing_fields = [field for field in required_fields if not data.get(field)]
    if missing_fields:
        return False, f'Missing required fields: {", ".join(missing_fields)}'
    
    # Validate string fields
    stock_symbol = data['stock_symbol'].strip()
    stock_name = data['stock_name'].strip()
    
    if not stock_symbol:
        return False, 'Stock symbol cannot be empty'
    
    if not stock_name:
        return False, 'Stock name cannot be empty'
    
    # Validate numeric fields
    try:
        quantity = float(data['quantity'])
        price = float(data['price'])
        
        if quantity <= 0:
            return False, 'Quantity must be greater than 0'
        
        if price <= 0:
            return False, 'Price must be greater than 0'
    except (ValueError, TypeError):
        return False, 'Quantity and price must be valid numbers'
    
    return True, None


def is_in_zone(current_price: float, zone_min: float, zone_max: float, 
               threshold_pct: float = 0.05) -> Tuple[bool, bool]:
    """
    Check if price is in zone or near zone.
    
    Args:
        current_price: Current stock price
        zone_min: Zone minimum value
        zone_max: Zone maximum value
        threshold_pct: Threshold percentage for "near" (default 5%)
    
    Returns:
        Tuple of (is_in_zone, is_near_zone)
    """
    if zone_min is None or zone_max is None:
        return False, False
    
    # Check if in zone
    if zone_min <= current_price <= zone_max:
        return True, False
    
    # Check if near zone (within threshold)
    lower_threshold = zone_min * (1 - threshold_pct)
    upper_threshold = zone_max * (1 + threshold_pct)
    
    if lower_threshold <= current_price < zone_min or zone_max < current_price <= upper_threshold:
        return False, True
    
    return False, False


def format_refresh_response(total: int, updated: int, failed: int) -> dict:
    """
    Format standardized refresh response.
    
    Args:
        total: Total stocks processed
        updated: Successfully updated count
        failed: Failed count
    
    Returns:
        Standardized response dictionary
    """
    return {
        'message': f'Total: {total}, Success: {updated}, Failed: {failed}',
        'total': total,
        'updated': updated,
        'failed': failed
    }


def clean_symbol(symbol: str) -> str:
    """
    Clean and uppercase stock symbol.
    
    Args:
        symbol: Stock symbol (may include .NS or .BO)
    
    Returns:
        Cleaned uppercase symbol
    """
    return symbol.strip().upper()

