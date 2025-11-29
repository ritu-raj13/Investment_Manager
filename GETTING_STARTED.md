# Getting Started

Get up and running with Personal Finance Manager in 15 minutes.

## System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.8 or higher
- **Node.js**: 14 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB for dependencies

---

## Installation

### 1. Clone or Download the Project

```bash
cd Investment_Manager
```

### 2. Backend Setup

#### Windows

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Install dependencies
pip install -r requirements.txt

# Run the migration (if upgrading from earlier version)
python migrate_to_personal_finance.py

# Run the server
python app.py
```

#### Mac/Linux

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the migration (if upgrading from earlier version)
python migrate_to_personal_finance.py

# Run the server
python app.py
```

**Backend runs at:** `http://localhost:5000`

Keep this terminal open!

### 3. Frontend Setup

Open a **NEW** terminal:

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start the development server
npm start
```

**Frontend opens at:** `http://localhost:3000`

The browser should open automatically.

---

## First Time Setup

### 1. Database Initialization

The database is created automatically when you first run the backend. The file `investment_manager.db` will be created in `backend/instance/` folder.

### 2. Test the Application

1. Open `http://localhost:3000` in your browser
2. You should see the Personal Finance Manager interface with 9 tabs
3. Navigate through tabs to explore features

### 3. Add Your First Stock

Navigate to **Stocks** tab and click **Add Stock**:

```
Symbol: RELIANCE.NS
Name: Reliance Industries
Group: Blue Chip
Market Cap: Large
Sector: Energy
Current Price: [Leave blank - optional]
Status: Watching
Buy Zone: 2400-2600 (or exact: 2500)
Sell Zone: 2800-3000 (or exact: 2900)
Average Zone: 2650
Notes: Strong fundamentals, good dividend yield
```

Click "Add Stock" - price fetches automatically (or use "Refresh Prices" button later).

**Tip:** Add multiple stocks first, then click "Refresh Prices" once to update all prices together!

### 4. Add Your First Transaction

Navigate to **Portfolio** tab (under Stocks) and click **Add Transaction**:

```
Stock Symbol: RELIANCE.NS
Stock Name: Reliance Industries
Type: BUY
Quantity: 10
Price: 2500
Date: [Today's date]
Reason: Entry at support level
```

The portfolio will now show your holdings with real-time P/L tracking!

---

## Daily Usage

### Starting the Application

**Every time you want to use the app:**

#### Terminal 1: Backend
```bash
cd backend
# Activate venv (Windows)
.\venv\Scripts\Activate.ps1
# Or (Mac/Linux)
source venv/bin/activate

python app.py
```

#### Terminal 2: Frontend
```bash
cd frontend
npm start
```

### Stopping the Application

- Press `Ctrl+C` in each terminal
- Deactivate virtual environment: `deactivate`

---

## Stock Symbol Format

### Indian Stocks

**NSE (National Stock Exchange):**
- Format: `SYMBOL.NS`
- Examples: `RELIANCE.NS`, `TCS.NS`, `INFY.NS`, `HDFCBANK.NS`

**BSE (Bombay Stock Exchange):**
- Format: `SYMBOL.BO`
- Examples: `RELIANCE.BO`, `TCS.BO`, `INFY.BO`

### How to Find Symbols

1. Go to https://www.google.com/finance
2. Search for your stock
3. The URL will show the symbol
   - Example: `/quote/RELIANCE:NSE` → use `RELIANCE.NS`

---

## Configuration

### Backend Configuration

Key settings in `backend/app.py`:
- **Database**: SQLite (`instance/investment_manager.db`)
- **Port**: 5000
- **CORS**: Enabled for frontend

### Frontend Configuration

API endpoint in `frontend/src/services/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

Change if backend runs on different port.

---

## Database Management

### Backup Your Data

```bash
# Copy the database file
cp backend/instance/investment_manager.db backend/instance/investment_manager_backup.db
```

Or use the **Settings** tab → **Backup Database** button.

### Restore Database

1. Go to **Settings** tab
2. Click **Choose Database File**
3. Select your backup `.db` file
4. Confirm → Current data backed up automatically before restore
5. Page reloads with restored data

### Migrate Database Schema

If updating from an earlier version:

```bash
cd backend
python migrate_to_personal_finance.py
```

The migrator automatically:
- Detects and adds missing columns/tables
- Preserves all existing data
- Creates backups before migration
- Runs safely multiple times (idempotent)

---

## Troubleshooting

### Port 5000 Already in Use

**Windows:**
```powershell
# Find process
netstat -ano | findstr :5000

# Kill process (use PID from above)
taskkill /PID <process_id> /F
```

**Mac/Linux:**
```bash
# Find and kill process
lsof -ti:5000 | xargs kill -9
```

### Port 3000 Already in Use

The terminal will ask if you want to use another port. Type `y` and press Enter.

### Python Not Found

**Windows:**
- Download from https://python.org
- Check "Add Python to PATH" during installation

**Mac:**
```bash
brew install python3
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv
```

### npm Not Found

Install Node.js from https://nodejs.org (includes npm)

### Virtual Environment Won't Activate (Windows)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Alternative:** Use Command Prompt instead:
```cmd
venv\Scripts\activate.bat
```

### Database Locked Error

- Close all other terminals accessing the backend
- Restart the backend server

### Prices Not Fetching

1. Check internet connection
2. Wait a few seconds (web scraping takes time)
3. Try "Refresh Prices" button again
4. If still failing, enter prices manually (field is optional)

---

## What's Available Now

### ✅ Fully Functional
- **Dashboard**: Net worth, asset allocation, cash flow visualization
- **Stock Tracking**: Full CRUD, price fetching, zones
- **Portfolio**: Transaction management, FIFO P/L, XIRR, holding periods
- **Analytics**: Charts, top gainers/losers, sector/market cap allocation
- **Health**: Portfolio health metrics, concentration analysis
- **Recommendations**: Rebalancing suggestions, price zone alerts
- **Settings**: Import/export, database backup/restore, thresholds

### 🔨 Backend Ready, Frontend Pending
- **Mutual Funds**: API endpoints ready (schemes, transactions, holdings)
- **Fixed Income**: FD, EPF, NPS APIs implemented
- **Savings/Lending**: Account and transaction APIs ready
- **Income & Expenses**: Complete transaction and budget APIs
- **Reports**: Dashboard aggregation APIs functional

See [ROADMAP.md](ROADMAP.md) for implementation timeline.

---

## Next Steps

After setup:

1. **Explore the Dashboard** - See net worth and allocation
2. **Add stocks** you want to track
3. **Record transactions** in your portfolio
4. **Set price zones** for buy/sell decisions
5. **Review Analytics** - Top gainers, sector allocation
6. **Check Health** - Concentration risk, diversification
7. **Use Recommendations** - Rebalancing guidance

---

## Need More Help?

- **Features Guide**: See [FEATURES.md](docs/FEATURES.md) for detailed feature documentation
- **API Documentation**: See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for endpoint details
- **Architecture**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for technical design
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md) to extend the platform

---

**Enjoy organized financial tracking!** 📊

