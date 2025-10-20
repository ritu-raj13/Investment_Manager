# Investment Manager - Architecture Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Technology Stack](#technology-stack)
3. [Backend Architecture](#backend-architecture)
4. [Frontend Architecture](#frontend-architecture)
5. [Database Schema](#database-schema)
6. [Data Flow](#data-flow)
7. [Key Features Implementation](#key-features-implementation)
8. [Code Organization](#code-organization)

---

## System Overview

Investment Manager is a **full-stack web application** designed for tracking Indian equity investments with automated price fetching, portfolio analytics, and action-based alerts.

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
4. **Fail-Safe Price Fetching**: Multiple fallback sources for reliability
5. **Data Integrity**: Server-side validation for all transactions

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

## Backend Architecture

### Module Structure

```
backend/
├── app.py              # Main Flask application & API routes
├── utils.py            # Utility functions (validation, parsing, calculations)
├── price_scraper.py    # Multi-source web scraper for stock prices
├── nse_api.py          # NSE India API client (fallback)
├── db_migrator.py      # Database migration tool
└── requirements.txt    # Python dependencies
```

### Core Modules

#### 1. **app.py** - Main Application
- **Flask app initialization** with CORS
- **Database models** (Stock, PortfolioTransaction, PortfolioSettings)
- **API routes** (22 endpoints organized by feature)
- **Business logic** for portfolio calculations and analytics

#### 2. **utils.py** - Shared Utilities
**Functions:**
- `parse_zone()` - Parse price zone strings ("250-300" → (250.0, 300.0))
- `calculate_holdings()` - Compute current holdings from transactions
- `validate_transaction_data()` - Validate transaction inputs
- `is_in_zone()` - Check if price is in/near a zone
- `format_refresh_response()` - Standardize price refresh responses
- `clean_symbol()` - Normalize stock symbols

**Why:** Eliminates code duplication across app.py endpoints

#### 3. **price_scraper.py** - Price Fetching
**PriceScraper Class:**
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

#### 3. **portfolio_settings** - User Preferences
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Always 1 (single row table) |
| total_amount | FLOAT | DEFAULT 0.0 | Manual total portfolio amount for % calculation |
| updated_at | DATETIME | NULL | Last update timestamp |

### Relationships
- **No foreign keys** (intentional design for simplicity)
- **Soft relationships** via symbol matching
- Allows flexible data management (stocks can be deleted without affecting transaction history)

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
     - Check if in/near zone (±5%)
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
- **Threshold**: ±5% for "near zone" alerts
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
        elif buy_max < current_price <= buy_max * 1.05:
            → NEAR_BUY_ZONE alert
    
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

