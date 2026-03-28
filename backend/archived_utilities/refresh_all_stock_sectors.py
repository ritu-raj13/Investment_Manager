"""
ARCHIVED one-time utility: backfill `stocks.sector` from Screener peer breadcrumb
for all tracked .NS / .BO symbols.

Run once after upgrading; new stocks get sector from add/fetch-details automatically.
Delete this file when no longer needed.

Usage (from backend/, venv active, Flask stopped recommended for SQLite):
    python -u archived_utilities/refresh_all_stock_sectors.py

(`-u` forces unbuffered stdout; the script also uses flush=True on each line.)
"""
from __future__ import annotations

import os
import sys
import time

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)
os.chdir(BACKEND_ROOT)

from app import app, db, Stock  # noqa: E402
from services.screener_parser import fetch_company_supplement  # noqa: E402


def _log(msg: str) -> None:
    print(msg, flush=True)


def refresh_all_sectors_from_screener(delay_sec: float = 0.55) -> dict:
    """
    Re-fetch Peer Comparison sector (second-to-last breadcrumb label) per Indian symbol.
    Returns counts for logging.
    """
    stocks = Stock.query.all()
    indian = [s for s in stocks if (s.symbol or "").endswith((".NS", ".BO"))]
    total_in = len(indian)
    _log(f"Found {len(stocks)} rows, {total_in} Indian symbols to fetch (delay {delay_sec}s between requests).")

    updated = 0
    failed = 0
    skipped = len(stocks) - total_in
    errors_sample: list[str] = []

    for i, stock in enumerate(indian, start=1):
        sym = stock.symbol or ""
        _log(f"[{i}/{total_in}] {sym} … (sleep + Screener)")
        try:
            time.sleep(delay_sec)
            sup = fetch_company_supplement(sym)
            sec = sup.get("sector") if sup else None
            if sec:
                stock.sector = sec
                updated += 1
                _log(f"    -> OK: {sec}")
            else:
                failed += 1
                _log(f"    -> FAIL: no sector parsed")
                if len(errors_sample) < 12:
                    errors_sample.append(f"{sym}: no sector parsed")
        except Exception as e:
            failed += 1
            _log(f"    -> FAIL: {e}")
            if len(errors_sample) < 12:
                errors_sample.append(f"{sym}: {e}")

    db.session.commit()
    return {
        "updated": updated,
        "failed": failed,
        "skipped": skipped,
        "errors_sample": errors_sample,
    }


def main():
    _log("=" * 60)
    _log("ARCHIVED UTIL: Refresh all stock sectors from Screener")
    _log("Stop the Flask app first if you use SQLite to avoid database locks.")
    _log("=" * 60)
    with app.app_context():
        out = refresh_all_sectors_from_screener()
    _log("")
    _log(
        f"Done: {out['updated']} updated, {out['failed']} failed, "
        f"{out['skipped']} skipped (non-Indian)."
    )
    if out["errors_sample"]:
        _log("Sample errors:")
        for line in out["errors_sample"]:
            _log(f"  - {line}")
    _log("=" * 60)


if __name__ == "__main__":
    main()
