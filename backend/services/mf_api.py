"""
Mutual Fund API Service

This module provides functions to fetch mutual fund NAV and scheme details
from AMFI (Association of Mutual Funds in India) and other sources.
"""

import requests
from datetime import datetime


def fetch_mf_nav(scheme_code):
    """
    Fetch current NAV for a mutual fund scheme
    
    Args:
        scheme_code: Scheme code (e.g., "119551" for SBI Bluechip Fund)
        
    Returns:
        dict: NAV data or None if fetch fails
    """
    try:
        # Use MF API (https://www.mfapi.in/)
        url = f'https://api.mfapi.in/mf/{scheme_code}/latest'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'data' in data and len(data['data']) > 0:
                latest = data['data'][0]
                
                return {
                    'scheme_code': scheme_code,
                    'scheme_name': data.get('meta', {}).get('scheme_name'),
                    'nav': float(latest.get('nav', 0)),
                    'date': latest.get('date'),
                    'fund_house': data.get('meta', {}).get('fund_house')
                }
        
        return None
    
    except Exception as e:
        print(f'Error fetching NAV for scheme {scheme_code}: {str(e)}')
        return None


def search_mf_schemes(query, limit=10):
    """
    Search for mutual fund schemes by name
    
    Args:
        query: Search query (scheme name or keyword)
        limit: Maximum number of results
        
    Returns:
        list: List of matching schemes
    """
    try:
        # Use MF API search (note: this is a simplified implementation)
        # In production, you might want to maintain a local cache of schemes
        
        # For now, return a placeholder
        # In real implementation, you would:
        # 1. Fetch scheme master list from AMFI
        # 2. Filter by query
        # 3. Return matching results
        
        return []
    
    except Exception as e:
        print(f'Error searching MF schemes: {str(e)}')
        return []


def fetch_all_mf_navs(scheme_codes):
    """
    Fetch NAVs for multiple schemes
    
    Args:
        scheme_codes: List of scheme codes
        
    Returns:
        dict: Dictionary with scheme_code as key and NAV data as value
    """
    navs = {}
    
    for scheme_code in scheme_codes:
        nav_data = fetch_mf_nav(scheme_code)
        if nav_data:
            navs[scheme_code] = nav_data
    
    return navs


def get_mf_historical_nav(scheme_code, start_date=None, end_date=None):
    """
    Fetch historical NAV data for a scheme
    
    Args:
        scheme_code: Scheme code
        start_date: Start date for historical data (YYYY-MM-DD)
        end_date: End date for historical data (YYYY-MM-DD)
        
    Returns:
        list: Historical NAV data
    """
    try:
        # Use MF API for historical data
        url = f'https://api.mfapi.in/mf/{scheme_code}'
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'data' in data:
                historical = data['data']
                
                # Filter by date range if provided
                if start_date or end_date:
                    filtered = []
                    for entry in historical:
                        entry_date = datetime.strptime(entry['date'], '%d-%m-%Y').date()
                        
                        if start_date and entry_date < datetime.strptime(start_date, '%Y-%m-%d').date():
                            continue
                        if end_date and entry_date > datetime.strptime(end_date, '%Y-%m-%d').date():
                            continue
                        
                        filtered.append(entry)
                    
                    return filtered
                
                return historical
        
        return []
    
    except Exception as e:
        print(f'Error fetching historical NAV for scheme {scheme_code}: {str(e)}')
        return []


def get_mf_scheme_details(scheme_code):
    """
    Get detailed information about a mutual fund scheme
    
    Args:
        scheme_code: Scheme code
        
    Returns:
        dict: Scheme details including metadata
    """
    try:
        url = f'https://api.mfapi.in/mf/{scheme_code}'
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and 'meta' in data:
                meta = data['meta']
                
                return {
                    'scheme_code': meta.get('scheme_code'),
                    'scheme_name': meta.get('scheme_name'),
                    'fund_house': meta.get('fund_house'),
                    'scheme_type': meta.get('scheme_type'),
                    'scheme_category': meta.get('scheme_category'),
                    'scheme_start_date': meta.get('scheme_start_date')
                }
        
        return None
    
    except Exception as e:
        print(f'Error fetching scheme details for {scheme_code}: {str(e)}')
        return None


def calculate_mf_returns(scheme_code, period_days=365):
    """
    Calculate returns for a mutual fund scheme over a period
    
    Args:
        scheme_code: Scheme code
        period_days: Number of days to calculate returns for (default: 365 = 1 year)
        
    Returns:
        dict: Returns data (absolute and percentage)
    """
    try:
        from datetime import date, timedelta
        
        # Fetch historical data
        end_date = date.today().strftime('%Y-%m-%d')
        start_date = (date.today() - timedelta(days=period_days)).strftime('%Y-%m-%d')
        
        historical = get_mf_historical_nav(scheme_code, start_date, end_date)
        
        if len(historical) < 2:
            return None
        
        # Get latest and oldest NAV in the period
        latest_nav = float(historical[0]['nav'])
        oldest_nav = float(historical[-1]['nav'])
        
        absolute_returns = latest_nav - oldest_nav
        percentage_returns = (absolute_returns / oldest_nav) * 100
        
        # Annualize if period is not 1 year
        if period_days != 365:
            annualized_returns = ((1 + percentage_returns / 100) ** (365 / period_days) - 1) * 100
        else:
            annualized_returns = percentage_returns
        
        return {
            'scheme_code': scheme_code,
            'period_days': period_days,
            'start_nav': oldest_nav,
            'end_nav': latest_nav,
            'absolute_returns': round(absolute_returns, 2),
            'percentage_returns': round(percentage_returns, 2),
            'annualized_returns': round(annualized_returns, 2),
            'start_date': historical[-1]['date'],
            'end_date': historical[0]['date']
        }
    
    except Exception as e:
        print(f'Error calculating returns for scheme {scheme_code}: {str(e)}')
        return None

