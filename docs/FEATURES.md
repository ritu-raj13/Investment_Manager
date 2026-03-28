# Investment Manager - Feature Documentation

**Last Updated:** November 29, 2025

## Table of Contents
- [Swing Trading Workflow (NEW Nov 2025)](#swing-trading-workflow-new-nov-2025)
- [Portfolio Management](#portfolio-management)
- [Profit & Loss Tracking](#profit--loss-tracking)
- [Advanced Portfolio Metrics](#advanced-portfolio-metrics)
  - [FIFO-Based Holding Period](#fifo-based-holding-period-tracking)
  - [XIRR Calculation](#xirr-extended-internal-rate-of-return)
- [Portfolio Allocation Color Coding](#portfolio-allocation-color-coding)
- [Analytics Dashboard](#analytics-dashboard)
- [Portfolio Health](#portfolio-health)
- [Recommendations](#recommendations)
- [Stock Tracking](#stock-tracking)
- [Alert System](#alert-system)
- [Phase 3: Enhanced Financial Features](#phase-3-enhanced-financial-features)
- [FAQs](#faqs)

---

## Swing Trading Workflow (NEW Nov 2025)

**Complete swing trading system** with multi-step buy/sell strategies, parent sector grouping, and advanced market cap limits.

### Projected Portfolio Management

**Location:** Settings → Stock Portfolio Settings

#### Projected Portfolio Amount
- **What Changed:** Renamed from "Total Portfolio Target Amount" → **"Projected Portfolio Amount"**
- **Purpose:** Set your target portfolio value for future planning
- **With Target Date:** Specify when you plan to reach this amount
- **Usage:** All rebalancing calculations use projected amount (not current invested amount)

**Example:**
```
Projected Portfolio Amount: ₹50,00,000
Target Date: March 31, 2026
Current Invested: ₹35,00,000

→ System calculates % allocations based on ₹50L target
→ Shows how much room you have to add in each stock/sector
```

---

### Multi-Step Buy/Sell Strategy

**Location:** Portfolio → Add/Edit Transaction

Track systematic averaging and scaling strategies for swing trading.

#### Multi-Step Buying (Up to 3 Steps)
**Purpose:** Average into positions systematically

**How It Works:**
1. **Step 1:** Initial entry (e.g., 1/3 position at ₹250)
2. **Step 2:** Average if price dips (e.g., 1/3 more at ₹240)
3. **Step 3:** Final average (e.g., last 1/3 at ₹230)

**System Tracking:**
- Automatically calculates average price after each step
- Displays `avg_price_after` for each transaction
- Shows completed steps (e.g., "2/3 steps")

**Example:**
```
RELIANCE - Buy Strategy
Step 1: Buy 10 shares @ ₹2,450 → Avg: ₹2,450
Step 2: Buy 10 shares @ ₹2,380 → Avg: ₹2,415
Step 3: Buy 10 shares @ ₹2,320 → Avg: ₹2,383

Final Position: 30 shares @ ₹2,383 average
```

#### Multi-Step Selling (Up to 2 Steps)
**Purpose:** Book profits systematically

**How It Works:**
1. **Step 1:** Partial exit (e.g., sell 50% at target)
2. **Step 2:** Final exit (e.g., sell remaining 50% at higher target or stop loss)

**System Tracking:**
- Tracks which sell step each transaction represents
- Helps review profit-booking discipline
- Maintains transaction history per step

**Example:**
```
INFY - Sell Strategy
Step 1: Sell 50 shares @ ₹1,650 (50% position)
Step 2: Sell 50 shares @ ₹1,720 (remaining 50%)

→ Locked profits at two different levels
→ Average sell price: ₹1,685
```

---

### Parent Sector Grouping

**Location:** Analytics → Parent Sector Management

**Purpose:** Group related child sectors under parent sectors to enforce diversification limits

#### What Are Parent Sectors?

**Concept:** Multiple child sectors can belong to one parent sector
- **Parent:** Auto
  - **Child:** Automobile, Auto Components, Auto Ancillaries
- **Parent:** Banking
  - **Child:** Banking, Finance, NBFCs
- **Parent:** IT
  - **Child:** IT Services, IT Software

#### Stock Count Limits per Parent Sector

**Default:** Maximum **2 stocks** per parent sector

**Why?** Prevents over-concentration in related industries

**Example Scenario:**
```
❌ BAD (before parent sectors):
- MARUTI (Automobile)
- TATA MOTORS (Automobile)
- MOTHERSON SUMI (Auto Components)
- MRF (Auto Components)
→ 4 auto-related stocks, high correlation risk

✅ GOOD (with parent sector limit):
Parent Sector: Auto (max 2 stocks)
- MARUTI (Automobile)
- MOTHERSON SUMI (Auto Components)
→ System warns if you try to add 3rd auto-related stock
```

#### Managing Parent Sectors

**Add Mapping:**
1. Go to Analytics → Parent Sector Management
2. Click "Add Mapping"
3. Enter child sector name (e.g., "Auto Components")
4. Enter parent sector (e.g., "Auto")

**Common Mappings (Pre-loaded):**
- Auto: Automobile, Auto Components, Auto Ancillaries
- Banking: Banking, Finance
- IT: IT Services, IT Software
- Pharma: Pharmaceuticals, Healthcare
- FMCG: FMCG, Consumer Goods
- Industrials: Capital Goods, Infrastructure, Construction
- Chemicals: Chemicals, Specialty Chemicals
- Metals: Metals, Steel
- Energy: Energy, Power, Oil & Gas

**Stock Tracker Integration:**
- When adding stocks, see parent sector in dropdown helper text
- System validates you don't exceed max stocks per parent

---

### Advanced Market Cap Limits (Three-Tier System)

**Location:** Settings → Stock Portfolio Settings

**Purpose:** Enforce strict caps at three levels: per-stock %, stock count, and portfolio %

#### Level 1: Per-Stock % Limits

**Actual Max % (used in rebalancing logic):**
- **Large Cap:** 5% max per stock
- **Mid Cap:** 3% max per stock
- **Small Cap:** 2.5% max per stock
- **Micro Cap:** 2% max per stock

**Display % (shown in UI with 0.5% leverage):**
- **Large Cap:** 5.5% display
- **Mid Cap:** 3.5% display
- **Small Cap:** 3% display
- **Micro Cap:** 2.5% display

**Why Leverage?** Gives you breathing room of +0.5% before hitting rebalancing alert

**Example:**
```
TCS (Large Cap):
- Current: 5.2% of portfolio
- Display limit: 5.5%
- Status: ✅ Green (within acceptable range)

If it reaches 5.6%:
- Status: ⚠️ Red (exceeds limit, rebalance needed)
```

#### Level 2: Stock Count Limits per Market Cap

**Defaults:**
- **Large Cap:** Max **15 stocks**
- **Mid Cap:** Max **8 stocks**
- **Small Cap:** Max **7 stocks**
- **Micro Cap:** Max **3 stocks**

**Purpose:** Prevent portfolio from becoming too fragmented or concentrated

**Example:**
```
Current Holdings:
- Large Cap: 12/15 stocks ✅
- Mid Cap: 9/8 stocks ⚠️ (1 over limit)
- Small Cap: 5/7 stocks ✅
- Micro Cap: 2/3 stocks ✅

→ Recommendations page shows: Reduce 1 Mid Cap stock
```

#### Level 3: Portfolio % Limits per Market Cap

**Defaults:**
- **Large Cap:** Max **50%** of total portfolio
- **Mid Cap:** Max **30%** of total portfolio
- **Small Cap:** Max **25%** of total portfolio
- **Micro Cap:** Max **10%** of total portfolio

**Purpose:** Maintain balanced exposure across market cap sizes

**Example:**
```
Projected Portfolio: ₹50,00,000

Current Allocation:
- Large Cap: ₹28,00,000 (56%) ⚠️ Exceeds 50% limit
- Mid Cap: ₹12,00,000 (24%) ✅
- Small Cap: ₹8,00,000 (16%) ✅
- Micro Cap: ₹3,00,000 (6%) ✅

→ Recommendations: Reduce Large Cap by ₹3,00,000 (6%)
```

#### Max Total Stocks in Portfolio

**Default:** **30 stocks maximum**

**Purpose:** Prevent over-diversification (too many stocks = hard to track)

**Alert:**
```
Current Holdings: 32 stocks
Max Limit: 30 stocks

⚠️ Portfolio exceeds total stock limit
→ Consider consolidating or closing underperformers
```

---

### Enhanced Recommendations Page

**Location:** Recommendations Tab

#### Sector Rebalancing (Attention-Sorted)

**New Sorting:** Cards now appear by **attention level**
- 🔴 **Red** (overweight) → shown first
- 🟡 **Yellow** (moderate overweight) → shown next
- 🟢 **Green** (balanced/underweight) → shown last

**Why?** See problem sectors first, action items at top

**Example Display:**
```
🔴 Auto (Parent Sector)
   3/2 stocks (1 over limit)
   ₹8,50,000 invested
   → Reduce 1 stock

🟡 Banking
   2/2 stocks (at limit)
   ₹12,00,000 invested
   → Monitor performance

🟢 IT
   1/2 stocks
   ₹6,00,000 invested
   → Balanced - can add 1 more
```

#### Market Cap Rebalancing (Three-Tier Insights)

**Enhanced Display:** Shows violations across all three limit types

**Card Format:**
```
Large Cap
─────────────────────────────
Stocks: 12/15 ✅
Portfolio %: 28.5%/50% ✅
Per-stock limit: 5%

Current Holdings (12 stocks):
TCS, INFY, RELIANCE, HDFC BANK, ICICI BANK, ...

Recommendations:
✅ Balanced - 12/15 stocks, 28.5%/50% portfolio
   Can add up to 3 more stocks
```

**Violation Example:**
```
Mid Cap
─────────────────────────────
Stocks: 10/8 ⚠️
Portfolio %: 35.2%/30% ⚠️
Per-stock limit: 3%

Current Holdings (10 stocks):
STOCK1, STOCK2, ... STOCK10

Recommendations:
⚠️ Stock count: 10/8 (reduce 2)
⚠️ Portfolio %: 35.2%/30% (over by 5.2%)
→ Reduce 2 stocks or ₹2,60,000 in holdings
```

---

### Key Benefits of Swing Trading Features

1. **📊 Projected Planning:** Plan future portfolio, not just track current
2. **📈 Systematic Entries/Exits:** Track multi-step buy/sell discipline
3. **🎯 Parent Sector Limits:** Avoid correlation risk across related sectors
4. **⚖️ Three-Tier Caps:** Enforce limits at per-stock, count, and portfolio levels
5. **🚨 Attention Sorting:** See problem areas first in rebalancing
6. **💡 Actionable Insights:** Exact stock counts and amounts to adjust

---

### Configuration (Settings Page)

**Stock Portfolio Settings Section:**

| Setting | Default | Purpose |
|---------|---------|---------|
| Projected Portfolio Amount | ₹0 | Target portfolio value |
| Target Date | - | When to reach target |
| **Per-Stock Limits** | | |
| Large Cap Max % | 5% (display 5.5%) | Per-stock ceiling |
| Mid Cap Max % | 3% (display 3.5%) | Per-stock ceiling |
| Small Cap Max % | 2.5% (display 3%) | Per-stock ceiling |
| Micro Cap Max % | 2% (display 2.5%) | Per-stock ceiling |
| **Stock Count Limits** | | |
| Max Large Cap Stocks | 15 | Stock count cap |
| Max Mid Cap Stocks | 8 | Stock count cap |
| Max Small Cap Stocks | 7 | Stock count cap |
| Max Micro Cap Stocks | 3 | Stock count cap |
| **Portfolio % Limits** | | |
| Max Large Cap Portfolio % | 50% | Total exposure cap |
| Max Mid Cap Portfolio % | 30% | Total exposure cap |
| Max Small Cap Portfolio % | 25% | Total exposure cap |
| Max Micro Cap Portfolio % | 10% | Total exposure cap |
| **Sector Limits** | | |
| Max Stocks per Parent Sector | 2 | Diversification rule |
| Max Total Stocks | 30 | Overall portfolio cap |

**All settings are fully configurable** - adjust to your risk profile and trading style!

---

## Portfolio Management

### Current Holdings Display
- **Active Holdings Count**: Shows number of stocks currently held
- **Total Transactions Count**: Displays total number of buy/sell transactions
- **Sticky Table Headers**: Column headers remain visible while scrolling through holdings
- **Sortable Columns**: Click column headers to sort by:
  - **% of Total** (default sort, descending) - Shows highest allocations first
  - Unrealized P/L - Absolute profit/loss amounts
  - Return % - Percentage returns
  - **Holding Period** - Days held (FIFO-based)
  - Toggle ascending/descending with ↑/↓ indicator
- **Search Filter**: Filter holdings by stock symbol

### Holdings Table Columns
| Column | Description | Sortable |
|--------|-------------|----------|
| Symbol | Stock ticker symbol | No |
| Quantity | Number of shares held | No |
| Avg Price | Average purchase price per share | No |
| Current Price | Latest market price | No |
| Invested | Total amount invested | No |
| **% of Total** | Percentage of portfolio (color-coded by market cap) | **Yes (Default Sort ↓)** |
| Current Value | Market value of holdings | No |
| Unrealized P/L | Paper profit/loss on current holdings | Yes |
| Return % | Percentage return on investment | Yes |
| 1D Change % | Daily price change percentage | No |
| **Holding Period** | Time held (FIFO-based, e.g., "1Y 3M", "45D") | Yes |

---

## Profit & Loss Tracking

### Realized P/L
**Definition**: Actual profit or loss from completed SELL transactions

**Calculation**:
```
Realized P/L = (Sell Price - Average Cost) × Quantity Sold
```

**Example**:
- Buy 50 shares @ ₹810.20 = ₹40,510 invested
- Sell 26 shares @ ₹932.50
- Realized P/L = (₹932.50 - ₹810.20) × 26 = **₹3,179.80 profit**

**Display**:
- Shown in summary card at top of Portfolio page
- **💰 Icon** indicates realized (booked) profit/loss
- Color-coded: Green for profit, Red for loss

### Unrealized P/L
**Definition**: Paper profit or loss on stocks still held

**Calculation**:
```
Unrealized P/L = Current Value - Invested Amount
Unrealized P/L % = (Unrealized P/L / Invested Amount) × 100
```

**Example**:
- Remaining 24 shares @ ₹810.20 avg cost = ₹19,444.80 invested
- Current price: ₹865
- Current value: 24 × ₹865 = ₹20,760
- Unrealized P/L = ₹20,760 - ₹19,444.80 = **₹1,315.20 potential profit**

**Display**:
- Shown in summary card at top of Portfolio page
- **📈 Icon** indicates unrealized (paper) gains/losses
- Per-stock unrealized P/L shown in holdings table
- Color-coded: Green for profit, Red for loss

### Total P/L
```
Total P/L = Realized P/L + Unrealized P/L
```
Represents complete investment performance combining actual and potential profits/losses.

---

## Advanced Portfolio Metrics

### FIFO-Based Holding Period Tracking

#### What is FIFO?

**FIFO = First-In-First-Out**

When you sell shares, the system automatically removes from the oldest purchase lots first. This ensures accurate holding period calculation for your remaining shares.

#### How It Works

**Example Scenario:**
1. **Jan 1, 2024**: Buy 10 shares @ ₹2,400
2. **Feb 1, 2024**: Buy 10 shares @ ₹2,450
3. **Mar 1, 2024**: Sell 12 shares @ ₹2,500

**FIFO Logic:**
- Sell 10 shares from Jan 1 lot (oldest)
- Sell 2 shares from Feb 1 lot
- **Remaining**: 8 shares from Feb 1 lot

**Holding Period Calculation:**
- Shows holding period from **Feb 1** (remaining shares)
- Not from Jan 1 (those shares were sold)
- Weighted average if multiple lots remain

#### Display Format

Holdings are shown in user-friendly format:
- Less than 30 days: `15D`
- 30-365 days: `2M 15D` or `11M 5D`
- Over 1 year: `1Y 3M` or `2Y 6M`

#### Features

- ✅ **Automatic lot tracking** - No manual entry needed
- ✅ **Weighted average** - For multiple remaining lots
- ✅ **Sortable column** - Click "Holding Period" header to sort
- ✅ **Chronological processing** - Ensures accurate calculations
- ✅ **Updates automatically** - With each buy/sell transaction

#### Benefits

1. **Tax Planning**: Know exactly how long you've held each position (LTCG vs STCG)
2. **Investment Strategy**: Track long-term vs short-term holdings
3. **Accurate Records**: FIFO method aligns with tax regulations
4. **Decision Making**: See which stocks you've held longest

#### Example with Multiple Lots

**Transaction History:**
```
2023-01-15: BUY 100 shares @ ₹500 = ₹50,000
2023-06-01: BUY 50 shares @ ₹550 = ₹27,500
2024-03-15: SELL 80 shares @ ₹600 = ₹48,000
```

**FIFO Calculation:**
- Sell 80 shares from Jan 15 lot (oldest)
- Remaining: 20 shares from Jan 15 + 50 shares from Jun 1

**Holding Period:**
- 20 shares held since Jan 15, 2023 (~654 days)
- 50 shares held since Jun 1, 2023 (~517 days)
- **Weighted Average: ~559 days** (~1Y 6M)

**Realized P/L:**
- Sold 80 @ ₹600, cost basis ₹500
- Realized: (₹600 - ₹500) × 80 = **₹8,000 profit**

---

### XIRR (Extended Internal Rate of Return)

#### What is XIRR?

XIRR calculates your **annualized portfolio return** accounting for:
- ⏱️ **Time value of money** - Earlier investments count differently
- 💰 **Irregular cash flows** - Different amounts at different times
- 📊 **All transactions** - Buys, sells, and current value

#### Why XIRR > Simple Returns?

**Simple Return** (basic calculation):
```
Return % = (Current Value - Invested) / Invested × 100
```
❌ Ignores WHEN you invested  
❌ Doesn't account for multiple transactions  
❌ Can't compare with other investments

**XIRR** (time-weighted):
```
Considers all cash flows with their dates
Calculates equivalent annual return
```
✅ Accounts for timing of investments  
✅ Handles irregular contributions  
✅ Directly comparable to FDs, Mutual Funds, etc.

#### Example

**Your Investments:**
- Jan 2024: Invest ₹50,000
- Jun 2024: Invest ₹30,000
- Sept 2024: Sell shares worth ₹20,000
- Oct 2024: Current portfolio value ₹80,000

**Simple Return:** Would give misleading number

**XIRR:** Shows true annualized return (e.g., 18.5%)
- You can now compare: "My portfolio returned 18.5% vs FD at 7%"

#### How It's Calculated

Uses **Newton-Raphson method** to solve:
```
NPV = Σ (Cash Flow / (1 + XIRR)^years) = 0
```

Where:
- All BUY transactions = Negative cash flows (money out)
- All SELL transactions = Positive cash flows (money in)
- Current portfolio value = Final positive cash flow (today)

#### Display

**Location:** Portfolio page summary cards (6th card)

**Format:**
```
📊 XIRR
+18.50%
Annualized return
```

**Color Coding:**
- 🟢 Green: Positive returns
- 🔴 Red: Negative returns
- Grey: N/A (insufficient data)

#### When XIRR Shows "N/A"

XIRR cannot be calculated if:
- No transactions exist
- Only BUY or only SELL transactions (need both for calculation)
- Portfolio has no current value
- Calculation doesn't converge (rare mathematical edge case)

#### Benefits

1. **Benchmark Comparison**: Compare with FDs (7%), Mutual Funds (12-15%), etc.
2. **True Performance**: See real returns adjusted for time
3. **Investment Decisions**: Evaluate if portfolio is meeting goals
4. **Professional Metric**: Same calculation used by financial professionals

#### Detailed Example

**Portfolio Activity:**
```
2023-01-01: BUY ₹1,00,000 (negative cash flow)
2023-06-01: BUY ₹50,000 (negative cash flow)
2023-12-01: SELL ₹30,000 (positive cash flow)
2024-10-30: Portfolio Value: ₹1,50,000 (final positive cash flow)
```

**XIRR Calculation:**
- Net invested: ₹1,00,000 + ₹50,000 - ₹30,000 = ₹1,20,000
- Current value: ₹1,50,000
- Time period: ~22 months
- **XIRR: ~17.8%** (annualized)

**Comparison:**
- Simple return: (₹1,50,000 - ₹1,20,000) / ₹1,20,000 = 25%
- But over 22 months, not 12 months
- XIRR properly annualizes: **17.8%**
- Now comparable to: "Bank FD at 7%" or "Mutual Fund at 12%"

---

## Portfolio Allocation Color Coding

### % of Total Column Color Logic

The **% of Total** column uses color coding to indicate if a stock's allocation is appropriate based on its market capitalization:

#### Thresholds by Market Cap

| Market Cap | Target Allocation | Color Logic |
|------------|-------------------|-------------|
| **Large Cap** | 5% | > 5.5%: 🔴 Red (Over-allocated)<br>5.0% - 5.5%: 🟢 Green (Good allocation)<br>< 5.0%: 🟠 Orange (Under-allocated) |
| **Mid Cap** | 3% | > 3.5%: 🔴 Red (Over-allocated)<br>3.0% - 3.5%: 🟢 Green (Good allocation)<br>< 3.0%: 🟠 Orange (Under-allocated) |
| **Small Cap** | 2% | > 2.5%: 🔴 Red (Over-allocated)<br>2.0% - 2.5%: 🟢 Green (Good allocation)<br>< 2.0%: 🟠 Orange (Under-allocated) |
| **Micro Cap** | 2% | > 2.5%: 🔴 Red (Over-allocated)<br>2.0% - 2.5%: 🟢 Green (Good allocation)<br>< 2.0%: 🟠 Orange (Under-allocated) |
| **Unknown** | N/A | 🔵 Blue (No threshold) |

#### Color Meanings

- **🔴 Red**: Position is over-allocated (more than +0.5% above threshold)
  - Action: Consider reducing position or increasing portfolio size
- **🟢 Green**: Position is well-allocated (at threshold to +0.5% above)
  - Action: Well-balanced, maintain position. Gives you breathing room up to +0.5%
- **🟠 Orange**: Position is under-allocated (below threshold)
  - Action: Consider increasing position if opportunity exists
- **🔵 Blue**: Market cap not set, no threshold applied
  - Action: Set market cap in Stock Tracking for allocation guidance

#### Example Scenarios

**Large Cap Stock (5% threshold, green range: 5.0% - 5.5%)**:
- 6.2% allocation → 🔴 Red (Over-allocated by 1.2%)
- 5.3% allocation → 🟢 Green (Good allocation, within acceptable range)
- 5.0% allocation → 🟢 Green (At threshold, perfect)
- 4.2% allocation → 🟠 Orange (Under-allocated by 0.8%)

**Mid Cap Stock (3% threshold, green range: 3.0% - 3.5%)**:
- 4.0% allocation → 🔴 Red (Over-allocated by 1.0%)
- 3.2% allocation → 🟢 Green (Good allocation, within acceptable range)
- 3.0% allocation → 🟢 Green (At threshold, perfect)
- 2.4% allocation → 🟠 Orange (Under-allocated by 0.6%)

**Small Cap Stock (2% threshold, green range: 2.0% - 2.5%)**:
- 3.0% allocation → 🔴 Red (Over-allocated by 1.0%)
- 2.3% allocation → 🟢 Green (Good allocation, within acceptable range)
- 2.0% allocation → 🟢 Green (At threshold, perfect)
- 1.5% allocation → 🟠 Orange (Under-allocated by 0.5%)

---

## Analytics Dashboard

### Performance Charts

#### Portfolio Value Comparison
- Bar chart showing Invested vs. Current Value
- Visual comparison of portfolio growth

#### Sector Allocation (Investment)
- Pie chart showing investment breakdown by sector
- **Hover Tooltip**: Sector name and invested amount

#### Market Cap Allocation (Investment)
- Pie chart showing investment breakdown by market cap
- **Hover Tooltip**: Market cap category and invested amount

### Stock Distribution

#### Number of Stocks by Sector
- Bar chart showing stock count across sectors
- Helps identify sector diversification

#### Number of Stocks by Market Cap
- Bar chart showing stock count by market cap category
- Visualize large/mid/small cap distribution

### Top Performers
- **Top 5 Gainers**: Stocks with highest unrealized returns
- **Top 5 Losers**: Stocks with lowest unrealized returns
- Displays symbol, name, return %, and absolute gain/loss

---

## Portfolio Health

### Purpose
Comprehensive health assessment of your portfolio using risk and diversification metrics.

### Overall Health Score (0-100)
- **Composite metric** combining:
  - Diversification (40% weight)
  - Low concentration (30% weight)
  - Balanced allocation (30% weight)
- **Color-coded scoring**:
  - Green (75-100): Excellent health
  - Yellow (50-74): Good, room for improvement
  - Red (0-49): Needs attention

### Concentration Risk Analysis

#### Top 3 Stocks Concentration
- Percentage of portfolio in top 3 stocks
- **Thresholds**:
  - < 40%: Well diversified
  - 40-70%: Moderate concentration
  - > 70%: High risk, over-concentrated

#### Top Sector Concentration
- Percentage in largest sector
- **Risk indicator**: > 50% = high sector risk

#### Top Market Cap Concentration
- Percentage in dominant market cap category
- **Risk indicator**: > 70% = imbalanced allocation

### Diversification Metrics

#### Number of Stocks
- Total unique holdings
- Target: 10-15 stocks for good diversification

#### Number of Sectors
- Unique sectors represented
- Target: 5-8 sectors

#### Number of Market Caps
- Unique market cap categories (Large/Mid/Small/Micro)
- Target: 3-4 categories for balanced risk

#### Herfindahl Index
- Measures portfolio concentration (0-1)
- Lower is better (closer to 0 = more diversified)
- Thresholds:
  - < 0.15: Well diversified
  - 0.15-0.25: Moderately diversified
  - > 0.25: Concentrated

### Allocation Health Summary
- **Over-Allocated Stocks**: Exceeding target % (red)
- **Balanced Stocks**: At target % (green)
- **Under-Allocated Stocks**: Below target % (orange)
- Uses same thresholds as Portfolio page color coding

---

## Recommendations

### Purpose
Actionable suggestions for portfolio management, rebalancing, and price-based opportunities.

### Alert Zones (Price-Based)
Stocks currently in or near your defined buy/sell/average zones.

#### In Buy Zone
- Stocks at or below target buy price
- **Action**: Consider buying

#### In Sell Zone
- Stocks at or above target sell price
- **Action**: Consider selling

#### In Average Zone
- Stocks within average price range
- **Action**: Consider averaging (adding more)

#### Near Zones (Within ±3%)
- Stocks approaching buy/sell/average zones
- Early warning to prepare actions

#### Edit tracking from zone rows
- Each stock row in **Price Zone Alert Details** includes an **Edit** control that opens the same add/edit dialog as **Stock Tracking** (`StockEditDialog` in the app), loaded with `GET /api/stocks/:id`.
- The recommendations dashboard includes a stable **`id`** on every `action_items` entry so the client can load and update the correct tracking record.
- After a successful save, the Recommendations page refreshes in the background (no full-page loading flash) so zone membership stays in sync with updated prices and zones.

### Rebalancing Recommendations

#### Stocks to Reduce
- Over-allocated stocks (% above target + 0.5%)
- Shows:
  - Current % vs. Target %
  - Excess % and amount to reduce
  - Market cap category
- **Table format** with actionable amounts

#### Stocks to Add
- Under-allocated stocks (% below target)
- **Priority indicators**:
  - Highlighted if stock is also in buy zone
  - Sorted by: buy zone stocks first, then by deficit %
- Shows:
  - Current % vs. Target %
  - Deficit % and amount to add
  - Market cap category

#### Sector Rebalancing Insights
- Identifies overweight/underweight sectors
- **Guidelines**:
  - > 40%: Highly concentrated, diversify
  - > 25%: Moderate concentration, monitor
  - < 5%: Underweight, consider increasing
- Shows sector %, number of stocks, and recommendations

#### Market Cap Rebalancing Insights
- Analyzes large/mid/small cap distribution
- **Target ranges**:
  - Large Cap: 50-65%
  - Mid Cap: 25-35%
  - Small/Micro Cap: 10-20%
- Provides recommendations to balance portfolio

### Benefits
- **Integrate price and allocation**: See both zone alerts and rebalancing needs
- **Prioritize actions**: Buy zone stocks highlighted in rebalancing
- **Actionable amounts**: Exact ₹ amounts to add/reduce
- **Context-aware**: Sector and market cap level guidance
- **At-a-glance summaries**: Top of the page shows **Price Zone Alerts** (Sell / Average / Buy counts) and **Rebalancing Alerts** (Reduce / Add / Concentration counts) with matching card styling.

---

## Stock Tracking

### Features
- Add stocks with buy/sell/average price zones
- Flexible price ranges (e.g., "250-300" or "250")
- Symbol normalization (handles .NS/.BO suffixes automatically)
- **Refresh Prices** updates **current price** only (fast; no Screener). **Refresh 1D Change** updates **day_change_pct** from Screener for Indian symbols (slower; run when you want fresh 1D % for the list and portfolio summaries).
- Real-time price updates
- Status tracking (BUY, SELL, HOLD, WATCHING)
- Editing a stock from the **Recommendations** page (price zone lists) uses the **same form** as Stock Tracking; see [Recommendations](#recommendations) — *Edit tracking from zone rows*.

### Screener-assisted sector and market cap (add / fetch-details)
- **Sector:** Parsed from Screener **Peer comparison** breadcrumb: the **second-to-last** industry/sector link text (if only one link exists, that value is used). New stocks and **fetch-details** set `sector` automatically. For a **one-time backfill** of existing rows, run `python -u archived_utilities/refresh_all_stock_sectors.py` from the `backend` folder for live progress logs (stop Flask first if using SQLite), then remove that script when no longer needed. After bulk label changes, review **Parent sector mappings**.
- **Market cap tier (Large / Mid / Small / Micro):** Uses three **cutoff values** (market cap in **Rs. Cr**) for the **100th, 250th, and 500th** company in Screener’s “Companies by Market Cap” list (market cap &gt; 0, sorted descending). **Fetch MC Thresholds** on **Settings → Stock Portfolio** loads those three values from Screener (editable in the same place). When adding a stock or using fetch-details, the app compares the company’s Screener **Market Cap** (Cr) to those cutoffs: **Large** if MC ≥ 100th cutoff, **Mid** if ≥ 250th and &lt; 100th, **Small** if ≥ 500th and &lt; 250th, **Micro** if &lt; 500th. If thresholds are not set, tier is left empty.

### Price Zone Alerts
Alert thresholds changed to **±3%** (previously ±5%):
```
Near Buy Zone: buy_max × 1.03
Near Sell Zone: sell_min × 0.97
Near Average Zone: avg_max × 1.03 / avg_min × 0.97
```

### Status Sync
- Automatically updates to 'HOLD' when stock is bought
- Returns to previous zone status when fully sold
- Handles partial sales correctly

---

## Alert System

### Zone Detection
- **In Buy Zone**: Current price ≤ buy zone max
- **Near Buy Zone**: Current price within 3% above buy zone max
- **In Sell Zone**: Current price ≥ sell zone min
- **Near Sell Zone**: Current price within 3% below sell zone min

### Recommendations
- Buy/sell recommendations based on current price vs. zones
- Notifications for stocks requiring action
- **See [Recommendations](#recommendations) page** for complete alert zones and actionable suggestions

---

## Transaction Management

### Features
- Add BUY/SELL transactions
- Edit existing transactions
- Delete transactions (with holdings recalculation)
- Transaction history with sortable columns
- Search/filter by stock symbol

### Automatic Calculations
- Average cost basis (FIFO/Average Cost method)
- Realized P/L calculation on sales
- Holdings quantity and invested amount updates
- Status synchronization with Stock Tracking

### Symbol Handling
- Flexible matching (.NS/.BO suffix handling)
- Automatic normalization for consistent grouping
- Prevents duplicate stocks due to suffix variations

---

## User Interface Enhancements

### Portfolio Page
- **Sticky headers** for table scrolling
- **Active Holdings & Transactions count** displayed prominently
- **6 Summary cards** showing key metrics:
  1. Total Invested
  2. Current Value
  3. 💰 Realized P/L (booked profits)
  4. 📈 Unrealized P/L (paper gains)
  5. 1 Day Change %
  6. **📊 XIRR** (annualized returns) ← NEW!
- **Color-coded allocation** in % of Total column
- **Enhanced sortable columns**:
  - Default sort by % of Total (descending)
  - Sort by Unrealized P/L, Return %, or Holding Period
- **11 table columns** including new Holding Period column
- **Search functionality** for quick stock lookup

### Analytics Page
- Performance visualization with 5 charts
- Top gainers and losers display
- Clean, focused layout on data insights
- Investment and stock count distribution

### Health Page (NEW)
- Overall health score (0-100) with gauge
- Concentration risk breakdown
- Diversification metrics
- Allocation health summary

### Recommendations Page (NEW)
- Price zone alerts (in/near buy/sell/average zones)
- Rebalancing suggestions (stocks to add/reduce)
- Sector and market cap insights
- Integrated actionable recommendations

---

## Data Persistence

### Database Schema
- SQLite (development) / PostgreSQL (production)
- Automatic schema migrations
- Transaction history preservation
- Price update tracking

### Automatic Daily Backup
**NEW (December 2025)**: Automated database backup system

**Features:**
- ✅ **Daily auto-backup** - Runs automatically on server startup
- ✅ **Smart detection** - Only creates backup if current date > last backup date
- ✅ **Keep last 5 backups** - Automatically deletes older backups
- ✅ **Zero configuration** - Works out of the box
- ✅ **Startup logs** - Shows backup status in console

**How It Works:**
```
Server Startup:
[AUTO-BACKUP] Checking backup status...
[AUTO-BACKUP] Last backup: Nov 29, 2025
[AUTO-BACKUP] Today: Dec 6, 2025
[AUTO-BACKUP] Creating new backup...
[BACKUP] ✓ Created: investment_manager_backup_20251206_212516.db
[AUTO-BACKUP] ✓ Complete! Total backups: 2
```

**Storage:**
- Location: `backend/backups/`
- Format: `investment_manager_backup_YYYYMMDD_HHMMSS.db`
- Retention: Last 5 backups only

**Benefits:**
- **No data loss** - Daily protection against accidental changes
- **Space efficient** - Auto-cleanup keeps storage minimal
- **Transparent** - See backup status in startup logs
- **Disaster recovery** - Easy restore from recent backup

### Manual Backup & Export
- CSV export functionality
- Transaction history export
- Manual backup tools included (see `utils/backup.py`)

---

## Security Features

### Authentication
- Login/logout functionality
- Session management
- Password hashing (bcrypt)
- Rate limiting on login attempts

### Environment Variables
- Configurable via `.env` file
- Separate dev/production configurations
- Secret key management
- Admin credentials from environment

---

## Deployment

### Development
- `scripts/dev/start_dev.bat` - Start backend & frontend
- Desktop shortcut compatible
- Automatic dependency installation
- Hot reload enabled

### Production
- Gunicorn WSGI server
- PostgreSQL database
- Environment-based configuration
- Cloud deployment ready (Railway/Heroku/Render)

---

## Future Enhancements

See [FUTURE_FEATURES.md](FUTURE_FEATURES.md) for planned features and improvements.

---

---

## Phase 3: Enhanced Financial Features

**New in November 2025:** Comprehensive financial health tracking and cross-asset portfolio management.

### Financial Health Dashboard

**Location:** Health tab → Financial Health section

Track your complete financial wellness with metrics used by financial planners:

#### Overall Financial Health Score
**What:** Composite score (0-100) based on multiple factors  
**Components:**
- Net worth growth
- Asset allocation balance
- Debt-to-income ratio
- Emergency fund adequacy
- Savings rate

**Color Coding:**
- 🟢 **75-100:** Excellent financial health
- 🟡 **50-74:** Good, room for improvement
- 🔴 **0-49:** Needs attention

#### Debt-to-Income Ratio
**What:** Percentage of your income going to debt payments  
**Formula:** `(Total Debt Payments / Monthly Income) × 100`

**Interpretation:**
- **<20%:** Excellent - healthy debt load
- **20-35%:** Good - manageable debt
- **36-49%:** Fair - higher debt burden
- **>50%:** Poor - debt is overwhelming

**Example:**
- Monthly income: ₹1,00,000
- Debt payments (loans, credit cards): ₹25,000
- Debt-to-income ratio: **25% (Good)**

#### Emergency Fund Status
**What:** Months of expenses covered by liquid savings  
**Formula:** `Total Liquid Savings / Average Monthly Expenses`

**Recommendation:**
- **Minimum:** 3-6 months of expenses
- **Ideal:** 6-12 months
- **If self-employed:** 12+ months

**Tracked Accounts:**
- Savings accounts
- Cash equivalents
- Excludes: FD, EPF, NPS (illiquid)

**Example:**
- Liquid savings: ₹4,50,000
- Monthly expenses: ₹75,000
- Emergency fund: **6 months (Ideal)**

#### Savings Rate
**What:** Percentage of income you're saving  
**Formula:** `[(Income - Expenses) / Income] × 100`

**Benchmarks:**
- **<10%:** Below average - increase savings
- **10-20%:** Good - standard savings rate
- **20-30%:** Excellent - high savings
- **>30%:** Exceptional - aggressive savings

**Tracked Period:** Last 30, 90, or 365 days

**Example:**
- Monthly income: ₹1,50,000
- Monthly expenses: ₹1,05,000
- Savings: ₹45,000
- Savings rate: **30% (Excellent)**

---

### Unified Portfolio XIRR

**Location:** Dashboard tab → Portfolio Returns section

**What:** Single return percentage across ALL your assets (stocks, mutual funds, FDs, EPF, NPS, etc.)

**Why It Matters:**  
- Traditional XIRR only tracks one asset type
- Unified XIRR shows TRUE portfolio performance
- Accounts for timing of ALL cash flows

**Calculation:**
- Combines cash flows from all asset types
- Uses Newton-Raphson method for accuracy
- Accounts for buy/sell timing across years

**Example:**
```
Stocks:     12.5% XIRR (₹10L invested)
Mutual Funds: 15.8% XIRR (₹8L invested)
Fixed Deposits: 7.5% XIRR (₹5L invested)

Unified XIRR: 12.1% (weighted by investments & timing)
```

**Features:**
- Overall portfolio XIRR
- Breakdown by asset type
- Visual charts showing contribution
- Export to CSV for analysis

---

### Global Settings & Allocation Targets

**Location:** Settings tab → Global Settings

Set portfolio targets and let the system track compliance:

#### Asset Allocation Targets
**Configure:**
- Maximum equity allocation (e.g., 70%)
- Maximum debt allocation (e.g., 30%)
- Minimum cash reserves (e.g., 10%)

**System Response:**
- Tracks current vs target allocation
- Highlights when over/under limits
- Provides rebalancing suggestions

**Example Setup:**
```
Max Equity: 70%
Max Debt: 30%
Min Cash: 10%

Current State:
Equity: 75% ⚠️ (5% over target)
Debt: 20% ✅ (within target)
Cash: 5% ⚠️ (5% below target)

→ System suggests: Reduce equity, increase cash
```

#### Budget & Emergency Fund Settings
**Configure:**
- Monthly income target
- Monthly expense budget
- Minimum emergency fund (months)

**System Tracking:**
- Alerts when expenses exceed budget
- Tracks progress toward emergency fund goal
- Monthly budget compliance reports

#### Currency & Display Preferences
- Currency symbol (₹, $, €, etc.)
- Number formatting
- Date format preferences

---

### Multi-Asset Net Worth Tracking

**Location:** Dashboard tab

**What:** Total net worth across ALL asset categories  
**Categories Tracked:**
1. **Equity:** Stocks, Equity Mutual Funds
2. **Debt:** FDs, Debt Funds, Bonds
3. **Retirement:** EPF, NPS
4. **Cash:** Savings accounts
5. **Other:** Gold, Lending, Crypto, etc.

**Features:**
- Total net worth (real-time)
- Breakdown by asset class
- Pie chart visualization
- Trend over time
- Export to Excel/CSV

**Example Display:**
```
Total Net Worth: ₹45,50,000

Equity: ₹20,00,000 (44%)
Debt: ₹12,00,000 (26%)
Retirement: ₹8,00,000 (18%)
Cash: ₹3,50,000 (8%)
Other: ₹2,00,000 (4%)
```

---

### Cash Flow Analysis

**Location:** Dashboard tab → Cash Flow section

**What:** Visual breakdown of income vs expenses

**Features:**
- Monthly income tracking
- Expense categorization
- Surplus/deficit calculation
- Trend analysis (3, 6, 12 months)
- Category-wise spending breakdown

**Visualizations:**
- Bar chart: Income vs Expenses by month
- Pie chart: Expense categories
- Line chart: Savings trend over time

**Example Insights:**
- "Your spending increased 15% in October"
- "Food & Dining is 25% of total expenses"
- "You saved ₹45,000 this month (30% of income)"

---

### Budget Tracking & Alerts

**Location:** Income & Expenses tab → Budgets section

**What:** Set spending limits by category and track compliance

**Features:**
- Category-level budgets (Food, Transport, Entertainment, etc.)
- Monthly or annual periods
- Real-time spend tracking
- Visual progress bars
- Alerts when approaching limits

**Budget Status:**
```
Food & Dining: ₹15,000 / ₹20,000 (75% used) ✅
Transport: ₹8,500 / ₹8,000 (106% used) ⚠️
Entertainment: ₹3,000 / ₹5,000 (60% used) ✅

→ Alert: Transport budget exceeded by ₹500
```

**Smart Features:**
- Rollover unused budget (optional)
- Trend comparison (this month vs last month)
- Spending patterns analysis
- Budget optimization suggestions

---

## How to Use Phase 3 Features

### Setup (One-time, 10 minutes)

1. **Configure Global Settings**
   - Go to Settings → Global Settings
   - Set allocation targets (equity/debt/cash %)
   - Set emergency fund goal (months)
   - Set income/expense targets

2. **Add All Your Assets**
   - Stocks → Portfolio tab
   - Mutual Funds → Mutual Funds tab
   - FDs, EPF, NPS → Fixed Income tab
   - Savings, Lending → Accounts tab

3. **Track Income & Expenses**
   - Add income transactions
   - Add expense transactions
   - Create category budgets

### Daily Use

1. **Check Dashboard**
   - View total net worth
   - Check unified XIRR
   - Review cash flow

2. **Monitor Health**
   - Financial health score
   - Debt-to-income ratio
   - Emergency fund status
   - Savings rate

3. **Stay on Budget**
   - Check budget compliance
   - Review spending alerts
   - Adjust as needed

---

## Phase 3 vs Phase 1-2: What's New?

| Feature | Phase 1-2 | Phase 3 |
|---------|-----------|---------|
| **Assets Tracked** | Stocks only | Stocks, MF, FD, EPF, NPS, Savings, Lending, Gold, etc. |
| **XIRR** | Stocks only | Unified across ALL assets |
| **Net Worth** | Portfolio value | Complete net worth (all assets) |
| **Health Metrics** | Portfolio concentration | Financial health score, debt-to-income, emergency fund |
| **Budgeting** | Not available | Full category-wise budgets & alerts |
| **Allocation** | Market cap/sector | Cross-asset allocation (equity/debt/cash) |
| **Goals** | Manual tracking | Automated target tracking & compliance |

---

## FAQs

### Q: What if I don't have a total portfolio amount set?
**A:** Holding Period and XIRR will still work! They don't need the total amount setting. Only the % of Total column requires it.

### Q: Does FIFO affect my actual holdings?
**A:** No, it's just for calculation purposes. Your total shares remain the same. Only the holding period tracking and realized P/L calculations use FIFO methodology.

### Q: Why is my XIRR showing N/A?
**A:** Possible reasons:
- Need at least 2 cash flows (minimum: 1 buy + current value)
- If you've only bought stocks (no sales yet), XIRR needs both inflows and outflows
- Calculation may not converge in rare edge cases

### Q: Can I sort by multiple columns?
**A:** Click any sortable column header to sort by that column. Click again to toggle between ascending/descending order. Only one column can be sorted at a time.

### Q: How often does XIRR update?
**A:** Automatically updates whenever:
- You add a new transaction (BUY/SELL)
- Portfolio value changes (price updates)
- You refresh the portfolio page

### Q: Is FIFO mandatory for my portfolio?
**A:** Yes, for calculation consistency and tax compliance. FIFO is the standard method used globally for stock lot tracking and aligns with tax regulations in most countries.

### Q: What's the difference between Realized and Unrealized P/L?
**A:**
- **Realized P/L**: Actual profit/loss from shares you've already sold (booked/locked in)
- **Unrealized P/L**: Paper profit/loss on shares you still own (not yet locked in, changes with price)

### Q: How is the holding period calculated when I have multiple buy transactions?
**A:** The system uses a weighted average based on FIFO. If you have shares from different purchase dates, it calculates the weighted average holding period based on the quantity from each lot.

---

## User-Configurable Portfolio Settings

### Portfolio Configuration (Settings Page)

Navigate to **Settings > Portfolio Configuration** to customize your portfolio allocation thresholds and preferences.

#### Configurable Parameters

| Setting | Description | Default Value | Range |
|---------|-------------|---------------|-------|
| **Total Portfolio Target Amount** | Target total portfolio value for % allocation calculations | ₹0 | Any positive number |
| **Large Cap Max %** | Maximum allowed allocation per Large Cap stock | 50% | 0-100% |
| **Mid Cap Max %** | Maximum allowed allocation per Mid Cap stock | 30% | 0-100% |
| **Small Cap Max %** | Maximum allowed allocation per Small Cap stock | 25% | 0-100% |
| **Micro Cap Max %** | Maximum allowed allocation per Micro Cap stock | 15% | 0-100% |
| **Maximum % per Sector** | Maximum allowed allocation for any single sector | 20% | 0-100% |

#### How These Settings Work

1. **Total Portfolio Amount**:
   - Used to calculate the "% of Total" column in Holdings view
   - Determines allocation percentages for each stock
   - Must be set in Settings (no longer editable from Portfolio page)

2. **Market Cap Allocation Limits**:
   - System checks if any market cap category exceeds its configured maximum
   - Triggers alerts on Recommendations page when limits are breached
   - Used by rebalancing engine to suggest portfolio adjustments
   - Each stock's allocation is color-coded based on these thresholds

3. **Sector Allocation Limit**:
   - Prevents over-concentration in any single sector
   - Recommendations page shows alert if any sector exceeds this limit
   - Helps maintain diversification across industries

#### Example Configuration

**Conservative Portfolio:**
- Large Cap: 50%
- Mid Cap: 30%
- Small Cap: 20%
- Micro Cap: 10%
- Sector Max: 20%

**Aggressive Portfolio:**
- Large Cap: 40%
- Mid Cap: 35%
- Small Cap: 30%
- Micro Cap: 20%
- Sector Max: 25%

#### Applying Changes

1. Navigate to **Settings** tab
2. Update desired values in **Portfolio Configuration** section
3. Click **Save Configuration**
4. System will reload to apply new thresholds
5. All calculations (rebalancing, alerts, color coding) will use your custom values

---

## Recommendations Page Organization

The Recommendations page is organized into **Alert Cards** at the top and **Detailed Sections** below.

### Alert Cards (Summary View)

Two main alert cards provide at-a-glance status:

#### 1. Price Zone Alerts Card
Shows count of stocks in or near your defined price zones:
- **Sell Alerts**: Holdings reaching sell zones
- **Average Alerts**: Holdings at averaging opportunities  
- **Buy Alerts**: Watching stocks at buy prices

#### 2. Rebalancing Alerts Card
Shows portfolio allocation issues:
- **Sector Alerts**: Number of over-allocated sectors (>max sector %)
- **Market Cap Alerts**: Number of over-allocated market cap categories

**Color Coding:**
- 🟢 **Green**: All balanced, no action needed
- 🟠 **Orange/Yellow**: Alerts present, review recommended

### Detailed Sections

#### Price Zone Alert Details
Expandable section showing:
- **In Buy Zone**: Watching stocks currently at buy prices
- **Near Buy Zone**: Watching stocks within 3% of buy zone
- **In Sell Zone**: Holdings at sell target prices
- **Near Sell Zone**: Holdings within 3% of sell zone  
- **In Average Zone**: Holdings at averaging price ranges
- **Near Average Zone**: Holdings approaching average zones

**Alert Logic:**
- **Buy Zones**: Only shown for WATCHING stocks (not holdings)
- **Sell/Average Zones**: Only shown for HOLDINGS (not watching stocks)

#### Rebalancing Details
Expandable accordions for:

1. **Stocks to Reduce**
   - Over-allocated individual stocks
   - Exceeds threshold + 0.5% green buffer
   - Table shows current vs target allocation

2. **Stocks to Add**
   - Under-allocated stocks
   - Below recommended threshold
   - Prioritizes stocks in buy zones

3. **Sector Rebalancing Insights**
   - Sectors exceeding max sector % (from Settings)
   - Over-allocated, balanced, or under-allocated status
   - Specific recommendations per sector

4. **Market Cap Rebalancing Insights**
   - Market cap categories exceeding thresholds (from Settings)
   - Uses your configured max % values
   - Shows excess allocation and reduction needed

---

## Recent Improvements

### December 2025: Data Protection & RAG Knowledge Base

- ✅ **Automatic daily backups** with smart date detection
- ✅ **Auto-cleanup** - keeps only last 5 backups
- ✅ **RAG Chatbot** for swing trading notes (see [KNOWLEDGE_BASE_README.md](../KNOWLEDGE_BASE_README.md))
- ✅ **PDF upload & indexing** with ChromaDB vector storage
- ✅ **LLM-powered organization** for scanned trading notes
- ✅ **Content synthesis** with local Ollama models
- ✅ **Book export** (HTML/PDF) for organized notes

### November 2025: Swing Trading Enhancement

- ✅ **Projected Portfolio Amount** with target date
- ✅ **Multi-step buy/sell tracking** (3 buy steps, 2 sell steps)
- ✅ **Parent sector grouping** with stock count limits
- ✅ **Three-tier market cap limits** (per-stock %, stock count, portfolio %)
- ✅ **Attention-sorted rebalancing** (red → yellow → green)
- ✅ **Enhanced market cap insights** with violation tracking
- ✅ **Parent sector management UI** in Analytics
- ✅ **Configurable stock limits** for all market caps
- ✅ **Max total stocks setting** to prevent over-diversification

### October 2025: Configuration Management

- ✅ Centralized portfolio settings in Settings page
- ✅ User-configurable allocation thresholds
- ✅ Removed redundant Total Portfolio Amount from Portfolio page
- ✅ All calculations dynamically use user-configured values

### Recommendations UI Overhaul
- ✅ Combined alert cards for better overview
- ✅ Equal-priority section headers
- ✅ Expandable detail sections for better organization
- ✅ Clear visual hierarchy

### Database Organization
- ✅ Consolidated to single database location (`instance/investment_manager.db`)
- ✅ No duplicate database files
- ✅ Proper Flask instance folder usage

### Alert Logic Improvements
- ✅ Buy zones only shown for watching stocks
- ✅ Sell/average zones only for holdings
- ✅ Dynamic threshold checking based on user settings
- ✅ Proper status indicators (overweight/balanced/underweight)

---

*Last Updated: November 29, 2025*

