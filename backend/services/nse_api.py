"""
NSE India API integration for fetching live stock prices
"""
import json
import requests
from typing import Any, Dict, Optional
from urllib.parse import urlencode


class NSEClient:
    """Client for NSE India API"""

    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9",
                # Omit "br" unless brotli is installed; else NSE returns undecoded binary and JSON parse fails.
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "DNT": "1",
                "Pragma": "no-cache",
                "Cache-Control": "no-cache",
            }
        )
        self._warm_cookies()

    def _warm_cookies(self) -> None:
        """NSE JSON APIs often require a recent homepage visit for cookies."""
        try:
            self.session.get(self.base_url, timeout=8)
        except Exception:
            pass

    def fetch_quote_equity(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        GET /api/quote-equity for symbol (NSE listing). .BO symbols may not resolve here.

        Returns:
            Parsed JSON dict, or None on failure.
        """
        clean_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()
        quote_url = f"{self.base_url}/api/quote-equity"
        referer = f"{self.base_url}/get-quote/equity?{urlencode({'symbol': clean_symbol})}"
        quote_headers = {"Referer": referer}

        for attempt in range(2):
            if attempt:
                self._warm_cookies()
            try:
                response = self.session.get(
                    quote_url,
                    params={"symbol": clean_symbol},
                    timeout=12,
                    headers=quote_headers,
                )
            except requests.RequestException as e:
                print(f"NSE API Error for {clean_symbol}: {e}")
                return None

            if response.status_code != 200:
                if attempt == 1:
                    print(
                        f"NSE API Error for {clean_symbol}: HTTP {response.status_code}"
                    )
                continue

            raw = (response.text or "").strip()
            if not raw:
                if attempt == 0:
                    continue
                print(f"NSE API Error for {clean_symbol}: empty response body")
                return None

            try:
                return json.loads(raw)
            except json.JSONDecodeError as e:
                if attempt == 0:
                    continue
                preview = raw[:120].replace("\n", " ")
                preview = preview.encode("ascii", "backslashreplace").decode("ascii")
                print(
                    f"NSE API Error for {clean_symbol}: invalid JSON ({e}); "
                    f"body starts: {preview!r}"
                )
                return None

        return None

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """
        Get current stock price from NSE

        Args:
            symbol: Stock symbol (e.g., 'RELIANCE', 'TCS', 'INFY')
                   Can also accept .NS suffix which will be stripped

        Returns:
            Current price as float or None if failed
        """
        data = self.fetch_quote_equity(symbol)
        if not data:
            return None

        price = None
        if "priceInfo" in data:
            price_info = data["priceInfo"]
            price = (
                price_info.get("lastPrice")
                or price_info.get("close")
                or price_info.get("intraDayHighLow", {}).get("max")
            )
        if not price and "metadata" in data:
            price = data["metadata"].get("lastPrice")
        if price:
            return float(price)
        return None


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


def get_nse_day_change_pct(symbol: str) -> Optional[float]:
    """
    Official session % change vs previous close from NSE quote-equity (priceInfo.pChange).

    Args:
        symbol: e.g. 'SBICARD.NS' (NSE-listed; .BO may not return data from this endpoint)

    Returns:
        Percentage change (e.g. 0.17 for +0.17%) or None.
    """
    data = nse_client.fetch_quote_equity(symbol)
    if not data or "priceInfo" not in data:
        return None
    pi = data["priceInfo"]
    p = pi.get("pChange")
    if p is not None:
        try:
            return float(p)
        except (TypeError, ValueError):
            pass
    prev = pi.get("previousClose") or pi.get("basePrice")
    chg = pi.get("change")
    if prev is not None and chg is not None:
        try:
            pf, cf = float(prev), float(chg)
            if pf > 0:
                return (cf / pf) * 100.0
        except (TypeError, ValueError):
            pass
    return None


if __name__ == "__main__":
    # Test the NSE API
    print("Testing NSE India API...")
    print("-" * 60)

    test_symbols = [
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
        "HDFCBANK.NS",
        "ICICIBANK.NS",
        "SBIN.NS",
        "ABDL.NS",
    ]

    for symbol in test_symbols:
        price = get_nse_price(symbol)
        pct = get_nse_day_change_pct(symbol)
        if price is not None:
            extra = f" ({pct:+.2f}%)" if pct is not None else ""
            print(f"[OK] {symbol:15} -> Rs.{price:,.2f}{extra}")
        else:
            print(f"[FAIL] {symbol:15} -> Failed to fetch")

    print("-" * 60)
