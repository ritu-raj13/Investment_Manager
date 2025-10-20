# Future Features & Roadmap

This document contains **planned features** for the Investment Manager application, organized by priority and implementation complexity.

**Note:** Implemented features are documented in `README.md`. This file only tracks future enhancements.

## 📚 Related Documentation
- **[README.md](README.md)** - Current features and usage guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical architecture (for implementation guidance)
- **[API_REFERENCE.md](API_REFERENCE.md)** - API documentation

---

## 🎯 High Priority Features

### 1. Historical Tracking ⭐⭐⭐⭐
**Priority:** MEDIUM | **Effort:** Medium

**Features:**
- 📅 Price history for each stock (store daily snapshots)
- 📈 Line chart showing price movement over time
- 🕐 Timeline of status changes (when did it enter buy zone?)
- 📊 Zone performance tracking (success rate of zones)

**Implementation:**
- New table: `price_history` (stock_id, price, date)
- Store snapshot on each refresh
- Chart component for price trends
- Historical trend analysis

**Status:** 📋 PLANNED

---

---

## 🚀 Medium Priority Features

### 3. Transaction Insights ⭐⭐⭐⭐
**Priority:** MEDIUM | **Effort:** Medium

**Features:**
- 📊 Win rate (profitable trades %)
- 💰 Average holding period
- 📈 Best/worst trades
- 🧮 Realized vs. unrealized gains
- 📅 Monthly P&L breakdown
- 🎯 Actual buy vs. planned zone (discipline tracker)

**Implementation:**
- Backend: Analytics calculations
- Frontend: Insights dashboard
- Closed positions tracking

**Status:** 📋 PLANNED

---

### 4. Tax Calculation ⭐⭐⭐⭐
**Priority:** MEDIUM | **Effort:** Medium

**Features:**
- 🏦 Automatic STCG/LTCG calculation (equity: <1 yr vs >1 yr)
- 💸 Tax liability estimate (15% STCG, 10% LTCG above ₹1L)
- 📊 Year-wise tax report
- 📄 Export for CA/tax filing

**Implementation:**
- Calculate holding period per transaction
- Apply Indian tax rules (STCG/LTCG)
- Generate tax report with breakdowns

**Status:** 📋 PLANNED

---

### 5. Dividend & Corporate Actions ⭐⭐⭐
**Priority:** LOW | **Effort:** Medium

**Features:**
- 💵 Dividend received tracking
- 📈 Stock splits/bonus adjustments
- 🎁 Total dividend income (yearly/monthly)
- 📊 Dividend yield calculation

**Implementation:**
- New table: `dividends` (stock_id, amount, date)
- Manual entry form
- Corporate actions adjustments

**Status:** 📋 PLANNED

---


## 🔬 Advanced Features

### 7. Technical Indicators ⭐⭐⭐
**Priority:** LOW | **Effort:** High

**Features:**
- 📊 RSI (Relative Strength Index)
- 📈 Moving averages (50-day, 200-day)
- 📉 Support/resistance levels
- 🔔 Breakout alerts

**Implementation:**
- Fetch historical data (yfinance)
- Calculate indicators (TA-Lib or custom)
- Display on stock cards
- Alert when conditions met

**Status:** 📋 FUTURE

---

### 8. Multi-User Support ⭐⭐
**Priority:** LOW | **Effort:** High

**Features:**
- 🔐 User authentication (login/signup)
- 👤 Multiple portfolios per user
- 🔒 Data isolation
- 🌐 Cloud deployment ready

**Implementation:**
- User authentication system (Flask-Login or JWT)
- User-specific data queries
- Password hashing (bcrypt)
- Session management

**Status:** 📋 FUTURE

---

### 9. Mobile App ⭐⭐⭐
**Priority:** LOW | **Effort:** Very High

**Features:**
- 📱 React Native mobile app
- 🔔 Push notifications
- 📊 Quick portfolio view
- 💹 Add transactions on-the-go

**Implementation:**
- React Native app
- REST API (already exists!)
- Mobile-optimized UI

**Status:** 📋 FUTURE

---

### 10. Integration with Brokers ⭐⭐⭐⭐
**Priority:** MEDIUM | **Effort:** Very High

**Features:**
- 🔗 Auto-sync transactions from broker
- 📊 Real-time portfolio updates
- 💰 Fetch actual holdings
- 📈 Compare planned vs. actual trades

**Implementation:**
- Zerodha Kite API integration
- Upstox API integration
- Background sync scheduler

**Status:** 📋 FUTURE (Complex - API access required)

---

## 📋 Implementation Notes

### Phase 1 (Completed ✅)

**Core Features:**
- ✅ Stock Tracking with buy/sell/average zones (supports ranges)
- ✅ Portfolio Management with P&L tracking
- ✅ Analytics Dashboard with interactive charts (Recharts)
- ✅ Smart Alerts (6 types: in/near buy/sell/average zones, holdings-aware)
- ✅ Automated price fetching (multi-source with fallbacks)
- ✅ Auto-fetch stock details (name, price, day change %) on symbol entry

**Data Management:**
- ✅ CSV Import/Export (stocks & transactions)
- ✅ Database Backup/Restore (full .db file)
- ✅ Universal database migrator (version-aware schema updates)

**UI/UX Enhancements:**
- ✅ Dark mode theme (default)
- ✅ Sticky navigation bar
- ✅ Back-to-top FAB (floating action button)
- ✅ Search & filtering across all pages
- ✅ Expand/collapse all groups (stock tracking)
- ✅ Sortable tables (holdings)
- ✅ Clear chart tooltips (dark theme compatible)

**Advanced Features:**
- ✅ 1D Change % (per stock and portfolio-level weighted average)
- ✅ Top 5 Gainers/Losers (filtered by positive/negative returns)
- ✅ % of Total Investment (stock-wise allocation with manual total amount)
- ✅ Autocomplete for Group & Sector (learns from existing data)
- ✅ One-click Refresh Alert Stocks (auto-detects alert stocks)
- ✅ Transaction validation (client + server side)

**Code Quality:**
- ✅ Modular architecture (utils.py with shared functions)
- ✅ DRY principle (no duplicate code for parse_zone, calculate_holdings, etc.)
- ✅ Comprehensive documentation (Architecture, API Reference)
- ✅ Type hints and docstrings

### Phase 2 (Next - Priority Order)
1. **Historical Tracking** - Foundation for trends
2. **Target Price Alerts** - High value, needs scheduler
3. **Transaction Insights** - Enhanced portfolio analytics

### Phase 3 (Later)
- Tax Calculation (STCG/LTCG)
- Dividend Tracking
- Technical Indicators
- Automated Reports

### Phase 4 (Future Scope)
- Multi-user support
- Mobile app
- Broker integrations

---

## 💡 Contribution Ideas

Want to contribute? Pick any **📋 PLANNED** feature and:
1. Create a new branch
2. Implement the feature
3. Test thoroughly
4. Submit a pull request

**Easy starters:**
- Export to CSV (Feature #1)
- Preset filters (Feature #3)
- Top 5 gainers/losers (Feature #8)

**Complex challenges:**
- Historical tracking (Feature #2)
- Target price alerts (Feature #4)
- Technical indicators (Feature #9)

---

## 📝 Feature Request Process

1. Check if feature already listed
2. Open an issue with:
   - Clear description
   - Use case / benefit
   - Priority suggestion
3. Maintainer will review and add to roadmap

---

**Last Updated:** October 2025
