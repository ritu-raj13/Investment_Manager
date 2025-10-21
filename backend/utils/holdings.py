"""
Holdings calculation utilities for Investment Manager
"""
from typing import Dict, List


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

