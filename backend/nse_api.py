"""
NSE India API integration for fetching live stock prices
"""
import requests
from typing import Optional

class NSEClient:
    """Client for NSE India API"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Pragma': 'no-cache',
            'Cache-Control': 'no-cache'
        })
        # Initialize session with a request to set cookies
        try:
            self.session.get(self.base_url, timeout=5)
        except:
            pass
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        """
        Get current stock price from NSE
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
                   Can also accept .NS suffix which will be stripped
        
        Returns:
            Current price as float or None if failed
        """
        # Clean symbol - remove .NS or .BO suffix
        clean_symbol = symbol.replace('.NS', '').replace('.BO', '').upper()
        
        try:
            # NSE Quote API endpoint
            url = f"{self.base_url}/api/quote-equity?symbol={clean_symbol}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Try to get the last price from various possible fields
                price = None
                
                # Check priceInfo section
                if 'priceInfo' in data:
                    price_info = data['priceInfo']
                    price = (price_info.get('lastPrice') or 
                            price_info.get('close') or 
                            price_info.get('intraDayHighLow', {}).get('max'))
                
                # Check metadata section as fallback
                if not price and 'metadata' in data:
                    price = data['metadata'].get('lastPrice')
                
                if price:
                    return float(price)
            
            return None
            
        except Exception as e:
            print(f"NSE API Error for {clean_symbol}: {str(e)}")
            return None
    
    def get_multiple_prices(self, symbols: list) -> dict:
        """
        Get prices for multiple stocks
        
        Args:
            symbols: List of stock symbols
        
        Returns:
            Dictionary mapping symbol to price
        """
        prices = {}
        for symbol in symbols:
            price = self.get_stock_price(symbol)
            if price:
                prices[symbol] = price
        return prices


# Create a singleton instance
nse_client = NSEClient()


def get_nse_price(symbol: str) -> Optional[float]:
    """
    Convenience function to get NSE stock price
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE.NS', 'TCS', 'INFY.NS')
    
    Returns:
        Current price or None
    """
    return nse_client.get_stock_price(symbol)


if __name__ == "__main__":
    # Test the NSE API
    print("Testing NSE India API...")
    print("-" * 60)
    
    test_symbols = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'HDFCBANK.NS',
        'ICICIBANK.NS',
        'SBIN.NS',
        'ABDL.NS',
    ]
    
    for symbol in test_symbols:
        price = get_nse_price(symbol)
        if price:
            print(f"[OK] {symbol:15} -> Rs.{price:,.2f}")
        else:
            print(f"[FAIL] {symbol:15} -> Failed to fetch")
    
    print("-" * 60)

