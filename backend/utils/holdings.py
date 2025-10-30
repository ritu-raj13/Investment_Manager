"""
Holdings calculation utilities for Investment Manager
"""
from typing import Dict, List
from datetime import datetime
from collections import deque


def normalize_symbol(symbol):
    """Remove .NS or .BO suffix for consistent grouping"""
    if not symbol:
        return ''
    return symbol.replace('.NS', '').replace('.BO', '').upper()


def calculate_holding_period_days(lots: deque) -> int:
    """
    Calculate weighted average holding period in days using FIFO lots.
    
    Args:
        lots: deque of remaining lots [(date, quantity, price), ...]
    
    Returns:
        Weighted average holding period in days
    """
    if not lots:
        return 0
    
    today = datetime.now().date()
    total_quantity = sum(lot[1] for lot in lots)
    
    if total_quantity == 0:
        return 0
    
    weighted_days = 0
    for purchase_date, quantity, _ in lots:
        # Convert purchase_date to date if it's a datetime object (handles both date and datetime)
        if isinstance(purchase_date, datetime):
            purchase_date = purchase_date.date()
        
        days_held = (today - purchase_date).days
        weight = quantity / total_quantity
        weighted_days += days_held * weight
    
    return int(weighted_days)


def calculate_holdings(transactions: List) -> Dict[str, Dict]:
    """
    Calculate current holdings from transaction history using FIFO method.
    
    Args:
        transactions: List of PortfolioTransaction objects
    
    Returns:
        Dict mapping symbol to holding data (quantity, invested_amount, realized_pnl, holding_period_days, lots)
    """
    holdings = {}
    
    # CRITICAL: Sort transactions by date to ensure correct FIFO and average cost calculation
    # Process in chronological order: oldest first
    sorted_transactions = sorted(transactions, key=lambda t: t.transaction_date)
    
    for txn in sorted_transactions:
        # CRITICAL: Normalize symbol to handle .NS/.BO suffix inconsistencies
        # Use the FIRST symbol variant we see (usually has suffix)
        symbol = txn.stock_symbol
        normalized = normalize_symbol(symbol)
        
        # Find if we already have this stock under a different symbol variant
        existing_key = None
        for key in holdings.keys():
            if normalize_symbol(key) == normalized:
                existing_key = key
                break
        
        # Use existing key if found, otherwise use current symbol
        if existing_key:
            symbol = existing_key
        if symbol not in holdings:
            holdings[symbol] = {
                'symbol': symbol,
                'name': txn.stock_name,
                'quantity': 0,
                'invested_amount': 0,
                'realized_pnl': 0,  # Track profit/loss from SELL transactions
                'transactions': [],
                'lots': deque()  # FIFO queue of purchase lots: [(date, quantity, price), ...]
            }
        
        if txn.transaction_type == 'BUY':
            # Add new lot to the end (newest)
            holdings[symbol]['lots'].append((txn.transaction_date, txn.quantity, txn.price))
            holdings[symbol]['quantity'] += txn.quantity
            holdings[symbol]['invested_amount'] += txn.quantity * txn.price
            
        elif txn.transaction_type == 'SELL':
            # FIFO: Remove from oldest lots first
            remaining_to_sell = txn.quantity
            total_cost_basis = 0  # Track cost basis of sold shares
            
            while remaining_to_sell > 0 and holdings[symbol]['lots']:
                lot_date, lot_qty, lot_price = holdings[symbol]['lots'][0]
                
                if lot_qty <= remaining_to_sell:
                    # Sell entire lot
                    total_cost_basis += lot_qty * lot_price
                    realized_pnl = (txn.price - lot_price) * lot_qty
                    holdings[symbol]['realized_pnl'] += realized_pnl
                    remaining_to_sell -= lot_qty
                    holdings[symbol]['lots'].popleft()  # Remove sold lot
                else:
                    # Partially sell from this lot
                    total_cost_basis += remaining_to_sell * lot_price
                    realized_pnl = (txn.price - lot_price) * remaining_to_sell
                    holdings[symbol]['realized_pnl'] += realized_pnl
                    # Update lot with remaining quantity
                    holdings[symbol]['lots'][0] = (lot_date, lot_qty - remaining_to_sell, lot_price)
                    remaining_to_sell = 0
            
            # Reduce quantity and invested amount
            holdings[symbol]['quantity'] -= txn.quantity
            holdings[symbol]['invested_amount'] -= total_cost_basis
        
        holdings[symbol]['transactions'].append(txn.to_dict())
    
    # Calculate holding period for each stock and mark current holdings
    for symbol, data in holdings.items():
        data['has_current_holdings'] = data['quantity'] > 0
        data['holding_period_days'] = calculate_holding_period_days(data['lots']) if data['quantity'] > 0 else 0
        # Remove lots from return data (internal use only)
        del data['lots']
    
    return holdings

