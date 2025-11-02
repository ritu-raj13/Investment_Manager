"""
Mutual Fund API Service

This module provides functions to fetch mutual fund NAV and scheme details
from web search and scraping.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re


def fetch_mf_nav_by_name(scheme_name):
    """
    Fetch current NAV for a mutual fund scheme by searching its name
    Uses mfapi.in direct search
    
    Args:
        scheme_name: Scheme name (e.g., "SBI Bluechip Fund")
        
    Returns:
        dict: NAV data or None if fetch fails
    """
    try:
        print(f"[MF_API] Fetching NAV for: {scheme_name}")
        
        # Method 1: Try mfapi.in search (most reliable)
        print(f"[MF_API] Trying mfapi.in search...")
        nav_data = _fetch_from_mfapi_search(scheme_name)
        if nav_data:
            print(f"[MF_API] ✓ Found via mfapi: {nav_data}")
            return nav_data
        
        # Method 2: Try direct Google Finance
        print(f"[MF_API] Trying direct MF lookup...")
        nav_data = _fetch_direct_nav(scheme_name)
        if nav_data:
            print(f"[MF_API] ✓ Found via direct lookup: {nav_data}")
            return nav_data
        
        print(f"[MF_API] ✗ All methods failed for: {scheme_name}")
        return None
    
    except Exception as e:
        print(f'[MF_API] ✗ Error fetching NAV for {scheme_name}: {str(e)}')
        return None


def _fetch_from_mfapi_search(scheme_name):
    """
    Fetch NAV by searching all schemes on mfapi.in
    Uses strict matching to prevent wrong scheme matches
    """
    try:
        print(f"[MFAPI] Searching for: {scheme_name}")
        
        # Fetch all schemes list
        url = 'https://api.mfapi.in/mf'
        response = requests.get(url, timeout=10)
        print(f"[MFAPI] Schemes list response: {response.status_code}")
        
        if response.status_code != 200:
            return None
            
        schemes = response.json()
        
        # Normalize search name
        search_name_normalized = _normalize_scheme_name(scheme_name)
        search_words = set(search_name_normalized.split())
        
        print(f"[MFAPI] Normalized search: {search_name_normalized}")
        print(f"[MFAPI] Searching through {len(schemes)} schemes...")
        
        # Strategy 1: Exact match (case-insensitive, normalized)
        for scheme in schemes:
            scheme_full_name = scheme.get('schemeName', '')
            normalized = _normalize_scheme_name(scheme_full_name)
            
            if search_name_normalized == normalized:
                print(f"[MFAPI] ✓ EXACT MATCH: {scheme_full_name}")
                return _fetch_nav_for_scheme(scheme)
        
        # Strategy 2: Very strict fuzzy match
        # Requirements:
        # 1. AMC name MUST match exactly (first word)
        # 2. All key words must be present
        # 3. Plan type must match (Direct/Regular, Growth/Dividend)
        
        search_amc = scheme_name.split()[0].lower()
        search_has_direct = 'direct' in scheme_name.lower()
        search_has_growth = 'growth' in scheme_name.lower()
        
        candidates = []
        
        for scheme in schemes:
            scheme_full_name = scheme.get('schemeName', '')
            scheme_lower = scheme_full_name.lower()
            
            # 1. AMC must match
            scheme_amc = scheme_full_name.split()[0].lower()
            if search_amc != scheme_amc:
                continue
            
            # 2. Plan type must match
            scheme_has_direct = 'direct' in scheme_lower
            scheme_has_growth = 'growth' in scheme_lower
            
            if search_has_direct != scheme_has_direct:
                continue
            if search_has_growth != scheme_has_growth:
                continue
            
            # 3. Calculate word overlap (excluding common words)
            common_words = {'fund', 'plan', 'option', 'scheme', '-', 'mutual'}
            scheme_words = set(_normalize_scheme_name(scheme_full_name).split()) - common_words
            relevant_search_words = search_words - common_words
            
            if not relevant_search_words:
                continue
                
            matching = scheme_words & relevant_search_words
            match_ratio = len(matching) / len(relevant_search_words)
            
            # Require 85% of meaningful words to match
            if match_ratio >= 0.85:
                candidates.append({
                    'scheme': scheme,
                    'name': scheme_full_name,
                    'match_ratio': match_ratio,
                    'matching_words': matching
                })
                print(f"[MFAPI] Candidate (match={match_ratio:.0%}): {scheme_full_name}")
        
        # Pick best candidate
        if candidates:
            best = max(candidates, key=lambda x: x['match_ratio'])
            print(f"[MFAPI] ✓ Best match ({best['match_ratio']:.0%}): {best['name']}")
            print(f"[MFAPI]   Your input: {scheme_name}")
            print(f"[MFAPI]   Matched to: {best['name']}")
            print(f"[MFAPI]   Matching words: {best['matching_words']}")
            return _fetch_nav_for_scheme(best['scheme'])
        
        print(f"[MFAPI] ✗ No matching scheme found")
        print(f"[MFAPI]   Tip: Try searching 'Tata Digital India' without 'Fund Direct Growth'")
        return None
    
    except Exception as e:
        print(f'[MFAPI] ✗ Error: {str(e)}')
        import traceback
        print(f"[MFAPI] Traceback: {traceback.format_exc()}")
        return None


def _normalize_scheme_name(name):
    """Normalize scheme name for comparison"""
    # Convert to lowercase
    normalized = name.lower()
    # Remove extra spaces and punctuation
    normalized = re.sub(r'[^\w\s]', ' ', normalized)
    normalized = re.sub(r'\s+', ' ', normalized)
    return normalized.strip()


def _fetch_nav_for_scheme(scheme):
    """Helper to fetch NAV given a scheme dict"""
    scheme_code = scheme.get('schemeCode')
    scheme_name = scheme.get('schemeName')
    
    nav_data = fetch_mf_nav(scheme_code)
    if nav_data:
        nav_value = nav_data.get('nav')
        print(f"[MFAPI] ✓ NAV fetched: {nav_value}")
        print(f"[MFAPI]   Scheme: {scheme_name}")
        print(f"[MFAPI]   Code: {scheme_code}")
        print(f"[MFAPI]   Date: {nav_data.get('date')}")
        return nav_data
    return None


def _fetch_direct_nav(scheme_name):
    """Direct NAV fetch using known patterns"""
    try:
        print(f"[DIRECT] Trying direct fetch for: {scheme_name}")
        
        # Extract AMC and scheme type from name
        # E.g., "Quant ELSS Tax Saver Fund Direct Growth"
        name_lower = scheme_name.lower()
        
        # Common patterns
        if 'direct' in name_lower and 'growth' in name_lower:
            # Try to construct search query
            amc = scheme_name.split()[0]  # First word is usually AMC
            
            # Use alternative API if available
            print(f"[DIRECT] Extracted AMC: {amc}")
            
        return None
    
    except Exception as e:
        print(f'[DIRECT] ✗ Error: {str(e)}')
        return None


def _fetch_from_google_search(scheme_name):
    """Fetch NAV from Google search results"""
    try:
        print(f"[GOOGLE] Searching for: {scheme_name}")
        
        # Search query
        query = f"{scheme_name} NAV latest"
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"[GOOGLE] Response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Save a snippet for debugging
            print(f"[GOOGLE] Page text length: {len(text)} chars")
            
            # More comprehensive patterns - look for decimals first
            patterns = [
                # Decimal patterns (more specific)
                r'NAV[:\s]*₹?\s*(\d+\.\d{2,4})',
                r'₹\s*(\d+\.\d{2,4})',
                r'Rs\.?\s*(\d+\.\d{2,4})',
                r'Current\s+NAV[:\s]*(\d+\.\d{2,4})',
                r'Latest\s+NAV[:\s]*(\d+\.\d{2,4})',
                # Fallback patterns
                r'(\d+\.\d{2,4})\s*₹',
                r'(\d+\.\d{2,4})\s*per\s*unit',
                r'Price[:\s]*(\d+\.\d{2,4})',
            ]
            
            found_values = []
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    try:
                        nav_value = float(match)
                        if 10 <= nav_value <= 10000:
                            found_values.append(nav_value)
                            print(f"[GOOGLE] Found potential NAV via pattern '{pattern}': {nav_value}")
                    except ValueError:
                        continue
            
            # Return the most common value if multiple found
            if found_values:
                from collections import Counter
                most_common = Counter(found_values).most_common(1)[0][0]
                result = {
                    'scheme_name': scheme_name,
                    'nav': most_common,
                    'date': datetime.now().strftime('%d-%m-%Y'),
                    'source': 'Google Search'
                }
                print(f"[GOOGLE] ✓ Success (selected most common): {result}")
                return result
            
            print(f"[GOOGLE] ✗ No valid NAV found in search results")
        
        return None
    
    except Exception as e:
        print(f'[GOOGLE] ✗ Error: {str(e)}')
        import traceback
        print(f"[GOOGLE] Traceback: {traceback.format_exc()}")
        return None


def _fetch_from_valueresearch(scheme_name):
    """Fetch NAV from ValueResearch Online"""
    try:
        print(f"[VR] Searching ValueResearch for: {scheme_name}")
        
        # Search on ValueResearch
        search_url = f"https://www.valueresearchonline.com/funds/newsearch.asp?search={scheme_name.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"[VR] Search response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for NAV in various elements
            nav_patterns = [
                r'NAV[:\s]*₹?\s*(\d+\.\d{2,4})',
                r'₹\s*(\d+\.\d{2,4})',
                r'Rs\.?\s*(\d+\.\d{2,4})',
            ]
            
            text = soup.get_text()
            for pattern in nav_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    nav_value = float(match)
                    if 10 <= nav_value <= 10000:
                        result = {
                            'scheme_name': scheme_name,
                            'nav': nav_value,
                            'date': datetime.now().strftime('%d-%m-%Y'),
                            'source': 'ValueResearch'
                        }
                        print(f"[VR] ✓ Success: {result}")
                        return result
        
        print(f"[VR] ✗ No NAV found")
        return None
    except Exception as e:
        print(f'[VR] ✗ Error: {str(e)}')
        return None


def _fetch_from_moneycontrol(scheme_name):
    """Fetch NAV from Moneycontrol"""
    try:
        print(f"[MC] Searching Moneycontrol for: {scheme_name}")
        
        # Moneycontrol search
        search_url = f"https://www.moneycontrol.com/mutual-funds/nav/search?search={scheme_name.replace(' ', '+')}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        print(f"[MC] Search response status: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Moneycontrol specific patterns
            nav_patterns = [
                r'NAV[:\s]*₹?\s*(\d+\.\d{2,4})',
                r'₹\s*(\d+\.\d{2,4})',
                r'Rs\.?\s*(\d+\.\d{2,4})',
            ]
            
            text = soup.get_text()
            for pattern in nav_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    nav_value = float(match)
                    if 10 <= nav_value <= 10000:
                        result = {
                            'scheme_name': scheme_name,
                            'nav': nav_value,
                            'date': datetime.now().strftime('%d-%m-%Y'),
                            'source': 'Moneycontrol'
                        }
                        print(f"[MC] ✓ Success: {result}")
                        return result
        
        print(f"[MC] ✗ No NAV found")
        return None
    except Exception as e:
        print(f'[MC] ✗ Error: {str(e)}')
        return None


def fetch_mf_nav(scheme_code):
    """
    Fetch current NAV for a mutual fund scheme by code
    Kept for backward compatibility
    
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

