"""
Parse Screener.in HTML: company ratios (market cap), peer hierarchy, and
market-cap screen ranking for Large/Mid/Small/Micro thresholds.
"""
from __future__ import annotations

import html as html_lib
import re
import time
from typing import Any, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

# Public screen: companies sorted by market cap (desc). ~25 rows per page.
SCREENER_MC_SCREEN_BASE = (
    "https://www.screener.in/screens/2662927/companies-by-market-cap/"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def parse_indian_number_cr(text: str) -> Optional[float]:
    """Parse Screener-style numbers like '8,64,651' or '1824312.13' to float (crores)."""
    if not text:
        return None
    cleaned = text.replace(",", "").replace("₹", "").strip()
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_market_cap_cr_from_soup(soup: BeautifulSoup) -> Optional[float]:
    """#top-ratios first li where name is 'Market Cap'."""
    for li in soup.select("#top-ratios li"):
        name_el = li.select_one("span.name")
        if not name_el:
            continue
        if "Market Cap" not in name_el.get_text():
            continue
        num_el = li.select_one("span.number")
        if not num_el:
            return None
        return parse_indian_number_cr(num_el.get_text())
    return None


def extract_peer_sector_second_last(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    """
    Peer comparison breadcrumb in section#peers: take second-to-last link text.
    Returns (sector, raw_concat_for_debug).
    """
    section = soup.select_one("section#peers")
    if not section:
        return None, None

    labels: List[str] = []
    for p in section.select("p.sub"):
        if p.get("id") == "benchmarks":
            continue
        links = p.find_all("a", href=True)
        texts = []
        for a in links:
            t = a.get_text(strip=True)
            if t:
                texts.append(html_lib.unescape(t))
        if len(texts) >= 2:
            labels = texts
            break
        if len(texts) == 1 and not labels:
            labels = texts

    if not labels:
        return None, None

    raw = " | ".join(labels)
    if len(labels) >= 2:
        return labels[-2], raw
    return labels[-1], raw


def parse_screener_company_page(
    soup: BeautifulSoup,
) -> dict:
    """Extract fields from a loaded company/consolidated HTML page."""
    out: dict = {
        "name": None,
        "price": None,
        "day_change_pct": None,
        "market_cap_cr": None,
        "sector": None,
        "sector_peer_raw": None,
    }

    h1 = soup.find("h1")
    if h1:
        name = h1.get_text(strip=True).split("::")[0].strip()
        out["name"] = name or None

    out["market_cap_cr"] = extract_market_cap_cr_from_soup(soup)
    sector, raw = extract_peer_sector_second_last(soup)
    out["sector"] = sector
    out["sector_peer_raw"] = raw

    # Price: first span.number in top-ratios for "Current Price", else heuristic
    for li in soup.select("#top-ratios li"):
        name_el = li.select_one("span.name")
        if name_el and "Current Price" in name_el.get_text():
            num_el = li.select_one("span.number")
            if num_el:
                val = parse_indian_number_cr(num_el.get_text())
                if val is not None and 0.01 < val < 100000:
                    out["price"] = val
                    break

    if out["price"] is None:
        for elem in soup.find_all("span", class_="number"):
            text = elem.get_text(strip=True)
            val = parse_indian_number_cr(text)
            if val is None or not (0.01 < val < 100000):
                continue
            parent_text = elem.find_parent().get_text() if elem.find_parent() else ""
            pl = parent_text.lower()
            if "market cap" in pl or "mcap" in pl:
                continue
            out["price"] = val
            break

    change_spans = soup.find_all("span", class_=re.compile(r"(up|down|change)", re.I))
    for span in change_spans[:5]:
        m = re.search(r"([+-]?\d+\.?\d*)\s*%", span.get_text(strip=True))
        if m:
            try:
                out["day_change_pct"] = float(m.group(1))
                break
            except ValueError:
                pass

    return out


def fetch_screener_company_session(session: requests.Session, symbol: str) -> Optional[BeautifulSoup]:
    clean = symbol.replace(".NS", "").replace(".BO", "").upper()
    url = f"https://www.screener.in/company/{clean}/consolidated/"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            url2 = f"https://www.screener.in/company/{clean}/"
            r = session.get(url2, timeout=15)
        if r.status_code != 200:
            return None
        ctype = r.headers.get("Content-Type", "")
        if "text/html" in ctype and "Register" in r.text[:3000] and "login" in r.text.lower()[:5000]:
            return None
        return BeautifulSoup(r.content, "lxml")
    except requests.RequestException:
        return None


def fetch_company_supplement(symbol: str) -> dict:
    """HTTP fetch + parse; returns dict (may have nulls)."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )
    soup = fetch_screener_company_session(session, symbol)
    if not soup:
        return {}
    return parse_screener_company_page(soup)


def _parse_mc_screen_page_market_caps(html: str) -> List[float]:
    soup = BeautifulSoup(html, "lxml")
    caps: List[float] = []
    for tr in soup.select('tr[data-row-company-id]'):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        # S.No | Name | CMP | P/E | Mar Cap ...
        mcap_text = tds[4].get_text(strip=True)
        val = parse_indian_number_cr(mcap_text)
        if val is not None and val > 1:
            caps.append(val)
    return caps


def fetch_market_cap_rank_thresholds(
    max_pages: int = 25,
    delay_sec: float = 0.45,
) -> Optional[Tuple[float, float, float]]:
    """
    Load Screener 'Companies by Market Cap' screen pages until we have >= 500 MC values.
    Returns (mc_at_rank_100, mc_at_rank_250, mc_at_rank_500) in Rs.Cr.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    all_caps: List[float] = []
    page = 1

    while len(all_caps) < 500 and page <= max_pages:
        url = f"{SCREENER_MC_SCREEN_BASE}?order=desc&page={page}"
        try:
            r = session.get(url, timeout=30)
            if r.status_code != 200:
                break
            chunk = _parse_mc_screen_page_market_caps(r.text)
            if not chunk:
                break
            all_caps.extend(chunk)
            if len(chunk) < 25:
                break
        except requests.RequestException:
            break
        page += 1
        time.sleep(delay_sec)

    if len(all_caps) < 500:
        return None

    # 1-based rank -> 0-based index
    return (all_caps[99], all_caps[249], all_caps[499])


def classify_market_cap_tier(
    mc_cr: Optional[float],
    t100: Optional[float],
    t250: Optional[float],
    t500: Optional[float],
) -> Optional[str]:
    """Returns Large / Mid / Small / Micro for Stock.market_cap storage (no ' Cap' suffix)."""
    if mc_cr is None or t100 is None or t250 is None or t500 is None:
        return None
    if mc_cr >= t100:
        return "Large"
    if mc_cr >= t250:
        return "Mid"
    if mc_cr >= t500:
        return "Small"
    return "Micro"
