"""
Backend services package for Investment Manager
Contains price scraping and API services
"""
from .price_scraper import get_scraped_price, get_stock_details
from .nse_api import get_nse_price

__all__ = [
    'get_scraped_price',
    'get_stock_details',
    'get_nse_price',
]

