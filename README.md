# Investment Manager

A comprehensive stock tracking and portfolio management application with automated price fetching, allocation tracking, and analytics for Indian equities.

## 📚 Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - System design, data flow, and technical architecture
- **[API Reference](API_REFERENCE.md)** - Complete REST API documentation
- **[Setup Instructions](SETUP_INSTRUCTIONS.md)** - Detailed installation and troubleshooting guide
- **[Future Features](FUTURE_FEATURES.md)** - Roadmap and planned enhancements

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
  - **Sortable columns** - Click to sort by Invested Amount, Gain/Loss, or Return %
  - **% of Total** - Real-time allocation based on YOUR manual total amount (not just invested sum)
  - **1D Change %** - Daily change percentage for each stock (green/red chips)
  - Symbol display without .NS/.BO suffix (clean view)
  - Real-time portfolio valuation with color-coded gains/losses
- **Transaction History** - All buy/sell transactions with clean symbol display
- **Search by symbol** - Quick filtering in both tabs
- **Portfolio summary cards** - Total invested, current value, gain/loss, return %, 1 day change (5 cards)
- Track quantity, average price, and transaction history
- Document reasons for each trade
- Simplified transaction form (symbol, quantity, price, reason)

### 📊 Analytics Dashboard
- **Action Items Card** - Prominent display of stocks requiring attention
- **Top Gainers/Losers** - Visual display of best/worst performing stocks
  - Top 5 Gainers (green cards with percentage and absolute gain)
  - Top 5 Losers (red cards with percentage and absolute loss)
  - Filtered by actual positive/negative returns (no false positives)
- **Interactive charts** - Visual portfolio insights with clear tooltips
  - Portfolio Value comparison (Invested vs Current)
  - Sector Allocation pie chart
  - Market Cap Allocation pie chart
- **Smart action items** - Intelligent alerts filtered by holdings
  - Buy Zone alerts → Only for stocks you DON'T own (entry opportunities)
  - Sell Zone alerts → Only for stocks you DO own (exit opportunities)
  - Average Zone alerts → Only for stocks you DO own (averaging opportunities)
- **Six alert types** - In/Near Buy, Sell, and Average zones (±5%)
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
- **SQLAlchemy** - ORM for database
- **SQLite** - Local database
- **BeautifulSoup4** - Web scraping
- **Requests** - HTTP client
- **yfinance** - Yahoo Finance API (fallback)

### Frontend
- **React** - UI framework
- **Material-UI (MUI)** - Component library
- **Axios** - HTTP client
- **React Router** - Navigation

## 📁 Project Structure

```
Investment_Manager/
├── backend/
│   ├── app.py                      # Flask API server
│   ├── price_scraper.py            # Web scraping for prices
│   ├── nse_api.py                  # NSE India API client
│   ├── migrate_db.py               # Database migration script
│   ├── requirements.txt            # Python dependencies
│   └── investment_manager.db       # SQLite database
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── StockTracking.js   # Stock tracking page
│   │   │   └── Portfolio.js        # Portfolio page
│   │   ├── services/
│   │   │   └── api.js              # API client
│   │   ├── App.js                  # Main app component
│   │   └── index.js                # Entry point
│   ├── public/
│   │   └── index.html
│   └── package.json                # Node dependencies
├── README.md                       # This file
├── SETUP_INSTRUCTIONS.md           # Detailed setup guide
└── .gitignore                      # Git ignore rules
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

## 🎯 Future Enhancements

Potential features for future versions:
- Debt instruments (Bonds, FDs)
- Mutual funds tracking
- Dividend tracking
- Tax calculation (STCG/LTCG)
- Charts and visualizations
- Price alerts
- Export to Excel/PDF
- Mobile app

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

**Built with ❤️ for smart investing**
