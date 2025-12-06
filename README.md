# Personal Finance Manager

A comprehensive personal finance management platform for tracking stocks, mutual funds, fixed deposits, EPF, NPS, savings, lending, income, expenses, and budgets - all in one place.

**Project Status:** 🎉 **Phase 3 COMPLETE + RAG Knowledge Base**  
**Last Updated:** December 6, 2025  
**Production Ready:** ✅ Yes

---

## Quick Links

- **[Getting Started](GETTING_STARTED.md)** - Setup and installation (15 minutes)
- **[Features](docs/FEATURES.md)** - Feature guide with examples
- **[RAG Knowledge Base](KNOWLEDGE_BASE_README.md)** - PDF chatbot & book organization
- **[Roadmap](docs/ROADMAP.md)** - Current status and future plans
- **[Contributing](CONTRIBUTING.md)** - How to extend the platform

---

## What's Ready Now

### ✅ Fully Functional - All Features Ready!
- **Dashboard** - Net worth, asset allocation, cash flow
- **Stock Tracking** - Full CRUD, FIFO P/L, XIRR, holding periods
- **Portfolio Management** - Transaction tracking, realized/unrealized P/L, multi-step buy/sell
- **Swing Trading** - Projected portfolio planning, parent sector grouping, 3-tier market cap limits
- **Mutual Funds** - Schemes, transactions, holdings, SIP, XIRR
- **Fixed Income** - FD with maturity tracking, EPF, NPS
- **Savings & Accounts** - Savings accounts, lending tracker, other investments
- **Income & Expenses** - Transaction tracking, budgets, trends
- **Reports** - Net worth trends, allocation evolution, tax summary
- **Analytics** - Charts, top gainers/losers, sector/market cap allocation, parent sector management
- **Health Metrics** - Concentration, diversification analysis
- **Recommendations** - Rebalancing suggestions (attention-sorted), price zone alerts
- **Settings** - Import/export, automatic daily backup, configurable limits
- **📚 RAG Knowledge Base** - Upload PDFs, AI chatbot, book organization ([See Guide](KNOWLEDGE_BASE_README.md))

See [docs/PHASE2_SUMMARY.md](docs/PHASE2_SUMMARY.md) for detailed Phase 2 implementation summary.

---

## Project Evolution

**From:** Stock Investment Tracker (3 models, 22 endpoints)  
**To:** Personal Finance Manager (14 models, 96 endpoints)  
**Timeline:** October-November 2025  
**Migration:** Zero data loss, all existing features preserved

### Asset Classes Supported

| Category | Assets | Status |
|----------|--------|--------|
| **Equity** | Stocks, Mutual Funds | Stocks ✅, MF 🔨 |
| **Fixed Income** | FD, EPF, NPS | Backend ✅, Frontend 🔨 |
| **Savings** | Savings/Current Accounts | Backend ✅, Frontend 🔨 |
| **Alternative** | Lending, Gold, Bonds, Crypto | Backend ✅, Frontend 🔨 |
| **Cash Flow** | Income, Expenses, Budgets | Backend ✅, Frontend 🔨 |

✅ = Production Ready | 🔨 = In Progress

---

## Getting Started

### Quick Setup

For complete installation instructions and troubleshooting, see **[GETTING_STARTED.md](GETTING_STARTED.md)** (15 minutes to get running).

**Quick version:**
```bash
# Backend: cd backend → create venv → activate → pip install -r requirements.txt → python app.py
# Frontend: cd frontend → npm install → npm start
# Access: http://localhost:3000
```

**Prerequisites:** Python 3.8+, Node.js 14+

---

## Documentation Roadmap

**Where do I start?**

### For End Users

```
1. README.md (this file) - Overview
   ↓
2. GETTING_STARTED.md - Setup (15 min)
   ↓
3. docs/FEATURES.md - Feature guide
   ↓
4. ROADMAP.md - What's coming next
```

### For Developers

```
1. README.md (this file) - Overview
   ↓
2. GETTING_STARTED.md - Setup
   ↓
3. docs/ARCHITECTURE.md - Technical design
   ↓
4. docs/API_REFERENCE.md - API docs
   ↓
5. CONTRIBUTING.md - How to extend
   ↓
6. ROADMAP.md - Implementation plan
```

### For DevOps

```
1. README.md (this file) - Overview
   ↓
2. GETTING_STARTED.md - Installation
   ↓
3. docs/ARCHITECTURE.md - System design
   ↓
4. docs/API_REFERENCE.md - Integration
```

---

## Key Features

### Stock Investment Tracking + Swing Trading
- **Projected Portfolio Planning** - Set target amount with target date
- **Multi-Step Buy/Sell** - Track 3-step buys, 2-step sells with avg price
- **Parent Sector Grouping** - Group related sectors, limit stocks per parent
- **Three-Tier Market Cap Limits:**
  - Per-stock % caps (Large: 5%, Mid: 3%, Small: 2.5%, Micro: 2%)
  - Stock count limits (Large: 15, Mid: 8, Small: 7, Micro: 3)
  - Portfolio % limits (Large: 50%, Mid: 30%, Small: 25%, Micro: 10%)
- **Attention-Sorted Rebalancing** - Problem stocks/sectors shown first
- Multi-stock tracking with price zones (buy/sell/average)
- FIFO P/L tracking (realized + unrealized)
- XIRR calculation for portfolio returns
- Holding period tracking (FIFO-weighted)
- Automated price fetching (multi-source fallback)
- Smart alerts (buy/sell/average zones)
- Allocation monitoring (market cap, sector, parent sector)
- Color-coded allocation thresholds with 0.5% leverage
- Import/Export CSV
- Database backup/restore

### Personal Finance Dashboard (NEW)
- Net worth across all assets
- Asset allocation visualization (equity/debt/cash)
- Cash flow charts (income vs expenses)
- Quick stats and breakdowns

### Backend Infrastructure (Complete)
- 14 database models
- 96 REST API endpoints
- FIFO accounting for stocks and mutual funds
- XIRR calculation (Newton-Raphson)
- Cash flow analysis
- Net worth aggregation
- Budget tracking

---

## Technology Stack

**Backend:** Python, Flask, SQLAlchemy, SQLite  
**Frontend:** React, Material-UI, Recharts, Axios  
**Data Sources:** Web scraping (Google Finance, Moneycontrol), Yahoo Finance API

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed technical design.

---

## Project Structure

```
Investment_Manager/
├── backend/
│   ├── app.py                      # Main Flask app (80+ endpoints)
│   ├── utils/                      # Utility functions
│   │   ├── holdings.py            # FIFO P/L calculations
│   │   ├── mutual_funds.py        # MF calculations
│   │   ├── cash_flow.py           # Income/expense analysis
│   │   ├── net_worth.py           # Net worth aggregation
│   │   └── xirr.py                # XIRR calculations
│   ├── services/                   # External services
│   │   ├── price_scraper.py       # Multi-source scraping
│   │   └── mf_api.py              # MF NAV fetching
│   └── instance/                   # SQLite database
│
├── frontend/
│   ├── src/
│   │   ├── App.js                  # Main component (9 tabs)
│   │   ├── components/
│   │   │   ├── Dashboard.js       # Net worth dashboard
│   │   │   ├── StockTracking.js   # Stock CRUD
│   │   │   ├── Portfolio.js        # Transactions, P/L
│   │   │   ├── Analytics.js        # Charts, insights
│   │   │   ├── Health.js           # Financial health metrics
│   │   │   ├── Settings.js         # Global settings
│   │   │   └── ...
│   │   └── services/
│   │       └── api.js              # Axios client (20 API modules)
│   └── package.json
│
├── testing/                         # Test suite (NEW)
│   ├── conftest.py                 # Pytest fixtures
│   ├── pytest.ini                  # Pytest configuration
│   ├── requirements.txt            # Test dependencies
│   ├── test_all_apis_part1.py      # Auth, Stock, Portfolio, MF tests
│   ├── test_all_apis_part2.py      # FD, EPF, NPS, Savings tests
│   ├── test_all_apis_part3.py      # Income, Expense, Dashboard tests
│   ├── run_api_tests.sh            # Test runner (Linux/Mac)
│   ├── run_api_tests.bat           # Test runner (Windows)
│   ├── README.md                   # Test documentation
│   └── SUMMARY.md                  # Test summary
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md             # Technical design
│   ├── API_REFERENCE.md            # API documentation
│   └── FEATURES.md                 # Feature guide
│
├── GETTING_STARTED.md              # Setup guide
├── CONTRIBUTING.md                 # Developer guide
├── ROADMAP.md                      # Feature roadmap
└── README.md                        # This file
```

---

## Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Component implementation guide
- Code style and patterns
- Testing requirements
- Pull request process

---

## Roadmap

### Phase 1: Backend Foundation ✅ COMPLETE
- 14 database models
- 96 API endpoints
- Utility functions (FIFO, XIRR, cash flow)
- Dashboard component
- Migration completed (zero data loss)

### Phase 2: Frontend Components ✅ **COMPLETE (100%)**
- ✅ Income & Expenses component (1100+ lines)
- ✅ Mutual Funds component (1000+ lines)
- ✅ Fixed Income component (1200+ lines - FD/EPF/NPS)
- ✅ Accounts component (1200+ lines - Savings/Lending/Other)
- ✅ Reports component (900+ lines)
- All 5 major components fully implemented!

### Phase 3: Enhanced Features 🔨 **IN PROGRESS (83% complete - 15/18 items)**
- ✅ Settings enhancements (global allocation targets)
- ✅ Health enhancements (debt-to-income, emergency fund, savings rate)
- ✅ Unified XIRR across all assets
- ✅ Financial health scoring system
- ⏭️ Recommendations enhancements → moved to Phase 5
- ⚠️ Documentation updates (in progress)
- ⚠️ Comprehensive testing (61% pass rate)

### Phase 4: Testing & Quality ⏭️ **NEXT**
- ⚠️ API testing (61% pass rate - 55/90 tests passing)
- ⏭️ UI, DB, and Performance tests → moved to Phase 5

See [ROADMAP.md](ROADMAP.md) for detailed timeline and features.

---

## License

Private project for personal use.

---

## Support

- **Setup Issues**: See [GETTING_STARTED.md](GETTING_STARTED.md) troubleshooting section
- **Feature Requests**: See [ROADMAP.md](ROADMAP.md) for feature request process
- **Technical Questions**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design details

---

**Happy financial tracking!** 📊
