"""
Data validation utilities for Investment Manager
"""
from typing import Optional, Tuple


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

