"""
Portfolio Health Calculation Utilities

This module provides functions to assess portfolio health including:
- Concentration risk (stock, sector, market cap)
- Diversification metrics
- Allocation health based on market cap thresholds
"""

def calculate_concentration_risk(holdings):
    """
    Calculate concentration risk metrics
    
    Args:
        holdings: List of holding dictionaries with symbol, sector, market_cap, invested_amount
        
    Returns:
        dict: Concentration metrics including stock, sector, and market cap concentration
    """
    if not holdings or len(holdings) == 0:
        return {
            'stock_concentration': 0,
            'top_3_stocks': [],
            'sector_concentration': 0,
            'top_sector': None,
            'market_cap_concentration': 0,
            'top_market_cap': None
        }
    
    total_invested = sum(h['invested_amount'] for h in holdings)
    
    if total_invested == 0:
        return {
            'stock_concentration': 0,
            'top_3_stocks': [],
            'sector_concentration': 0,
            'top_sector': None,
            'market_cap_concentration': 0,
            'top_market_cap': None
        }
    
    # Stock concentration (top 3 stocks)
    sorted_by_invested = sorted(holdings, key=lambda x: x['invested_amount'], reverse=True)
    top_3 = sorted_by_invested[:3]
    top_3_total = sum(h['invested_amount'] for h in top_3)
    stock_concentration_pct = (top_3_total / total_invested) * 100
    
    top_3_stocks = [{
        'symbol': h['symbol'],
        'invested_amount': h['invested_amount'],
        'percentage': (h['invested_amount'] / total_invested) * 100
    } for h in top_3]
    
    # Sector concentration (top sector)
    sector_totals = {}
    for h in holdings:
        sector = h.get('sector') or 'Other'
        sector_totals[sector] = sector_totals.get(sector, 0) + h['invested_amount']
    
    if sector_totals:
        top_sector = max(sector_totals.items(), key=lambda x: x[1])
        sector_concentration_pct = (top_sector[1] / total_invested) * 100
        top_sector_info = {
            'name': top_sector[0],
            'invested_amount': top_sector[1],
            'percentage': sector_concentration_pct
        }
    else:
        sector_concentration_pct = 0
        top_sector_info = None
    
    # Market cap concentration (top market cap)
    market_cap_totals = {}
    for h in holdings:
        market_cap = h.get('market_cap') or 'Unknown'
        market_cap_totals[market_cap] = market_cap_totals.get(market_cap, 0) + h['invested_amount']
    
    if market_cap_totals:
        top_market_cap = max(market_cap_totals.items(), key=lambda x: x[1])
        market_cap_concentration_pct = (top_market_cap[1] / total_invested) * 100
        top_market_cap_info = {
            'name': top_market_cap[0],
            'invested_amount': top_market_cap[1],
            'percentage': market_cap_concentration_pct
        }
    else:
        market_cap_concentration_pct = 0
        top_market_cap_info = None
    
    return {
        'stock_concentration': round(stock_concentration_pct, 2),
        'top_3_stocks': top_3_stocks,
        'sector_concentration': round(sector_concentration_pct, 2),
        'top_sector': top_sector_info,
        'market_cap_concentration': round(market_cap_concentration_pct, 2),
        'top_market_cap': top_market_cap_info
    }


def calculate_diversification_score(holdings):
    """
    Calculate diversification metrics
    
    Args:
        holdings: List of holding dictionaries
        
    Returns:
        dict: Diversification metrics including counts and Herfindahl index
    """
    if not holdings or len(holdings) == 0:
        return {
            'num_stocks': 0,
            'num_sectors': 0,
            'num_market_caps': 0,
            'herfindahl_index': 0,
            'diversification_score': 0
        }
    
    # Count unique sectors (excluding None/empty)
    sectors = set(h.get('sector') for h in holdings if h.get('sector'))
    num_sectors = len(sectors)
    
    # Count unique market caps (excluding None/empty/Unknown)
    market_caps = set(h.get('market_cap') for h in holdings if h.get('market_cap') and h.get('market_cap') != 'Unknown')
    num_market_caps = len(market_caps)
    
    num_stocks = len(holdings)
    
    # Calculate Herfindahl-Hirschman Index (HHI)
    # Lower HHI = better diversification (ranges 0-1, closer to 0 is better)
    total_invested = sum(h['invested_amount'] for h in holdings)
    if total_invested > 0:
        hhi = sum((h['invested_amount'] / total_invested) ** 2 for h in holdings)
    else:
        hhi = 1.0  # Maximum concentration
    
    # Calculate diversification score (0-100, higher is better)
    # Based on: number of stocks, sectors, market caps, and HHI
    stock_score = min(num_stocks / 15 * 100, 100)  # 15+ stocks = 100 points
    sector_score = min(num_sectors / 8 * 100, 100)  # 8+ sectors = 100 points
    market_cap_score = min(num_market_caps / 4 * 100, 100)  # 4 market caps = 100 points
    hhi_score = (1 - hhi) * 100  # Lower HHI = higher score
    
    # Weighted average
    diversification_score = (
        stock_score * 0.3 +
        sector_score * 0.3 +
        market_cap_score * 0.2 +
        hhi_score * 0.2
    )
    
    return {
        'num_stocks': num_stocks,
        'num_sectors': num_sectors,
        'num_market_caps': num_market_caps,
        'herfindahl_index': round(hhi, 4),
        'diversification_score': round(diversification_score, 2)
    }


def calculate_allocation_health(holdings):
    """
    Calculate allocation health based on market cap thresholds
    Uses the same logic as Portfolio page color coding:
    - Large Cap: 5% target (green: 5-5.5%, red: >5.5%, orange: <5%)
    - Mid Cap: 3% target (green: 3-3.5%, red: >3.5%, orange: <3%)
    - Small/Micro Cap: 2% target (green: 2-2.5%, red: >2.5%, orange: <2%)
    
    Args:
        holdings: List of holding dictionaries with market_cap and invested_amount
        
    Returns:
        dict: Counts of over-allocated, balanced, and under-allocated stocks
    """
    if not holdings or len(holdings) == 0:
        return {
            'over_allocated': 0,
            'balanced': 0,
            'under_allocated': 0,
            'details': []
        }
    
    total_invested = sum(h['invested_amount'] for h in holdings)
    
    if total_invested == 0:
        return {
            'over_allocated': 0,
            'balanced': 0,
            'under_allocated': 0,
            'details': []
        }
    
    over_allocated = 0
    balanced = 0
    under_allocated = 0
    details = []
    
    for holding in holdings:
        market_cap = holding.get('market_cap', 'Unknown')
        percentage = (holding['invested_amount'] / total_invested) * 100
        
        # Determine threshold based on market cap
        if market_cap == 'Large Cap':
            threshold = 5.0
        elif market_cap == 'Mid Cap':
            threshold = 3.0
        elif market_cap in ['Small Cap', 'Micro Cap']:
            threshold = 2.0
        else:
            # Unknown market cap - no threshold, consider balanced
            details.append({
                'symbol': holding['symbol'],
                'status': 'balanced',
                'percentage': round(percentage, 2),
                'threshold': None
            })
            balanced += 1
            continue
        
        # Apply allocation logic (with +0.5% green range)
        if percentage > threshold + 0.5:
            status = 'over_allocated'
            over_allocated += 1
        elif percentage >= threshold:
            status = 'balanced'
            balanced += 1
        else:
            status = 'under_allocated'
            under_allocated += 1
        
        details.append({
            'symbol': holding['symbol'],
            'status': status,
            'percentage': round(percentage, 2),
            'threshold': threshold
        })
    
    return {
        'over_allocated': over_allocated,
        'balanced': balanced,
        'under_allocated': under_allocated,
        'details': details
    }


def calculate_overall_health_score(concentration_risk, diversification, allocation_health):
    """
    Calculate overall portfolio health score (0-100)
    
    Formula:
    - Diversification score: 40%
    - Low concentration: 30%
    - Balanced allocation: 30%
    
    Args:
        concentration_risk: dict from calculate_concentration_risk
        diversification: dict from calculate_diversification_score
        allocation_health: dict from calculate_allocation_health
        
    Returns:
        float: Overall health score (0-100, higher is better)
    """
    # Diversification component (40%)
    diversification_component = diversification['diversification_score'] * 0.4
    
    # Concentration component (30%) - invert so lower concentration = higher score
    # Stock concentration ideal: <40%, bad: >70%
    stock_conc = concentration_risk['stock_concentration']
    if stock_conc < 40:
        conc_score = 100
    elif stock_conc < 70:
        conc_score = 100 - ((stock_conc - 40) / 30 * 50)  # Linear decay
    else:
        conc_score = 50 - ((stock_conc - 70) / 30 * 50)  # Faster decay
        conc_score = max(0, conc_score)
    
    concentration_component = conc_score * 0.3
    
    # Allocation component (30%) - higher % of balanced stocks = better
    total_stocks = (allocation_health['over_allocated'] + 
                   allocation_health['balanced'] + 
                   allocation_health['under_allocated'])
    
    if total_stocks > 0:
        balanced_pct = (allocation_health['balanced'] / total_stocks) * 100
    else:
        balanced_pct = 0
    
    allocation_component = balanced_pct * 0.3
    
    # Overall score
    overall_score = diversification_component + concentration_component + allocation_component
    
    return round(overall_score, 2)

