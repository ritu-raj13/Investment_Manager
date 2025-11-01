# Personal Finance Manager - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Platform Transformation](#platform-transformation)
3. [Technology Stack](#technology-stack)
4. [Module Organization](#module-organization)
5. [Backend Architecture](#backend-architecture)
6. [Frontend Architecture](#frontend-architecture)
7. [Database Schema](#database-schema)
8. [Data Flow](#data-flow)
9. [Key Design Decisions](#key-design-decisions)
10. [Performance & Security](#performance--security)

---

## System Overview

Personal Finance Manager is a **full-stack web application** evolved from a stock tracker to comprehensive financial management. Track stocks, mutual funds, fixed deposits, EPF, NPS, savings, lending, income, expenses, and budgets - all in one place.

### Architecture Pattern
- **Pattern**: Client-Server Architecture with RESTful API
- **Frontend**: React SPA (Single Page Application)
- **Backend**: Flask REST API
- **Database**: SQLite (file-based, embedded)
- **Communication**: HTTP/JSON over localhost

### Design Principles
1. **Separation of Concerns**: Clear boundaries between UI, business logic, and data
2. **RESTful API**: Stateless communication with standard HTTP methods
3. **Single Responsibility**: Each module has one clear purpose
4. **Fail-Safe Design**: Multiple fallback sources for external data
5. **Data Integrity**: Server-side validation for all transactions
6. **FIFO Accounting**: Tax-compliant P/L tracking (India)

---

## Platform Transformation

**Date:** October-November 2025  
**Status:** Phase 1 Complete (Backend + Core Frontend)

### From: Stock Investment Tracker
- Single asset type (Indian equities)
- 22 API endpoints
- 3 database models
- Basic P/L tracking

### To: Personal Finance Manager
- **8 asset types** (Stocks, MF, FD, EPF, NPS, Savings, Lending, Other)
- **70+ API endpoints** (3x expansion)
- **14 database models** (4.5x expansion)
- **Comprehensive tracking** (net worth, cash flow, budgets, XIRR)

### What Changed

#### Database Expansion (+11 models)
```
Original Models (3):
- Stock
- PortfolioTransaction
- PortfolioSettings

Added Models (11):
- MutualFund, MutualFundTransaction
- FixedDeposit
- EPFAccount, EPFContribution
- NPSAccount, NPSContribution
- SavingsAccount, SavingsTransaction
- LendingRecord
- OtherInvestment
- IncomeTransaction, ExpenseTransaction
- Budget
- GlobalSettings
```

#### API Expansion (+48 endpoints)

| Category | Endpoints | Status |
|----------|-----------|--------|
| Stocks (original) | 22 | ✅ Production |
| Mutual Funds | 10 | ✅ Ready |
| Fixed Income (FD/EPF/NPS) | 16 | ✅ Ready |
| Savings & Lending | 10 | ✅ Ready |
| Income & Expenses | 13 | ✅ Ready |
| Budgets | 5 | ✅ Ready |
| Dashboard | 4 | ✅ Ready |
| **Total** | **80** | **All Functional** |

#### Frontend Evolution

```
Before (6 tabs):          After (9 tabs):
1. Stock Tracking    →    1. Dashboard (NEW)
2. Portfolio         →    2. Stocks
3. Analytics         →    3. Mutual Funds (NEW)
4. Health            →    4. Fixed Income (NEW)
5. Recommendations   →    5. Accounts (NEW)
6. Settings          →    6. Income & Expenses (NEW)
                           7. Reports (NEW)
                           8. Health
                           9. Settings
```

### Migration Success
- ✅ Zero data loss (all 35 stocks, 23 transactions preserved)
- ✅ Backward compatible (existing features work)
- ✅ Production-ready backend
- ✅ Comprehensive documentation

See [ROADMAP.md](../ROADMAP.md) for implementation timeline.

---

## Technology Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Core language |
| **Flask** | 3.0.0 | Web framework & REST API |
| **Flask-CORS** | 4.0.0 | Cross-origin requests |
| **Flask-SQLAlchemy** | 3.1.1 | ORM for database |
| **SQLAlchemy** | 2.0.44 | Database toolkit |
| **SQLite** | 3.x | Embedded database |
| **BeautifulSoup4** | 4.14.2 | Web scraping |
| **lxml** | 6.0.2 | HTML/XML parser |
| **Requests** | 2.32.5 | HTTP client |
| **yfinance** | 0.2.32 | Yahoo Finance API (fallback) |
| **Pandas** | 2.3.3 | CSV import/export |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI framework |
| **Material-UI (MUI)** | 5.x | Component library |
| **Axios** | Latest | HTTP client |
| **Recharts** | 2.x | Data visualization |

---

## Module Organization

### Project Structure

```
Investment_Manager/
├── backend/
│   ├── app.py                      # Main Flask application
│   ├── config/                     # Environment configurations
│   │   ├── __init__.py            # Config loader
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Dev (SQLite)
│   │   └── production.py          # Prod (PostgreSQL)
│   ├── utils/                      # Utility modules
│   │   ├── holdings.py            # P/L calculations (FIFO)
│   │   ├── mutual_funds.py        # MF calculations (NEW)
│   │   ├── cash_flow.py           # Income/expense analysis (NEW)
│   │   ├── net_worth.py           # Net worth aggregation (NEW)
│   │   ├── xirr.py                # XIRR calculation (NEW)
│   │   ├── zones.py               # Price zone logic
│   │   └── helpers.py             # General utilities
│   ├── services/                   # External services
│   │   ├── price_scraper.py       # Multi-source scraping
│   │   ├── mf_api.py              # MF NAV fetching (NEW)
│   │   └── nse_api.py             # NSE API client
│   ├── migrations/                 # DB migrations
│   │   ├── migrate_to_personal_finance.py  # Main migration (NEW)
│   │   └── db_migrator.py         # Universal migrator
│   ├── instance/                   # SQLite database (dev)
│   └── requirements.txt            # Dependencies
│
├── frontend/
│   ├── src/
│   │   ├── App.js                  # Main component (9 tabs)
│   │   ├── components/
│   │   │   ├── Dashboard.js       # Net worth dashboard (NEW)
│   │   │   ├── StockTracking.js   # Stock CRUD
│   │   │   ├── Portfolio.js        # Transactions, P/L
│   │   │   ├── Analytics.js        # Charts, insights
│   │   │   ├── Health.js           # Portfolio health
│   │   │   ├── Recommendations.js  # Rebalancing
│   │   │   ├── Settings.js         # Import/export, backup
│   │   │   └── Login.js            # Authentication
│   │   └── services/
│   │       └── api.js              # Axios client (20 API modules)
│   └── package.json
│
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md             # This file
│   ├── API_REFERENCE.md            # API docs
│   └── FEATURES.md                 # Feature guide
│
├── GETTING_STARTED.md              # Setup guide
├── CONTRIBUTING.md                 # Developer guide
├── ROADMAP.md                      # Feature roadmap
└── README.md                        # Entry point
```

### Backend Module Responsibilities

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `utils/holdings.py` | Stock P/L (FIFO) | `calculate_holdings()`, `calculate_holding_period_days()` |
| `utils/mutual_funds.py` | MF tracking (FIFO) | `calculate_mf_holdings()`, `calculate_mf_xirr()` |
| `utils/cash_flow.py` | Income/expense | `calculate_monthly_cash_flow()`, `get_expense_trends()` |
| `utils/net_worth.py` | Portfolio aggregation | `calculate_total_net_worth()`, `get_asset_allocation()` |
| `utils/xirr.py` | Returns calculation | `xirr()`, `calculate_portfolio_xirr()` |
| `services/price_scraper.py` | Stock prices | `get_scraped_price()`, multi-source fallback |
| `services/mf_api.py` | MF NAVs | `fetch_mf_nav()`, `fetch_all_mf_navs()` |

### Frontend API Service Modules

All in `frontend/src/services/api.js`:

```javascript
export const stockAPI = { ... }            // 8 endpoints
export const portfolioAPI = { ... }        // 7 endpoints
export const mutualFundsAPI = { ... }      // 10 endpoints
export const fixedDepositsAPI = { ... }    // 6 endpoints
export const epfAPI = { ... }              // 5 endpoints
export const npsAPI = { ... }              // 5 endpoints
export const savingsAPI = { ... }          // 6 endpoints
export const lendingAPI = { ... }          // 4 endpoints
export const otherInvestmentsAPI = { ... } // 4 endpoints
export const incomeAPI = { ... }           // 6 endpoints
export const expensesAPI = { ... }         // 7 endpoints
export const budgetsAPI = { ... }          // 5 endpoints
export const dashboardAPI = { ... }        // 4 endpoints
export const globalSettingsAPI = { ... }   // 2 endpoints
```

---

## Backend Architecture

### Module Structure

```
backend/
├── app.py                      # Main Flask application & API routes
├── config/                     # Environment-specific configurations
│   ├── __init__.py            # Config loader (auto-detects env)
│   ├── base.py                # Base configuration (shared)
│   ├── development.py         # Development settings (SQLite)
│   └── production.py          # Production settings (PostgreSQL)
├── utils/                      # Utility functions (organized by purpose)
│   ├── __init__.py
│   ├── auth.py                # Authentication (Flask-Login setup)
│   ├── validation.py          # Data validation
│   ├── zones.py               # Zone calculations
│   ├── holdings.py            # Holdings & P/L calculations
│   └── helpers.py             # General helpers
├── services/                   # External services
│   ├── __init__.py
│   ├── price_scraper.py       # Multi-source web scraper
│   └── nse_api.py             # NSE India API client
├── migrations/                 # Database migrations
│   ├── db_migrator.py         # SQLite schema migrations
│   └── migrate_to_postgres.py # SQLite to PostgreSQL migration
├── instance/                   # SQLite database (development)
├── requirements.txt            # Python dependencies
└── venv/                       # Virtual environment
```

### Core Modules

#### 1. **app.py** - Main Application
- **Flask app initialization** with CORS, Flask-Login, Rate Limiter
- **Database models** (Stock, PortfolioTransaction, PortfolioSettings, User)
- **API routes** (25+ endpoints organized by feature)
- **Authentication** endpoints (login, logout, check)
- **Business logic** for portfolio calculations, P/L tracking, and analytics

#### 2. **config/** - Configuration Management
**Modules:**
- `base.py` - Shared configuration (SECRET_KEY, DEBUG, CORS, etc.)
- `development.py` - SQLite, local development settings
- `production.py` - PostgreSQL, cloud deployment settings
- Auto-detection via `FLASK_ENV` environment variable

**Why:** Clean separation of dev/prod configuration, environment-based switching

#### 3. **utils/** - Shared Utilities (Organized Package)

**Core Modules:**
- `holdings.py` - Stock P/L calculations with FIFO lot tracking
- `mutual_funds.py` - MF holdings, XIRR, allocation (NEW)
- `cash_flow.py` - Income/expense analysis, trends (NEW)
- `net_worth.py` - Portfolio aggregation, asset allocation (NEW)
- `xirr.py` - XIRR calculation (Newton-Raphson method) (NEW)
- `zones.py` - Price zone parsing and logic
- `helpers.py` - Symbol normalization, formatting
- `validation.py` - Input validation
- `auth.py` - Authentication helpers

**Why:** Modular organization, eliminates code duplication, clear responsibilities

**Key Algorithm - FIFO Lot Tracking:**
```python
from collections import deque

def calculate_holdings(transactions):
    holdings = {}
    for t in sorted(transactions, key=lambda x: x.transaction_date):
        if t.transaction_type == 'BUY':
            lots_queue.append({'qty': t.quantity, 'price': t.price_per_unit})
            invested_amount += t.quantity * t.price_per_unit
        elif t.transaction_type == 'SELL':
            remaining_qty = t.quantity
            while remaining_qty > 0 and lots_queue:
                lot = lots_queue[0]
                consumed = min(remaining_qty, lot['qty'])
                realized_pnl += consumed * (t.price_per_unit - lot['price'])
                invested_amount -= consumed * lot['price']  # Remove cost basis
                # ... continue FIFO consumption
    return holdings
```

#### 4. **services/** - External Services
**Modules:**
- `price_scraper.py` - Multi-source scraping with fallbacks
- `nse_api.py` - NSE India API client

**PriceScraper Features:**
- Multi-source scraping with fallbacks
- Robust price extraction using regex patterns
- Browser-like headers to avoid blocking

**Scraping Sources (in order):**
1. **Google Finance** - Primary (reliable, fast)
2. **Moneycontrol** - Fallback #1
3. **Investing.com** - Fallback #2
4. **Screener.in** - OPTIONAL for name & day change % only (NOT for price)

**Public API:**
- `get_scraped_price(symbol)` - Get price only (reliable)
- `get_stock_details(symbol)` - Get price + name + day_change_pct

#### 4. **nse_api.py** - NSE India API Client
- Direct API calls to NSE India
- Used as fallback when web scraping fails
- Often blocked/rate-limited (hence fallback only)

#### 5. **db_migrator.py** - Database Migrations
- Universal migration tool
- Automatically detects and applies schema changes
- Creates backups before migration
- Version-aware (checks existing columns before adding)

### API Endpoint Organization

**Stock Tracking** (8 endpoints)
- CRUD operations for stocks
- Price refresh (all/alert stocks)
- Auto-fetch stock details
- Groups & sectors lists

**Portfolio Management** (7 endpoints)
- Transaction CRUD
- Portfolio summary with P&L
- Settings (manual total amount)

**Analytics** (1 endpoint)
- Dashboard with metrics, action items, charts data, top gainers/losers

**Data Management** (6 endpoints)
- CSV import/export (stocks & transactions)
- Database backup/restore

---

## Frontend Architecture

### Component Structure

```
frontend/src/
├── App.js                      # Root component & routing
├── index.js                    # React entry point
├── components/
│   ├── StockTracking.js        # Stock management page
│   ├── Portfolio.js            # Portfolio & transactions page
│   ├── Analytics.js            # Analytics dashboard page
│   └── Settings.js             # Data management page
└── services/
    └── api.js                  # Axios API client (centralized)
```

### Component Hierarchy

```
App (MUI Theme + Tabs)
├── StockTracking
│   ├── Search & Filter Bar
│   ├── Add Stock Dialog (Autocomplete for Group/Sector)
│   ├── Refresh Buttons (All / Alert Stocks)
│   ├── Expand/Collapse All
│   └── Stock Cards (Grouped & Collapsible)
│
├── Portfolio
│   ├── Manual Total Amount Editor
│   ├── Portfolio Summary Cards (5 metrics)
│   ├── Current Holdings Table (sortable, % allocation)
│   └── Transaction History Table (searchable)
│
├── Analytics
│   ├── Action Items Card
│   ├── Top Gainers/Losers
│   ├── Charts (Portfolio Value, Sector, Market Cap)
│   └── Insights
│
└── Settings
    ├── CSV Import/Export
    └── Database Backup/Restore
```

### Key Frontend Patterns

#### 1. **Centralized API Client** (`api.js`)
- All HTTP requests go through this module
- Organized by feature (stockAPI, portfolioAPI, analyticsAPI, dataAPI)
- Consistent error handling
- Base URL configuration

#### 2. **Material-UI Component Library**
- Cards, Dialogs, Tables, Chips, Buttons
- Dark theme by default
- Responsive design with Grid system

#### 3. **State Management**
- Local component state (useState)
- useEffect for data fetching on mount
- No global state library (not needed for this app size)

#### 4. **Form Validation**
- Client-side validation for immediate feedback
- Server-side validation as final authority
- Error messages displayed via Snackbar notifications

---

## Database Schema

### Tables

#### 1. **stocks** - Stock Tracking
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| symbol | VARCHAR(20) | UNIQUE, NOT NULL | Stock symbol (e.g., RELIANCE.NS) |
| name | VARCHAR(100) | NOT NULL | Company name |
| group_name | VARCHAR(50) | NULL | Pattern/strategy group |
| sector | VARCHAR(100) | NULL | Industry sector |
| market_cap | VARCHAR(20) | NULL | Large/Mid/Small/Micro |
| buy_zone_price | VARCHAR(50) | NULL | Buy zone (supports ranges: "250-300") |
| sell_zone_price | VARCHAR(50) | NULL | Sell zone |
| average_zone_price | VARCHAR(50) | NULL | Average zone |
| status | VARCHAR(20) | NULL | WATCHING / HOLD |
| current_price | FLOAT | NULL | Last fetched price |
| day_change_pct | FLOAT | NULL | 1-day change percentage |
| last_updated | DATETIME | NULL | Last price update timestamp |
| notes | TEXT | NULL | Analysis notes |

#### 2. **portfolio_transactions** - Buy/Sell History
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| stock_symbol | VARCHAR(20) | NOT NULL | Stock symbol |
| stock_name | VARCHAR(100) | NOT NULL | Company name |
| transaction_type | VARCHAR(10) | NOT NULL | BUY or SELL |
| quantity | FLOAT | NOT NULL | Number of shares |
| price | FLOAT | NOT NULL | Price per share |
| transaction_date | DATETIME | NOT NULL | Date of transaction |
| reason | TEXT | NULL | Trade reason/strategy |
| notes | TEXT | NULL | Additional notes |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

#### 3. **portfolio_settings** - Stock Portfolio Preferences
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Always 1 (single row table) |
| total_amount | FLOAT | DEFAULT 0.0 | Manual total portfolio amount for % calculation |
| max_large_cap_pct | FLOAT | DEFAULT 5.5 | Max allocation % for large cap |
| max_mid_cap_pct | FLOAT | DEFAULT 3.5 | Max allocation % for mid cap |
| max_small_cap_pct | FLOAT | DEFAULT 2.5 | Max allocation % for small/micro cap |
| updated_at | DATETIME | NULL | Last update timestamp |

### New Tables (Personal Finance Transformation)

#### 4. **mutual_funds** - Mutual Fund Schemes
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| scheme_code | VARCHAR(20) | UNIQUE | AMFI scheme code |
| scheme_name | VARCHAR(200) | NOT NULL | Full scheme name |
| fund_house | VARCHAR(100) | NULL | AMC name |
| category | VARCHAR(50) | NULL | Equity/Debt/Hybrid |
| sub_category | VARCHAR(100) | NULL | Large Cap, ELSS, etc. |
| current_nav | FLOAT | NULL | Latest NAV |
| day_change_pct | FLOAT | NULL | 1-day NAV change % |
| expense_ratio | FLOAT | NULL | Annual expense ratio |
| last_updated | DATETIME | NULL | Last NAV fetch timestamp |
| notes | TEXT | NULL | Analysis notes |

#### 5. **mutual_fund_transactions** - MF Buy/Sell/Switch
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| scheme_code | VARCHAR(20) | NOT NULL | Scheme code |
| scheme_name | VARCHAR(200) | NOT NULL | Scheme name |
| transaction_type | VARCHAR(10) | NOT NULL | BUY/SELL/SWITCH |
| units | FLOAT | NOT NULL | Number of units |
| nav | FLOAT | NOT NULL | NAV at transaction |
| amount | FLOAT | NOT NULL | Total amount |
| transaction_date | DATETIME | NOT NULL | Transaction date |
| is_sip | BOOLEAN | DEFAULT FALSE | Is this a SIP transaction |
| sip_id | VARCHAR(50) | NULL | SIP reference ID |
| reason | TEXT | NULL | Investment reason |
| notes | TEXT | NULL | Additional notes |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

#### 6. **fixed_deposits** - Fixed Deposit Tracking
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| bank_name | VARCHAR(100) | NOT NULL | Bank/institution name |
| account_number | VARCHAR(50) | NULL | FD account number |
| principal_amount | FLOAT | NOT NULL | Initial deposit amount |
| interest_rate | FLOAT | NOT NULL | Annual interest rate % |
| start_date | DATETIME | NOT NULL | FD start date |
| maturity_date | DATETIME | NOT NULL | Maturity date |
| interest_frequency | VARCHAR(20) | DEFAULT 'QUARTERLY' | Interest payout frequency |
| maturity_amount | FLOAT | NULL | Expected maturity amount |
| status | VARCHAR(20) | DEFAULT 'ACTIVE' | ACTIVE/MATURED/CLOSED |
| notes | TEXT | NULL | Additional notes |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

#### 7. **epf_accounts** - EPF Account Master
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| employer_name | VARCHAR(100) | NOT NULL | Current/past employer |
| uan_number | VARCHAR(20) | UNIQUE | Universal Account Number |
| opening_balance | FLOAT | DEFAULT 0.0 | Balance at account opening |
| opening_date | DATETIME | NULL | Account opening date |
| current_balance | FLOAT | DEFAULT 0.0 | Current total balance |
| interest_rate | FLOAT | NULL | Current interest rate % |
| last_updated | DATETIME | NULL | Last balance update |

#### 8. **epf_contributions** - EPF Monthly Contributions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| epf_account_id | INTEGER | NOT NULL | FK to epf_accounts |
| month_year | VARCHAR(7) | NOT NULL | Format: YYYY-MM |
| employee_contribution | FLOAT | NOT NULL | Employee's 12% contribution |
| employer_contribution | FLOAT | NOT NULL | Employer's contribution |
| interest_earned | FLOAT | DEFAULT 0.0 | Interest for the month |
| transaction_date | DATETIME | NOT NULL | Contribution date |

#### 9. **nps_accounts** - NPS Account Master
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| pran_number | VARCHAR(20) | UNIQUE | PRAN number |
| tier | VARCHAR(10) | DEFAULT 'TIER_1' | TIER_1/TIER_2 |
| opening_balance | FLOAT | DEFAULT 0.0 | Initial balance |
| opening_date | DATETIME | NULL | Account opening date |
| current_balance | FLOAT | DEFAULT 0.0 | Current NAV-based balance |
| last_updated | DATETIME | NULL | Last update timestamp |

#### 10. **nps_contributions** - NPS Contributions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| nps_account_id | INTEGER | NOT NULL | FK to nps_accounts |
| contribution_amount | FLOAT | NOT NULL | Amount contributed |
| units_allotted | FLOAT | NULL | Units allotted |
| nav | FLOAT | NULL | NAV at contribution |
| contribution_date | DATETIME | NOT NULL | Contribution date |
| contribution_type | VARCHAR(20) | DEFAULT 'REGULAR' | REGULAR/VOLUNTARY |

#### 11. **savings_accounts** - Savings Account Master
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| bank_name | VARCHAR(100) | NOT NULL | Bank name |
| account_number | VARCHAR(50) | UNIQUE | Account number |
| account_type | VARCHAR(20) | DEFAULT 'SAVINGS' | SAVINGS/CURRENT |
| current_balance | FLOAT | DEFAULT 0.0 | Current balance |
| interest_rate | FLOAT | NULL | Annual interest rate % |
| last_updated | DATETIME | NULL | Last balance update |

#### 12. **savings_transactions** - Savings Deposits/Withdrawals
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| savings_account_id | INTEGER | NOT NULL | FK to savings_accounts |
| transaction_type | VARCHAR(20) | NOT NULL | DEPOSIT/WITHDRAWAL/INTEREST |
| amount | FLOAT | NOT NULL | Transaction amount |
| balance_after | FLOAT | NULL | Balance after transaction |
| transaction_date | DATETIME | NOT NULL | Transaction date |
| description | TEXT | NULL | Transaction description |

#### 13. **lending_records** - Loans Given to Others
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| borrower_name | VARCHAR(100) | NOT NULL | Name of borrower |
| principal_amount | FLOAT | NOT NULL | Initial loan amount |
| interest_rate | FLOAT | DEFAULT 0.0 | Annual interest rate % |
| start_date | DATETIME | NOT NULL | Loan start date |
| expected_return_date | DATETIME | NULL | Expected repayment date |
| amount_repaid | FLOAT | DEFAULT 0.0 | Total repaid so far |
| status | VARCHAR(20) | DEFAULT 'ACTIVE' | ACTIVE/REPAID/DEFAULTED |
| notes | TEXT | NULL | Additional notes |

#### 14. **other_investments** - Gold, Bonds, Real Estate, Crypto
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| investment_type | VARCHAR(50) | NOT NULL | GOLD/BOND/REAL_ESTATE/CRYPTO/OTHER |
| name | VARCHAR(200) | NOT NULL | Asset name/description |
| quantity | FLOAT | NULL | Quantity (e.g., grams, units) |
| purchase_price | FLOAT | NOT NULL | Purchase price per unit |
| current_value | FLOAT | NULL | Current market value |
| purchase_date | DATETIME | NOT NULL | Purchase date |
| notes | TEXT | NULL | Additional notes |

#### 15. **income_transactions** - Income Tracking
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| source | VARCHAR(100) | NOT NULL | Salary/Business/Freelance/Dividend/Interest/Other |
| category | VARCHAR(50) | NULL | Sub-category |
| amount | FLOAT | NOT NULL | Income amount |
| transaction_date | DATETIME | NOT NULL | Receipt date |
| is_recurring | BOOLEAN | DEFAULT FALSE | Is this recurring income |
| description | TEXT | NULL | Income description |
| notes | TEXT | NULL | Additional notes |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

#### 16. **expense_transactions** - Expense Tracking
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| category | VARCHAR(100) | NOT NULL | Groceries/Rent/Transport/Entertainment/etc. |
| sub_category | VARCHAR(100) | NULL | Detailed sub-category |
| amount | FLOAT | NOT NULL | Expense amount |
| payment_method | VARCHAR(50) | NULL | Cash/Card/UPI/NetBanking |
| transaction_date | DATETIME | NOT NULL | Expense date |
| is_recurring | BOOLEAN | DEFAULT FALSE | Is this recurring expense |
| description | TEXT | NULL | Expense description |
| notes | TEXT | NULL | Additional notes |
| created_at | DATETIME | NOT NULL | Record creation timestamp |

#### 17. **budgets** - Monthly/Annual Budget Limits
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| category | VARCHAR(100) | NOT NULL | Budget category (matches expense categories) |
| budget_amount | FLOAT | NOT NULL | Budget limit |
| period | VARCHAR(20) | DEFAULT 'MONTHLY' | MONTHLY/ANNUAL |
| start_date | DATETIME | NOT NULL | Budget period start |
| end_date | DATETIME | NULL | Budget period end |
| alert_threshold | FLOAT | DEFAULT 90.0 | Alert when % of budget used |
| is_active | BOOLEAN | DEFAULT TRUE | Is budget currently active |

#### 18. **global_settings** - Global App Settings
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Always 1 (single row table) |
| equity_allocation_target | FLOAT | DEFAULT 60.0 | Target equity % |
| debt_allocation_target | FLOAT | DEFAULT 30.0 | Target debt % |
| cash_allocation_target | FLOAT | DEFAULT 10.0 | Target cash % |
| emergency_fund_months | INTEGER | DEFAULT 6 | Target emergency fund months |
| currency | VARCHAR(10) | DEFAULT 'INR' | Preferred currency |
| monthly_income_target | FLOAT | NULL | Target monthly income |
| monthly_expense_target | FLOAT | NULL | Target monthly expense |
| updated_at | DATETIME | NULL | Last update timestamp |

### Relationships

**Stock Portfolio (Original):**
- No foreign keys (intentional simplicity)
- Soft relationships via symbol matching
- Allows flexible data management

**New Asset Types:**
- Soft foreign keys for related tables:
  - `epf_contributions.epf_account_id` → `epf_accounts.id`
  - `nps_contributions.nps_account_id` → `nps_accounts.id`
  - `savings_transactions.savings_account_id` → `savings_accounts.id`
- No CASCADE constraints (manual data management)
- Flexible schema allows evolution

---

## Data Flow

### 1. Stock Price Fetching Flow

```
User clicks "Refresh Prices"
    ↓
Frontend → POST /api/stocks/refresh-prices
    ↓
Backend iterates through all stocks
    ↓
For each stock:
  Try: get_scraped_price(symbol)
    ├─→ Google Finance scraper → Success? → Update DB
    ├─→ Moneycontrol scraper → Success? → Update DB
    ├─→ Investing.com scraper → Success? → Update DB
    ├─→ NSE API → Success? → Update DB
    └─→ Yahoo Finance API → Success? → Update DB
    ↓
Response: {total, updated, failed}
    ↓
Frontend displays Snackbar notification
```

### 2. Add Stock with Auto-Fetch Flow

```
User enters symbol & tabs out
    ↓
Frontend → GET /api/stocks/fetch-details/{symbol}
    ↓
Backend calls get_stock_details(symbol)
  ├─→ get_stock_price() → Reliable price
  └─→ fetch_from_screener() → Optional name & day_change_pct
    ↓
Returns: {symbol, name, price, day_change_pct, status}
    ↓
Frontend auto-fills form fields
    ↓
User reviews & clicks "Add Stock"
    ↓
Frontend → POST /api/stocks
    ↓
Backend validates & saves to DB
    ↓
Frontend refreshes stock list
```

### 3. Portfolio Analytics Calculation Flow

```
Frontend loads Analytics page
    ↓
Frontend → GET /api/analytics/dashboard
    ↓
Backend:
  1. Query all stocks
  2. Query all transactions
  3. Calculate holdings using calculate_holdings()
  4. For each holding:
     - Get current price from stocks table
     - Calculate P&L, gain/loss %
  5. Identify action items (in/near buy/sell/average zones)
  6. Calculate top gainers/losers
  7. Aggregate data for charts
    ↓
Returns: {
  portfolio_metrics, holdings, action_items, 
  top_gainers, top_losers, chart_data
}
    ↓
Frontend renders:
  - Action Items Card
  - Top Gainers/Losers Cards
  - Charts (Recharts)
```

### 4. Alert Stock Refresh Flow

```
User clicks "Refresh Alert Stocks"
    ↓
Frontend → POST /api/stocks/refresh-alert-stocks
    ↓
Backend:
  1. Get all stocks & holdings
  2. For each stock:
     - Parse buy/sell/average zones
     - Check if in/near zone (±3%)
     - Consider holdings status
  3. Collect alert stock IDs
  4. Refresh ONLY alert stocks
    ↓
Returns: {total, updated, failed}
    ↓
Frontend displays simplified notification
```

---

## Key Features Implementation

### 1. **Zone-Based Alerts**

**Concept:** Alert user when stock price enters or nears predefined price zones.

**Implementation:**
- **Zone Format**: Supports ranges ("250-300") and exact values ("250")
- **Parsing**: `parse_zone()` in utils.py converts string to (min, max) tuple
- **Threshold**: ±3% for "near zone" alerts
- **Holdings-Aware**: 
  - Buy zone alerts → Only for stocks NOT in holdings
  - Sell/Average zone alerts → Only for stocks IN holdings

**Algorithm:**
```python
for stock in all_stocks:
    buy_min, buy_max = parse_zone(stock.buy_zone_price)
    
    if not in_holdings:
        if buy_min <= current_price <= buy_max:
            → IN_BUY_ZONE alert
        elif buy_max < current_price <= buy_max * 1.03:
            → NEAR_BUY_ZONE alert (within 3%)
    
    # Similar logic for sell/average zones for holdings
```

### 2. **Autocomplete Group & Sector Fields**

**Concept:** Learn from existing data to suggest groups/sectors, allow free input for new values.

**Implementation:**
- **Backend**: 
  - GET /api/stocks/groups → Returns distinct group_name values
  - GET /api/stocks/sectors → Returns distinct sector values
- **Frontend**:
  - MUI Autocomplete with `freeSolo` prop
  - Load existing values on mount
  - Refresh options after saving new stock
  - New values automatically appear in future dropdowns

### 3. **Manual Total Amount & % Allocation**

**Concept:** Track stock allocation against a target portfolio size.

**Implementation:**
- **Database**: `portfolio_settings` table with `total_amount` field
- **Backend**: GET/PUT /api/portfolio/settings
- **Frontend**:
  - Editable chip at top of Portfolio page
  - % Allocation column: `(invested_amount / total_amount) * 100`
  - Reactive: Updates when total amount or holdings change

### 4. **Top Gainers/Losers**

**Concept:** Highlight best and worst performing holdings.

**Implementation:**
- **Backend** (get_analytics_dashboard):
```python
# Filter by actual positive/negative gains
gainers = [h for h in holdings if h['gain_loss_pct'] > 0]
top_gainers = sorted(gainers, key=lambda x: x['gain_loss_pct'], reverse=True)[:5]

losers = [h for h in holdings if h['gain_loss_pct'] < 0]
top_losers = sorted(losers, key=lambda x: x['gain_loss_pct'])[:5]
```
- **Frontend**: Renders green/red cards with % and absolute value

### 5. **CSV Import/Export & Database Backup**

**Concept:** Allow data portability and safety.

**Implementation:**
- **CSV Export**: Pandas DataFrame → to_csv() → send_file()
- **CSV Import**: read_csv() → iterate rows → skip duplicates → insert
- **DB Backup**: shutil.copy2() → send_file() with timestamp
- **DB Restore**: File upload → backup current DB → replace with uploaded file

---

## Code Organization

### Backend Best Practices

✅ **Separation of Concerns**
- `app.py` → API routes & models
- `utils.py` → Reusable logic
- `price_scraper.py` → External data fetching
- `nse_api.py` → API client
- `db_migrator.py` → Schema management

✅ **DRY Principle** (Don't Repeat Yourself)
- Utility functions eliminate duplication
- `parse_zone()` used in 3+ places
- `calculate_holdings()` used in analytics & portfolio summary

✅ **Fail-Safe Design**
- Try-except blocks around all external calls
- Multiple fallback sources for price fetching
- Validation at both client and server

✅ **Clear Naming**
- Functions describe action: `calculate_holdings()`, `validate_transaction_data()`
- Variables describe content: `holding_symbols`, `alert_stock_ids`

### Frontend Best Practices

✅ **Component Modularity**
- Each page is a separate component
- Reusable UI patterns (cards, tables, dialogs)

✅ **Centralized API Client**
- Single source of truth for API calls
- Easy to update backend URL
- Consistent error handling

✅ **User Experience**
- Immediate feedback (Snackbar notifications)
- Loading states for async operations
- Client-side validation before server calls
- Sticky navigation and back-to-top button

---

## Database Migration Strategy

### Problem
When adding new features, database schema needs updates, but users have existing data.

### Solution: Universal Migrator (`db_migrator.py`)

**Features:**
- Auto-detects missing columns and adds them
- Converts column types if needed (e.g., numeric zones → VARCHAR for ranges)
- Creates backup before migration
- Idempotent (safe to run multiple times)

**Usage:**
```bash
cd backend
python db_migrator.py
```

**Migration Logic:**
1. Check if database exists → If not, exit (app will create fresh)
2. Connect to database
3. For each table:
   - Get current columns
   - Compare with expected schema
   - Add missing columns
   - Convert types if needed
4. Commit changes
5. Close connection

---

## Security Considerations

### Current State (Local-Only App)
- **No Authentication**: Not needed (runs on localhost only)
- **No Encryption**: Database not encrypted (file-based)
- **Local Network Only**: Flask debug server on 127.0.0.1

### If Deploying to Production
Would need:
1. **User Authentication** (Flask-Login or JWT)
2. **Database Encryption** at rest
3. **HTTPS** for all communications
4. **Input Sanitization** (already have validation)
5. **CORS** restrictions (whitelist only frontend domain)
6. **Rate Limiting** on API endpoints
7. **Production WSGI Server** (Gunicorn/uWSGI, not Flask debug server)

---

## Performance Considerations

### Current Optimizations
1. **Singleton Price Scraper** - Reuses HTTP session
2. **Query Optimization** - Filter in SQL, not Python
3. **Lazy Loading** - Data fetched only when tab opened
4. **Batch Operations** - Refresh all prices in one request

### Scalability Limits
- **SQLite**: Good for 1 user, <10K transactions
- **For 10+ users**: Migrate to PostgreSQL/MySQL
- **For high traffic**: Add caching layer (Redis)

---

## Testing Strategy

### Current State
- **Manual Testing**: UI interactions, price fetching, calculations
- **No Automated Tests**: Intentional (MVP focus)

### Future Testing Approach
1. **Backend Unit Tests**:
   - `test_utils.py` → Test all utility functions
   - `test_price_scraper.py` → Mock HTTP responses
   - `test_api.py` → Test all endpoints

2. **Frontend Tests**:
   - Component tests (React Testing Library)
   - API mocking (Mock Service Worker)

3. **Integration Tests**:
   - End-to-end workflows (Playwright/Cypress)

---

## Future Architecture Enhancements

### 1. Background Price Refresh
**Current**: Manual refresh button
**Future**: APScheduler for automated daily refresh at market close

### 2. Real-Time Price Updates
**Current**: Polling/manual refresh
**Future**: WebSocket connection for live price streaming

### 3. Multi-User Support
**Current**: Single-user local app
**Future**: User accounts, JWT authentication, PostgreSQL

### 4. Mobile App
**Current**: Web-only
**Future**: React Native app using same REST API

---

## Conclusion

Investment Manager follows a **simple, pragmatic architecture** optimized for:
- **Single-user local usage**
- **Fast development & iteration**
- **Easy maintenance**
- **Data ownership** (all local, no cloud)

The codebase is **well-organized**, **documented**, and **refactored** for clarity and maintainability, making it easy to add features or deploy to production with appropriate security enhancements.

---

**Document Version**: 1.0  
**Last Updated**: October 2025  
**Maintained By**: Investment Manager Development Team

