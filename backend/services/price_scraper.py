"""
Multi-Source Stock Price Scraper for Investment Manager

This module fetches Indian stock prices and details from multiple sources:
1. Google Finance (primary for price)
2. Moneycontrol (fallback for price)
3. Investing.com (fallback for price)
4. Screener.in (optional for company name and day change %)

Designed to be resilient with automatic fallbacks when sources fail.
"""
import requests
from bs4 import BeautifulSoup
import re
from typing import Optional
import time

class PriceScraper:
    """
    Multi-source web scraper for fetching Indian stock prices and details.
    
    Features:
    - Automatic fallback between multiple sources
    - Robust price extraction with regex patterns
    - Company name and day change % fetching
    - Browser-like headers to avoid blocking
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def clean_symbol(self, symbol: str) -> str:
        """
        Remove exchange suffix from symbol.
        
        Args:
            symbol: Stock symbol with suffix (e.g., 'RELIANCE.NS', 'TCS.BO')
        
        Returns:
            Clean symbol without suffix (e.g., 'RELIANCE', 'TCS')
        """
        return symbol.replace('.NS', '').replace('.BO', '').upper()
    
    def extract_price_from_text(self, text: str) -> Optional[float]:
        """
        Extract numeric price from text using regex patterns.
        
        Handles formats like: ₹2,650.50, 2650.50, 2,650
        
        Args:
            text: String containing price information
        
        Returns:
            Extracted price as float or None if not found
        """
        # Look for patterns like: 2,650.50 or 2650.50 or ₹2,650
        patterns = [
            r'₹?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # ₹2,650.50
            r'(\d+\.\d{2})',  # 2650.50
            r'(\d{1,3}(?:,\d{3})+)',  # 2,650
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Get the first match and clean it
                price_str = matches[0].replace(',', '')
                try:
                    return float(price_str)
                except:
                    continue
        return None
    
    def fetch_from_google_finance(self, symbol: str) -> Optional[float]:
        """Scrape Google Finance"""
        clean_sym = self.clean_symbol(symbol)
        
        try:
            # Google Finance URL
            url = f"https://www.google.com/finance/quote/{clean_sym}:NSE"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Method 1: Look for the main price in specific classes
                # Google Finance typically uses these patterns
                price_classes = [
                    'YMlKec fxKbKc',  # Main price class
                    'YMlKec',
                    'fxKbKc',
                ]
                
                for class_name in price_classes:
                    price_div = soup.find('div', {'class': class_name})
                    if price_div:
                        text = price_div.get_text(strip=True)
                        # Remove currency symbols and commas
                        text = text.replace('₹', '').replace(',', '').strip()
                        try:
                            price = float(text)
                            if 10 < price < 1000000:  # Sanity check
                                print(f"[OK] Google Finance: {symbol} -> Rs.{price}")
                                return price
                        except:
                            continue
                
                # Method 2: Look for meta tags (Google sometimes uses these)
                meta_price = soup.find('meta', {'itemprop': 'price'})
                if meta_price and meta_price.get('content'):
                    try:
                        price = float(meta_price['content'])
                        if 10 < price < 1000000:
                            print(f"[OK] Google Finance (meta): {symbol} -> Rs.{price}")
                            return price
                    except:
                        pass
        
        except Exception as e:
            print(f"[WARN] Google Finance failed for {symbol}: {str(e)}")
        
        return None
    
    def fetch_from_moneycontrol(self, symbol: str) -> Optional[float]:
        """Scrape Moneycontrol"""
        clean_sym = self.clean_symbol(symbol)
        
        try:
            # Moneycontrol uses specific URL format
            url = f"https://www.moneycontrol.com/india/stockpricequote/{clean_sym}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Look for price in common locations
                price_spans = soup.find_all('span', {'class': re.compile(r'.*price.*|.*value.*', re.I)})
                
                for span in price_spans[:10]:  # Check first 10 matches
                    text = span.get_text(strip=True)
                    price = self.extract_price_from_text(text)
                    if price and 10 < price < 1000000:
                        print(f"[OK] Moneycontrol: {symbol} -> Rs.{price}")
                        return price
        
        except Exception as e:
            print(f"[WARN] Moneycontrol failed for {symbol}: {str(e)}")
        
        return None
    
    def fetch_from_screener(self, symbol: str) -> Optional[dict]:
        """
        Scrape Screener.in for stock details (name, price, day change %).
        
        NOTE: This source sometimes returns market cap instead of price.
        Use get_stock_price() for reliable price fetching.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS')
        
        Returns:
            Dict with keys: price, name, day_change_pct (all optional)
            Or None if fetch fails
        """
        clean_sym = self.clean_symbol(symbol)
        
        try:
            # Screener.in URL format
            url = f"https://www.screener.in/company/{clean_sym}/"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Get company name from h1
                name_elem = soup.find('h1')
                company_name = name_elem.get_text(strip=True) if name_elem else None
                
                # Clean up company name (remove "Ltd.", "Limited", etc. if needed)
                if company_name:
                    company_name = company_name.split('::')[0].strip()
                
                # Get price - Screener shows it in specific location
                # Look for the stock price which is typically in a span with specific ID or in the top section
                price = None
                
                # Method 1: Try to find price by looking for "Stock Price" label nearby
                price_elements = soup.find_all('span', class_='number')
                for elem in price_elements:
                    # Get the text and check if it's a reasonable price (not market cap which is in crores)
                    text = elem.get_text(strip=True).replace(',', '')
                    try:
                        val = float(text)
                        # Stock prices are typically between 1 and 100,000
                        # Market cap would be much larger (in crores/lakhs)
                        if 0.01 < val < 500000:
                            # Check if this is the first occurrence (usually price comes before market cap)
                            parent_text = elem.find_parent().get_text() if elem.find_parent() else ""
                            # Skip if it looks like market cap section
                            if 'market cap' not in parent_text.lower() and 'mcap' not in parent_text.lower():
                                price = val
                                break
                    except:
                        continue
                
                # Method 2: If method 1 failed, try finding by position (first number after company name)
                if not price:
                    # Screener typically shows price right after company name in top section
                    top_section = soup.find('div', {'id': 'top-ratios'}) or soup.find('div', class_='company-ratios')
                    if top_section:
                        first_number = top_section.find('span', class_='number')
                        if first_number:
                            try:
                                val = float(first_number.get_text(strip=True).replace(',', ''))
                                if 0.01 < val < 500000:
                                    price = val
                            except:
                                pass
                
                # Get day change percentage
                day_change_pct = None
                # Look for percentage change - usually near the price
                # Screener.in typically shows change in a span with class containing 'up' or 'down'
                change_spans = soup.find_all('span', class_=re.compile(r'(up|down|change)', re.I))
                for span in change_spans[:5]:  # Check first 5 matches
                    text = span.get_text(strip=True)
                    # Look for percentage pattern like "+2.5%" or "-1.3%"
                    match = re.search(r'([+-]?\d+\.?\d*)\s*%', text)
                    if match:
                        try:
                            day_change_pct = float(match.group(1))
                            break
                        except:
                            pass
                
                if price and 10 < price < 1000000:
                    result = {'price': price, 'name': company_name, 'day_change_pct': day_change_pct}
                    if day_change_pct is not None:
                        print(f"[OK] Screener.in: {symbol} -> {company_name} @ Rs.{price} ({day_change_pct:+.2f}%)")
                    else:
                        print(f"[OK] Screener.in: {symbol} -> {company_name} @ Rs.{price}")
                    return result
        
        except Exception as e:
            print(f"[WARN] Screener.in failed for {symbol}: {str(e)}")
        
        return None
    
    def fetch_from_investing_com(self, symbol: str) -> Optional[float]:
        """Scrape Investing.com"""
        clean_sym = self.clean_symbol(symbol)
        
        try:
            # Investing.com India stocks
            url = f"https://in.investing.com/search/?q={clean_sym}"
            
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'lxml')
                
                # Look for price patterns
                page_text = soup.get_text()
                price = self.extract_price_from_text(page_text[:3000])
                
                if price and 10 < price < 1000000:
                    print(f"[OK] Investing.com: {symbol} -> Rs.{price}")
                    return price
        
        except Exception as e:
            print(f"[WARN] Investing.com failed for {symbol}: {str(e)}")
        
        return None
    
    def get_stock_details(self, symbol: str) -> Optional[dict]:
        """
        Get comprehensive stock details: price, name, and day change %.
        
        Strategy:
        1. ALWAYS uses reliable sources for price (Google Finance/Moneycontrol/Investing.com)
        2. OPTIONALLY fetches name and day_change_pct from Screener.in
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS', 'TCS.NS')
        
        Returns:
            Dict with keys: price, name, day_change_pct (all optional)
            Returns None if price cannot be fetched
        """
        # Only for Indian stocks
        if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            return None
        
        result = {
            'price': None,
            'name': None,
            'day_change_pct': None
        }
        
        # ALWAYS use working price scraper for price (NEVER use Screener for price)
        try:
            price = self.get_stock_price(symbol)
            if price:
                result['price'] = price
                print(f"[OK] Price fetched: {symbol} -> Rs.{price}")
        except Exception as e:
            print(f"[ERROR] Price fetch failed for {symbol}: {str(e)}")
        
        # OPTIONALLY try to get name and day_change_pct from Screener (non-blocking)
        try:
            screener_data = self.fetch_from_screener(symbol)
            if screener_data:
                if screener_data.get('name'):
                    result['name'] = screener_data['name']
                    print(f"[OK] Name from Screener: {screener_data['name']}")
                if screener_data.get('day_change_pct') is not None:
                    result['day_change_pct'] = screener_data['day_change_pct']
                    print(f"[OK] Day change from Screener: {screener_data['day_change_pct']}%")
        except Exception as e:
            print(f"[WARN] Screener fetch failed (non-critical): {str(e)}")
        
        return result if result['price'] else None
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        """
        Fetch stock price using multiple fallback sources (RELIABLE METHOD).
        
        This is the recommended method for price fetching. It tries:
        1. Google Finance
        2. Moneycontrol  
        3. Investing.com
        
        NOTE: Screener.in is NOT used here as it sometimes returns market cap.
        
        Args:
            symbol: Stock symbol (e.g., 'RELIANCE.NS', 'TCS.NS', 'ABDL.NS')
        
        Returns:
            Current price as float or None if all sources fail
        """
        # Only for Indian stocks
        if not (symbol.endswith('.NS') or symbol.endswith('.BO')):
            return None
        
        # Use ORIGINAL working sources ONLY (NO Screener for now)
        sources = [
            self.fetch_from_google_finance,
            self.fetch_from_moneycontrol,
            self.fetch_from_investing_com,
        ]
        
        for source in sources:
            try:
                price = source(symbol)
                if price:
                    return price
                # Small delay between attempts
                time.sleep(0.5)
            except Exception as e:
                print(f"[ERROR] Source failed for {symbol}: {str(e)}")
                continue
        
        print(f"[FAIL] All sources failed for {symbol}")
        return None


# ============================================================================
# Singleton Instance and Public API
# ============================================================================

# Create singleton instance for reuse across the application
price_scraper = PriceScraper()


def get_scraped_price(symbol: str) -> Optional[float]:
    """
    Public API: Get stock price using web scraping.
    
    This is a convenience wrapper around PriceScraper.get_stock_price().
    Recommended for reliable price fetching.
    
    Args:
        symbol: Stock symbol with exchange suffix (e.g., 'RELIANCE.NS', 'TCS.NS')
    
    Returns:
        Current price as float or None if fetching fails
    
    Example:
        >>> price = get_scraped_price('RELIANCE.NS')
        >>> print(f"Price: Rs.{price}")
    """
    return price_scraper.get_stock_price(symbol)


def get_stock_details(symbol: str) -> Optional[dict]:
    """
    Public API: Get comprehensive stock details (price + name + day change).
    
    This fetches:
    - Price: From reliable sources (Google Finance/Moneycontrol)
    - Name: Company name from Screener.in (optional)
    - Day Change %: 1-day percentage change (optional)
    
    Args:
        symbol: Stock symbol with exchange suffix (e.g., 'RELIANCE.NS', 'TCS.NS')
    
    Returns:
        Dict with optional keys: price, name, day_change_pct
        Returns None if price cannot be fetched
    
    Example:
        >>> details = get_stock_details('TCS.NS')
        >>> print(f"{details['name']}: Rs.{details['price']} ({details['day_change_pct']:+.2f}%)")
    """
    return price_scraper.get_stock_details(symbol)


if __name__ == "__main__":
    # Test the scraper
    print("Testing Web Scraper...")
    print("-" * 60)
    
    test_symbols = [
        'RELIANCE.NS',
        'TCS.NS',
        'INFY.NS',
        'HDFCBANK.NS',
        'ICICIBANK.NS',
        'ABDL.NS',
    ]
    
    for symbol in test_symbols:
        print(f"\nTesting: {symbol}")
        price = get_scraped_price(symbol)
        if price:
            print(f"  SUCCESS: Rs.{price:,.2f}")
        else:
            print(f"  FAILED: Could not fetch price")
        print("-" * 60)
        time.sleep(1)  # Be polite to servers

