"""
Portfolio Rebalancing Utilities

This module provides functions to generate rebalancing recommendations:
- Identify over-allocated stocks (reduce)
- Identify under-allocated stocks (add)
- Sector and market cap rebalancing suggestions
- Parent sector analysis with max 2 stocks per parent sector limit
"""

def get_allocation_threshold(market_cap):
    """
    Get target allocation threshold based on market cap
    
    Args:
        market_cap: Market cap category (Large Cap, Mid Cap, Small Cap, Micro Cap, Unknown)
        
    Returns:
        tuple: (threshold, green_max) where green_max = threshold + 0.5
        threshold is the actual max, green_max is the display max with 0.5% leverage
    """
    if market_cap == 'Large Cap':
        return (5.0, 5.5)  # Actual: 5%, Display: 5.5%
    elif market_cap == 'Mid Cap':
        return (3.0, 3.5)  # Actual: 3%, Display: 3.5%
    elif market_cap == 'Small Cap':
        return (2.5, 3.0)  # Actual: 2.5%, Display: 3%
    elif market_cap == 'Micro Cap':
        return (2.0, 2.5)  # Actual: 2%, Display: 2.5%
    else:
        return (None, None)


def identify_stocks_to_reduce(holdings, total_current_value, max_large_cap_pct=5.0, max_mid_cap_pct=3.0, 
                             max_small_cap_pct=2.5, max_micro_cap_pct=2.0):
    """
    Identify over-allocated stocks that should be reduced
    
    Args:
        holdings: List of holding dictionaries
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount, for % calculation)
        max_large_cap_pct: Max % for large cap (actual: 5%, display: 5.5%)
        max_mid_cap_pct: Max % for mid cap (actual: 3%, display: 3.5%)
        max_small_cap_pct: Max % for small cap (actual: 2.5%, display: 3%)
        max_micro_cap_pct: Max % for micro cap (actual: 2%, display: 2.5%)
        
    Returns:
        list: Stocks to reduce with details
    """
    if not holdings or total_current_value == 0:
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
        
        # Use invested_amount for percentage (SAME as Holdings screen)
        invested_amount = holding.get('invested_amount', 0)
        
        percentage = (invested_amount / total_current_value) * 100
        
        # Over-allocated: percentage > green_max (threshold + 0.5%)
        if percentage > green_max:
            excess_pct = percentage - green_max
            reduce_amount = (excess_pct / 100) * total_current_value
            
            stocks_to_reduce.append({
                'symbol': holding['symbol'],
                'name': holding.get('name', ''),
                'market_cap': market_cap,
                'current_pct': round(percentage, 2),
                'target_pct': green_max,
                'excess_pct': round(excess_pct, 2),
                'reduce_amount': round(reduce_amount, 2),
                'current_value': holding.get('current_value', 0),
                'current_invested': invested_amount,
                'reason': f'Over-allocated by {excess_pct:.1f}%'
            })
    
    # Sort by excess percentage (highest first)
    stocks_to_reduce.sort(key=lambda x: x['excess_pct'], reverse=True)
    
    return stocks_to_reduce


def identify_stocks_to_add(holdings, stocks, total_current_value, max_large_cap_pct=5.0, max_mid_cap_pct=3.0, 
                          max_small_cap_pct=2.5, max_micro_cap_pct=2.0):
    """
    Identify under-allocated stocks that could be added
    Prioritizes stocks in buy zones
    
    Args:
        holdings: List of holding dictionaries
        stocks: List of Stock objects from database
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount, for % calculation)
        max_large_cap_pct: Max % for large cap (actual: 5%, display: 5.5%)
        max_mid_cap_pct: Max % for mid cap (actual: 3%, display: 3.5%)
        max_small_cap_pct: Max % for small cap (actual: 2.5%, display: 3%)
        max_micro_cap_pct: Max % for micro cap (actual: 2%, display: 2.5%)
        
    Returns:
        list: Stocks to add with details
    """
    if not holdings or total_current_value == 0:
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
        
        # Use invested_amount for percentage (SAME as Holdings screen)
        invested_amount = holding.get('invested_amount', 0)
        
        percentage = (invested_amount / total_current_value) * 100
        
        # Under-allocated: percentage < threshold
        if percentage < threshold:
            deficit_pct = threshold - percentage
            add_amount = (deficit_pct / 100) * total_current_value
            
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


def get_sector_recommendations(holdings, total_current_value, max_stocks_per_sector=2):
    """
    Generate sector-level rebalancing recommendations based on stock count per sector
    
    Args:
        holdings: List of holding dictionaries with sector info
        total_current_value: Total portfolio target amount (from settings, for % calculation)
        max_stocks_per_sector: Maximum number of stocks per sector (from settings, default: 2)
        
    Returns:
        list: Sector recommendations with analysis
    """
    if not holdings:
        return []
    
    # Use provided total_current_value (from settings.total_amount)
    # If not provided or 0, calculate from holdings
    if total_current_value == 0:
        total_current_value = 0
    for h in holdings:
        current_value = h.get('current_value', 0)
        if current_value == 0 and h.get('quantity') and h.get('current_price'):
            current_value = h['quantity'] * h['current_price']
        total_current_value += current_value
    
    if total_current_value == 0:
        return []
    
    # Group by sector
    sector_data = {}
    for holding in holdings:
        sector = holding.get('sector', 'Other')
        # Use invested_amount (SAME as Holdings screen)
        invested_amount = holding.get('invested_amount', 0)
        
        if sector not in sector_data:
            sector_data[sector] = {
                'invested_amount': 0,
                'stocks': []
            }
        sector_data[sector]['invested_amount'] += invested_amount
        sector_data[sector]['stocks'].append(holding['symbol'])
    
    # Calculate percentages and generate recommendations based on stock count
    recommendations = []
    
    for sector, data in sector_data.items():
        percentage = (data['invested_amount'] / total_current_value) * 100
        num_stocks = len(data['stocks'])
        
        # Sector allocation guidelines: Max stocks per sector (default: 2)
        if num_stocks > max_stocks_per_sector:
            excess = num_stocks - max_stocks_per_sector
            recommendation = f'{num_stocks} stocks (max: {max_stocks_per_sector}) - Reduce by {excess} stock(s)'
            status = 'overweight'
        elif num_stocks == max_stocks_per_sector:
            recommendation = f'At maximum ({max_stocks_per_sector} stocks) - Monitor performance'
            status = 'moderate_overweight'
        elif num_stocks == 1:
            recommendation = f'Balanced - Can add {max_stocks_per_sector - 1} more if opportunity arises'
            status = 'underweight'
        else:
            recommendation = 'Balanced allocation'
            status = 'balanced'
        
        recommendations.append({
            'sector': sector,
            'current_value': round(data['invested_amount'], 2),
            'percentage': round(percentage, 2),
            'num_stocks': num_stocks,
            'stocks': data['stocks'],
            'status': status,
            'recommendation': recommendation,
            'max_stocks_allowed': max_stocks_per_sector
        })
    
    # Sort by attention level (red > yellow > green)
    # Status priority: overweight (red) -> moderate_overweight (yellow) -> balanced/underweight (green)
    status_priority = {
        'overweight': 0,
        'moderate_overweight': 1,
        'balanced': 2,
        'underweight': 3
    }
    recommendations.sort(key=lambda x: (status_priority.get(x['status'], 99), -x['percentage']))
    
    return recommendations


def get_market_cap_recommendations(holdings, total_current_value, settings=None):
    """
    Generate market cap level rebalancing recommendations with stock count and portfolio % limits
    
    Args:
        holdings: List of holding dictionaries with market_cap info
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount, for % calculation)
        settings: PortfolioSettings object with all limits (per-stock %, stock counts, portfolio %)
        
    Returns:
        list: Market cap recommendations with analysis including:
          - Per-stock % violations
          - Total stock count violations  
          - Total portfolio % violations
    """
    if not holdings:
        return []
    
    # Extract per-stock max percentages from settings (actual max, not display)
    max_large_cap_pct = 5.0  # Default
    max_mid_cap_pct = 3.0    # Default
    max_small_cap_pct = 2.5  # Default
    max_micro_cap_pct = 2.0  # Default
    
    # Extract stock count limits from settings
    max_large_cap_stocks = 15  # Default
    max_mid_cap_stocks = 8     # Default
    max_small_cap_stocks = 7   # Default
    max_micro_cap_stocks = 3   # Default
    
    # Extract portfolio % limits from settings
    max_large_cap_portfolio_pct = 50.0  # Default
    max_mid_cap_portfolio_pct = 30.0    # Default
    max_small_cap_portfolio_pct = 25.0  # Default
    max_micro_cap_portfolio_pct = 10.0  # Default
    
    if settings:
        max_large_cap_pct = getattr(settings, 'max_large_cap_pct', 5.0)
        max_mid_cap_pct = getattr(settings, 'max_mid_cap_pct', 3.0)
        max_small_cap_pct = getattr(settings, 'max_small_cap_pct', 2.5)
        max_micro_cap_pct = getattr(settings, 'max_micro_cap_pct', 2.0)
        
        max_large_cap_stocks = getattr(settings, 'max_large_cap_stocks', 15)
        max_mid_cap_stocks = getattr(settings, 'max_mid_cap_stocks', 8)
        max_small_cap_stocks = getattr(settings, 'max_small_cap_stocks', 7)
        max_micro_cap_stocks = getattr(settings, 'max_micro_cap_stocks', 3)
        
        max_large_cap_portfolio_pct = getattr(settings, 'max_large_cap_portfolio_pct', 50.0)
        max_mid_cap_portfolio_pct = getattr(settings, 'max_mid_cap_portfolio_pct', 30.0)
        max_small_cap_portfolio_pct = getattr(settings, 'max_small_cap_portfolio_pct', 25.0)
        max_micro_cap_portfolio_pct = getattr(settings, 'max_micro_cap_portfolio_pct', 10.0)
    
    # Use provided total_current_value (from settings.total_amount)
    # If not provided or 0, calculate from holdings
    if total_current_value == 0:
        total_current_value = 0
    for h in holdings:
        current_value = h.get('current_value', 0)
        if current_value == 0 and h.get('quantity') and h.get('current_price'):
            current_value = h['quantity'] * h['current_price']
        total_current_value += current_value
    
    if total_current_value == 0:
        return []
    
    # Group by market cap
    market_cap_data = {}
    for holding in holdings:
        market_cap = holding.get('market_cap', 'Unknown')
        
        # Normalize market cap to include "Cap" suffix if missing
        if market_cap and market_cap != 'Unknown' and not market_cap.endswith(' Cap'):
            market_cap = f'{market_cap} Cap'
        
        # Use invested_amount (SAME as Holdings screen)
        invested_amount = holding.get('invested_amount', 0)
        
        if market_cap not in market_cap_data:
            market_cap_data[market_cap] = {
                'invested_amount': 0,
                'stocks': []
            }
        market_cap_data[market_cap]['invested_amount'] += invested_amount
        market_cap_data[market_cap]['stocks'].append(holding['symbol'])
    
    # Market cap allocation limits (from user settings - actual max, not display)
    MAX_PER_STOCK_PCT = {
        'Large Cap': max_large_cap_pct,  # Actual: 5%
        'Mid Cap': max_mid_cap_pct,  # Actual: 3%
        'Small Cap': max_small_cap_pct,  # Actual: 2.5%
        'Micro Cap': max_micro_cap_pct  # Actual: 2%
    }
    
    MAX_STOCK_COUNTS = {
        'Large Cap': max_large_cap_stocks,   # Default: 15
        'Mid Cap': max_mid_cap_stocks,       # Default: 8
        'Small Cap': max_small_cap_stocks,   # Default: 7
        'Micro Cap': max_micro_cap_stocks    # Default: 3
    }
    
    MAX_PORTFOLIO_PCT = {
        'Large Cap': max_large_cap_portfolio_pct,   # Default: 50%
        'Mid Cap': max_mid_cap_portfolio_pct,       # Default: 30%
        'Small Cap': max_small_cap_portfolio_pct,   # Default: 25%
        'Micro Cap': max_micro_cap_portfolio_pct    # Default: 10%
    }
    
    recommendations = []
    
    for market_cap, data in market_cap_data.items():
        percentage = (data['invested_amount'] / total_current_value) * 100
        num_stocks = len(data['stocks'])
        
        # Get all three limits for this market cap
        per_stock_limit = MAX_PER_STOCK_PCT.get(market_cap, None)
        stock_count_limit = MAX_STOCK_COUNTS.get(market_cap, None)
        portfolio_pct_limit = MAX_PORTFOLIO_PCT.get(market_cap, None)
        
        # Generate recommendations based on three-tier limit system
        if market_cap in MAX_PER_STOCK_PCT:
            violations = []
            status = 'balanced'
            
            # Check 1: Stock count violation
            if stock_count_limit and num_stocks > stock_count_limit:
                excess_stocks = num_stocks - stock_count_limit
                violations.append(f'⚠️ Stock count: {num_stocks}/{stock_count_limit} (reduce {excess_stocks})')
                status = 'overweight'
            
            # Check 2: Portfolio % violation
            if portfolio_pct_limit and percentage > portfolio_pct_limit:
                excess_pct = percentage - portfolio_pct_limit
                violations.append(f'⚠️ Portfolio %: {percentage:.1f}%/{portfolio_pct_limit}% (over by {excess_pct:.1f}%)')
                status = 'overweight'
            
            # If no violations but close to limits
            if not violations:
                if stock_count_limit and num_stocks >= stock_count_limit * 0.9:
                    violations.append(f'Near stock count limit ({num_stocks}/{stock_count_limit})')
                    status = 'moderate_overweight'
                
                if portfolio_pct_limit and percentage >= portfolio_pct_limit * 0.9:
                    violations.append(f'Near portfolio % limit ({percentage:.1f}%/{portfolio_pct_limit}%)')
                    status = 'moderate_overweight'
            
            # Generate recommendation text
            if violations:
                recommendation = ' | '.join(violations)
            elif percentage < (portfolio_pct_limit or 100) * 0.3:
                recommendation = f'Low allocation - Can add more stocks (up to {stock_count_limit} stocks, {portfolio_pct_limit}% portfolio)'
                status = 'underweight'
            else:
                recommendation = f'✅ Balanced - {num_stocks}/{stock_count_limit} stocks, {percentage:.1f}%/{portfolio_pct_limit}% portfolio'
            
            target_range = f'Max {per_stock_limit}% per stock'
        
        else:  # Unknown
            recommendation = 'Set market cap for better allocation guidance'
            target_range = 'N/A'
            status = 'unknown'
            per_stock_limit = None
            stock_count_limit = None
            portfolio_pct_limit = None
        
        recommendations.append({
            'market_cap': market_cap,
            'current_value': round(data['invested_amount'], 2),
            'percentage': round(percentage, 2),
            'num_stocks': num_stocks,
            'stocks': data['stocks'],
            'target_range': target_range,
            'per_stock_limit': per_stock_limit,
            'stock_count_limit': stock_count_limit,
            'portfolio_pct_limit': portfolio_pct_limit,
            'status': status,
            'recommendation': recommendation
        })
    
    # Sort by attention level (red > yellow > green)
    # Status priority: overweight (red) -> moderate_overweight (yellow) -> balanced/underweight (green)
    status_priority = {
        'overweight': 0,
        'moderate_overweight': 1,
        'balanced': 2,
        'underweight': 3,
        'unknown': 99
    }
    recommendations.sort(key=lambda x: (status_priority.get(x['status'], 99), -x['percentage']))
    
    return recommendations


def check_parent_sector_limits(holdings, parent_sector_mappings, max_stocks_per_sector=2):
    """
    Check parent sector limits (configurable max stocks per parent sector)
    
    Args:
        holdings: List of holding dictionaries with sector info
        parent_sector_mappings: Dict mapping sector_name -> parent_sector
        max_stocks_per_sector: Maximum stocks per parent sector (from settings, default: 2)
        
    Returns:
        list: Warnings for parent sectors exceeding the limit
    """
    # Group stocks by parent sector
    parent_sector_stocks = {}
    
    for holding in holdings:
        sector = holding.get('sector', 'Other')
        # Get parent sector from mapping, or use sector itself as parent
        parent_sector = parent_sector_mappings.get(sector, sector)
        
        if parent_sector not in parent_sector_stocks:
            parent_sector_stocks[parent_sector] = []
        parent_sector_stocks[parent_sector].append(holding['symbol'])
    
    # Check for violations (>max_stocks_per_sector)
    warnings = []
    for parent_sector, stocks in parent_sector_stocks.items():
        if len(stocks) > max_stocks_per_sector:
            warnings.append({
                'parent_sector': parent_sector,
                'stock_count': len(stocks),
                'stocks': stocks,
                'warning': f'Exceeds limit: {len(stocks)} stocks (max: {max_stocks_per_sector})',
                'recommendation': f'Consider reducing to {max_stocks_per_sector} stocks in {parent_sector} sector'
            })
    
    return warnings


def get_parent_sector_recommendations(holdings, parent_sector_mappings, total_current_value, max_stocks_per_sector=2):
    """
    Generate parent sector level rebalancing recommendations with configurable stock limit
    
    Args:
        holdings: List of holding dictionaries with sector info
        parent_sector_mappings: Dict mapping sector_name -> parent_sector
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount)
        max_stocks_per_sector: Maximum stocks per parent sector (from settings, default: 2)
        
    Returns:
        list: Parent sector recommendations with stock count analysis
    """
    if not holdings:
        return []
    
    # Group by parent sector
    parent_sector_data = {}
    for holding in holdings:
        sector = holding.get('sector', 'Other')
        parent_sector = parent_sector_mappings.get(sector, sector)
        invested_amount = holding.get('invested_amount', 0)
        
        if parent_sector not in parent_sector_data:
            parent_sector_data[parent_sector] = {
                'invested_amount': 0,
                'stocks': [],
                'child_sectors': set()
            }
        
        parent_sector_data[parent_sector]['invested_amount'] += invested_amount
        parent_sector_data[parent_sector]['stocks'].append(holding['symbol'])
        parent_sector_data[parent_sector]['child_sectors'].add(sector)
    
    # Generate recommendations
    recommendations = []
    for parent_sector, data in parent_sector_data.items():
        num_stocks = len(data['stocks'])
        percentage = (data['invested_amount'] / total_current_value * 100) if total_current_value > 0 else 0
        
        # Check stock count limit
        if num_stocks > max_stocks_per_sector:
            status = 'overconcentrated'
            excess = num_stocks - max_stocks_per_sector
            recommendation = f'ALERT: {num_stocks} stocks in sector (max: {max_stocks_per_sector}) - Consider reducing by {excess} stock(s)'
        elif num_stocks == max_stocks_per_sector:
            status = 'at_limit'
            recommendation = f'At maximum stock limit ({max_stocks_per_sector}) - Monitor performance'
        elif num_stocks < max_stocks_per_sector and num_stocks > 0:
            remaining = max_stocks_per_sector - num_stocks
            status = 'balanced'
            recommendation = f'Balanced - Can add {remaining} more stock(s) if opportunity arises'
        else:
            status = 'balanced'
            recommendation = 'Balanced allocation'
        
        recommendations.append({
            'parent_sector': parent_sector,
            'current_value': round(data['invested_amount'], 2),
            'percentage': round(percentage, 2),
            'num_stocks': num_stocks,
            'stocks': data['stocks'],
            'child_sectors': list(data['child_sectors']),
            'status': status,
            'recommendation': recommendation,
            'stock_limit': max_stocks_per_sector
        })
    
    # Sort by attention level (red > yellow > green)
    # Status priority: overconcentrated (red) -> at_limit (yellow) -> balanced (green)
    status_priority = {
        'overconcentrated': 0,
        'at_limit': 1,
        'balanced': 2
    }
    recommendations.sort(key=lambda x: (status_priority.get(x['status'], 99), -x['num_stocks'], -x['percentage']))
    
    return recommendations


def get_rebalancing_suggestions(holdings, stocks, total_current_value, settings=None, parent_sector_mappings=None):
    """
    Generate complete rebalancing suggestions
    
    Args:
        holdings: List of holding dictionaries
        stocks: List of Stock objects from database
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount)
        settings: PortfolioSettings object with user-configured thresholds
        parent_sector_mappings: Dict mapping sector_name -> parent_sector (optional)
        
    Returns:
        dict: Complete rebalancing recommendations
    """
    # Calculate total current value if not provided or if 0
    if total_current_value == 0:
        for h in holdings:
            current_value = h.get('current_value', 0)
            if current_value == 0 and h.get('quantity') and h.get('current_price'):
                current_value = h['quantity'] * h['current_price']
            total_current_value += current_value
    
    # Extract settings or use new defaults
    max_large_cap = settings.max_large_cap_pct if settings else 5.0
    max_mid_cap = settings.max_mid_cap_pct if settings else 3.0
    max_small_cap = settings.max_small_cap_pct if settings else 2.5
    max_micro_cap = settings.max_micro_cap_pct if settings else 2.0
    max_stocks_per_sector = settings.max_stocks_per_sector if settings else 2
    max_total_stocks = settings.max_total_stocks if settings else 30
    
    result = {
        'stocks_to_reduce': identify_stocks_to_reduce(holdings, total_current_value, max_large_cap, max_mid_cap, max_small_cap, max_micro_cap),
        'stocks_to_add': identify_stocks_to_add(holdings, stocks, total_current_value, max_large_cap, max_mid_cap, max_small_cap, max_micro_cap),
        'sector_rebalancing': get_sector_recommendations(holdings, total_current_value, max_stocks_per_sector),
        'market_cap_rebalancing': get_market_cap_recommendations(holdings, total_current_value, settings),
        'total_stocks': len(holdings),
        'max_total_stocks': max_total_stocks,
        'total_stocks_status': 'overweight' if len(holdings) > max_total_stocks else 'balanced'
    }
    
    # Add parent sector analysis if mappings provided
    if parent_sector_mappings:
        result['parent_sector_warnings'] = check_parent_sector_limits(holdings, parent_sector_mappings, max_stocks_per_sector)
        result['parent_sector_analysis'] = get_parent_sector_recommendations(holdings, parent_sector_mappings, total_current_value, max_stocks_per_sector)
    
    return result

