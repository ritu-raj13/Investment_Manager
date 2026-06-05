"""
Unified stock price and 1-day change fetching.

Fallback order (both price and day_change_pct):
  Yahoo → Screener → Google Finance → NSE API
"""
from __future__ import annotations

import time
from typing import Any, Dict, Optional, Tuple

import yfinance as yf

from services.nse_api import get_nse_day_change_pct, get_nse_price
from services.screener_parser import fetch_company_supplement

CHAIN_LABEL = "Yahoo -> Screener -> Google -> NSE"
HTML_STEP_DELAY_SEC = 0.35


def yahoo_last_close(symbol: str) -> Optional[float]:
    """Last daily close from Yahoo."""
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="1mo", auto_adjust=False)
        if hist is None or hist.empty:
            hist = t.history(period="3mo", auto_adjust=False)
        if hist is not None and not hist.empty:
            return round(float(hist["Close"].iloc[-1]), 2)
    except Exception as e:
        print(f"[WARN] Yahoo price failed for {symbol}: {e}")
    return None


def yahoo_day_change_pct(symbol: str) -> Optional[float]:
    """Prior row vs last close % from Yahoo daily bars."""
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="10d", auto_adjust=False)
        if hist is None or hist.empty or len(hist) < 2:
            hist = t.history(period="3mo", auto_adjust=False)
        if hist is None or hist.empty or len(hist) < 2:
            return None
        c = hist["Close"].astype(float)
        last = float(c.iloc[-1])
        prev = float(c.iloc[-2])
        if prev > 0:
            return (last - prev) / prev * 100.0
    except Exception as e:
        print(f"[WARN] Yahoo 1D%% failed for {symbol}: {e}")
    return None


def _screener_supplement(symbol: str, cached: Optional[dict]) -> dict:
    if cached is not None:
        return cached
    return fetch_company_supplement(symbol) or {}


def _price_from_screener(sup: dict) -> Optional[float]:
    price = sup.get("price")
    if price is not None:
        try:
            p = float(price)
            if 0.01 < p < 100000:
                return round(p, 2)
        except (TypeError, ValueError):
            pass
    return None


def _day_change_from_screener(sup: dict) -> Optional[float]:
    pct = sup.get("day_change_pct")
    if pct is not None:
        try:
            return float(pct)
        except (TypeError, ValueError):
            pass
    return None


def fetch_stock_price(
    symbol: str,
    *,
    screener_supplement: Optional[dict] = None,
    quiet: bool = False,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Returns (price, source) where source is Yahoo|Screener|Google|NSE.
    """
    from services.price_scraper import price_scraper

    sym = (symbol or "").strip().upper()
    is_indian = sym.endswith(".NS") or sym.endswith(".BO")

    price = yahoo_last_close(sym)
    if price is not None:
        return price, "Yahoo"

    if is_indian:
        sup = _screener_supplement(sym, screener_supplement)
        price = _price_from_screener(sup)
        if price is not None:
            return price, "Screener"
        time.sleep(HTML_STEP_DELAY_SEC)

        price = price_scraper.fetch_from_google_finance(sym, quiet=quiet)
        if price is not None:
            return round(price, 2), "Google"
        time.sleep(HTML_STEP_DELAY_SEC)

        price = get_nse_price(sym)
        if price is not None:
            return round(float(price), 2), "NSE"

    return None, None


def fetch_stock_day_change_pct(
    symbol: str,
    *,
    screener_supplement: Optional[dict] = None,
    quiet: bool = False,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Returns (day_change_pct, source) where source is Yahoo|Screener|Google|NSE.
    """
    from services.price_scraper import price_scraper

    sym = (symbol or "").strip().upper()
    is_indian = sym.endswith(".NS") or sym.endswith(".BO")

    pct = yahoo_day_change_pct(sym)
    if pct is not None:
        return pct, "Yahoo"

    if is_indian:
        sup = _screener_supplement(sym, screener_supplement)
        pct = _day_change_from_screener(sup)
        if pct is not None:
            return pct, "Screener"
        time.sleep(HTML_STEP_DELAY_SEC)

        pct = price_scraper.fetch_day_change_from_google_finance(sym, quiet=quiet)
        if pct is not None:
            return pct, "Google"
        time.sleep(HTML_STEP_DELAY_SEC)

        if sym.endswith(".NS"):
            pct = get_nse_day_change_pct(sym)
            if pct is not None:
                return pct, "NSE"

    return None, None
