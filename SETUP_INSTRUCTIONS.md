# Setup Instructions - Investment Manager

Detailed step-by-step setup guide for the Investment Manager application.

## 📚 Related Documentation
- **[README.md](README.md)** - Feature overview
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture
- **[API_REFERENCE.md](API_REFERENCE.md)** - API documentation

## System Requirements

- **Operating System**: Windows 10/11, macOS, or Linux
- **Python**: 3.8 or higher
- **Node.js**: 14 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 500MB for dependencies

## Installation Steps

### 1. Clone or Download the Project

```bash
cd Investment_Manager
```

### 2. Backend Setup

#### Windows:

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

# Run the server
python app.py
```

#### Mac/Linux:

```bash
# Navigate to backend
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
```

**Backend runs at**: `http://localhost:5000`

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

**Frontend opens at**: `http://localhost:3000`

The browser should open automatically.

## First Time Setup

### 1. Database Initialization

The database is created automatically when you first run the backend. The file `investment_manager.db` will be created in the `backend` folder.

### 2. Test the Application

1. Open `http://localhost:3000` in your browser
2. You should see the Investment Manager interface
3. Click "Add Stock" to add your first stock

### 3. Add Your First Stock

Example:
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

Click "Add Stock" - price fetches automatically (or leave blank and use "Refresh Prices" later).

**Best Practice:** Add multiple stocks with price blank, then click "Refresh Prices" once to update all together!

## Configuration

### Backend Configuration

All configuration is in `backend/app.py`:

- **Database**: SQLite (file-based, no setup needed)
- **Port**: 5000 (change in `app.py` if needed)
- **CORS**: Enabled for frontend communication

### Frontend Configuration

API endpoint is in `frontend/src/services/api.js`:

```javascript
const API_BASE_URL = 'http://localhost:5000/api';
```

Change if backend runs on different port.

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

## Daily Usage

### Starting the Application

**Every time you want to use the app:**

1. **Start Backend:**
   ```bash
   cd backend
   # Activate venv (Windows)
   .\venv\Scripts\Activate.ps1
   # Or (Mac/Linux)
   source venv/bin/activate
   
   python app.py
   ```

2. **Start Frontend:** (new terminal)
   ```bash
   cd frontend
   npm start
   ```

### Stopping the Application

- Press `Ctrl+C` in each terminal
- Deactivate virtual environment: `deactivate`

## Database Management

### Backup Your Data

```bash
# Copy the database file
cp backend/investment_manager.db backend/investment_manager_backup.db
```

### Reset Database

If you want to start fresh:

```bash
# Delete the database
rm backend/investment_manager.db

# Restart backend - new database is created automatically
python app.py
```

### Migrate Database Schema

If you update to a new version with schema changes:

```bash
cd backend
python db_migrator.py
```

The universal migrator automatically:
- Detects and adds missing columns
- Converts column types if needed
- Creates backups before migration
- Runs safely multiple times

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

### Virtual Environment Won't Activate

**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Alternative:**
Use Command Prompt instead:
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
4. If still failing, enter prices manually (optional field)

## Performance Tips

### For Large Portfolios (50+ stocks)

1. Don't refresh prices too frequently (once a day is enough)
2. Consider organizing stocks into focused groups
3. Archive old transactions (export to Excel, then delete from app)

### Database Optimization

The SQLite database is optimized for up to 10,000 transactions. For larger datasets:

1. Regular backups
2. Periodic cleanup of old transactions
3. Consider exporting historical data

## Security Notes

1. **Local Only**: This app runs locally - no cloud, no external access
2. **Data Privacy**: All your data stays on your computer
3. **Network**: Only outbound connections for fetching prices
4. **Firewall**: Backend server only accepts local connections

## Development Mode

The app runs in development mode by default:

- **Hot reloading**: Changes to code auto-refresh
- **Debug mode**: Detailed error messages
- **No caching**: Always fresh data

For production deployment (advanced users), additional configuration needed.

## Getting Help

1. Check this document
2. Review README.md
3. Check code comments in `backend/app.py` and frontend files
4. Common errors usually relate to:
   - Missing dependencies
   - Port conflicts
   - Virtual environment not activated

## Next Steps

After setup:

1. **Add stocks** you want to track
2. **Record transactions** in your portfolio
3. **Set price zones** for buy/sell decisions
4. **Use "Refresh Prices"** daily or weekly
5. **Review portfolio** performance regularly

---

**Enjoy organized investment tracking!** 📈
