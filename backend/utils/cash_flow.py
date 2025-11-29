"""
Cash Flow Utilities

This module provides income/expense tracking and analysis functions.
"""

from datetime import datetime, date, timedelta
from collections import defaultdict


def calculate_monthly_cash_flow(income_transactions, expense_transactions, start_date, end_date):
    """
    Calculate monthly cash flow (income vs expenses)
    
    Args:
        income_transactions: List of IncomeTransaction objects
        expense_transactions: List of ExpenseTransaction objects
        start_date: Start date for analysis
        end_date: End date for analysis
        
    Returns:
        list: Monthly cash flow data with income, expense, and net
    """
    # Ensure dates are date objects
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()
    
    # Group by month
    monthly_income = defaultdict(float)
    monthly_expense = defaultdict(float)
    
    for txn in income_transactions:
        txn_date = txn.transaction_date
        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()
        
        if start_date <= txn_date <= end_date:
            month_key = txn_date.strftime('%Y-%m')
            monthly_income[month_key] += txn.amount
    
    for txn in expense_transactions:
        txn_date = txn.transaction_date
        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()
        
        if start_date <= txn_date <= end_date:
            month_key = txn_date.strftime('%Y-%m')
            monthly_expense[month_key] += txn.amount
    
    # Generate month list
    cash_flow = []
    current_date = start_date.replace(day=1)
    
    while current_date <= end_date:
        month_key = current_date.strftime('%Y-%m')
        income = monthly_income.get(month_key, 0)
        expense = monthly_expense.get(month_key, 0)
        net = income - expense
        
        cash_flow.append({
            'month': month_key,
            'income': round(income, 2),
            'expense': round(expense, 2),
            'net': round(net, 2),
            'savings_rate': round((net / income * 100) if income > 0 else 0, 2)
        })
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            current_date = current_date.replace(month=current_date.month + 1)
    
    return cash_flow


def get_expense_trends(expense_transactions, months=12):
    """
    Get expense trends over last N months
    
    Args:
        expense_transactions: List of ExpenseTransaction objects
        months: Number of months to analyze
        
    Returns:
        dict: Expense trends by month and category
    """
    today = date.today()
    start_date = today - timedelta(days=months * 30)
    
    # Group by month and category
    monthly_trends = defaultdict(lambda: defaultdict(float))
    
    for txn in expense_transactions:
        txn_date = txn.transaction_date
        if isinstance(txn_date, datetime):
            txn_date = txn_date.date()
        
        if txn_date >= start_date:
            month_key = txn_date.strftime('%Y-%m')
            category = txn.category
            monthly_trends[month_key][category] += txn.amount
    
    # Format output
    trends = []
    for month_key in sorted(monthly_trends.keys()):
        trends.append({
            'month': month_key,
            'categories': dict(monthly_trends[month_key]),
            'total': round(sum(monthly_trends[month_key].values()), 2)
        })
    
    return trends


def calculate_savings_rate(income_transactions, expense_transactions, period='monthly'):
    """
    Calculate savings rate (% of income saved)
    
    Args:
        income_transactions: List of IncomeTransaction objects
        expense_transactions: List of ExpenseTransaction objects
        period: 'monthly' or 'yearly' or 'all'
        
    Returns:
        dict: Savings rate data
    """
    today = date.today()
    
    # Determine date range
    if period == 'monthly':
        start_date = today.replace(day=1)
    elif period == 'yearly':
        start_date = today.replace(month=1, day=1)
    else:  # all
        start_date = date(2000, 1, 1)  # Far past date
    
    # Calculate totals
    total_income = sum(
        txn.amount for txn in income_transactions
        if (txn.transaction_date if isinstance(txn.transaction_date, date) else txn.transaction_date.date()) >= start_date
    )
    
    total_expense = sum(
        txn.amount for txn in expense_transactions
        if (txn.transaction_date if isinstance(txn.transaction_date, date) else txn.transaction_date.date()) >= start_date
    )
    
    net_savings = total_income - total_expense
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    return {
        'period': period,
        'total_income': round(total_income, 2),
        'total_expense': round(total_expense, 2),
        'net_savings': round(net_savings, 2),
        'savings_rate': round(savings_rate, 2)
    }


def get_category_breakdown(transactions, transaction_type='expense'):
    """
    Get breakdown of transactions by category
    
    Args:
        transactions: List of transaction objects (Income or Expense)
        transaction_type: 'income' or 'expense'
        
    Returns:
        dict: Category breakdown with totals and percentages
    """
    category_totals = defaultdict(float)
    total_amount = 0
    
    for txn in transactions:
        if transaction_type == 'expense':
            category = txn.category
        else:
            category = txn.source
        
        category_totals[category] += txn.amount
        total_amount += txn.amount
    
    # Calculate percentages
    breakdown = []
    for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_amount * 100) if total_amount > 0 else 0
        breakdown.append({
            'category': category,
            'amount': round(amount, 2),
            'percentage': round(percentage, 2)
        })
    
    return {
        'total': round(total_amount, 2),
        'categories': breakdown
    }


def get_recurring_transactions(transactions):
    """
    Identify recurring transactions (marked as recurring)
    
    Args:
        transactions: List of transaction objects (Income or Expense)
        
    Returns:
        list: Recurring transactions with frequency analysis
    """
    recurring = []
    
    for txn in transactions:
        if txn.is_recurring:
            recurring.append({
                'id': txn.id,
                'description': txn.description or (txn.source if hasattr(txn, 'source') else txn.category),
                'amount': txn.amount,
                'last_date': txn.transaction_date.isoformat() if txn.transaction_date else None,
                'type': 'income' if hasattr(txn, 'source') else 'expense'
            })
    
    return recurring


def predict_next_month_expense(expense_transactions, months_to_analyze=6):
    """
    Predict next month's expense based on historical averages
    
    Args:
        expense_transactions: List of ExpenseTransaction objects
        months_to_analyze: Number of past months to consider
        
    Returns:
        dict: Predicted expense by category and total
    """
    today = date.today()
    start_date = today - timedelta(days=months_to_analyze * 30)
    
    # Filter recent transactions
    recent = [
        txn for txn in expense_transactions
        if (txn.transaction_date if isinstance(txn.transaction_date, date) else txn.transaction_date.date()) >= start_date
    ]
    
    # Calculate average by category
    category_totals = defaultdict(list)
    
    # Group by month and category
    monthly_data = defaultdict(lambda: defaultdict(float))
    
    for txn in recent:
        txn_date = txn.transaction_date if isinstance(txn.transaction_date, date) else txn.transaction_date.date()
        month_key = txn_date.strftime('%Y-%m')
        monthly_data[month_key][txn.category] += txn.amount
    
    # Calculate averages
    predictions = {}
    total_predicted = 0
    
    for category in set(txn.category for txn in recent):
        amounts = [monthly_data[month].get(category, 0) for month in monthly_data.keys()]
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        predictions[category] = round(avg_amount, 2)
        total_predicted += avg_amount
    
    return {
        'total_predicted': round(total_predicted, 2),
        'by_category': predictions,
        'confidence': 'medium' if len(monthly_data) >= 3 else 'low'
    }

