"""
Portfolio rebalancing recommendation utilities.

Implements an 8-constraint model with:
1) legacy reduce/add/sector/market-cap analysis blocks
2) unified constraint diagnostics matrix
3) actionable + blocked recommendations sorted by impact % desc
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


ALLOCATION_BUFFER_PCT = 0.0

SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
HARD_BLOCK_DOMAINS = {
    "market_cap_stock_count",
    "market_cap_portfolio_pct",
    "overall_stock_count",
    "parent_sector_stock_count",
    "parent_sector_allocation_pct",
    "child_sector_stock_count",
    "child_sector_allocation_pct",
}


def normalize_market_cap(market_cap: Optional[str]) -> str:
    if not market_cap:
        return "Unknown"
    value = str(market_cap).strip()
    if value == "Unknown":
        return "Unknown"
    return value if value.endswith(" Cap") else f"{value} Cap"


@dataclass
class ThresholdConfig:
    per_stock_pct: Dict[str, float]
    per_stock_display_pct: Dict[str, float]
    stock_count_limits: Dict[str, int]
    portfolio_pct_limits: Dict[str, float]
    max_stocks_per_sector: int
    max_stocks_per_parent_sector: int
    max_parent_sector_pct: float
    max_child_sector_pct: float
    max_total_stocks: int


def build_threshold_config(settings) -> ThresholdConfig:
    per_stock = {
        "Large Cap": float(getattr(settings, "max_large_cap_pct", 5.0) if settings else 5.0),
        "Mid Cap": float(getattr(settings, "max_mid_cap_pct", 3.0) if settings else 3.0),
        "Small Cap": float(getattr(settings, "max_small_cap_pct", 2.5) if settings else 2.5),
        "Micro Cap": float(getattr(settings, "max_micro_cap_pct", 2.0) if settings else 2.0),
    }
    display = {k: v + ALLOCATION_BUFFER_PCT for k, v in per_stock.items()}
    stock_count_limits = {
        "Large Cap": int(getattr(settings, "max_large_cap_stocks", 15) if settings else 15),
        "Mid Cap": int(getattr(settings, "max_mid_cap_stocks", 8) if settings else 8),
        "Small Cap": int(getattr(settings, "max_small_cap_stocks", 7) if settings else 7),
        "Micro Cap": int(getattr(settings, "max_micro_cap_stocks", 3) if settings else 3),
    }
    portfolio_pct_limits = {
        "Large Cap": float(getattr(settings, "max_large_cap_portfolio_pct", 50.0) if settings else 50.0),
        "Mid Cap": float(getattr(settings, "max_mid_cap_portfolio_pct", 30.0) if settings else 30.0),
        "Small Cap": float(getattr(settings, "max_small_cap_portfolio_pct", 25.0) if settings else 25.0),
        "Micro Cap": float(getattr(settings, "max_micro_cap_portfolio_pct", 10.0) if settings else 10.0),
    }
    return ThresholdConfig(
        per_stock_pct=per_stock,
        per_stock_display_pct=display,
        stock_count_limits=stock_count_limits,
        portfolio_pct_limits=portfolio_pct_limits,
        max_stocks_per_sector=int(getattr(settings, "max_stocks_per_sector", 2) if settings else 2),
        max_stocks_per_parent_sector=int(getattr(settings, "max_stocks_per_parent_sector", 4) if settings else 4),
        max_parent_sector_pct=float(getattr(settings, "max_parent_sector_pct", 15.0) if settings else 15.0),
        max_child_sector_pct=float(getattr(settings, "max_child_sector_pct", 8.0) if settings else 8.0),
        max_total_stocks=int(getattr(settings, "max_total_stocks", 30) if settings else 30),
    )


def _safe_total(target_total: float, holdings: List[dict]) -> float:
    if target_total and target_total > 0:
        return float(target_total)
    running = 0.0
    for holding in holdings:
        current_value = float(holding.get("current_value", 0) or 0)
        if current_value == 0 and holding.get("quantity") and holding.get("current_price"):
            current_value = float(holding["quantity"]) * float(holding["current_price"])
        running += current_value
    return running


def _build_market_cap_groups(holdings: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for holding in holdings:
        cap = normalize_market_cap(holding.get("market_cap"))
        if cap not in out:
            out[cap] = {"invested_amount": 0.0, "stocks": []}
        invested = float(holding.get("invested_amount", 0) or 0)
        out[cap]["invested_amount"] += invested
        out[cap]["stocks"].append(holding.get("symbol", ""))
    return out


def _group_holdings_by_key(holdings: List[dict], key_name: str) -> Dict[str, dict]:
    grouped: Dict[str, dict] = {}
    for holding in holdings:
        key = (holding.get(key_name) or "Other").strip() or "Other"
        if key not in grouped:
            grouped[key] = {"invested_amount": 0.0, "stocks": []}
        grouped[key]["invested_amount"] += float(holding.get("invested_amount", 0) or 0)
        grouped[key]["stocks"].append(holding.get("symbol", ""))
    return grouped


def identify_stocks_to_reduce(
    holdings,
    total_current_value,
    max_large_cap_pct=5.0,
    max_mid_cap_pct=3.0,
    max_small_cap_pct=2.5,
    max_micro_cap_pct=2.0,
):
    if not holdings or total_current_value == 0:
        return []

    display_limits = {
        "Large Cap": max_large_cap_pct + ALLOCATION_BUFFER_PCT,
        "Mid Cap": max_mid_cap_pct + ALLOCATION_BUFFER_PCT,
        "Small Cap": max_small_cap_pct + ALLOCATION_BUFFER_PCT,
        "Micro Cap": max_micro_cap_pct + ALLOCATION_BUFFER_PCT,
    }

    out = []
    for holding in holdings:
        market_cap = normalize_market_cap(holding.get("market_cap"))
        max_allowed = display_limits.get(market_cap)
        if max_allowed is None:
            continue

        invested_amount = float(holding.get("invested_amount", 0) or 0)
        pct = (invested_amount / total_current_value) * 100 if total_current_value else 0
        if pct <= max_allowed:
            continue

        excess_pct = pct - max_allowed
        reduce_amount = (excess_pct / 100) * total_current_value
        out.append({
            "symbol": holding["symbol"],
            "name": holding.get("name", ""),
            "market_cap": market_cap,
            "current_pct": round(pct, 2),
            "target_pct": round(max_allowed, 2),
            "excess_pct": round(excess_pct, 2),
            "reduce_amount": round(reduce_amount, 2),
            "current_value": float(holding.get("current_value", 0) or 0),
            "current_invested": invested_amount,
            "reason": f"Over-allocated by {excess_pct:.1f}%",
        })
    out.sort(key=lambda item: item["reduce_amount"], reverse=True)
    return out


def identify_stocks_to_add(
    holdings,
    stocks,
    total_current_value,
    max_large_cap_pct=5.0,
    max_mid_cap_pct=3.0,
    max_small_cap_pct=2.5,
    max_micro_cap_pct=2.0,
):
    if not holdings or total_current_value == 0:
        return []

    thresholds = {
        "Large Cap": max_large_cap_pct,
        "Mid Cap": max_mid_cap_pct,
        "Small Cap": max_small_cap_pct,
        "Micro Cap": max_micro_cap_pct,
    }
    stock_map = {}
    for stock in stocks or []:
        normalized = stock.symbol.replace(".NS", "").replace(".BO", "").upper()
        stock_map[normalized] = stock

    out = []
    for holding in holdings:
        cap = normalize_market_cap(holding.get("market_cap"))
        threshold = thresholds.get(cap)
        if threshold is None:
            continue
        invested_amount = float(holding.get("invested_amount", 0) or 0)
        pct = (invested_amount / total_current_value) * 100 if total_current_value else 0
        if pct >= threshold:
            continue

        deficit_pct = threshold - pct
        add_amount = (deficit_pct / 100) * total_current_value
        symbol = holding.get("symbol")
        normalized = symbol.replace(".NS", "").replace(".BO", "").upper()
        stock_obj = stock_map.get(normalized)

        in_buy_zone = False
        near_buy_zone = False
        current_price = holding.get("current_price")
        if stock_obj and current_price and stock_obj.buy_zone_price:
            try:
                from utils.zones import parse_zone

                buy_min, buy_max = parse_zone(stock_obj.buy_zone_price)
                if buy_max and current_price <= buy_max:
                    in_buy_zone = True
                elif buy_max and current_price <= buy_max * 1.03:
                    near_buy_zone = True
                elif buy_min and buy_min * 0.97 <= current_price < buy_min:
                    near_buy_zone = True
            except Exception:
                pass

        out.append({
            "symbol": symbol,
            "name": holding.get("name", ""),
            "market_cap": cap,
            "sector": (holding.get("sector") or "Other").strip() or "Other",
            "parent_sector": (holding.get("parent_sector") or "Other").strip() or "Other",
            "current_pct": round(pct, 2),
            "target_pct": round(threshold, 2),
            "deficit_pct": round(deficit_pct, 2),
            "add_amount": round(add_amount, 2),
            "current_invested": invested_amount,
            "in_buy_zone": in_buy_zone,
            "near_buy_zone": near_buy_zone,
            "current_price": current_price,
            "reason": f"Under-allocated by {deficit_pct:.1f}%",
        })
    out.sort(key=lambda item: (not item["in_buy_zone"], -item["add_amount"]))
    return out


def get_sector_recommendations(holdings, total_current_value, max_stocks_per_sector=2, key_name="sector", label="sector"):
    if not holdings:
        return []

    total_for_pct = _safe_total(total_current_value, holdings)
    if total_for_pct <= 0:
        return []

    grouped = _group_holdings_by_key(holdings, key_name)
    out = []
    for key, data in grouped.items():
        num_stocks = len(data["stocks"])
        pct = (data["invested_amount"] / total_for_pct) * 100 if total_for_pct else 0
        if num_stocks > max_stocks_per_sector:
            status = "overweight"
            recommendation = f"{num_stocks} stocks in this {label} (max {max_stocks_per_sector})"
        elif num_stocks == max_stocks_per_sector:
            status = "moderate_overweight"
            recommendation = f"At limit for this {label}; avoid adding new names"
        else:
            status = "balanced"
            recommendation = "Within stock-count limit"

        out.append({
            key_name: key,
            "current_value": round(data["invested_amount"], 2),
            "percentage": round(pct, 2),
            "num_stocks": num_stocks,
            "stocks": data["stocks"],
            "status": status,
            "recommendation": recommendation,
            "max_stocks_allowed": max_stocks_per_sector,
        })

    status_priority = {"overweight": 0, "moderate_overweight": 1, "balanced": 2}
    out.sort(key=lambda item: (status_priority.get(item["status"], 99), -item["percentage"]))
    return out


def get_market_cap_recommendations(holdings, total_current_value, settings=None):
    if not holdings:
        return []
    cfg = build_threshold_config(settings)
    total_for_pct = _safe_total(total_current_value, holdings)
    if total_for_pct <= 0:
        return []

    grouped = _build_market_cap_groups(holdings)
    out = []
    for cap, data in grouped.items():
        pct = (data["invested_amount"] / total_for_pct) * 100 if total_for_pct else 0
        num_stocks = len(data["stocks"])
        stock_count_limit = cfg.stock_count_limits.get(cap)
        portfolio_pct_limit = cfg.portfolio_pct_limits.get(cap)
        per_stock_limit = cfg.per_stock_pct.get(cap)

        status = "balanced"
        recommendation_parts = []
        if stock_count_limit and num_stocks > stock_count_limit:
            status = "overweight"
            recommendation_parts.append(f"Stock count {num_stocks}/{stock_count_limit}")
        if portfolio_pct_limit and pct > portfolio_pct_limit:
            status = "overweight"
            recommendation_parts.append(f"Bucket {pct:.1f}%/{portfolio_pct_limit}%")
        if not recommendation_parts:
            recommendation = "Within limits"
        else:
            recommendation = " | ".join(recommendation_parts)

        out.append({
            "market_cap": cap,
            "current_value": round(data["invested_amount"], 2),
            "percentage": round(pct, 2),
            "num_stocks": num_stocks,
            "stocks": data["stocks"],
            "target_range": f"Max {per_stock_limit}% per stock" if per_stock_limit is not None else "N/A",
            "per_stock_limit": per_stock_limit,
            "stock_count_limit": stock_count_limit,
            "portfolio_pct_limit": portfolio_pct_limit,
            "status": status,
            "recommendation": recommendation,
        })
    out.sort(key=lambda item: (item["status"] != "overweight", -item["percentage"]))
    return out


def _severity_by_impact(impact_pct: float) -> str:
    if impact_pct >= 10:
        return "critical"
    if impact_pct >= 5:
        return "high"
    if impact_pct >= 2:
        return "medium"
    return "low"


def _build_constraint_matrix(holdings: List[dict], total_for_pct: float, cfg: ThresholdConfig, market_caps: List[dict]):
    diagnostics = []
    blocker_index = {"global": [], "market_cap": {}, "parent_sector": {}, "child_sector": {}}

    def register(diagnostic):
        diagnostics.append(diagnostic)
        if diagnostic["block_add"] and diagnostic["status"] == "breach":
            if diagnostic["scope"] == "portfolio":
                blocker_index["global"].append(diagnostic)
            elif diagnostic["scope"] == "bucket":
                key = diagnostic.get("scope_key")
                blocker_index["market_cap"].setdefault(key, []).append(diagnostic)
            elif diagnostic["scope"] == "parent_sector":
                key = diagnostic.get("scope_key")
                blocker_index["parent_sector"].setdefault(key, []).append(diagnostic)
            elif diagnostic["scope"] == "child_sector":
                key = diagnostic.get("scope_key")
                blocker_index["child_sector"].setdefault(key, []).append(diagnostic)

    for row in market_caps:
        cap = row["market_cap"]
        if cap == "Unknown":
            continue
        stock_count_limit = row.get("stock_count_limit")
        if stock_count_limit and row["num_stocks"] > stock_count_limit:
            excess = row["num_stocks"] - stock_count_limit
            impact_pct = (excess / row["num_stocks"]) * 100 if row["num_stocks"] else 0
            register({
                "id": f"market-cap-count-{cap.lower().replace(' ', '-')}",
                "domain": "market_cap_stock_count",
                "status": "breach",
                "impact_pct": round(impact_pct, 2),
                "impact_amount_inr": round(row["current_value"], 2),
                "block_add": True,
                "scope": "bucket",
                "scope_key": cap,
                "related_symbols": row.get("stocks", []),
                "message": f"{cap} count {row['num_stocks']} exceeds limit {stock_count_limit}",
            })
        else:
            register({
                "id": f"market-cap-count-{cap.lower().replace(' ', '-')}",
                "domain": "market_cap_stock_count",
                "status": "ok",
                "impact_pct": 0.0,
                "impact_amount_inr": 0.0,
                "block_add": True,
                "scope": "bucket",
                "scope_key": cap,
                "related_symbols": row.get("stocks", []),
                "message": f"{cap} count within limit",
            })

        portfolio_limit = row.get("portfolio_pct_limit")
        if portfolio_limit and row["percentage"] > portfolio_limit:
            impact_pct = row["percentage"] - portfolio_limit
            register({
                "id": f"market-cap-pct-{cap.lower().replace(' ', '-')}",
                "domain": "market_cap_portfolio_pct",
                "status": "breach",
                "impact_pct": round(impact_pct, 2),
                "impact_amount_inr": round(total_for_pct * impact_pct / 100, 2),
                "block_add": True,
                "scope": "bucket",
                "scope_key": cap,
                "related_symbols": row.get("stocks", []),
                "message": f"{cap} allocation {row['percentage']:.2f}% exceeds limit {portfolio_limit:.2f}%",
            })
        else:
            register({
                "id": f"market-cap-pct-{cap.lower().replace(' ', '-')}",
                "domain": "market_cap_portfolio_pct",
                "status": "ok",
                "impact_pct": 0.0,
                "impact_amount_inr": 0.0,
                "block_add": True,
                "scope": "bucket",
                "scope_key": cap,
                "related_symbols": row.get("stocks", []),
                "message": f"{cap} allocation within limit",
            })

    total_stocks = len(holdings)
    if total_stocks > cfg.max_total_stocks:
        excess = total_stocks - cfg.max_total_stocks
        impact_pct = (excess / total_stocks) * 100 if total_stocks else 0
        register({
            "id": "overall-stock-count",
            "domain": "overall_stock_count",
            "status": "breach",
            "impact_pct": round(impact_pct, 2),
            "impact_amount_inr": round(total_for_pct * impact_pct / 100, 2),
            "block_add": True,
            "scope": "portfolio",
            "scope_key": "portfolio",
            "related_symbols": [h.get("symbol", "") for h in holdings],
            "message": f"Total holdings {total_stocks} exceed max {cfg.max_total_stocks}",
        })
    else:
        register({
            "id": "overall-stock-count",
            "domain": "overall_stock_count",
            "status": "ok",
            "impact_pct": 0.0,
            "impact_amount_inr": 0.0,
            "block_add": True,
            "scope": "portfolio",
            "scope_key": "portfolio",
            "related_symbols": [h.get("symbol", "") for h in holdings],
            "message": "Overall stock count within limit",
        })

    parent_groups = _group_holdings_by_key(holdings, "parent_sector")
    child_groups = _group_holdings_by_key(holdings, "sector")

    for parent, data in parent_groups.items():
        parent_count = len(data["stocks"])
        parent_pct = (data["invested_amount"] / total_for_pct) * 100 if total_for_pct else 0
        if parent_count > cfg.max_stocks_per_parent_sector:
            register({
                "id": f"parent-count-{parent.lower().replace(' ', '-')}",
                "domain": "parent_sector_stock_count",
                "status": "breach",
                "impact_pct": round((parent_count - cfg.max_stocks_per_parent_sector) * 100 / parent_count, 2) if parent_count else 0.0,
                "impact_amount_inr": round(data["invested_amount"], 2),
                "block_add": True,
                "scope": "parent_sector",
                "scope_key": parent,
                "related_symbols": data["stocks"],
                "message": f"Parent sector {parent} count {parent_count} exceeds {cfg.max_stocks_per_parent_sector}",
            })
        if parent_pct > cfg.max_parent_sector_pct:
            impact_pct = parent_pct - cfg.max_parent_sector_pct
            register({
                "id": f"parent-pct-{parent.lower().replace(' ', '-')}",
                "domain": "parent_sector_allocation_pct",
                "status": "breach",
                "impact_pct": round(impact_pct, 2),
                "impact_amount_inr": round(total_for_pct * impact_pct / 100, 2),
                "block_add": True,
                "scope": "parent_sector",
                "scope_key": parent,
                "related_symbols": data["stocks"],
                "message": f"Parent sector {parent} allocation {parent_pct:.2f}% exceeds {cfg.max_parent_sector_pct:.2f}%",
            })

    for child, data in child_groups.items():
        child_count = len(data["stocks"])
        child_pct = (data["invested_amount"] / total_for_pct) * 100 if total_for_pct else 0
        if child_count > cfg.max_stocks_per_sector:
            register({
                "id": f"child-count-{child.lower().replace(' ', '-')}",
                "domain": "child_sector_stock_count",
                "status": "breach",
                "impact_pct": round((child_count - cfg.max_stocks_per_sector) * 100 / child_count, 2) if child_count else 0.0,
                "impact_amount_inr": round(data["invested_amount"], 2),
                "block_add": True,
                "scope": "child_sector",
                "scope_key": child,
                "related_symbols": data["stocks"],
                "message": f"Child sector {child} count {child_count} exceeds {cfg.max_stocks_per_sector}",
            })
        if child_pct > cfg.max_child_sector_pct:
            impact_pct = child_pct - cfg.max_child_sector_pct
            register({
                "id": f"child-pct-{child.lower().replace(' ', '-')}",
                "domain": "child_sector_allocation_pct",
                "status": "breach",
                "impact_pct": round(impact_pct, 2),
                "impact_amount_inr": round(total_for_pct * impact_pct / 100, 2),
                "block_add": True,
                "scope": "child_sector",
                "scope_key": child,
                "related_symbols": data["stocks"],
                "message": f"Child sector {child} allocation {child_pct:.2f}% exceeds {cfg.max_child_sector_pct:.2f}%",
            })

    diagnostics.sort(
        key=lambda item: (
            item["status"] != "breach",
            -float(item.get("impact_pct", 0) or 0),
            -float(item.get("impact_amount_inr", 0) or 0),
        )
    )
    return diagnostics, blocker_index


def _build_stock_lookup(stocks):
    out = {}
    for stock in stocks or []:
        normalized = stock.symbol.replace(".NS", "").replace(".BO", "").upper()
        out[normalized] = stock
    return out


def _trim_signal(stock_obj, row):
    in_sell_zone = False
    near_sell_zone = False
    if stock_obj and stock_obj.sell_zone_price and stock_obj.current_price:
        try:
            from utils.zones import parse_zone

            sell_min, _ = parse_zone(stock_obj.sell_zone_price)
            if sell_min and stock_obj.current_price >= sell_min:
                in_sell_zone = True
            elif sell_min and stock_obj.current_price >= sell_min * 0.97:
                near_sell_zone = True
        except Exception:
            pass
    in_profit = float(row.get("current_value", 0) or 0) > float(row.get("current_invested", 0) or 0)
    signal_score = (2 if in_sell_zone else 0) + (1 if near_sell_zone else 0) + (1 if in_profit else 0)
    return in_sell_zone, near_sell_zone, in_profit, signal_score


def _add_signal(row):
    if row.get("in_buy_zone"):
        return "In Buy Zone", 2
    if row.get("near_buy_zone"):
        return "Near Buy Zone", 1
    return "No Buy Signal", 0


def _rank_recommendations(items: List[dict]) -> List[dict]:
    items.sort(
        key=lambda item: (
            -float(item.get("impact_pct", 0) or 0),
            -SEVERITY_RANK.get(item.get("severity", "info"), 0),
            -int(item.get("signal_score", 0) or 0),
            -float(item.get("impact_amount_inr", 0) or 0),
        )
    )
    for index, item in enumerate(items, start=1):
        item["priority_rank"] = index
        item["id"] = item.get("id") or f"{item.get('action_type', 'action').lower()}-{index}"
    return items


def _build_recommendation_sets(
    stocks,
    stocks_to_reduce: List[dict],
    stocks_to_add: List[dict],
    diagnostics: List[dict],
    blockers: dict,
):
    stock_lookup = _build_stock_lookup(stocks)
    actionable = []
    blocked = []

    for row in stocks_to_reduce:
        normalized = row["symbol"].replace(".NS", "").replace(".BO", "").upper()
        stock_obj = stock_lookup.get(normalized)
        in_sell_zone, near_sell_zone, in_profit, signal_score = _trim_signal(stock_obj, row)
        actionable.append({
            "action_type": "OVER_ALLOCATED_STOCK",
            "proposed_trade": "trim",
            "severity": _severity_by_impact(float(row.get("excess_pct", 0) or 0)),
            "signal_score": signal_score,
            "symbol": row["symbol"],
            "title": f"Trim {row['symbol']} exposure",
            "impact_amount_inr": row["reduce_amount"],
            "impact_pct": row["excess_pct"],
            "why": row["reason"],
            "how_to_apply": "Trim in tranches, prioritizing current sell/profit signals.",
            "related_symbols": [row["symbol"]],
            "details": {
                "market_cap": row.get("market_cap"),
                "current_pct": row.get("current_pct"),
                "target_pct": row.get("target_pct"),
                "in_sell_zone": in_sell_zone,
                "near_sell_zone": near_sell_zone,
                "in_profit": in_profit,
            },
        })

    for row in stocks_to_add:
        signal_label, signal_score = _add_signal(row)
        recommendation = {
            "action_type": "UNDER_ALLOCATED_STOCK",
            "proposed_trade": "add",
            "severity": "medium" if signal_score > 0 else "low",
            "signal_score": signal_score,
            "symbol": row["symbol"],
            "title": f"Add allocation to {row['symbol']}",
            "impact_amount_inr": row["add_amount"],
            "impact_pct": row["deficit_pct"],
            "why": row["reason"],
            "how_to_apply": "Accumulate in small tranches while respecting all active constraints.",
            "related_symbols": [row["symbol"]],
            "details": {
                "market_cap": row.get("market_cap"),
                "sector": row.get("sector"),
                "parent_sector": row.get("parent_sector"),
                "current_pct": row.get("current_pct"),
                "target_pct": row.get("target_pct"),
                "in_buy_zone": row.get("in_buy_zone", False),
                "near_buy_zone": row.get("near_buy_zone", False),
                "signal": signal_label,
            },
        }
        relevant_blockers = []
        relevant_blockers.extend(blockers.get("global", []))
        relevant_blockers.extend(blockers.get("market_cap", {}).get(row.get("market_cap"), []))
        relevant_blockers.extend(blockers.get("parent_sector", {}).get(row.get("parent_sector"), []))
        relevant_blockers.extend(blockers.get("child_sector", {}).get(row.get("sector"), []))
        if relevant_blockers:
            blocked.append({
                **recommendation,
                "blockers": [b["message"] for b in relevant_blockers],
                "blocker_domains": sorted({b["domain"] for b in relevant_blockers}),
                "how_to_apply": "Resolve listed breaches first, then revisit this add action.",
            })
        else:
            actionable.append(recommendation)

    for diagnostic in diagnostics:
        if diagnostic.get("status") != "breach":
            continue
        if diagnostic.get("domain") not in HARD_BLOCK_DOMAINS:
            continue
        actionable.append({
            "action_type": diagnostic["domain"].upper(),
            "proposed_trade": "consolidate",
            "severity": _severity_by_impact(float(diagnostic.get("impact_pct", 0) or 0)),
            "signal_score": 0,
            "symbol": None,
            "title": f"Resolve {diagnostic['domain'].replace('_', ' ')} breach",
            "impact_amount_inr": diagnostic.get("impact_amount_inr", 0),
            "impact_pct": diagnostic.get("impact_pct", 0),
            "why": diagnostic.get("message"),
            "how_to_apply": "Consolidate/trim holdings in this scope until limits are met.",
            "related_symbols": diagnostic.get("related_symbols", []),
            "details": {
                "scope": diagnostic.get("scope"),
                "scope_key": diagnostic.get("scope_key"),
                "block_add": diagnostic.get("block_add", False),
            },
        })

    if not actionable and not blocked:
        actionable.append({
            "action_type": "HOLD",
            "proposed_trade": "hold",
            "severity": "info",
            "signal_score": 0,
            "symbol": None,
            "title": "Hold current allocation",
            "impact_amount_inr": 0,
            "impact_pct": 0,
            "why": "No active breaches across configured constraints.",
            "how_to_apply": "Continue monitoring and add only in buy-zone opportunities.",
            "related_symbols": [],
            "details": {},
        })

    _rank_recommendations(actionable)
    _rank_recommendations(blocked)
    return actionable, blocked


def get_rebalancing_suggestions(holdings, stocks, total_current_value, settings=None):
    cfg = build_threshold_config(settings)
    total_for_pct = _safe_total(total_current_value, holdings)

    stocks_to_reduce = identify_stocks_to_reduce(
        holdings,
        total_for_pct,
        cfg.per_stock_pct["Large Cap"],
        cfg.per_stock_pct["Mid Cap"],
        cfg.per_stock_pct["Small Cap"],
        cfg.per_stock_pct["Micro Cap"],
    )
    stocks_to_add = identify_stocks_to_add(
        holdings,
        stocks,
        total_for_pct,
        cfg.per_stock_pct["Large Cap"],
        cfg.per_stock_pct["Mid Cap"],
        cfg.per_stock_pct["Small Cap"],
        cfg.per_stock_pct["Micro Cap"],
    )
    sector_rebalancing = get_sector_recommendations(
        holdings,
        total_for_pct,
        cfg.max_stocks_per_sector,
        key_name="sector",
        label="child sector",
    )
    parent_sector_rebalancing = get_sector_recommendations(
        holdings,
        total_for_pct,
        cfg.max_stocks_per_parent_sector,
        key_name="parent_sector",
        label="parent sector",
    )
    market_cap_rebalancing = get_market_cap_recommendations(holdings, total_for_pct, settings)
    diagnostics, blockers = _build_constraint_matrix(holdings, total_for_pct, cfg, market_cap_rebalancing)
    actionable, blocked = _build_recommendation_sets(
        stocks,
        stocks_to_reduce,
        stocks_to_add,
        diagnostics,
        blockers,
    )

    critical_count = sum(1 for item in actionable if item.get("severity") == "critical")
    high_count = sum(1 for item in actionable if item.get("severity") == "high")
    medium_count = sum(1 for item in actionable if item.get("severity") == "medium")
    blocked_count = len(blocked)
    capital_at_risk = round(
        sum(float(item.get("impact_amount_inr", 0) or 0) for item in actionable if item.get("severity") in {"critical", "high"}),
        2,
    )

    return {
        "stocks_to_reduce": stocks_to_reduce,
        "stocks_to_add": stocks_to_add,
        "sector_rebalancing": sector_rebalancing,
        "parent_sector_rebalancing": parent_sector_rebalancing,
        "parent_sector_analysis": parent_sector_rebalancing,
        "parent_sector_warnings": [
            {
                "parent_sector": row.get("parent_sector"),
                "stock_count": row.get("num_stocks", 0),
                "stocks": row.get("stocks", []),
                "recommendation": row.get("recommendation"),
            }
            for row in parent_sector_rebalancing
            if row.get("num_stocks", 0) > cfg.max_stocks_per_parent_sector
        ],
        "market_cap_rebalancing": market_cap_rebalancing,
        "total_stocks": len(holdings),
        "max_total_stocks": cfg.max_total_stocks,
        "total_stocks_status": "overweight" if len(holdings) > cfg.max_total_stocks else "balanced",
        "summary_metrics": {
            "total_actions": len(actionable) + blocked_count,
            "actionable_actions": len(actionable),
            "blocked_actions": blocked_count,
            "critical_actions": critical_count,
            "high_actions": high_count,
            "medium_actions": medium_count,
            "capital_at_risk_inr": capital_at_risk,
            "total_for_pct": round(total_for_pct, 2),
        },
        "actionable_recommendations": actionable,
        "blocked_recommendations": blocked,
        "constraint_diagnostics": diagnostics,
        "thresholds_used": {
            "per_stock_pct": cfg.per_stock_pct,
            "per_stock_display_pct": cfg.per_stock_display_pct,
            "stock_count_limits": cfg.stock_count_limits,
            "portfolio_pct_limits": cfg.portfolio_pct_limits,
            "max_stocks_per_sector": cfg.max_stocks_per_sector,
            "max_stocks_per_parent_sector": cfg.max_stocks_per_parent_sector,
            "max_parent_sector_pct": cfg.max_parent_sector_pct,
            "max_child_sector_pct": cfg.max_child_sector_pct,
            "max_total_stocks": cfg.max_total_stocks,
        },
    }

