"""
Multi-source stock data helpers for Investment Manager.

Unified price / 1D change chains live in services.market_data (Yahoo → Screener → Google → NSE).
This module provides HTML scrapers (Google Finance, Screener) and get_stock_details().
"""
import re
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

from services.market_data import fetch_stock_day_change_pct, fetch_stock_price
from services.screener_parser import fetch_company_supplement


class PriceScraper:
    """HTML scrapers for Indian stocks (Google Finance, Screener)."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            }
        )

    def clean_symbol(self, symbol: str) -> str:
        return symbol.replace(".NS", "").replace(".BO", "").upper()

    def _google_finance_soup(self, symbol: str) -> Optional[BeautifulSoup]:
        clean_sym = self.clean_symbol(symbol)
        url = f"https://www.google.com/finance/quote/{clean_sym}:NSE"
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                return BeautifulSoup(response.content, "lxml")
        except Exception as e:
            print(f"[WARN] Google Finance request failed for {symbol}: {e}")
        return None

    def fetch_from_google_finance(self, symbol: str, *, quiet: bool = False) -> Optional[float]:
        """Scrape last price from Google Finance."""
        soup = self._google_finance_soup(symbol)
        if not soup:
            return None

        price_classes = ["YMlKec fxKbKc", "YMlKec", "fxKbKc"]
        for class_name in price_classes:
            price_div = soup.find("div", {"class": class_name})
            if price_div:
                text = price_div.get_text(strip=True).replace("₹", "").replace(",", "").strip()
                try:
                    price = float(text)
                    if 0.01 < price < 100000:
                        if not quiet:
                            print(f"[OK] Google Finance: {symbol} -> Rs.{price}")
                        return price
                except ValueError:
                    continue

        meta_price = soup.find("meta", {"itemprop": "price"})
        if meta_price and meta_price.get("content"):
            try:
                price = float(meta_price["content"])
                if 0.01 < price < 100000:
                    if not quiet:
                        print(f"[OK] Google Finance (meta): {symbol} -> Rs.{price}")
                    return price
            except ValueError:
                pass

        if not quiet:
            print(f"[WARN] Google Finance: no price for {symbol}")
        return None

    def fetch_day_change_from_google_finance(
        self, symbol: str, *, quiet: bool = False
    ) -> Optional[float]:
        """Scrape 1-day % change from Google Finance quote page."""
        soup = self._google_finance_soup(symbol)
        if not soup:
            return None

        # Prefer change elements near the quote header (daily % is usually small)
        candidates = []
        for elem in soup.find_all(["div", "span"], limit=200):
            text = elem.get_text(strip=True)
            m = re.search(r"([+-]?\d+\.?\d*)\s*%", text)
            if not m:
                continue
            try:
                val = float(m.group(1))
            except ValueError:
                continue
            if -30.0 <= val <= 30.0 and len(text) < 40:
                candidates.append(val)

        if candidates:
            pct = candidates[0]
            if not quiet:
                print(f"[OK] Google Finance 1D: {symbol} -> {pct:+.2f}%")
            return pct

        if not quiet:
            print(f"[WARN] Google Finance: no 1D %% for {symbol}")
        return None

    def fetch_price_from_screener(self, symbol: str, *, quiet: bool = False) -> Optional[float]:
        """Price from Screener.in company page."""
        try:
            sup = fetch_company_supplement(symbol)
            price = sup.get("price") if sup else None
            if price is not None and 0.01 < float(price) < 100000:
                if not quiet:
                    print(f"[OK] Screener: {symbol} -> Rs.{price}")
                return float(price)
        except Exception as e:
            if not quiet:
                print(f"[WARN] Screener price failed for {symbol}: {e}")
        return None

    def get_stock_details(self, symbol: str) -> Optional[dict]:
        """
        Price and 1D via unified chain; name/sector/market cap from one Screener fetch.
        """
        if not (symbol.endswith(".NS") or symbol.endswith(".BO")):
            return None

        result = {
            "price": None,
            "name": None,
            "day_change_pct": None,
            "market_cap_cr": None,
            "parent_sector": None,
            "sector": None,
            "sector_peer_raw": None,
        }

        sup = {}
        try:
            sup = fetch_company_supplement(symbol) or {}
            if sup.get("name"):
                result["name"] = sup["name"]
            if sup.get("market_cap_cr") is not None:
                result["market_cap_cr"] = sup["market_cap_cr"]
            if sup.get("parent_sector"):
                result["parent_sector"] = sup["parent_sector"]
            if sup.get("sector"):
                result["sector"] = sup["sector"]
            if sup.get("sector_peer_raw"):
                result["sector_peer_raw"] = sup["sector_peer_raw"]
        except Exception as e:
            print(f"[WARN] Screener supplement failed for {symbol}: {e}")

        price, price_src = fetch_stock_price(symbol, screener_supplement=sup)
        if price is not None:
            result["price"] = price
            print(f"[OK] Price ({price_src}): {symbol} -> Rs.{price}")

        pct, pct_src = fetch_stock_day_change_pct(symbol, screener_supplement=sup)
        if pct is not None:
            result["day_change_pct"] = pct
            print(f"[OK] 1D ({pct_src}): {symbol} -> {pct:+.2f}%")

        return result if result["price"] else None

    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Unified chain: Yahoo → Screener → Google → NSE."""
        price, _ = fetch_stock_price(symbol)
        return price


price_scraper = PriceScraper()


def get_scraped_price(symbol: str) -> Optional[float]:
    """Get stock price via unified fallback chain."""
    price, _ = fetch_stock_price(symbol)
    return price


def get_stock_details(symbol: str) -> Optional[dict]:
    """Get price, 1D change, and Screener metadata."""
    return price_scraper.get_stock_details(symbol)


if __name__ == "__main__":
    from services.market_data import CHAIN_LABEL

    print(f"Testing unified price chain ({CHAIN_LABEL})...")
    print("-" * 60)
    for symbol in ["RELIANCE.NS", "TCS.NS", "INFY.NS"]:
        price, src = fetch_stock_price(symbol)
        pct, src1d = fetch_stock_day_change_pct(symbol)
        print(f"{symbol}: price={price} ({src}), 1D={pct} ({src1d})")
        print("-" * 60)
        time.sleep(1)
