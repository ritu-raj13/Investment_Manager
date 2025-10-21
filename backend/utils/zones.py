"""
Zone calculation utilities for Investment Manager
"""
from typing import Optional, Tuple


def parse_zone(zone_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse zone string and return (min, max) tuple.
    
    Args:
        zone_str: Zone string like "250-300" or "250"
    
    Returns:
        Tuple of (min_val, max_val) or (None, None) if invalid
    
    Examples:
        "250-300" -> (250.0, 300.0)
        "250" -> (250.0, 250.0)
        "" -> (None, None)
    """
    if not zone_str:
        return None, None
    
    zone_str = str(zone_str).strip()
    
    if '-' in zone_str:
        parts = zone_str.split('-')
        try:
            return float(parts[0]), float(parts[1])
        except (ValueError, IndexError):
            return None, None
    else:
        try:
            val = float(zone_str)
            return val, val
        except ValueError:
            return None, None


def is_in_zone(current_price: float, zone_min: float, zone_max: float, 
               threshold_pct: float = 0.05) -> Tuple[bool, bool]:
    """
    Check if price is in zone or near zone.
    
    Args:
        current_price: Current stock price
        zone_min: Zone minimum value
        zone_max: Zone maximum value
        threshold_pct: Threshold percentage for "near" (default 5%)
    
    Returns:
        Tuple of (is_in_zone, is_near_zone)
    """
    if zone_min is None or zone_max is None:
        return False, False
    
    # Check if in zone
    if zone_min <= current_price <= zone_max:
        return True, False
    
    # Check if near zone (within threshold)
    lower_threshold = zone_min * (1 - threshold_pct)
    upper_threshold = zone_max * (1 + threshold_pct)
    
    if lower_threshold <= current_price < zone_min or zone_max < current_price <= upper_threshold:
        return False, True
    
    return False, False

