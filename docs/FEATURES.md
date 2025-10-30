# Investment Manager - Feature Documentation

**Last Updated:** October 30, 2025

## Table of Contents
- [Portfolio Management](#portfolio-management)
- [Profit & Loss Tracking](#profit--loss-tracking)
- [Advanced Portfolio Metrics](#advanced-portfolio-metrics)
  - [FIFO-Based Holding Period](#fifo-based-holding-period-tracking)
  - [XIRR Calculation](#xirr-extended-internal-rate-of-return)
- [Portfolio Allocation Color Coding](#portfolio-allocation-color-coding)
- [Analytics Dashboard](#analytics-dashboard)
- [Stock Tracking](#stock-tracking)
- [Alert System](#alert-system)
- [FAQs](#faqs)

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

### Action Items
- Stocks requiring attention based on price zones
- Categories:
  - **In Buy Zone**: Stocks at or below target buy price
  - **In Sell Zone**: Stocks at or above target sell price
  - **Near Buy Zone**: Within ±3% of buy price
  - **Near Sell Zone**: Within ±3% of sell price

### Pie Charts

#### Sector Allocation
- Visual breakdown of portfolio by sector
- **Hover Tooltip Shows**:
  - Sector name
  - Total invested amount
  - **Number of stocks** in that sector

#### Market Cap Allocation
- Visual breakdown by market capitalization
- **Hover Tooltip Shows**:
  - Market cap category (Large/Mid/Small/Micro)
  - Total invested amount
  - **Number of stocks** in that category

### Top Performers
- **Top Gainers**: Stocks with highest returns
- **Top Losers**: Stocks with lowest returns
- Shows symbol, name, and return percentage

---

## Stock Tracking

### Features
- Add stocks with buy/sell/average price zones
- Flexible price ranges (e.g., "250-300" or "250")
- Symbol normalization (handles .NS/.BO suffixes automatically)
- Real-time price updates
- Status tracking (BUY, SELL, HOLD, WATCHING)

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
- Analytics page highlights actionable stocks

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
- Removed redundant statistics (moved to Portfolio page)
- Enhanced tooltips with stock counts
- Clean, focused layout on actionable insights
- Visual charts for quick portfolio analysis

---

## Data Persistence

### Database Schema
- SQLite (development) / PostgreSQL (production)
- Automatic schema migrations
- Transaction history preservation
- Price update tracking

### Backup & Export
- CSV export functionality
- Transaction history export
- Database backup tools included

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

*Last Updated: October 30, 2025*

