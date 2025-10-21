"""
General helper utilities for Investment Manager
"""


def format_refresh_response(total: int, updated: int, failed: int) -> dict:
    """
    Format standardized refresh response.
    
    Args:
        total: Total stocks processed
        updated: Successfully updated count
        failed: Failed count
    
    Returns:
        Standardized response dictionary
    """
    return {
        'message': f'Total: {total}, Success: {updated}, Failed: {failed}',
        'total': total,
        'updated': updated,
        'failed': failed
    }


def clean_symbol(symbol: str) -> str:
    """
    Clean and uppercase stock symbol.
    
    Args:
        symbol: Stock symbol (may include .NS or .BO)
    
    Returns:
        Cleaned uppercase symbol
    """
    return symbol.strip().upper()

