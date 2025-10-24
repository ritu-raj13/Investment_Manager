# Investment Manager - API Reference

Complete reference for all REST API endpoints in the Investment Manager application.

## Table of Contents
1. [Base URL](#base-url)
2. [Response Format](#response-format)
3. [Stock Tracking API](#stock-tracking-api)
4. [Portfolio API](#portfolio-api)
5. [Analytics API](#analytics-api)
6. [Data Management API](#data-management-api)
7. [Error Handling](#error-handling)

---

## Base URL

```
http://localhost:5000/api
```

All endpoints are prefixed with `/api`.

---

## Response Format

### Success Response
```json
{
  "data": { ... },
  "status": 200
}
```

### Error Response
```json
{
  "error": "Error message",
  "status": 400|404|500
}
```

---

## Stock Tracking API

### 1. Get All Stocks

**GET** `/stocks`

Get list of all tracked stocks.

**Response:**
```json
[
  {
    "id": 1,
    "symbol": "RELIANCE.NS",
    "name": "Reliance Industries",
    "group_name": "Bull Run",
    "sector": "Energy",
    "market_cap": "Large",
    "buy_zone_price": "2400-2600",
    "sell_zone_price": "2800-3000",
    "average_zone_price": "2650-2750",
    "status": "WATCHING",
    "current_price": 2750.50,
    "day_change_pct": 1.25,
    "last_updated": "2025-10-19T10:30:00",
    "notes": "Strong fundamentals"
  }
]
```

---

### 2. Get Single Stock

**GET** `/stocks/<stock_id>`

Get details of a specific stock.

**Parameters:**
- `stock_id` (path, integer) - Stock ID

**Response:** Same as single stock object above

**Errors:**
- `404` - Stock not found

---

### 3. Create Stock

**POST** `/stocks`

Add a new stock to tracking.

**Request Body:**
```json
{
  "symbol": "TCS.NS",
  "name": "Tata Consultancy Services",
  "group_name": "Blue Chip",
  "sector": "IT",
  "market_cap": "Large",
  "buy_zone_price": "3200-3400",
  "sell_zone_price": "3800-4000",
  "average_zone_price": "3500",
  "status": "WATCHING",
  "current_price": 3650.00,
  "day_change_pct": -0.5,
  "notes": "Market leader in IT services"
}
```

**Required Fields:**
- `symbol` (string) - Stock symbol with exchange suffix (.NS or .BO)

**Optional Fields:** All others (name auto-fetched if missing)

**Auto-Fetch Behavior:**
- If `name`, `current_price`, or `day_change_pct` missing, automatically fetches from Screener.in
- If auto-fetch fails, name is required; price can be left blank

**Response:** Created stock object with `201` status

**Errors:**
- `400` - Missing required fields or invalid data
- `400` - Stock symbol already exists

---

### 4. Update Stock

**PUT** `/stocks/<stock_id>`

Update an existing stock.

**Parameters:**
- `stock_id` (path, integer) - Stock ID

**Request Body:** Same as Create Stock (all fields optional)

**Response:** Updated stock object

**Errors:**
- `404` - Stock not found

---

### 5. Delete Stock

**DELETE** `/stocks/<stock_id>`

Delete a stock from tracking.

**Parameters:**
- `stock_id` (path, integer) - Stock ID

**Response:**
```json
{
  "message": "Stock deleted successfully"
}
```

**Errors:**
- `404` - Stock not found

---

### 6. Fetch Stock Details (Auto-Fetch)

**GET** `/stocks/fetch-details/<symbol>`

Fetch stock details from web sources (Screener.in + price scrapers).

**Parameters:**
- `symbol` (path, string) - Stock symbol (e.g., "RELIANCE.NS")

**Response:**
```json
{
  "symbol": "RELIANCE.NS",
  "name": "Reliance Industries",
  "price": 2750.50,
  "day_change_pct": 1.25,
  "status": "WATCHING",
  "in_holdings": false,
  "quantity": null
}
```

**Notes:**
- `status` is "HOLD" if stock is in holdings, "WATCHING" otherwise
- `in_holdings` and `quantity` indicate portfolio ownership

**Errors:**
- `404` - Could not fetch stock details
- `500` - Fetch operation failed

---

### 7. Refresh All Stock Prices

**POST** `/stocks/refresh-prices`

Refresh current prices for ALL tracked stocks.

**Request Body:** None

**Response:**
```json
{
  "message": "Total: 25, Success: 23, Failed: 2",
  "total": 25,
  "updated": 23,
  "failed": 2
}
```

**Process:**
- Iterates through all stocks
- Tries multiple sources (Google Finance → Moneycontrol → Investing.com → NSE API → Yahoo Finance)
- Updates database with new prices
- Also attempts to fetch day_change_pct (optional)

**Time:** ~10-30 seconds for 10-20 stocks

---

### 8. Refresh Alert Stock Prices

**POST** `/stocks/refresh-alert-stocks`

Refresh prices ONLY for stocks appearing in Analytics alerts.

**Request Body:** None

**Response:**
```json
{
  "message": "Total: 8, Success: 7, Failed: 1",
  "total": 8,
  "updated": 7,
  "failed": 1
}
```

**Alert Detection Logic:**
- **Buy Zone Alerts** (for non-holdings):
  - In buy zone: `buy_min <= price <= buy_max`
  - Near buy zone: `buy_max < price <= buy_max * 1.03` (within 3%)
- **Sell Zone Alerts** (for holdings):
  - In sell zone: `sell_min <= price <= sell_max`
  - Near sell zone: `sell_min * 0.97 <= price < sell_min` (within 3%)
- **Average Zone Alerts** (for holdings):
  - In average zone: `avg_min <= price <= avg_max`
  - Near average zone: `±3%` of zone boundaries

**Benefits:**
- Faster than refreshing all stocks
- Focuses on actionable alerts
- Automatically identifies relevant stocks

---

### 9. Get Stock Groups

**GET** `/stocks/groups`

Get all unique group names from tracked stocks.

**Response:**
```json
["Bull Run", "Cup with Handle", "Blue Chip", "Breakout"]
```

**Usage:** Populate autocomplete dropdown for Group field

---

### 10. Get Stock Sectors

**GET** `/stocks/sectors`

Get all unique sectors from tracked stocks.

**Response:**
```json
["Energy", "IT", "Banking", "FMCG", "Auto"]
```

**Usage:** Populate autocomplete dropdown for Sector field

---

## Portfolio API

### 11. Get All Transactions

**GET** `/portfolio/transactions`

Get all portfolio transactions, ordered by date (newest first).

**Response:**
```json
[
  {
    "id": 1,
    "stock_symbol": "RELIANCE.NS",
    "stock_name": "Reliance Industries",
    "transaction_type": "BUY",
    "quantity": 10.0,
    "price": 2600.00,
    "transaction_date": "2025-01-15T00:00:00",
    "reason": "Entry at support level",
    "notes": "First position in energy sector",
    "created_at": "2025-01-15T14:30:00"
  }
]
```

---

### 12. Create Transaction

**POST** `/portfolio/transactions`

Add a new buy or sell transaction.

**Request Body:**
```json
{
  "stock_symbol": "TCS.NS",
  "stock_name": "Tata Consultancy Services",
  "transaction_type": "BUY",
  "quantity": 5,
  "price": 3650.00,
  "transaction_date": "2025-10-19T00:00:00",
  "reason": "Strong quarterly results",
  "notes": "Adding to IT allocation"
}
```

**Required Fields:**
- `stock_symbol` (string, non-empty)
- `stock_name` (string, non-empty)
- `transaction_type` (string) - "BUY" or "SELL"
- `quantity` (number > 0)
- `price` (number > 0)
- `transaction_date` (ISO date string)

**Optional Fields:**
- `reason` (string)
- `notes` (string)

**Validation:**
- Symbol and name cannot be blank (trimmed)
- Quantity and price must be positive numbers
- Validated on both client and server

**Response:** Created transaction object with `201` status

**Errors:**
- `400` - Missing required fields
- `400` - Invalid data (negative quantity, empty symbol, etc.)

---

### 13. Update Transaction

**PUT** `/portfolio/transactions/<transaction_id>`

Update an existing transaction.

**Parameters:**
- `transaction_id` (path, integer) - Transaction ID

**Request Body:** Same as Create Transaction (all fields optional)

**Validation:** Same rules as Create Transaction

**Response:** Updated transaction object

**Errors:**
- `404` - Transaction not found
- `400` - Invalid data

---

### 14. Delete Transaction

**DELETE** `/portfolio/transactions/<transaction_id>`

Delete a transaction.

**Parameters:**
- `transaction_id` (path, integer) - Transaction ID

**Response:**
```json
{
  "message": "Transaction deleted successfully"
}
```

**Errors:**
- `404` - Transaction not found

---

### 15. Get Portfolio Summary

**GET** `/portfolio/summary`

Get portfolio summary with current holdings and P&L.

**Response:**
```json
{
  "holdings": [
    {
      "symbol": "RELIANCE.NS",
      "name": "Reliance Industries",
      "quantity": 10.0,
      "avg_price": 2600.00,
      "current_price": 2750.50,
      "invested_amount": 26000.00,
      "current_value": 27505.00,
      "gain_loss": 1505.00,
      "gain_loss_pct": 5.79,
      "day_change_pct": 1.25
    }
  ],
  "total_invested": 26000.00,
  "total_current_value": 27505.00,
  "total_gain_loss": 1505.00,
  "total_gain_loss_pct": 5.79,
  "portfolio_day_change_pct": 0.95
}
```

**Calculations:**
- `avg_price` = invested_amount / quantity
- `current_value` = quantity × current_price
- `gain_loss` = current_value - invested_amount
- `gain_loss_pct` = (gain_loss / invested_amount) × 100
- `portfolio_day_change_pct` = weighted average of all holdings' day_change_pct

**Notes:**
- Only includes holdings with quantity > 0
- Current prices fetched from stocks table
- If stock not in stocks table or price is null, current_price = 0

---

### 16. Get Portfolio Settings

**GET** `/portfolio/settings`

Get portfolio settings (manual total amount).

**Response:**
```json
{
  "id": 1,
  "total_amount": 500000.00,
  "updated_at": "2025-10-19T10:00:00"
}
```

**Notes:**
- If settings don't exist, creates default with total_amount = 0.0

---

### 17. Update Portfolio Settings

**PUT** `/portfolio/settings`

Update portfolio settings.

**Request Body:**
```json
{
  "total_amount": 500000.00
}
```

**Response:** Updated settings object

**Usage:** Set target portfolio size for % allocation calculations

---

## Analytics API

### 18. Get Analytics Dashboard

**GET** `/analytics/dashboard`

Get comprehensive analytics data for dashboard.

**Response:**
```json
{
  "portfolio_metrics": {
    "total_invested": 150000.00,
    "total_current_value": 165000.00,
    "total_gain_loss": 15000.00,
    "total_gain_loss_pct": 10.00,
    "portfolio_day_change_pct": 1.2,
    "holdings_count": 8
  },
  "holdings": [
    {
      "symbol": "TCS.NS",
      "name": "Tata Consultancy Services",
      "quantity": 5,
      "invested_amount": 18250.00,
      "current_value": 20000.00,
      "current_price": 4000.00,
      "gain_loss": 1750.00,
      "gain_loss_pct": 9.59,
      "day_change_pct": 1.5,
      "sector": "IT",
      "market_cap": "Large"
    }
  ],
  "action_items": {
    "in_buy_zone": [
      {
        "symbol": "INFY.NS",
        "name": "Infosys",
        "current_price": 1450.00,
        "zone": "1400-1500",
        "sector": "IT",
        "market_cap": "Large"
      }
    ],
    "in_sell_zone": [
      {
        "symbol": "RELIANCE.NS",
        "name": "Reliance Industries",
        "current_price": 2850.00,
        "zone": "2800-3000",
        "sector": "Energy",
        "market_cap": "Large"
      }
    ],
    "in_average_zone": [],
    "near_buy_zone": [
      {
        "symbol": "HDFCBANK.NS",
        "name": "HDFC Bank",
        "current_price": 1620.00,
        "zone": "1500-1600",
        "distance_pct": 1.25,
        "sector": "Banking",
        "market_cap": "Large"
      }
    ],
    "near_sell_zone": [],
    "near_average_zone": []
  },
  "action_items_count": 3,
  "top_gainers": [
    {
      "symbol": "TCS.NS",
      "name": "Tata Consultancy Services",
      "gain_loss_pct": 12.5,
      "gain_loss": 2500.00,
      "current_value": 22500.00,
      "invested_amount": 20000.00
    }
  ],
  "top_losers": [
    {
      "symbol": "BANKEX.NS",
      "name": "Bank Example",
      "gain_loss_pct": -5.2,
      "gain_loss": -1000.00,
      "current_value": 19000.00,
      "invested_amount": 20000.00
    }
  ],
  "stocks_tracked": 25,
  "total_transactions": 45
}
```

**Action Items Logic:**
- **Buy Zone**: Only for stocks NOT in holdings
- **Sell Zone**: Only for stocks IN holdings
- **Average Zone**: Only for stocks IN holdings
- **Near Zones**: ±3% threshold from zone boundaries

**Top Gainers/Losers:**
- Top 5 holdings by gain/loss percentage
- Gainers: Only positive gain_loss_pct
- Losers: Only negative gain_loss_pct

---

## Data Management API

### 19. Export Stocks to CSV

**GET** `/export/stocks`

Export all tracked stocks to CSV file.

**Response:** File download (`stocks_export_YYYYMMDD_HHMMSS.csv`)

**CSV Columns:** All stock fields

**Errors:**
- `404` - No stocks to export

---

### 20. Import Stocks from CSV

**POST** `/import/stocks`

Import stocks from CSV file.

**Request:** `multipart/form-data`
- `file` (file) - CSV file

**CSV Format:** Must match export format (same columns)

**Behavior:**
- Skips stocks with duplicate symbols (no updates)
- Adds new stocks only
- Validates each row

**Response:**
```json
{
  "message": "Import completed: 15 imported, 3 skipped",
  "imported": 15,
  "skipped": 3,
  "errors": ["Row 5: Invalid price format"]
}
```

**Errors:**
- `400` - No file provided
- `400` - Invalid file format (not CSV)
- `500` - Import failed

---

### 21. Export Transactions to CSV

**GET** `/export/transactions`

Export all transactions to CSV file.

**Response:** File download (`transactions_export_YYYYMMDD_HHMMSS.csv`)

**CSV Columns:** All transaction fields

**Errors:**
- `404` - No transactions to export

---

### 22. Import Transactions from CSV

**POST** `/import/transactions`

Import transactions from CSV file.

**Request:** `multipart/form-data`
- `file` (file) - CSV file

**CSV Format:** Must match export format

**Behavior:**
- Adds all transactions (no duplicate checking by design)
- Validates each row (dates, numeric values)

**Response:**
```json
{
  "message": "Import completed: 28 transactions imported",
  "imported": 28,
  "errors": []
}
```

**Errors:**
- `400` - No file provided
- `400` - Invalid file format
- `500` - Import failed

---

### 23. Backup Database

**GET** `/backup/database`

Download complete database backup.

**Response:** File download (`investment_manager_backup_YYYYMMDD_HHMMSS.db`)

**Process:**
1. Creates `backups/` directory if missing
2. Copies `investment_manager.db` with timestamp
3. Returns file for download

**Errors:**
- `404` - Database file not found
- `500` - Backup failed

---

### 24. Restore Database

**POST** `/restore/database`

Restore database from backup file.

**Request:** `multipart/form-data`
- `file` (file) - .db file

**Process:**
1. Validates file is .db format
2. Backs up current database (safety)
3. Replaces current database with uploaded file

**Response:**
```json
{
  "message": "Database restored successfully. Please restart the application.",
  "backup_created": "investment_manager_before_restore_YYYYMMDD_HHMMSS.db"
}
```

**⚠️ Important:** Requires application restart to take effect

**Errors:**
- `400` - No file or invalid format
- `500` - Restore failed

---

## Error Handling

### HTTP Status Codes

| Code | Meaning | When Used |
|------|---------|-----------|
| `200` | OK | Successful GET, PUT, DELETE |
| `201` | Created | Successful POST (resource created) |
| `400` | Bad Request | Validation errors, missing fields |
| `404` | Not Found | Resource doesn't exist |
| `500` | Internal Server Error | Unexpected server error |

### Error Response Format

```json
{
  "error": "Detailed error message",
  "status": 400
}
```

### Common Errors

#### Missing Required Fields
```json
{
  "error": "Missing required fields: stock_symbol, quantity",
  "status": 400
}
```

#### Validation Error
```json
{
  "error": "Quantity must be greater than 0",
  "status": 400
}
```

#### Not Found
```json
{
  "error": "Stock not found",
  "status": 404
}
```

#### Duplicate
```json
{
  "error": "Stock with this symbol already exists",
  "status": 400
}
```

---

## Rate Limiting

**Current:** No rate limiting (local app)

**If Deployed:** Recommend:
- Max 100 requests/minute per IP
- Max 10 price refresh requests/hour (web scraping is slow)

---

## CORS Configuration

**Current:** All origins allowed (`CORS(app)`)

**If Deployed:** Restrict to frontend domain only:
```python
CORS(app, origins=["https://yourdomain.com"])
```

---

## API Versioning

**Current:** No versioning (v1 implicit)

**Future:** Add `/api/v2/` prefix for breaking changes

---

## Example Usage (JavaScript/Axios)

### Fetch All Stocks
```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

async function getAllStocks() {
  try {
    const response = await axios.get(`${API_BASE}/stocks`);
    return response.data;
  } catch (error) {
    console.error('Error fetching stocks:', error.response.data);
    throw error;
  }
}
```

### Create Transaction
```javascript
async function addTransaction(data) {
  try {
    const response = await axios.post(
      `${API_BASE}/portfolio/transactions`,
      {
        stock_symbol: data.symbol,
        stock_name: data.name,
        transaction_type: data.type, // "BUY" or "SELL"
        quantity: parseFloat(data.quantity),
        price: parseFloat(data.price),
        transaction_date: data.date,
        reason: data.reason,
        notes: data.notes
      }
    );
    return response.data;
  } catch (error) {
    if (error.response.status === 400) {
      alert(`Validation Error: ${error.response.data.error}`);
    }
    throw error;
  }
}
```

### Refresh Alert Stocks
```javascript
async function refreshAlertStocks() {
  try {
    const response = await axios.post(
      `${API_BASE}/stocks/refresh-alert-stocks`
    );
    console.log(response.data.message);
    // "Total: 8, Success: 7, Failed: 1"
    return response.data;
  } catch (error) {
    console.error('Refresh failed:', error);
    throw error;
  }
}
```

---

## Changelog

### Version 1.0 (October 2025)
- Initial API release
- 22 endpoints covering all features
- Comprehensive documentation

---

**Document Version**: 1.0  
**Last Updated**: October 2025  
**Base URL**: `http://localhost:5000/api`  
**Format**: JSON  
**Authentication**: None (local app)

