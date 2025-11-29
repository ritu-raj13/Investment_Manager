"""
Net Worth Utilities

This module provides calculations for total net worth and asset allocation across all asset types.
"""

from utils.holdings import calculate_holdings
from utils.mutual_funds import calculate_mf_holdings
from datetime import datetime, date


def calculate_total_net_worth(all_assets):
    """
    Calculate total net worth across all assets
    
    Args:
        all_assets: Dictionary with keys:
            - stocks: PortfolioTransaction list
            - mutual_funds: MutualFundTransaction list
            - fixed_deposits: FixedDeposit list
            - epf: EPFAccount list
            - nps: NPSAccount list
            - savings: SavingsAccount list
            - lending: LendingRecord list (active only)
            - other: OtherInvestment list
            
    Returns:
        dict: Net worth breakdown by asset type and total
    """
    net_worth = {
        'stocks': 0,
        'mutual_funds': 0,
        'fixed_deposits': 0,
        'epf': 0,
        'nps': 0,
        'savings': 0,
        'lending': 0,
        'other': 0,
        'total': 0
    }
    
    # Calculate stock holdings value
    stock_holdings = calculate_holdings(all_assets.get('stocks', []))
    net_worth['stocks'] = sum(h['invested_amount'] for h in stock_holdings.values() if h['quantity'] > 0)
    
    # Calculate mutual fund holdings value
    mf_holdings = calculate_mf_holdings(all_assets.get('mutual_funds', []))
    net_worth['mutual_funds'] = sum(h['invested_amount'] for h in mf_holdings.values() if h['units'] > 0)
    
    # Calculate fixed deposits value
    fds = all_assets.get('fixed_deposits', [])
    net_worth['fixed_deposits'] = sum(fd.principal_amount for fd in fds if fd.status == 'active')
    
    # Calculate EPF value
    epf_accounts = all_assets.get('epf', [])
    net_worth['epf'] = sum(acc.current_balance for acc in epf_accounts)
    
    # Calculate NPS value
    nps_accounts = all_assets.get('nps', [])
    net_worth['nps'] = sum(acc.current_value for acc in nps_accounts)
    
    # Calculate savings value
    savings_accounts = all_assets.get('savings', [])
    net_worth['savings'] = sum(acc.current_balance for acc in savings_accounts)
    
    # Calculate lending value (outstanding amounts)
    lending_records = all_assets.get('lending', [])
    net_worth['lending'] = sum(rec.outstanding_amount or 0 for rec in lending_records if rec.status == 'active')
    
    # Calculate other investments value
    other_investments = all_assets.get('other', [])
    net_worth['other'] = sum(inv.current_value or inv.purchase_value for inv in other_investments)
    
    # Calculate total
    net_worth['total'] = sum(net_worth.values()) - net_worth['total']  # Exclude total from sum
    
    # Round all values
    for key in net_worth:
        net_worth[key] = round(net_worth[key], 2)
    
    return net_worth


def get_asset_allocation(all_assets):
    """
    Get asset allocation breakdown (equity/debt/cash/alternative)
    
    Args:
        all_assets: Dictionary with all asset types
        
    Returns:
        dict: Allocation percentages by asset class
    """
    allocation = {
        'equity': 0,      # Stocks + Equity MFs
        'debt': 0,        # Debt MFs + FDs + EPF + NPS (debt portion)
        'cash': 0,        # Savings accounts
        'alternative': 0  # Lending + Other investments
    }
    
    # Stocks are equity
    stock_holdings = calculate_holdings(all_assets.get('stocks', []))
    allocation['equity'] += sum(h['invested_amount'] for h in stock_holdings.values() if h['quantity'] > 0)
    
    # Mutual funds - categorize by type
    # TODO: Implement MF categorization when scheme data is available
    mf_holdings = calculate_mf_holdings(all_assets.get('mutual_funds', []))
    mf_value = sum(h['invested_amount'] for h in mf_holdings.values() if h['units'] > 0)
    # For now, assume 60% equity, 40% debt (can be refined with actual MF categories)
    allocation['equity'] += mf_value * 0.6
    allocation['debt'] += mf_value * 0.4
    
    # Fixed deposits are debt
    fds = all_assets.get('fixed_deposits', [])
    allocation['debt'] += sum(fd.principal_amount for fd in fds if fd.status == 'active')
    
    # EPF is debt
    epf_accounts = all_assets.get('epf', [])
    allocation['debt'] += sum(acc.current_balance for acc in epf_accounts)
    
    # NPS - assume 50% equity, 50% debt
    nps_accounts = all_assets.get('nps', [])
    nps_value = sum(acc.current_value for acc in nps_accounts)
    allocation['equity'] += nps_value * 0.5
    allocation['debt'] += nps_value * 0.5
    
    # Savings accounts are cash
    savings_accounts = all_assets.get('savings', [])
    allocation['cash'] += sum(acc.current_balance for acc in savings_accounts)
    
    # Lending is alternative
    lending_records = all_assets.get('lending', [])
    allocation['alternative'] += sum(rec.outstanding_amount or 0 for rec in lending_records if rec.status == 'active')
    
    # Other investments are alternative
    other_investments = all_assets.get('other', [])
    allocation['alternative'] += sum(inv.current_value or inv.purchase_value for inv in other_investments)
    
    # Calculate percentages
    total = sum(allocation.values())
    
    if total > 0:
        return {
            'equity': round((allocation['equity'] / total) * 100, 2),
            'debt': round((allocation['debt'] / total) * 100, 2),
            'cash': round((allocation['cash'] / total) * 100, 2),
            'alternative': round((allocation['alternative'] / total) * 100, 2),
            'total_value': round(total, 2)
        }
    
    return {
        'equity': 0,
        'debt': 0,
        'cash': 0,
        'alternative': 0,
        'total_value': 0
    }


def calculate_debt_to_income_ratio(liabilities, monthly_income):
    """
    Calculate debt-to-income ratio
    
    Args:
        liabilities: Total liabilities (loans, credit card debt, etc.)
        monthly_income: Average monthly income
        
    Returns:
        float: Debt-to-income ratio as percentage
    """
    if monthly_income == 0:
        return 0
    
    return round((liabilities / monthly_income) * 100, 2)


def calculate_emergency_fund_months(cash_balance, monthly_expenses):
    """
    Calculate how many months of expenses are covered by emergency fund (cash)
    
    Args:
        cash_balance: Total cash/savings balance
        monthly_expenses: Average monthly expenses
        
    Returns:
        float: Number of months covered
    """
    if monthly_expenses == 0:
        return 0
    
    return round(cash_balance / monthly_expenses, 1)


def get_asset_growth_rate(current_value, invested_value):
    """
    Calculate simple growth rate
    
    Args:
        current_value: Current asset value
        invested_value: Total invested amount
        
    Returns:
        float: Growth rate as percentage
    """
    if invested_value == 0:
        return 0
    
    return round(((current_value - invested_value) / invested_value) * 100, 2)


def calculate_portfolio_diversification_score(holdings_by_type):
    """
    Calculate diversification score using Herfindahl Index
    Lower score = more diversified
    
    Args:
        holdings_by_type: Dictionary with asset type as key and value as amount
        
    Returns:
        dict: Diversification score and rating
    """
    total = sum(holdings_by_type.values())
    
    if total == 0:
        return {'score': 0, 'rating': 'N/A'}
    
    # Calculate Herfindahl Index (sum of squared market shares)
    herfindahl_index = sum((value / total) ** 2 for value in holdings_by_type.values())
    
    # Normalize to 0-100 scale (lower is better)
    # With 8 asset types, perfect diversification = 1/8 = 0.125 each
    # HHI would be 8 * (0.125^2) = 0.125
    # Worst case (all in one) HHI = 1
    
    diversification_score = int((1 - herfindahl_index) * 100)
    
    # Rating
    if diversification_score >= 80:
        rating = 'Excellent'
    elif diversification_score >= 60:
        rating = 'Good'
    elif diversification_score >= 40:
        rating = 'Moderate'
    else:
        rating = 'Poor'
    
    return {
        'score': diversification_score,
        'rating': rating,
        'herfindahl_index': round(herfindahl_index, 3)
    }


def get_liquidity_analysis(all_assets):
    """
    Analyze portfolio liquidity (how quickly assets can be converted to cash)
    
    Args:
        all_assets: Dictionary with all asset types
        
    Returns:
        dict: Liquidity breakdown
    """
    net_worth = calculate_total_net_worth(all_assets)
    total = net_worth['total']
    
    if total == 0:
        return {
            'high_liquidity': 0,
            'medium_liquidity': 0,
            'low_liquidity': 0
        }
    
    # High liquidity: Stocks, MF, Savings (can be sold/withdrawn quickly)
    high_liquidity = net_worth['stocks'] + net_worth['mutual_funds'] + net_worth['savings']
    
    # Medium liquidity: FDs (can be broken early with penalty), Other
    medium_liquidity = net_worth['fixed_deposits'] + net_worth['other']
    
    # Low liquidity: EPF, NPS (locked till retirement), Lending
    low_liquidity = net_worth['epf'] + net_worth['nps'] + net_worth['lending']
    
    return {
        'high_liquidity': round((high_liquidity / total) * 100, 2),
        'medium_liquidity': round((medium_liquidity / total) * 100, 2),
        'low_liquidity': round((low_liquidity / total) * 100, 2),
        'high_liquidity_value': round(high_liquidity, 2),
        'medium_liquidity_value': round(medium_liquidity, 2),
        'low_liquidity_value': round(low_liquidity, 2)
    }


def calculate_unified_portfolio_xirr(all_assets):
    """
    Calculate unified XIRR across all asset types (Phase 3)
    
    Args:
        all_assets: Dictionary with all asset types and their transactions/details
        
    Returns:
        dict: XIRR data including overall and by asset type
    """
    from utils.xirr import xirr
    
    all_cash_flows = []
    xirr_by_type = {}
    
    # Process Stock transactions
    stock_transactions = all_assets.get('stocks', [])
    stock_flows = []
    for txn in stock_transactions:
        txn_date = txn.transaction_date if isinstance(txn.transaction_date, date) else txn.transaction_date.date()
        if txn.transaction_type == 'BUY':
            amount = -(txn.quantity * txn.price)
        elif txn.transaction_type == 'SELL':
            amount = txn.quantity * txn.price
        else:
            continue
        stock_flows.append((txn_date, amount))
        all_cash_flows.append((txn_date, amount))
    
    # Add current stock value
    stock_holdings = calculate_holdings(stock_transactions)
    current_stock_value = sum(h['invested_amount'] for h in stock_holdings.values() if h['quantity'] > 0)
    if current_stock_value > 0:
        today = datetime.now().date()
        stock_flows.append((today, current_stock_value))
        all_cash_flows.append((today, current_stock_value))
    
    stock_xirr = xirr(stock_flows) if len(stock_flows) >= 2 else None
    xirr_by_type['stocks'] = round(stock_xirr * 100, 2) if stock_xirr else None
    
    # Process Mutual Fund transactions
    mf_transactions = all_assets.get('mutual_funds', [])
    mf_flows = []
    for txn in mf_transactions:
        txn_date = txn.transaction_date if isinstance(txn.transaction_date, date) else txn.transaction_date.date()
        if txn.transaction_type == 'BUY':
            amount = -txn.amount
        elif txn.transaction_type == 'SELL':
            amount = txn.amount
        else:
            continue
        mf_flows.append((txn_date, amount))
        all_cash_flows.append((txn_date, amount))
    
    # Add current MF value
    mf_holdings = calculate_mf_holdings(mf_transactions)
    current_mf_value = sum(h['invested_amount'] for h in mf_holdings.values() if h['units'] > 0)
    if current_mf_value > 0:
        today = datetime.now().date()
        mf_flows.append((today, current_mf_value))
    
    mf_xirr = xirr(mf_flows) if len(mf_flows) >= 2 else None
    xirr_by_type['mutual_funds'] = round(mf_xirr * 100, 2) if mf_xirr else None
    
    # Process Fixed Deposits
    fds = all_assets.get('fixed_deposits', [])
    fd_flows = []
    for fd in fds:
        start_date = fd.start_date if isinstance(fd.start_date, date) else fd.start_date.date()
        fd_flows.append((start_date, -fd.principal_amount))
        all_cash_flows.append((start_date, -fd.principal_amount))
        
        if fd.status == 'active' and fd.maturity_amount:
            maturity_date = fd.maturity_date if isinstance(fd.maturity_date, date) else fd.maturity_date.date()
            if maturity_date >= datetime.now().date():
                # Use current value (principal) for active FDs
                fd_flows.append((datetime.now().date(), fd.principal_amount))
            else:
                fd_flows.append((maturity_date, fd.maturity_amount))
                all_cash_flows.append((maturity_date, fd.maturity_amount))
    
    fd_xirr = xirr(fd_flows) if len(fd_flows) >= 2 else None
    xirr_by_type['fixed_deposits'] = round(fd_xirr * 100, 2) if fd_xirr else None
    
    # Process EPF
    epf_accounts = all_assets.get('epf', [])
    epf_flows = []
    from sqlalchemy import inspect
    
    for acc in epf_accounts:
        # Add opening balance if available
        if acc.opening_balance and acc.opening_balance > 0:
            opening_date = acc.opening_date if acc.opening_date else datetime(2020, 1, 1).date()
            opening_date = opening_date if isinstance(opening_date, date) else opening_date.date()
            epf_flows.append((opening_date, -acc.opening_balance))
            all_cash_flows.append((opening_date, -acc.opening_balance))
        
        # Add current balance
        if acc.current_balance and acc.current_balance > 0:
            epf_flows.append((datetime.now().date(), acc.current_balance))
    
    epf_xirr = xirr(epf_flows) if len(epf_flows) >= 2 else None
    xirr_by_type['epf'] = round(epf_xirr * 100, 2) if epf_xirr else None
    
    # Process NPS
    nps_accounts = all_assets.get('nps', [])
    nps_flows = []
    for acc in nps_accounts:
        # Add opening balance
        if acc.opening_balance and acc.opening_balance > 0:
            opening_date = acc.opening_date if acc.opening_date else datetime(2020, 1, 1).date()
            opening_date = opening_date if isinstance(opening_date, date) else opening_date.date()
            nps_flows.append((opening_date, -acc.opening_balance))
            all_cash_flows.append((opening_date, -acc.opening_balance))
        
        # Add current value
        if hasattr(acc, 'current_value') and acc.current_value and acc.current_value > 0:
            nps_flows.append((datetime.now().date(), acc.current_value))
        elif acc.current_balance and acc.current_balance > 0:
            nps_flows.append((datetime.now().date(), acc.current_balance))
    
    nps_xirr = xirr(nps_flows) if len(nps_flows) >= 2 else None
    xirr_by_type['nps'] = round(nps_xirr * 100, 2) if nps_xirr else None
    
    # Calculate overall portfolio XIRR
    # Combine all cash flows and calculate unified XIRR
    net_worth = calculate_total_net_worth(all_assets)
    
    # Remove duplicates from today (we added multiple current values)
    # Keep only the sum of all current values
    today = datetime.now().date()
    all_cash_flows_filtered = [(d, a) for d, a in all_cash_flows if d != today]
    
    # Add total current portfolio value as final inflow
    if net_worth['total'] > 0:
        all_cash_flows_filtered.append((today, net_worth['total']))
    
    overall_xirr = xirr(all_cash_flows_filtered) if len(all_cash_flows_filtered) >= 2 else None
    
    return {
        'overall_xirr': round(overall_xirr * 100, 2) if overall_xirr else None,
        'xirr_by_type': xirr_by_type,
        'total_portfolio_value': net_worth['total'],
        'calculation_date': today.isoformat()
    }


