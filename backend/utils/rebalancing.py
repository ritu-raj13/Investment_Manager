"""
Portfolio Rebalancing Utilities

This module provides functions to generate rebalancing recommendations:
- Identify over-allocated stocks (reduce)
- Identify under-allocated stocks (add)
- Sector and market cap rebalancing suggestions
"""

def get_allocation_threshold(market_cap):
    """
    Get target allocation threshold based on market cap
    
    Args:
        market_cap: Market cap category (Large Cap, Mid Cap, Small Cap, Micro Cap, Unknown)
        
    Returns:
        tuple: (threshold, green_max) where green_max = threshold + 0.5
    """
    if market_cap == 'Large Cap':
        return (5.0, 5.5)
    elif market_cap == 'Mid Cap':
        return (3.0, 3.5)
    elif market_cap in ['Small Cap', 'Micro Cap']:
        return (2.0, 2.5)
    else:
        return (None, None)


def identify_stocks_to_reduce(holdings, total_invested, max_large_cap_pct=50.0, max_mid_cap_pct=30.0, 
                             max_small_cap_pct=25.0, max_micro_cap_pct=15.0):
    """
    Identify over-allocated stocks that should be reduced
    
    Args:
        holdings: List of holding dictionaries
        total_invested: Total portfolio invested amount
        max_large_cap_pct: Max % for large cap (from settings)
        max_mid_cap_pct: Max % for mid cap (from settings)
        max_small_cap_pct: Max % for small cap (from settings)
        max_micro_cap_pct: Max % for micro cap (from settings)
        
    Returns:
        list: Stocks to reduce with details
    """
    if not holdings or total_invested == 0:
        return []
    
    stocks_to_reduce = []
    
    for holding in holdings:
        market_cap = holding.get('market_cap', 'Unknown')
        
        # Normalize market cap to include "Cap" suffix if missing
        if market_cap and market_cap != 'Unknown' and not market_cap.endswith(' Cap'):
            market_cap = f'{market_cap} Cap'
        
        threshold, green_max = get_allocation_threshold(market_cap)
        
        if threshold is None:
            continue  # Skip unknown market cap stocks
        
        percentage = (holding['invested_amount'] / total_invested) * 100
        
        # Over-allocated: percentage > green_max (threshold + 0.5%)
        if percentage > green_max:
            excess_pct = percentage - green_max
            reduce_amount = (excess_pct / 100) * total_invested
            
            stocks_to_reduce.append({
                'symbol': holding['symbol'],
                'name': holding.get('name', ''),
                'market_cap': market_cap,
                'current_pct': round(percentage, 2),
                'target_pct': green_max,
                'excess_pct': round(excess_pct, 2),
                'reduce_amount': round(reduce_amount, 2),
                'current_invested': holding['invested_amount'],
                'reason': f'Over-allocated by {excess_pct:.1f}%'
            })
    
    # Sort by excess percentage (highest first)
    stocks_to_reduce.sort(key=lambda x: x['excess_pct'], reverse=True)
    
    return stocks_to_reduce


def identify_stocks_to_add(holdings, stocks, total_invested, max_large_cap_pct=50.0, max_mid_cap_pct=30.0, 
                          max_small_cap_pct=25.0, max_micro_cap_pct=15.0):
    """
    Identify under-allocated stocks that could be added
    Prioritizes stocks in buy zones
    
    Args:
        holdings: List of holding dictionaries
        stocks: List of Stock objects from database
        total_invested: Total portfolio invested amount
        max_large_cap_pct: Max % for large cap (from settings)
        max_mid_cap_pct: Max % for mid cap (from settings)
        max_small_cap_pct: Max % for small cap (from settings)
        max_micro_cap_pct: Max % for micro cap (from settings)
        
    Returns:
        list: Stocks to add with details
    """
    if not holdings or total_invested == 0:
        return []
    
    # Create a map of symbols to holdings
    holdings_map = {h['symbol']: h for h in holdings}
    
    # Create a map of symbols to stocks (for zone info)
    stocks_map = {}
    for stock in stocks:
        # Normalize symbol
        normalized = stock.symbol.replace('.NS', '').replace('.BO', '').upper()
        stocks_map[normalized] = stock
    
    stocks_to_add = []
    
    for holding in holdings:
        market_cap = holding.get('market_cap', 'Unknown')
        
        # Normalize market cap to include "Cap" suffix if missing
        if market_cap and market_cap != 'Unknown' and not market_cap.endswith(' Cap'):
            market_cap = f'{market_cap} Cap'
        
        threshold, green_max = get_allocation_threshold(market_cap)
        
        if threshold is None:
            continue  # Skip unknown market cap stocks
        
        percentage = (holding['invested_amount'] / total_invested) * 100
        
        # Under-allocated: percentage < threshold
        if percentage < threshold:
            deficit_pct = threshold - percentage
            add_amount = (deficit_pct / 100) * total_invested
            
            # Check if stock is in buy zone
            symbol = holding['symbol']
            normalized_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
            stock_obj = stocks_map.get(normalized_symbol)
            
            in_buy_zone = False
            current_price = holding.get('current_price')
            zone_info = ''
            
            if stock_obj and current_price:
                # Parse buy zone
                buy_zone = stock_obj.buy_zone_price
                if buy_zone:
                    try:
                        from utils.zones import parse_zone
                        buy_min, buy_max = parse_zone(buy_zone)
                        if buy_max and current_price <= buy_max:
                            in_buy_zone = True
                            zone_info = f' (In Buy Zone: ≤₹{buy_max})'
                    except:
                        pass
            
            reason = f'Under-allocated by {deficit_pct:.1f}%'
            if in_buy_zone:
                reason += zone_info
            
            stocks_to_add.append({
                'symbol': holding['symbol'],
                'name': holding.get('name', ''),
                'market_cap': market_cap,
                'current_pct': round(percentage, 2),
                'target_pct': threshold,
                'deficit_pct': round(deficit_pct, 2),
                'add_amount': round(add_amount, 2),
                'current_invested': holding['invested_amount'],
                'in_buy_zone': in_buy_zone,
                'current_price': current_price,
                'reason': reason
            })
    
    # Sort: buy zone stocks first, then by deficit percentage
    stocks_to_add.sort(key=lambda x: (not x['in_buy_zone'], -x['deficit_pct']))
    
    return stocks_to_add


def get_sector_recommendations(holdings, max_sector_pct=20.0):
    """
    Generate sector-level rebalancing recommendations
    
    Args:
        holdings: List of holding dictionaries with sector info
        max_sector_pct: Maximum % allocation per sector (from settings)
        
    Returns:
        list: Sector recommendations with analysis
    """
    if not holdings:
        return []
    
    total_invested = sum(h['invested_amount'] for h in holdings)
    
    if total_invested == 0:
        return []
    
    # Group by sector
    sector_data = {}
    for holding in holdings:
        sector = holding.get('sector', 'Other')
        if sector not in sector_data:
            sector_data[sector] = {
                'invested': 0,
                'stocks': []
            }
        sector_data[sector]['invested'] += holding['invested_amount']
        sector_data[sector]['stocks'].append(holding['symbol'])
    
    # Calculate percentages and generate recommendations
    recommendations = []
    MAX_SECTOR_ALLOCATION = max_sector_pct
    
    for sector, data in sector_data.items():
        percentage = (data['invested'] / total_invested) * 100
        num_stocks = len(data['stocks'])
        
        # Sector allocation guidelines: Max 15% per sector
        if percentage > MAX_SECTOR_ALLOCATION:
            excess = percentage - MAX_SECTOR_ALLOCATION
            recommendation = f'Over-allocated by {excess:.1f}% - Reduce to max {MAX_SECTOR_ALLOCATION}%'
            status = 'overweight'
        elif percentage >= MAX_SECTOR_ALLOCATION * 0.9:  # 13.5% - 15%
            recommendation = f'Near maximum allocation ({MAX_SECTOR_ALLOCATION}%) - Monitor closely'
            status = 'moderate_overweight'
        elif percentage < 5 and num_stocks >= 2:
            recommendation = 'Low allocation - Could increase if sector looks promising'
            status = 'underweight'
        else:
            recommendation = 'Balanced allocation'
            status = 'balanced'
        
        recommendations.append({
            'sector': sector,
            'invested_amount': round(data['invested'], 2),
            'percentage': round(percentage, 2),
            'num_stocks': num_stocks,
            'stocks': data['stocks'],
            'status': status,
            'recommendation': recommendation,
            'max_allowed': MAX_SECTOR_ALLOCATION
        })
    
    # Sort by percentage (highest first)
    recommendations.sort(key=lambda x: x['percentage'], reverse=True)
    
    return recommendations


def get_market_cap_recommendations(holdings, max_large_cap_pct=50.0, max_mid_cap_pct=30.0, 
                                   max_small_cap_pct=25.0, max_micro_cap_pct=15.0):
    """
    Generate market cap level rebalancing recommendations
    
    Args:
        holdings: List of holding dictionaries with market_cap info
        max_large_cap_pct: Maximum % allocation for Large Cap (from settings)
        max_mid_cap_pct: Maximum % allocation for Mid Cap (from settings)
        max_small_cap_pct: Maximum % allocation for Small Cap (from settings)
        max_micro_cap_pct: Maximum % allocation for Micro Cap (from settings)
        
    Returns:
        list: Market cap recommendations with analysis
    """
    if not holdings:
        return []
    
    total_invested = sum(h['invested_amount'] for h in holdings)
    
    if total_invested == 0:
        return []
    
    # Group by market cap
    market_cap_data = {}
    for holding in holdings:
        market_cap = holding.get('market_cap', 'Unknown')
        
        # Normalize market cap to include "Cap" suffix if missing
        if market_cap and market_cap != 'Unknown' and not market_cap.endswith(' Cap'):
            market_cap = f'{market_cap} Cap'
        
        if market_cap not in market_cap_data:
            market_cap_data[market_cap] = {
                'invested': 0,
                'stocks': []
            }
        market_cap_data[market_cap]['invested'] += holding['invested_amount']
        market_cap_data[market_cap]['stocks'].append(holding['symbol'])
    
    # Market cap allocation limits (from user settings)
    MAX_ALLOCATIONS = {
        'Large Cap': max_large_cap_pct,
        'Mid Cap': max_mid_cap_pct,
        'Small Cap': max_small_cap_pct,
        'Micro Cap': max_micro_cap_pct
    }
    
    recommendations = []
    
    for market_cap, data in market_cap_data.items():
        percentage = (data['invested'] / total_invested) * 100
        num_stocks = len(data['stocks'])
        
        max_allowed = MAX_ALLOCATIONS.get(market_cap, None)
        
        # Generate recommendations based on max allocation limits
        if market_cap in MAX_ALLOCATIONS:
            if percentage > max_allowed:
                excess = percentage - max_allowed
                recommendation = f'Over-allocated by {excess:.1f}% - Reduce to max {max_allowed}%'
                status = 'overweight'
            elif percentage >= max_allowed * 0.9:  # Within 90% of max
                recommendation = f'Near maximum allocation ({max_allowed}%) - Monitor closely'
                status = 'moderate_overweight'
            elif percentage < max_allowed * 0.5:  # Less than 50% of max
                recommendation = f'Low allocation - Could increase up to {max_allowed}%'
                status = 'underweight'
            else:
                recommendation = f'Balanced allocation (max: {max_allowed}%)'
                status = 'balanced'
            
            target_range = f'Max {max_allowed}%'
        
        else:  # Unknown
            recommendation = 'Set market cap for better allocation guidance'
            target_range = 'N/A'
            status = 'unknown'
            max_allowed = None
        
        recommendations.append({
            'market_cap': market_cap,
            'invested_amount': round(data['invested'], 2),
            'percentage': round(percentage, 2),
            'num_stocks': num_stocks,
            'stocks': data['stocks'],
            'target_range': target_range,
            'max_allowed': max_allowed,
            'status': status,
            'recommendation': recommendation
        })
    
    # Sort by percentage (highest first)
    recommendations.sort(key=lambda x: x['percentage'], reverse=True)
    
    return recommendations


def get_rebalancing_suggestions(holdings, stocks, total_invested, settings=None):
    """
    Generate complete rebalancing suggestions
    
    Args:
        holdings: List of holding dictionaries
        stocks: List of Stock objects from database
        total_invested: Total portfolio invested amount
        settings: PortfolioSettings object with user-configured thresholds
        
    Returns:
        dict: Complete rebalancing recommendations
    """
    # Extract settings or use defaults
    max_large_cap = settings.max_large_cap_pct if settings else 50.0
    max_mid_cap = settings.max_mid_cap_pct if settings else 30.0
    max_small_cap = settings.max_small_cap_pct if settings else 25.0
    max_micro_cap = settings.max_micro_cap_pct if settings else 15.0
    max_sector = settings.max_sector_pct if settings else 20.0
    
    return {
        'stocks_to_reduce': identify_stocks_to_reduce(holdings, total_invested, max_large_cap, max_mid_cap, max_small_cap, max_micro_cap),
        'stocks_to_add': identify_stocks_to_add(holdings, stocks, total_invested, max_large_cap, max_mid_cap, max_small_cap, max_micro_cap),
        'sector_rebalancing': get_sector_recommendations(holdings, max_sector),
        'market_cap_rebalancing': get_market_cap_recommendations(holdings, max_large_cap, max_mid_cap, max_small_cap, max_micro_cap)
    }

