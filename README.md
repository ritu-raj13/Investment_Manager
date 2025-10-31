# Investment Manager 🚀

A **production-ready** stock tracking and portfolio management application with secure authentication, cloud deployment, and multi-device access. Track your Indian equity investments from anywhere - laptop, mobile, or tablet!

## 🌟 **NEW: Production-Ready Features**

- 🔐 **Secure Authentication** - Single-user login with password hashing
- ☁️ **Cloud Deployment Ready** - Deploy to Railway, Heroku, or Render in 30 minutes
- 📱 **Multi-Device Access** - Use on laptop, mobile, tablet simultaneously
- 🔄 **Automatic Data Sync** - Centralized PostgreSQL database
- 🛡️ **Enterprise Security** - Rate limiting, CSRF protection, secure sessions
- 🌐 **Access Anywhere** - Any device, any network, always synced

**👉 Want to deploy? Start here:** [docs/DEPLOYMENT_QUICKSTART.md](docs/DEPLOYMENT_QUICKSTART.md)

---

## 📚 Documentation

### 🚀 **Quick Start**
- **[START_HERE.md](START_HERE.md)** ⭐ **5-minute quickstart guide**
- **[docs/DEPLOYMENT_QUICKSTART.md](docs/DEPLOYMENT_QUICKSTART.md)** - Complete 30-minute deployment guide

### 📖 **Features & API**
- **[docs/FEATURES.md](docs/FEATURES.md)** ⭐ **Complete feature documentation** (P/L tracking, allocation colors, etc.)
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete REST API documentation
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System design, data flow, and technical architecture

### 🔧 **Setup & Development**
- **[docs/SETUP_INSTRUCTIONS.md](docs/SETUP_INSTRUCTIONS.md)** - Detailed installation and troubleshooting guide
- **[docs/WINDOWS_SETUP_NOTE.md](docs/WINDOWS_SETUP_NOTE.md)** - Windows-specific setup notes
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Codebase organization

### 🔮 **Roadmap**
- **[docs/FUTURE_FEATURES.md](docs/FUTURE_FEATURES.md)** - Planned enhancements

## ✨ Features

### 📊 Stock Tracking
- Track multiple stocks with buy/sell/average zone prices
- Organize stocks by groups (patterns like "Bull Run", "Cup with Handle")
- Categorize by sector and market cap (Large/Mid/Small/Micro)
- **Search functionality** - Find stocks by name, symbol, sector, status, or market cap
- **Simple status tracking** - Watching (grey) and Holding (purple)
- **Expand/Collapse All groups** - Quick view control with one click
- **Refresh Alert Stocks** - One-click refresh for all stocks appearing in Analytics alerts
  - Automatically identifies stocks in/near buy/sell/average zones
  - Only refreshes alert stocks (faster than refreshing all)
  - Orange button for quick access
- Status indicators (Watching, Buy Zone, Sell Zone, Hold Zone, Average Zone)
- **Automated price fetching** using web scraping
- Notes for analysis and reasoning

### 💼 Portfolio Management
- **Manual Total Amount** - Set your target portfolio size for allocation tracking
  - Editable field at top of page with save/cancel
  - Persists across sessions in database
  - Use for planned portfolio allocation calculations
- **Current Holdings** - Complete holdings view with sorting
  - **Sticky Headers** - Column headers remain visible while scrolling through holdings
  - **Sortable columns** - Click to sort by Invested Amount, Unrealized P/L, or Return %
  - **% of Total with Smart Colors** - Real-time allocation with color coding by market cap:
    - 🔴 Red: Over-allocated (> threshold + 0.5%)
    - 🟢 Green: Well-allocated (at threshold to +0.5%)
    - 🟠 Orange: Under-allocated (< threshold)
    - Thresholds: Large Cap 5%, Mid Cap 3%, Small Cap 2%
  - **1D Change %** - Daily change percentage for each stock (green/red chips)
  - Symbol display without .NS/.BO suffix (clean view)
  - Real-time portfolio valuation with color-coded gains/losses
- **Profit & Loss Tracking**
  - **💰 Realized P/L** - Actual profit/loss from completed SELL transactions
  - **📈 Unrealized P/L** - Paper gains/losses on current holdings
  - Per-stock and total portfolio P/L metrics
  - Accurate average cost basis calculation (FIFO method)
- **Transaction History** - All buy/sell transactions with clean symbol display
- **Search by symbol** - Quick filtering in both tabs
- **Portfolio summary cards** - Total invested, current value, realized P/L, unrealized P/L, 1 day change (5 cards)
- **Active Holdings Count** - See number of stocks held and total transactions
- Track quantity, average price, and transaction history
- Document reasons for each trade
- Simplified transaction form (symbol, quantity, price, reason)

### 📊 Analytics Dashboard
- **Action Items Card** - Prominent display of stocks requiring attention
- **Top Gainers/Losers** - Visual display of best/worst performing stocks
  - Top 5 Gainers (green cards with percentage and absolute gain)
  - Top 5 Losers (red cards with percentage and absolute loss)
  - Filtered by actual positive/negative returns (no false positives)
- **Interactive charts** - Visual portfolio insights with enhanced tooltips
  - Portfolio Value comparison (Invested vs Current)
  - Sector Allocation pie chart with hover tooltips showing:
    - 📊 Stock count in each sector
    - Total invested amount
  - Market Cap Allocation pie chart with hover tooltips showing:
    - 📊 Stock count in each market cap category
    - Total invested amount
- **Smart action items** - Intelligent alerts filtered by holdings
  - Buy Zone alerts → Only for stocks you DON'T own (entry opportunities)
  - Sell Zone alerts → Only for stocks you DO own (exit opportunities)
  - Average Zone alerts → Only for stocks you DO own (averaging opportunities)
- **Six alert types** - In/Near Buy, Sell, and Average zones (±3% threshold)
- **Fast performance** - Uses prices from Stock Tracking (no redundant API calls)

### 🎨 Modern UI
- Beautiful dark mode interface
- **Sticky navigation bar** - Tabs stay visible when scrolling
- **Back to top button** - Floating button appears when scrolling down
- Card-based layout with grouping
- Responsive design for all screen sizes
- Glass-morphism effects on navigation
- Smooth animations and transitions
- Collapsible groups for better organization
- Color-coded status indicators

### ⚙️ Data Management
- **Import/Export CSV** - Import and export stocks and transactions
- **Database Backup** - One-click full database backup (.db file)
- **Database Restore** - Restore from previous backups
- Settings page with all data management tools

### 🔄 Automated Data & Price Fetching
- **Screener.in integration** (primary) - Auto-fetches company name + price from symbol
- **Web scraping** from Google Finance, Moneycontrol, Investing.com (fallbacks)
- NSE India API (fallback)
- Yahoo Finance API (last resort)
- **Smart auto-fetch** - Just enter symbol, name & price populate automatically!
- **Smart status** - Auto-sets Watching or Holding based on portfolio holdings
- One-click "Refresh Alert Stocks" for targeted updates
- One-click "Refresh Prices" for all stocks
- Works for ALL Indian stocks (NSE/BSE)

## 🚀 Quick Start

### Option 1: Test Production Mode Locally ⭐ **Recommended**

Test the production-ready app with authentication before deploying:

```bash
# Windows
test_production_locally.bat

# Mac/Linux
chmod +x test_production_locally.sh
./test_production_locally.sh
```

Then in another terminal:
```bash
cd frontend
npm install
npm start
```

**Login Credentials (local testing):**
- Username: `admin`
- Password: `admin123`

### Option 2: Development Mode (No Authentication)

### Prerequisites
- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

### Installation

#### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the Flask server
python app.py
```

Backend runs at: `http://localhost:5000`

#### 2. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start React app
npm start
```

Frontend opens at: `http://localhost:3000`

## 📖 Usage Guide

### Adding Stocks

1. Go to **Stock Tracking** tab
2. Click **Add Stock**
3. Enter stock symbol and let it auto-fetch details:
   ```
   Symbol: RELIANCE.NS (for NSE) or RELIANCE.BO (for BSE)
   [Tab out - name & price auto-fetch from Screener.in!]
   
   Name: [Auto-filled: Reliance Industries]
   Current Price: [Auto-filled: ₹2,750.50]
   Status: [Auto-set: Watching or Holding based on your portfolio]
   
   Group: Bull Run (optional)
   Market Cap: Large (optional)
   Sector: Energy (optional)
   Buy Zone: 2400-2600 (or exact: 2500)
   Sell Zone: 2800-3000 (or exact: 2900)
   Average Zone: 2650-2750
   Notes: Strong fundamentals
   ```
4. Click **Add Stock**
5. Price fetches automatically, or click **Refresh Prices** later

**Tip:** Add all stocks first (leave price blank), then click "Refresh Prices" once to update all prices together!

### Data Management (Settings Page)

**Export Data:**
1. Go to **Settings** tab
2. Click **Export Stocks CSV** or **Export Transactions CSV**
3. File downloads automatically with timestamp

**Import Data:**
1. Go to **Settings** tab
2. Click **Choose File** button for Stocks or Transactions
3. Select your CSV file
4. Confirm import → Data is added automatically

**Backup Database:**
1. Go to **Settings** tab
2. Click **Backup Database**
3. Complete .db file downloads with timestamp
4. Store safely (external drive, cloud storage)

**Restore Database:**
1. Go to **Settings** tab  
2. Click **Choose Database File**
3. Select your backup .db file
4. Confirm → Current data backed up automatically before restore
5. Page reloads with restored data

### Refreshing Prices

**Best Practice Workflow:**
1. Add all your stocks (leave Current Price blank)
2. Click **"Refresh Prices"** button once
3. All stock prices fetch automatically in 10-30 seconds
4. Repeat daily or as needed

**Benefits:**
- Faster than entering prices manually
- More accurate (live data)
- One-click update for all stocks

### Managing Portfolio

**Setting Up Total Amount (for % Allocation):**
1. Go to **My Portfolio** tab
2. At the top, click **Edit** on "Total Portfolio Amount"
3. Enter your target portfolio size (e.g., ₹5,00,000)
4. Click **Save**
5. The % allocation for each stock will calculate based on this amount

**Adding Transactions:**
1. Go to **My Portfolio** tab
2. Click **Add Transaction**
3. Fill in transaction details:
   - Stock symbol and name
   - Transaction type (BUY/SELL)
   - Quantity and price
   - Date and reason
4. View performance in two tabs:
   - **Current Holdings**: Live P&L for each stock with % allocation
   - **Transaction History**: Complete trade log

**Understanding % Allocation:**
- Shows what % of your TOTAL target amount each stock represents
- Example: If you set ₹5L target and invest ₹1L in a stock → shows 20%
- Helps maintain planned portfolio allocation
- Updates dynamically as you add/remove transactions

## 🛠️ Technology Stack

### Backend
- **Flask** - Python web framework
- **Flask-Login** - User authentication & session management
- **Flask-Limiter** - Rate limiting (brute-force protection)
- **Flask-CORS** - Cross-origin resource sharing
- **SQLAlchemy** - ORM for database
- **PostgreSQL** (production) / **SQLite** (development)
- **Gunicorn** - Production WSGI server
- **BeautifulSoup4** + **lxml** - Web scraping for prices
- **Requests** - HTTP client
- **yfinance** - Yahoo Finance API (fallback)
- **bcrypt / werkzeug** - Password hashing
- **python-dotenv** - Environment variable management
- **Pandas** - CSV import/export

### Frontend
- **React** - UI framework with Hooks
- **Material-UI (MUI)** - Component library (dark theme)
- **Axios** - HTTP client with auth interceptors
- **Recharts** - Data visualization

### Security & Deployment
- **bcrypt password hashing** - Secure credential storage
- **Session-based authentication** - HTTPOnly cookies
- **CSRF protection** - Flask-WTF tokens
- **Rate limiting** - 5 login attempts/minute
- **Environment-based configuration** - Dev/Production separation
- **HTTPS** - Enforced in production (Railway/Heroku/Render)
- **PostgreSQL connection pooling** - Production database
- **Database migration tools** - SQLite → PostgreSQL

## 📁 Project Structure

```
Investment_Manager/
├── backend/
│   ├── app.py                      # Flask API server
│   ├── config/                     # Environment configurations
│   │   ├── base.py                # Shared settings
│   │   ├── development.py         # Dev (SQLite)
│   │   └── production.py          # Prod (PostgreSQL)
│   ├── utils/                      # Utility modules
│   │   ├── auth.py                # Authentication
│   │   ├── holdings.py            # P/L calculations
│   │   ├── zones.py               # Price zones
│   │   └── helpers.py             # General utilities
│   ├── services/                   # External services
│   │   ├── price_scraper.py       # Web scraping
│   │   └── nse_api.py             # NSE API
│   ├── migrations/                 # DB migrations
│   ├── instance/                   # SQLite database (dev)
│   └── requirements.txt            # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Login.js           # Authentication
│   │   │   ├── StockTracking.js   # Stock tracking
│   │   │   ├── Portfolio.js        # Portfolio & P/L
│   │   │   ├── Analytics.js        # Analytics dashboard
│   │   │   └── Settings.js         # Settings & exports
│   │   ├── services/
│   │   │   └── api.js              # API client (axios)
│   │   ├── App.js                  # Main app component
│   │   └── index.js                # Entry point
│   ├── public/
│   └── package.json                # Node dependencies
├── docs/                            # Documentation
│   ├── FEATURES.md                 # Feature documentation
│   ├── API_REFERENCE.md            # API docs
│   ├── ARCHITECTURE.md             # System design
│   └── ...                         # Setup & deployment guides
├── scripts/                         # Helper scripts
│   └── dev/                        # Development scripts
│       └── start_dev.bat           # Start dev servers
├── README.md                        # This file
└── START_HERE.md                    # Quick start guide
```

## 🔧 API Endpoints

The application provides a comprehensive REST API with 22 endpoints across 4 categories:

- **Stock Tracking** (8 endpoints) - CRUD operations, price refresh, auto-fetch
- **Portfolio Management** (7 endpoints) - Transactions, P&L, settings
- **Analytics** (1 endpoint) - Dashboard data with action items and charts
- **Data Management** (6 endpoints) - CSV import/export, database backup/restore

**📖 For complete API documentation, see [API_REFERENCE.md](API_REFERENCE.md)**

### Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/stocks` | GET | List all stocks |
| `/api/stocks` | POST | Add new stock (auto-fetches details) |
| `/api/stocks/refresh-prices` | POST | Refresh all stock prices |
| `/api/stocks/refresh-alert-stocks` | POST | Refresh only alert stocks |
| `/api/portfolio/transactions` | GET/POST | Manage transactions |
| `/api/portfolio/summary` | GET | Portfolio P&L summary |
| `/api/analytics/dashboard` | GET | Analytics data |
| `/api/export/stocks` | GET | Export stocks to CSV |
| `/api/backup/database` | GET | Download DB backup |

## 💡 Tips & Best Practices

### Stock Symbols
- **NSE stocks**: Add `.NS` suffix (e.g., `RELIANCE.NS`, `TCS.NS`)
- **BSE stocks**: Add `.BO` suffix (e.g., `RELIANCE.BO`)

### Price Updates
- Click "Refresh Prices" once a day
- Takes 10-30 seconds for 10-20 stocks
- Be patient - web scraping needs time

### Portfolio Tracking
- Record every transaction with reason
- Use notes to document your analysis
- Review performance weekly/monthly

### Organization
- Use Groups for trading patterns (Bull Run, Cup with Handle, etc.)
- Use Sector for industry classification (FMCG, Banking, IT, etc.)
- **Price Zones support ranges**: Enter "250-300" or exact "275"
- Set realistic buy/sell zones based on your analysis
- Update status as markets move

### Portfolio Allocation
- Set your **Total Portfolio Amount** to track planned allocation
- Monitor **% of Total** column to see stock-wise distribution
- Rebalance when any stock exceeds your target allocation
- Example: If you plan 10% in tech but have 15% → consider rebalancing

## 🔄 Database Migration

If you have existing data and need to update the database schema:

```bash
cd backend
python db_migrator.py
```

The universal migrator will:
- Auto-detect missing columns and add them
- Convert column types if needed (e.g., zones to support ranges)
- Create backup before migration
- Run safely multiple times (idempotent)

## 🐛 Troubleshooting

### Backend won't start
- Check if port 5000 is free
- Activate virtual environment
- Install all requirements

### Frontend won't start
- Check if port 3000 is free
- Run `npm install` again
- Delete `node_modules` and reinstall

### Prices not fetching
- Check internet connection
- Wait a few seconds between refreshes
- Web scraping may be temporarily blocked (wait and retry)

### Database errors
- Run `python migrate_db.py` to update schema
- Or delete `investment_manager.db` to start fresh

## 📱 **Multi-Device Usage**

Once deployed to the cloud:

1. **Laptop/Desktop:** Bookmark your deployment URL
2. **Mobile (iOS):** Safari → Share → Add to Home Screen
3. **Mobile (Android):** Chrome → Menu → Add to Home screen
4. **Tablet:** Same as mobile

**All devices sync automatically** through the centralized PostgreSQL database!

Access your portfolio from:
- ✅ Home laptop → Work laptop
- ✅ WiFi → Mobile data
- ✅ Café tablet → Office desktop
- ✅ **Always the same data, always in sync!**

---

## 💰 **Deployment Costs**

### Railway (Recommended) ⭐
- ~$5-8/month (first $5 free)
- Easiest setup, auto-deploy from GitHub
- PostgreSQL included

### Heroku
- $7/month minimum
- Well-established, reliable platform

### Render
- $7/month for backend
- Free frontend hosting

**All include:** SSL/HTTPS, automatic backups, PostgreSQL database

---

## 🎯 Future Enhancements

Potential features for future versions:
- Multi-user support (family accounts)
- Debt instruments (Bonds, FDs)
- Mutual funds tracking
- Dividend tracking
- Tax calculation (STCG/LTCG)
- Price alerts via email/SMS
- Export to Excel/PDF
- Native mobile app

## ⚠️ Disclaimer

This is a personal portfolio tracking tool for educational and personal use.

- **Not Financial Advice** - This tool is for tracking only, not for making investment decisions
- **No Warranty** - Provided "as is" without warranties of any kind
- **Use at Your Own Risk** - Always verify data independently
- **For Personal Use** - Designed for individual portfolio management

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.

This project is open source. Feel free to use, modify, and enhance as needed.

## 🤝 Contributing

This is a personal project, but suggestions and improvements are welcome!

## 📧 Support

For issues or questions, please check:
1. **[README.md](README.md)** - Feature overview and quick start
2. **[SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)** - Detailed setup and troubleshooting
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical details and system design
4. **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation

## 🏗️ Code Quality

This codebase follows best practices:
- ✅ **Modular Architecture** - Clear separation of concerns
- ✅ **DRY Principle** - Utility functions eliminate duplication
- ✅ **Comprehensive Documentation** - Architecture, API, and setup guides
- ✅ **Type Hints** - Python type annotations for clarity
- ✅ **Consistent Naming** - Descriptive function and variable names
- ✅ **Error Handling** - Graceful failure with multiple fallbacks
- ✅ **Database Migrations** - Version-aware schema updates

---

## 🎯 Recent Updates (October 31, 2025)

### User-Configurable Portfolio Settings
- ✅ Centralized configuration in Settings page
- ✅ Customize allocation thresholds per your investment strategy
- ✅ Market Cap limits: Large (50%), Mid (30%), Small (25%), Micro (15%)
- ✅ Sector diversification limit (20% per sector)
- ✅ All calculations dynamically use your custom values

### Recommendations & Health Pages
- ✅ **Recommendations Tab**: Price zone alerts + rebalancing suggestions
- ✅ **Health Tab**: Portfolio health metrics & concentration analysis
- ✅ Expandable sections for detailed analysis
- ✅ Smart alert filtering (buy zones for watching stocks, sell/average for holdings)

### Enhanced Portfolio Features
- ✅ FIFO-based holding period tracking
- ✅ XIRR (annualized return) calculation
- ✅ Realized P/L and Unrealized P/L separation
- ✅ Color-coded allocation percentages
- ✅ Sortable columns with default "% of Total" descending sort

---

**Built with ❤️ for smart investing**

*Last updated: October 31, 2025*
