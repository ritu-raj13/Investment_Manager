"""
Zone calculation utilities for Investment Manager
"""
from typing import Optional, Tuple, TypedDict


NEAR_ZONE_PCT = 0.03


class ZoneSignal(TypedDict, total=False):
    tier: str
    distance_pct: float
    distance_type: str


def parse_zone(zone_str: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Parse zone string and return (min, max) tuple.

    Args:
        zone_str: Zone string like "250-300" or "250"

    Returns:
        Tuple of (min_val, max_val) or (None, None) if invalid
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
    try:
        val = float(zone_str)
        return val, val
    except ValueError:
        return None, None


def _is_point_zone(zone_min: float, zone_max: float) -> bool:
    return zone_min == zone_max


def classify_buy_signal(
    current_price: float,
    buy_min: Optional[float],
    buy_max: Optional[float],
    near_pct: float = NEAR_ZONE_PCT,
) -> Optional[ZoneSignal]:
    """Buy favors lower prices: ideal below min, in at band, near above max."""
    if buy_max is None or buy_min is None or current_price is None:
        return None

    if _is_point_zone(buy_min, buy_max):
        ideal_cutoff = buy_max * (1 - near_pct)
        if current_price < ideal_cutoff:
            distance_pct = ((buy_max - current_price) / buy_max) * 100
            return {'tier': 'ideal', 'distance_pct': distance_pct, 'distance_type': 'below'}
        if current_price <= buy_max:
            return {'tier': 'in'}
        if current_price <= buy_max * (1 + near_pct):
            distance_pct = ((current_price - buy_max) / buy_max) * 100
            return {'tier': 'near', 'distance_pct': distance_pct, 'distance_type': 'above'}
        return None

    if current_price < buy_min:
        distance_pct = ((buy_min - current_price) / buy_min) * 100
        return {'tier': 'ideal', 'distance_pct': distance_pct, 'distance_type': 'below'}
    if buy_min <= current_price <= buy_max:
        return {'tier': 'in'}
    if buy_max < current_price <= buy_max * (1 + near_pct):
        distance_pct = ((current_price - buy_max) / buy_max) * 100
        return {'tier': 'near', 'distance_pct': distance_pct, 'distance_type': 'above'}
    return None


def classify_average_signal(
    current_price: float,
    avg_min: Optional[float],
    avg_max: Optional[float],
    near_pct: float = NEAR_ZONE_PCT,
) -> Optional[ZoneSignal]:
    """Average favors lower prices: ideal below min (no floor), in at band, near above max."""
    if avg_max is None or avg_min is None or current_price is None:
        return None

    if current_price < avg_min:
        distance_pct = ((avg_min - current_price) / avg_min) * 100
        return {'tier': 'ideal', 'distance_pct': distance_pct, 'distance_type': 'below'}
    if avg_min <= current_price <= avg_max:
        return {'tier': 'in'}
    if avg_max < current_price <= avg_max * (1 + near_pct):
        distance_pct = ((current_price - avg_max) / avg_max) * 100
        return {'tier': 'near', 'distance_pct': distance_pct, 'distance_type': 'above'}
    return None


def classify_sell_signal(
    current_price: float,
    sell_min: Optional[float],
    sell_max: Optional[float],
    near_pct: float = NEAR_ZONE_PCT,
) -> Optional[ZoneSignal]:
    """Sell favors higher prices: near below min, in at band, ideal above max."""
    if sell_min is None or sell_max is None or current_price is None:
        return None

    if current_price > sell_max:
        distance_pct = ((current_price - sell_max) / sell_max) * 100
        return {'tier': 'ideal', 'distance_pct': distance_pct, 'distance_type': 'above'}
    if sell_min <= current_price <= sell_max:
        return {'tier': 'in'}
    if sell_min * (1 - near_pct) <= current_price < sell_min:
        distance_pct = ((sell_min - current_price) / sell_min) * 100
        return {'tier': 'near', 'distance_pct': distance_pct, 'distance_type': 'below'}
    return None
