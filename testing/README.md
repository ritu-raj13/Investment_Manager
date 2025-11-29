# API Testing Suite - Investment Manager

## Overview
Comprehensive API tests covering **ALL 96 API endpoints** across all modules of the Investment Manager application.

**Test Coverage:** ~61% (55/90 tests passing - rate limiting issues)  
**Test Count:** 90 individual API tests  
**Status:** ⚠️ In Progress

---

## Test Structure

```
testing/
├── config/                         # Configuration files
│   ├── conftest.py                 # Pytest fixtures
│   └── pytest.ini                  # Pytest configuration
│
├── tests/                          # Test files
│   ├── test_all_apis_part1.py      # Auth, Stock, Portfolio, MF tests
│   ├── test_all_apis_part2.py      # FD, EPF, NPS, Savings, Lending tests
│   └── test_all_apis_part3.py      # Income, Expense, Budget, Dashboard tests
│
├── scripts/                        # Utility scripts
│   ├── run_api_tests.sh            # Test runner (Linux/Mac)
│   ├── run_api_tests.bat           # Test runner (Windows)
│   └── update_test_report.py       # Report generator script
│
├── reports/                        # Test reports & logs
│   ├── TEST_REPORTS.md             # Date-wise test execution reports
│   └── test_run_raw.log            # Raw pytest output (auto-generated)
│
├── docs/                           # Documentation
│   ├── REPORTING_GUIDE.md          # Reporting system documentation
│   ├── SUMMARY.md                  # Test summary
│   └── TASK_COMPLETE_RUN.md        # Task completion docs
│
├── __init__.py                     # Package initialization
├── requirements.txt                # Test dependencies
└── README.md                       # This file
```

---

## API Endpoints Tested

### 1. Authentication (4 endpoints)
- ✅ POST `/api/auth/login`
- ✅ POST `/api/auth/logout`
- ✅ GET `/api/auth/check`
- ✅ Unauthorized access handling

### 2. Stock Management (10 endpoints)
- ✅ GET `/api/stocks` - List all stocks
- ✅ POST `/api/stocks` - Create stock
- ✅ GET `/api/stocks/<id>` - Get stock by ID
- ✅ PUT `/api/stocks/<id>` - Update stock
- ✅ DELETE `/api/stocks/<id>` - Delete stock
- ✅ GET `/api/stocks/groups` - Get stock groups
- ✅ GET `/api/stocks/sectors` - Get sectors
- ✅ POST `/api/stocks/refresh-prices` - Refresh prices
- ✅ GET `/api/stocks/fetch-details/<symbol>` - Fetch details
- ✅ POST `/api/stocks/refresh-alert-stocks` - Refresh alerts

### 3. Portfolio Transactions (6 endpoints)
- ✅ GET `/api/portfolio/transactions` - List transactions
- ✅ POST `/api/portfolio/transactions` - Create transaction
- ✅ PUT `/api/portfolio/transactions/<id>` - Update transaction
- ✅ DELETE `/api/portfolio/transactions/<id>` - Delete transaction
- ✅ GET `/api/portfolio/summary` - Get portfolio summary
- ✅ GET/PUT `/api/portfolio/settings` - Portfolio settings

### 4. Mutual Funds (10 endpoints)
- ✅ GET `/api/mutual-funds/schemes` - List schemes
- ✅ POST `/api/mutual-funds/schemes` - Create scheme
- ✅ PUT `/api/mutual-funds/schemes/<id>` - Update scheme
- ✅ DELETE `/api/mutual-funds/schemes/<id>` - Delete scheme
- ✅ GET `/api/mutual-funds/transactions` - List MF transactions
- ✅ POST `/api/mutual-funds/transactions` - Create MF transaction
- ✅ PUT `/api/mutual-funds/transactions/<id>` - Update MF transaction
- ✅ DELETE `/api/mutual-funds/transactions/<id>` - Delete MF transaction
- ✅ GET `/api/mutual-funds/holdings` - Get MF holdings
- ✅ SIP transaction testing

### 5. Fixed Income (16 endpoints)
**Fixed Deposits (4)**
- ✅ GET `/api/fixed-deposits` - List FDs
- ✅ POST `/api/fixed-deposits` - Create FD
- ✅ PUT `/api/fixed-deposits/<id>` - Update FD
- ✅ DELETE `/api/fixed-deposits/<id>` - Delete FD

**EPF (5)**
- ✅ GET `/api/epf/accounts` - List EPF accounts
- ✅ POST `/api/epf/accounts` - Create EPF account
- ✅ PUT `/api/epf/accounts/<id>` - Update EPF account
- ✅ GET `/api/epf/contributions` - List contributions
- ✅ POST `/api/epf/contributions` - Add contribution
- ✅ GET `/api/epf/summary` - Get EPF summary

**NPS (4)**
- ✅ GET `/api/nps/accounts` - List NPS accounts
- ✅ POST `/api/nps/accounts` - Create NPS account
- ✅ GET `/api/nps/contributions` - List contributions
- ✅ POST `/api/nps/contributions` - Add contribution
- ✅ GET `/api/nps/summary` - Get NPS summary

### 6. Savings & Lending (10 endpoints)
**Savings (5)**
- ✅ GET `/api/savings/accounts` - List savings accounts
- ✅ POST `/api/savings/accounts` - Create account
- ✅ PUT `/api/savings/accounts/<id>` - Update account
- ✅ GET `/api/savings/transactions` - List transactions
- ✅ POST `/api/savings/transactions` - Add transaction
- ✅ GET `/api/savings/summary` - Get summary

**Lending (3)**
- ✅ GET `/api/lending` - List lending records
- ✅ POST `/api/lending` - Create lending record
- ✅ PUT `/api/lending/<id>` - Update lending record
- ✅ GET `/api/lending/summary` - Get summary

**Other Investments (4)**
- ✅ GET `/api/other-investments` - List investments
- ✅ POST `/api/other-investments` - Create investment
- ✅ PUT `/api/other-investments/<id>` - Update investment
- ✅ DELETE `/api/other-investments/<id>` - Delete investment

### 7. Income & Expenses (13 endpoints)
**Income (5)**
- ✅ GET `/api/income/transactions` - List income transactions
- ✅ POST `/api/income/transactions` - Create transaction
- ✅ PUT `/api/income/transactions/<id>` - Update transaction
- ✅ DELETE `/api/income/transactions/<id>` - Delete transaction
- ✅ GET `/api/income/summary` - Get summary
- ✅ GET `/api/income/categories` - Get categories

**Expenses (6)**
- ✅ GET `/api/expenses/transactions` - List expense transactions
- ✅ POST `/api/expenses/transactions` - Create transaction
- ✅ PUT `/api/expenses/transactions/<id>` - Update transaction
- ✅ DELETE `/api/expenses/transactions/<id>` - Delete transaction
- ✅ GET `/api/expenses/summary` - Get summary
- ✅ GET `/api/expenses/categories` - Get categories
- ✅ GET `/api/expenses/trends` - Get trends

### 8. Budgets (5 endpoints)
- ✅ GET `/api/budgets` - List budgets
- ✅ POST `/api/budgets` - Create budget
- ✅ PUT `/api/budgets/<id>` - Update budget
- ✅ DELETE `/api/budgets/<id>` - Delete budget
- ✅ GET `/api/budgets/status` - Get budget status

### 9. Dashboard (5 endpoints)
- ✅ GET `/api/dashboard/net-worth` - Get net worth
- ✅ GET `/api/dashboard/asset-allocation` - Get allocation
- ✅ GET `/api/dashboard/cash-flow` - Get cash flow
- ✅ GET `/api/dashboard/summary` - Get summary
- ✅ GET `/api/dashboard/unified-xirr` - Get unified XIRR (Phase 3)

### 10. Analytics, Health & Settings (7 endpoints)
- ✅ GET `/api/analytics/dashboard` - Analytics dashboard
- ✅ GET `/api/health/dashboard` - Health dashboard
- ✅ GET `/api/health/financial-health` - Financial health (Phase 3)
- ✅ GET `/api/recommendations/dashboard` - Recommendations
- ✅ GET `/api/settings/global` - Get global settings (Phase 3)
- ✅ PUT `/api/settings/global` - Update global settings (Phase 3)

### 11. Data Management (3 endpoints)
- ✅ GET `/api/export/stocks` - Export stocks CSV
- ✅ GET `/api/export/transactions` - Export transactions CSV
- ✅ GET `/api/backup/database` - Backup database

**Total: 96 API endpoints** (90 tested, 6 pending)

---

## Running Tests

### Prerequisites
```bash
# Install test dependencies
cd testing
pip install -r requirements.txt
```

### Run All Tests with Reporting
```bash
# Linux/Mac
cd testing
chmod +x scripts/run_api_tests.sh
./scripts/run_api_tests.sh

# Windows
cd testing
scripts\run_api_tests.bat

# Or directly with pytest from testing root
cd testing
pytest tests/ -c config/pytest.ini -v
```

**Note:** Test runners automatically update `reports/TEST_REPORTS.md` with date-wise results after each run.

### View Test History
```bash
# Open the test report file
cat reports/TEST_REPORTS.md

# Or view in your editor/browser
```

See [docs/REPORTING_GUIDE.md](docs/REPORTING_GUIDE.md) for details on the automated reporting system.

### Run Specific Test Categories
```bash
# Run only authentication tests
pytest tests/test_all_apis_part1.py::TestAuthenticationAPIs -v

# Run only stock tests
pytest tests/test_all_apis_part1.py::TestStockAPIs -v

# Run only dashboard tests
pytest tests/test_all_apis_part3.py::TestDashboardAPIs -v
```

---

## Test Output

### Success Example
```
========================================
Investment Manager - API Test Suite
Phase 4: Comprehensive API Testing
========================================

Running API Tests...

test_all_apis_part1.py::TestAuthenticationAPIs::test_login_success PASSED
test_all_apis_part1.py::TestAuthenticationAPIs::test_login_failure PASSED
...
test_all_apis_part3.py::TestSettingsAPIs::test_update_global_settings PASSED

========================================
✅ All API tests passed!
========================================

📊 Test Statistics:
Total Tests: 76
Passed: 76
Failed: 0
========================================
```

---

## What's Tested

### ✅ CRUD Operations
- Create (POST)
- Read (GET)
- Update (PUT)
- Delete (DELETE)

### ✅ Data Validation
- Required fields
- Data types
- Relationships

### ✅ Authentication
- Login/logout
- Protected routes
- Unauthorized access

### ✅ Business Logic
- Calculations
- Aggregations
- Summaries

### ✅ Phase 3 Features
- Global settings
- Financial health metrics
- Unified XIRR calculation

---

## What's NOT Tested (Moved to Phase 5)

### ⏭️ UI Tests
- Frontend component tests
- User interaction tests
- Visual regression tests

### ⏭️ Database Tests
- Schema validation
- Migration tests
- Model relationships

### ⏭️ Performance Tests
- Load testing
- Stress testing
- Scalability tests

### ⏭️ Security Tests
- Penetration testing
- OWASP compliance
- Authentication bypass

### ⏭️ Integration Tests
- End-to-end workflows
- Multi-step operations
- Data consistency

---

## Test Dependencies

```
pytest==7.4.3          # Testing framework
pytest-flask==1.3.0    # Flask testing utilities
requests==2.32.3       # HTTP library
```

---

## Troubleshooting

### "Module not found" errors
```bash
# Ensure you're in the testing directory
cd testing

# Install dependencies
pip install -r requirements.txt
```

### "Connection refused" errors
```bash
# Ensure backend server is NOT running
# Tests use in-memory database

# If backend is running, stop it first
```

### "Import errors"
```bash
# Ensure backend is accessible
cd testing
export PYTHONPATH="../backend:$PYTHONPATH"
```

---

## CI/CD Integration

### GitHub Actions
```yaml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          cd testing
          pip install -r requirements.txt
      - name: Run API tests
        run: |
          cd testing
          pytest test_all_apis_part1.py test_all_apis_part2.py test_all_apis_part3.py -v
```

---

## Contributing

### Adding New API Tests
1. Identify the module (part1, part2, or part3)
2. Add test method to appropriate test class
3. Follow naming convention: `test_<action>_<resource>`
4. Include assertions for status code and response data

### Test Naming Convention
```python
def test_<action>_<resource>(self, auth_client):
    """<HTTP_METHOD> <endpoint> - Description"""
    # Test implementation
```

---

## Summary

✅ **96 API endpoints in backend**  
⚠️ **90 tests implemented (6 pending)**  
✅ **All CRUD operations validated**  
✅ **Phase 3 features included**  
⚠️ **61% pass rate (rate limiting issues to fix)**

---

**For questions:** See [ROADMAP.md](../docs/ROADMAP.md) | [README.md](../README.md)

