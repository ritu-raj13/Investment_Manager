"""
Portfolio rebalancing recommendation utilities.

This module normalizes settings thresholds and produces:
1) Legacy-style reduce/add/sector/market-cap analysis blocks
2) A prioritized actionable recommendation queue for end users
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


ALLOCATION_BUFFER_PCT = 0.5


def normalize_market_cap(market_cap: Optional[str]) -> str:
    if not market_cap:
        return "Unknown"
    v = str(market_cap).strip()
    if v == "Unknown":
        return "Unknown"
    return v if v.endswith(" Cap") else f"{v} Cap"


@dataclass
class ThresholdConfig:
    per_stock_pct: Dict[str, float]
    per_stock_display_pct: Dict[str, float]
    stock_count_limits: Dict[str, int]
    portfolio_pct_limits: Dict[str, float]
    max_stocks_per_sector: int
    max_total_stocks: int


def build_threshold_config(settings) -> ThresholdConfig:
    # Defaults align with PortfolioSettings defaults.
    large = float(getattr(settings, "max_large_cap_pct", 5.0) if settings else 5.0)
    mid = float(getattr(settings, "max_mid_cap_pct", 3.0) if settings else 3.0)
    small = float(getattr(settings, "max_small_cap_pct", 2.5) if settings else 2.5)
    micro = float(getattr(settings, "max_micro_cap_pct", 2.0) if settings else 2.0)

    per_stock = {
        "Large Cap": large,
        "Mid Cap": mid,
        "Small Cap": small,
        "Micro Cap": micro,
    }
    display = {k: v + ALLOCATION_BUFFER_PCT for k, v in per_stock.items()}

    count_limits = {
        "Large Cap": int(getattr(settings, "max_large_cap_stocks", 15) if settings else 15),
        "Mid Cap": int(getattr(settings, "max_mid_cap_stocks", 8) if settings else 8),
        "Small Cap": int(getattr(settings, "max_small_cap_stocks", 7) if settings else 7),
        "Micro Cap": int(getattr(settings, "max_micro_cap_stocks", 3) if settings else 3),
    }

    portfolio_limits = {
        "Large Cap": float(getattr(settings, "max_large_cap_portfolio_pct", 50.0) if settings else 50.0),
        "Mid Cap": float(getattr(settings, "max_mid_cap_portfolio_pct", 30.0) if settings else 30.0),
        "Small Cap": float(getattr(settings, "max_small_cap_portfolio_pct", 25.0) if settings else 25.0),
        "Micro Cap": float(getattr(settings, "max_micro_cap_portfolio_pct", 10.0) if settings else 10.0),
    }

    return ThresholdConfig(
        per_stock_pct=per_stock,
        per_stock_display_pct=display,
        stock_count_limits=count_limits,
        portfolio_pct_limits=portfolio_limits,
        max_stocks_per_sector=int(getattr(settings, "max_stocks_per_sector", 2) if settings else 2),
        max_total_stocks=int(getattr(settings, "max_total_stocks", 30) if settings else 30),
    )


def _safe_total(target_total: float, holdings: List[dict]) -> float:
    if target_total and target_total > 0:
        return float(target_total)
    running = 0.0
    for h in holdings:
        current_value = h.get("current_value", 0) or 0
        if current_value == 0 and h.get("quantity") and h.get("current_price"):
            current_value = h["quantity"] * h["current_price"]
        running += float(current_value)
    return running


def _build_market_cap_groups(holdings: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for h in holdings:
        cap = normalize_market_cap(h.get("market_cap"))
        if cap not in out:
            out[cap] = {"invested_amount": 0.0, "stocks": []}
        invested = float(h.get("invested_amount", 0) or 0)
        out[cap]["invested_amount"] += invested
        out[cap]["stocks"].append(h.get("symbol", ""))
    return out


def identify_stocks_to_reduce(
    holdings,
    total_current_value,
    max_large_cap_pct=5.0,
    max_mid_cap_pct=3.0,
    max_small_cap_pct=2.5,
    max_micro_cap_pct=2.0,
):
    """
    Identify over-allocated stocks that should be reduced
    
    Args:
        holdings: List of holding dictionaries
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount, for % calculation)
        max_large_cap_pct: Max % for large cap (actual: 5%, display: 5.5%)
        max_mid_cap_pct: Max % for mid cap (actual: 3%, display: 3.5%)
        max_small_cap_pct: Max % for small cap (actual: 2.5%, display: 3%)
        max_micro_cap_pct: Max % for micro cap (actual: 2%, display: 2.5%)
        
    Returns:
        list: Stocks to reduce with details
    """
    if not holdings or total_current_value == 0:
        return []

    display_limits = {
        "Large Cap": max_large_cap_pct + ALLOCATION_BUFFER_PCT,
        "Mid Cap": max_mid_cap_pct + ALLOCATION_BUFFER_PCT,
        "Small Cap": max_small_cap_pct + ALLOCATION_BUFFER_PCT,
        "Micro Cap": max_micro_cap_pct + ALLOCATION_BUFFER_PCT,
    }

    stocks_to_reduce = []

    for holding in holdings:
        market_cap = normalize_market_cap(holding.get("market_cap"))
        green_max = display_limits.get(market_cap)
        if green_max is None:
            continue

        invested_amount = float(holding.get("invested_amount", 0) or 0)
        percentage = (invested_amount / total_current_value) * 100

        if percentage > green_max:
            excess_pct = percentage - green_max
            reduce_amount = (excess_pct / 100) * total_current_value

            stocks_to_reduce.append({
                "symbol": holding["symbol"],
                "name": holding.get("name", ""),
                "market_cap": market_cap,
                "current_pct": round(percentage, 2),
                "target_pct": round(green_max, 2),
                "excess_pct": round(excess_pct, 2),
                "reduce_amount": round(reduce_amount, 2),
                "current_value": float(holding.get("current_value", 0) or 0),
                "current_invested": invested_amount,
                "reason": f"Over-allocated by {excess_pct:.1f}%",
            })

    stocks_to_reduce.sort(key=lambda x: x["reduce_amount"], reverse=True)
    return stocks_to_reduce


def identify_stocks_to_add(
    holdings,
    stocks,
    total_current_value,
    max_large_cap_pct=5.0,
    max_mid_cap_pct=3.0,
    max_small_cap_pct=2.5,
    max_micro_cap_pct=2.0,
):
    """
    Identify under-allocated stocks that could be added
    Prioritizes stocks in buy zones
    
    Args:
        holdings: List of holding dictionaries
        stocks: List of Stock objects from database
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount, for % calculation)
        max_large_cap_pct: Max % for large cap (actual: 5%, display: 5.5%)
        max_mid_cap_pct: Max % for mid cap (actual: 3%, display: 3.5%)
        max_small_cap_pct: Max % for small cap (actual: 2.5%, display: 3%)
        max_micro_cap_pct: Max % for micro cap (actual: 2%, display: 2.5%)
        
    Returns:
        list: Stocks to add with details
    """
    if not holdings or total_current_value == 0:
        return []

    thresholds = {
        "Large Cap": max_large_cap_pct,
        "Mid Cap": max_mid_cap_pct,
        "Small Cap": max_small_cap_pct,
        "Micro Cap": max_micro_cap_pct,
    }

    stocks_map = {}
    for stock in stocks:
        normalized = stock.symbol.replace(".NS", "").replace(".BO", "").upper()
        stocks_map[normalized] = stock

    stocks_to_add = []

    for holding in holdings:
        market_cap = normalize_market_cap(holding.get("market_cap"))
        threshold = thresholds.get(market_cap)
        if threshold is None:
            continue

        invested_amount = float(holding.get("invested_amount", 0) or 0)
        percentage = (invested_amount / total_current_value) * 100

        if percentage < threshold:
            deficit_pct = threshold - percentage
            add_amount = (deficit_pct / 100) * total_current_value

            symbol = holding["symbol"]
            normalized_symbol = symbol.replace(".NS", "").replace(".BO", "").upper()
            stock_obj = stocks_map.get(normalized_symbol)

            in_buy_zone = False
            near_buy_zone = False
            current_price = holding.get("current_price")
            zone_info = ""

            if stock_obj and current_price:
                buy_zone = stock_obj.buy_zone_price
                if buy_zone:
                    try:
                        from utils.zones import parse_zone

                        buy_min, buy_max = parse_zone(buy_zone)
                        if buy_max and current_price <= buy_max:
                            in_buy_zone = True
                            zone_info = " (In Buy Zone)"
                        elif buy_max and current_price <= buy_max * 1.03:
                            near_buy_zone = True
                            zone_info = " (Near Buy Zone)"
                        elif buy_min and current_price >= buy_min * 0.97 and current_price < buy_min:
                            near_buy_zone = True
                            zone_info = " (Near Buy Zone)"
                    except Exception:
                        pass

            reason = f"Under-allocated by {deficit_pct:.1f}%"
            if in_buy_zone or near_buy_zone:
                reason += zone_info

            stocks_to_add.append({
                "symbol": holding["symbol"],
                "name": holding.get("name", ""),
                "market_cap": market_cap,
                "current_pct": round(percentage, 2),
                "target_pct": round(threshold, 2),
                "deficit_pct": round(deficit_pct, 2),
                "add_amount": round(add_amount, 2),
                "current_invested": invested_amount,
                "in_buy_zone": in_buy_zone,
                "near_buy_zone": near_buy_zone,
                "current_price": current_price,
                "reason": reason,
            })

    stocks_to_add.sort(key=lambda x: (not x["in_buy_zone"], -x["add_amount"]))
    return stocks_to_add


def get_sector_recommendations(holdings, total_current_value, max_stocks_per_sector=2):
    """
    Generate sector-level rebalancing recommendations based on stock count per sector
    
    Args:
        holdings: List of holding dictionaries with sector info
        total_current_value: Total portfolio target amount (from settings, for % calculation)
        max_stocks_per_sector: Maximum number of stocks per sector (from settings, default: 2)
        
    Returns:
        list: Sector recommendations with analysis
    """
    if not holdings:
        return []

    total_for_pct = _safe_total(total_current_value, holdings)
    if total_for_pct == 0:
        return []

    sector_data = {}
    for holding in holdings:
        sector = holding.get("sector", "Other")
        invested_amount = float(holding.get("invested_amount", 0) or 0)

        if sector not in sector_data:
            sector_data[sector] = {
                "invested_amount": 0.0,
                "stocks": [],
            }
        sector_data[sector]["invested_amount"] += invested_amount
        sector_data[sector]["stocks"].append(holding["symbol"])

    recommendations = []

    for sector, data in sector_data.items():
        percentage = (data["invested_amount"] / total_for_pct) * 100
        num_stocks = len(data["stocks"])

        if num_stocks > max_stocks_per_sector:
            excess = num_stocks - max_stocks_per_sector
            recommendation = f"{num_stocks} stocks (max: {max_stocks_per_sector}) - reduce by {excess}"
            status = "overweight"
        elif num_stocks == max_stocks_per_sector:
            recommendation = f"At maximum ({max_stocks_per_sector}) - avoid new additions"
            status = "moderate_overweight"
        elif num_stocks == 1:
            recommendation = f"Balanced - can add up to {max_stocks_per_sector - 1} if needed"
            status = "underweight"
        else:
            recommendation = "Balanced allocation"
            status = "balanced"

        recommendations.append({
            "sector": sector,
            "current_value": round(data["invested_amount"], 2),
            "percentage": round(percentage, 2),
            "num_stocks": num_stocks,
            "stocks": data["stocks"],
            "status": status,
            "recommendation": recommendation,
            "max_stocks_allowed": max_stocks_per_sector,
        })

    status_priority = {
        "overweight": 0,
        "moderate_overweight": 1,
        "balanced": 2,
        "underweight": 3,
    }
    recommendations.sort(key=lambda x: (status_priority.get(x["status"], 99), -x["percentage"]))
    return recommendations


def get_market_cap_recommendations(holdings, total_current_value, settings=None):
    """
    Generate market cap level rebalancing recommendations with stock count and portfolio % limits
    
    Args:
        holdings: List of holding dictionaries with market_cap info
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount, for % calculation)
        settings: PortfolioSettings object with all limits (per-stock %, stock counts, portfolio %)
        
    Returns:
        list: Market cap recommendations with analysis including:
          - Per-stock % violations
          - Total stock count violations  
          - Total portfolio % violations
    """
    if not holdings:
        return []
    cfg = build_threshold_config(settings)
    total_for_pct = _safe_total(total_current_value, holdings)
    if total_for_pct == 0:
        return []

    market_cap_data = _build_market_cap_groups(holdings)
    recommendations = []

    for market_cap, data in market_cap_data.items():
        percentage = (data["invested_amount"] / total_for_pct) * 100
        num_stocks = len(data["stocks"])

        per_stock_limit = cfg.per_stock_pct.get(market_cap)
        stock_count_limit = cfg.stock_count_limits.get(market_cap)
        portfolio_pct_limit = cfg.portfolio_pct_limits.get(market_cap)

        if per_stock_limit is not None:
            violations: List[str] = []
            status = "balanced"

            if stock_count_limit and num_stocks > stock_count_limit:
                excess_stocks = num_stocks - stock_count_limit
                violations.append(f"Stock count {num_stocks}/{stock_count_limit} (reduce {excess_stocks})")
                status = "overweight"

            if portfolio_pct_limit and percentage > portfolio_pct_limit:
                excess_pct = percentage - portfolio_pct_limit
                violations.append(f"Portfolio {percentage:.1f}%/{portfolio_pct_limit}% (over by {excess_pct:.1f}%)")
                status = "overweight"

            if not violations:
                if stock_count_limit and num_stocks >= stock_count_limit * 0.9:
                    violations.append(f"Near stock count limit ({num_stocks}/{stock_count_limit})")
                    status = "moderate_overweight"
                if portfolio_pct_limit and percentage >= portfolio_pct_limit * 0.9:
                    violations.append(f"Near portfolio limit ({percentage:.1f}%/{portfolio_pct_limit}%)")
                    status = "moderate_overweight"

            if violations:
                recommendation = " | ".join(violations)
            elif percentage < (portfolio_pct_limit or 100) * 0.3:
                recommendation = f"Low allocation - can add (limit {stock_count_limit} stocks, {portfolio_pct_limit}% bucket)"
                status = "underweight"
            else:
                recommendation = f"Balanced - {num_stocks}/{stock_count_limit} stocks, {percentage:.1f}%/{portfolio_pct_limit}%"

            target_range = f"Max {per_stock_limit}% per stock"
        else:
            recommendation = "Set market cap for better allocation guidance"
            target_range = "N/A"
            status = "unknown"
            per_stock_limit = None
            stock_count_limit = None
            portfolio_pct_limit = None

        recommendations.append({
            "market_cap": market_cap,
            "current_value": round(data["invested_amount"], 2),
            "percentage": round(percentage, 2),
            "num_stocks": num_stocks,
            "stocks": data["stocks"],
            "target_range": target_range,
            "per_stock_limit": per_stock_limit,
            "stock_count_limit": stock_count_limit,
            "portfolio_pct_limit": portfolio_pct_limit,
            "status": status,
            "recommendation": recommendation,
        })

    status_priority = {
        "overweight": 0,
        "moderate_overweight": 1,
        "balanced": 2,
        "underweight": 3,
        "unknown": 99,
    }
    recommendations.sort(key=lambda x: (status_priority.get(x["status"], 99), -x["percentage"]))
    return recommendations


def _build_sector_groups(holdings: List[dict]) -> Dict[str, List[dict]]:
    groups: Dict[str, List[dict]] = {}
    for h in holdings:
        sector = h.get("sector") or "Other"
        groups.setdefault(sector, []).append(h)
    return groups


def build_actionable_recommendations(
    holdings: List[dict],
    stocks,
    stocks_to_reduce: List[dict],
    stocks_to_add: List[dict],
    sector_rebalancing: List[dict],
    market_cap_rebalancing: List[dict],
    total_for_pct: float,
    cfg: ThresholdConfig,
) -> List[dict]:
    actions: List[dict] = []
    stock_by_symbol = {}
    for stock in stocks or []:
        norm = stock.symbol.replace(".NS", "").replace(".BO", "").upper()
        stock_by_symbol[norm] = stock

    for row in stocks_to_reduce:
        normalized = row["symbol"].replace(".NS", "").replace(".BO", "").upper()
        stock_obj = stock_by_symbol.get(normalized)
        current_price = stock_obj.current_price if stock_obj else None
        in_sell_zone = False
        near_sell_zone = False
        if stock_obj and stock_obj.sell_zone_price and current_price:
            try:
                from utils.zones import parse_zone

                sell_min, _ = parse_zone(stock_obj.sell_zone_price)
                if sell_min and current_price >= sell_min:
                    in_sell_zone = True
                elif sell_min and current_price >= sell_min * 0.97:
                    near_sell_zone = True
            except Exception:
                pass

        in_profit = float(row.get("current_value", 0) or 0) > float(row.get("current_invested", 0) or 0)
        score_boost = (10 if in_sell_zone else 0) + (5 if near_sell_zone else 0) + (4 if in_profit else 0)
        if in_sell_zone and in_profit:
            how_to_apply = "High-conviction trim candidate for allocation correction."
        elif in_sell_zone or near_sell_zone:
            how_to_apply = "Prioritize trimming this position for allocation correction."
        else:
            how_to_apply = "Trim this position to bring allocation back within limit."

        actions.append({
            "action_type": "OVER_ALLOCATED_STOCK",
            "severity": "critical",
            "severity_score": 90 + score_boost,
            "symbol": row["symbol"],
            "title": f"Trim {row['symbol']} exposure",
            "impact_amount_inr": row["reduce_amount"],
            "impact_pct": row["excess_pct"],
            "why": row["reason"],
            "how_to_apply": how_to_apply,
            "related_symbols": [row["symbol"]],
            "details": {
                "current_pct": row["current_pct"],
                "target_pct": row["target_pct"],
                "market_cap": row["market_cap"],
                "in_sell_zone": in_sell_zone,
                "near_sell_zone": near_sell_zone,
                "in_profit": in_profit,
            },
        })

    for row in stocks_to_add:
        if row.get("in_buy_zone"):
            severity = "medium"
            severity_score = 40
            title = f"Add allocation to {row['symbol']}"
            how_to_apply = "Can add in small tranches while staying within limits."
        elif row.get("near_buy_zone"):
            severity = "medium"
            severity_score = 28
            title = f"Watch {row['symbol']} for buy-zone entry"
            how_to_apply = "Watch closely; add only when price enters buy zone or conviction is high."
        else:
            severity = "low"
            severity_score = 12
            title = f"Add allocation to {row['symbol']}"
            how_to_apply = "Low priority: add only after higher-priority rebalancing actions."

        actions.append({
            "action_type": "UNDER_ALLOCATED_STOCK",
            "severity": severity,
            "severity_score": severity_score,
            "symbol": row["symbol"],
            "title": title,
            "impact_amount_inr": row["add_amount"],
            "impact_pct": row["deficit_pct"],
            "why": f"Under-allocated by {row['deficit_pct']:.1f}%",
            "how_to_apply": how_to_apply,
            "related_symbols": [row["symbol"]],
            "details": {
                "current_pct": row["current_pct"],
                "target_pct": row["target_pct"],
                "in_buy_zone": row.get("in_buy_zone", False),
                "near_buy_zone": row.get("near_buy_zone", False),
            },
        })

    sector_groups = _build_sector_groups(holdings)
    for sector, items in sector_groups.items():
        count = len(items)
        if count > cfg.max_stocks_per_sector:
            invested = sum(float(x.get("invested_amount", 0) or 0) for x in items)
            pct = (invested / total_for_pct * 100) if total_for_pct else 0
            actions.append({
                "action_type": "SECTOR_STOCK_COUNT_LIMIT",
                "severity": "high",
                "severity_score": 70,
                "symbol": None,
                "title": f"Reduce sector concentration in {sector}",
                "impact_amount_inr": invested,
                "impact_pct": pct,
                "why": f"{sector} has {count} stocks (limit {cfg.max_stocks_per_sector}).",
                "how_to_apply": "Trim weakest-conviction names in this sector before adding new ones.",
                "related_symbols": [x.get("symbol", "") for x in items],
                "details": {
                    "sector": sector,
                    "current_stock_count": count,
                    "stock_limit": cfg.max_stocks_per_sector,
                },
            })

    for row in market_cap_rebalancing:
        cap = row["market_cap"]
        if cap == "Unknown":
            continue
        if row["percentage"] > (row.get("portfolio_pct_limit") or 0):
            excess_pct = row["percentage"] - row["portfolio_pct_limit"]
            excess_amount = total_for_pct * (excess_pct / 100.0)
            actions.append({
                "action_type": "MARKET_CAP_PORTFOLIO_LIMIT",
                "severity": "critical",
                "severity_score": 85,
                "symbol": None,
                "title": f"{cap} bucket exceeds portfolio limit",
                "impact_amount_inr": round(excess_amount, 2),
                "impact_pct": round(excess_pct, 2),
                "why": f"{cap} is {row['percentage']:.2f}% vs limit {row['portfolio_pct_limit']:.2f}%.",
                "how_to_apply": "Shift excess allocation from this market-cap bucket to under-allocated buckets.",
                "related_symbols": row.get("stocks", []),
                "details": row,
            })
        if row["num_stocks"] > (row.get("stock_count_limit") or 0):
            actions.append({
                "action_type": "MARKET_CAP_STOCK_COUNT_LIMIT",
                "severity": "high",
                "severity_score": 60,
                "symbol": None,
                "title": f"{cap} stock count exceeds limit",
                "impact_amount_inr": row["current_value"],
                "impact_pct": row["percentage"],
                "why": f"{cap} has {row['num_stocks']} stocks vs limit {row['stock_count_limit']}.",
                "how_to_apply": "Consolidate overlapping names in this market-cap bucket.",
                "related_symbols": row.get("stocks", []),
                "details": row,
            })

    total_stocks = len(holdings)
    if total_stocks > cfg.max_total_stocks:
        excess_count = total_stocks - cfg.max_total_stocks
        excess_impact = (total_for_pct * (excess_count / total_stocks)) if total_stocks else 0
        actions.append({
            "action_type": "OVERALL_PORTFOLIO_LIMIT",
            "severity": "high",
            "severity_score": 65,
            "symbol": None,
            "title": "Total stock count exceeds portfolio limit",
            "impact_amount_inr": round(excess_impact, 2),
            "impact_pct": round((excess_count / total_stocks) * 100.0, 2) if total_stocks else 0.0,
            "why": f"{total_stocks} holdings vs max {cfg.max_total_stocks}.",
            "how_to_apply": "Stop adding new names; consolidate low-conviction positions.",
            "related_symbols": [h.get("symbol", "") for h in holdings],
            "details": {
                "total_stocks": total_stocks,
                "max_total_stocks": cfg.max_total_stocks,
                "excess_count": excess_count,
            },
        })

    actions.sort(
        key=lambda x: (
            -(x.get("impact_amount_inr") or 0),
            -(x.get("severity_score") or 0),
            -(x.get("impact_pct") or 0),
        )
    )

    for idx, item in enumerate(actions, start=1):
        item["priority_rank"] = idx
        item["id"] = f"{item['action_type'].lower()}-{idx}"
    return actions


def get_rebalancing_suggestions(holdings, stocks, total_current_value, settings=None, parent_sector_mappings=None):
    """
    Generate complete rebalancing suggestions
    
    Args:
        holdings: List of holding dictionaries
        stocks: List of Stock objects from database
        total_current_value: Total portfolio PROJECTED amount (from settings.projected_portfolio_amount)
        settings: PortfolioSettings object with user-configured thresholds
        parent_sector_mappings: Dict mapping sector_name -> parent_sector (optional)
        
    Returns:
        dict: Complete rebalancing recommendations
    """
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
    sector_rebalancing = get_sector_recommendations(holdings, total_for_pct, cfg.max_stocks_per_sector)
    market_cap_rebalancing = get_market_cap_recommendations(holdings, total_for_pct, settings)
    actionable = build_actionable_recommendations(
        holdings,
        stocks,
        stocks_to_reduce,
        stocks_to_add,
        sector_rebalancing,
        market_cap_rebalancing,
        total_for_pct,
        cfg,
    )

    critical_count = sum(1 for a in actionable if a.get("severity") == "critical")
    high_count = sum(1 for a in actionable if a.get("severity") == "high")
    medium_count = sum(1 for a in actionable if a.get("severity") == "medium")
    capital_at_risk = round(sum(float(a.get("impact_amount_inr", 0) or 0) for a in actionable if a.get("severity") in {"critical", "high"}), 2)

    result = {
        "stocks_to_reduce": stocks_to_reduce,
        "stocks_to_add": stocks_to_add,
        "sector_rebalancing": sector_rebalancing,
        "market_cap_rebalancing": market_cap_rebalancing,
        "total_stocks": len(holdings),
        "max_total_stocks": cfg.max_total_stocks,
        "total_stocks_status": "overweight" if len(holdings) > cfg.max_total_stocks else "balanced",
        "summary_metrics": {
            "total_actions": len(actionable),
            "critical_actions": critical_count,
            "high_actions": high_count,
            "medium_actions": medium_count,
            "capital_at_risk_inr": capital_at_risk,
            "total_for_pct": round(total_for_pct, 2),
        },
        "actionable_recommendations": actionable,
        "thresholds_used": {
            "per_stock_pct": cfg.per_stock_pct,
            "per_stock_display_pct": cfg.per_stock_display_pct,
            "stock_count_limits": cfg.stock_count_limits,
            "portfolio_pct_limits": cfg.portfolio_pct_limits,
            "max_stocks_per_sector": cfg.max_stocks_per_sector,
            "max_total_stocks": cfg.max_total_stocks,
        },
    }

    return result

