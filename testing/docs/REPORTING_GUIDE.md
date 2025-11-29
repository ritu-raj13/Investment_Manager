# Test Reporting System

## Overview

The testing framework includes **automated date-wise reporting** that tracks test execution results over time in `testing/reports/TEST_REPORTS.md`.

**Status:** ✅ Fully Implemented  
**Last Updated:** November 1, 2025

---

## Files

### 1. `reports/TEST_REPORTS.md`
- **Purpose:** Historical test execution report with date-wise entries (latest at top)
- **Format:** Markdown with test history table and detailed reports
- **Auto-updated:** After each test run

### 2. `scripts/update_test_report.py`  
- **Purpose:** Parses test results and updates TEST_REPORTS.md
- **Runs:** Automatically after test execution
- **Functions:** Parse pytest output, extract statistics, append to history

### 3. `scripts/run_api_tests.sh` / `run_api_tests.bat`
- **Purpose:** Execute tests from backend venv and generate reports
- **Process:** Run pytest → Save output → Update report → Display summary

### 4. `reports/test_run_raw.log`
- **Purpose:** Raw pytest output (auto-generated each run)
- **Used by:** update_test_report.py for parsing

---

## Usage

### Run Tests & Generate Report
```bash
# Linux/Mac
cd testing
./scripts/run_api_tests.sh

# Windows
cd testing
scripts\run_api_tests.bat
```

### View Test History
```bash
# View report (latest results at top)
cat reports/TEST_REPORTS.md
```

---

## Report Format

### Test History Table
| Date | Total | Passed | Failed | Errors | Pass Rate | Status | Notes |
|------|-------|--------|--------|--------|-----------|--------|-------|
| 2025-11-01 PM | 90 | 55 | 11 | 24 | 61.1% | 🟡 In Progress | Rate limiting fixed |
| 2025-11-01 AM | 90 | 55 | 11 | 24 | 61.1% | 🟡 In Progress | First run |

**Status Indicators:**
- ✅ **Passing** - 95%+ pass rate
- 🟢 **Good** - 80-94% pass rate  
- 🟡 **In Progress** - 60-79% pass rate
- 🔴 **Failing** - <60% pass rate

---

## Features

### ✅ Date-Wise Tracking
- Each test run adds new entry at top
- Historical trends visible
- Maintains chronological order

### ✅ Automated Updates  
- No manual editing required
- Runs after each test execution
- Consistent formatting

### ✅ Detailed Reports
- Full test breakdown per date
- Identifies failing tests
- Lists issues and recommendations

---

## Integration with CI/CD

### GitHub Actions Example
```yaml
- name: Run API Tests
  run: |
    cd backend
    source venv/bin/activate
    cd ../testing
    pytest tests/ -c config/pytest.ini -v

- name: Upload Test Report
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: testing/reports/TEST_REPORTS.md
```

---

## Maintenance

### Manual Report Entry
Add row to history table in TEST_REPORTS.md:
```markdown
| 2025-11-02 | 90 | 85 | 5 | 0 | 94.4% | 🟢 Good | Fixed rate limiting |
```

### Archiving Old Reports
```bash
# Archive quarterly
cp reports/TEST_REPORTS.md reports/archive/TEST_REPORTS_2025_Q4.md
```

---

## Troubleshooting

**Report not updating?**
- Check if `test_run_raw.log` exists in reports/
- Run `python scripts/update_test_report.py` manually
- Verify pytest output format

**Wrong statistics?**
- Check regex patterns in update_test_report.py
- Verify log file has complete output

---

## See Also

- **Main Documentation:** `testing/README.md`
- **Test Coverage Analysis:** `testing/TEST_COVERAGE_ANALYSIS.md`
- **Audit Report:** `docs/DOCUMENTATION_AUDIT_REPORT.md`

---

**Version:** 1.0.0

---

## Files

### 1. `TEST_REPORTS.md`
- **Purpose:** Historical test execution report
- **Format:** Markdown with date-wise entries
- **Sections:**
  - Latest Test Run (summary)
  - Test History (table)
  - Detailed Reports (per date)

### 2. `update_test_report.py`
- **Purpose:** Parses test results and updates TEST_REPORTS.md
- **Runs:** Automatically after each test execution
- **Functions:**
  - Parse pytest output from `test_run_raw.log`
  - Extract statistics (passed/failed/errors)
  - Append new row to history table
  - Update latest run section

### 3. `run_api_tests.sh` / `run_api_tests.bat`
- **Purpose:** Execute tests and generate reports
- **Process:**
  1. Run pytest
  2. Save output to `test_run_raw.log`
  3. Run `update_test_report.py`
  4. Display summary

### 4. `test_run_raw.log`
- **Purpose:** Raw pytest output
- **Generated:** Each test run
- **Used by:** `update_test_report.py` for parsing

---

## Usage

### Run Tests & Generate Report

```bash
# Linux/Mac
cd testing
./run_api_tests.sh

# Windows
cd testing
run_api_tests.bat
```

### Manual Report Update

```bash
cd testing
python update_test_report.py
```

---

## Report Format

### Test History Table

| Date | Total | Passed | Failed | Errors | Pass Rate | Status | Notes |
|------|-------|--------|--------|--------|-----------|--------|-------|
| 2025-11-01 | 90 | 55 | 11 | 24 | 61.1% | 🟡 In Progress | First run |

### Status Indicators

- ✅ **Passing** - 95%+ pass rate
- 🟢 **Good** - 80-94% pass rate
- 🟡 **In Progress** - 60-79% pass rate
- 🔴 **Failing** - <60% pass rate

---

## Features

### ✅ Date-Wise Tracking
- Each test run adds new row to history table
- Maintains chronological order
- Shows trends over time

### ✅ Automated Updates
- No manual editing required
- Runs after each test execution
- Consistent formatting

### ✅ Detailed Reports
- Full test breakdown per date
- Identifies failing tests
- Lists issues and recommendations

### ✅ Summary Statistics
- Pass/fail counts
- Error tracking
- Execution time
- Pass rate percentage

---

## Workflow

```
1. Developer runs: ./run_api_tests.sh
   ↓
2. Pytest executes all tests
   ↓
3. Output saved to: test_run_raw.log
   ↓
4. update_test_report.py parses results
   ↓
5. TEST_REPORTS.md updated with new entry
   ↓
6. Developer views results in TEST_REPORTS.md
```

---

## Example Report Entry

### Test Run: November 1, 2025

**Execution Time:** 37.17 seconds  
**Pass Rate:** 61.1% (55/90)  
**Status:** 🟡 In Progress

**Summary:**
- ✅ Fixed Income tests: 15/15 passing
- ✅ Dashboard tests: 12/12 passing
- 🔴 Stock API tests: Rate limiting issues
- 🟡 Other tests: Minor fixes needed

**Actions Required:**
1. Fix rate limiting in auth_client fixture
2. Update test data for Other Investments
3. Add error handling in delete/update tests

---

## Benefits

### For Developers
- **Quick Status Check** - See latest results at top of file
- **Historical Trends** - Compare pass rates over time
- **Issue Tracking** - Identify recurring problems

### For QA
- **Regression Detection** - Spot when pass rate drops
- **Test Coverage** - See what's tested
- **Quality Metrics** - Track improvement over time

### For Project Management
- **Progress Tracking** - Visual timeline of testing status
- **Release Readiness** - Quick quality check before deployment
- **Documentation** - Test history for audits

---

## Maintenance

### Adding Custom Notes

Edit `run_api_tests.sh` or `.bat`:
```bash
python update_test_report.py "Your custom note here"
```

### Manual Entry

Add row to history table:
```markdown
| 2025-11-02 | 90 | 85 | 5 | 0 | 94.4% | 🟢 Good | Fixed rate limiting |
```

### Archiving Old Reports

Create archive files for quarters/years:
```bash
# Copy old entries to archive
cp TEST_REPORTS.md TEST_REPORTS_2025_Q4.md
# Clean up old entries from main file
```

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
- name: Run API Tests
  run: |
    cd testing
    ./run_api_tests.sh

- name: Upload Test Report
  uses: actions/upload-artifact@v2
  with:
    name: test-reports
    path: testing/TEST_REPORTS.md

- name: Commit Updated Report
  run: |
    git config user.name "GitHub Actions"
    git config user.email "actions@github.com"
    git add testing/TEST_REPORTS.md
    git commit -m "Update test report [skip ci]"
    git push
```

---

## Troubleshooting

### Report not updating?
- Check if `test_run_raw.log` exists
- Verify pytest output format hasn't changed
- Run `python update_test_report.py` manually to see errors

### Wrong statistics?
- Pytest output format might have changed
- Check regex patterns in `update_test_report.py`
- Verify log file has complete output

### Duplicate entries?
- Script doesn't check for duplicates by design
- Each run adds new row
- Remove duplicates manually if needed

---

## Future Enhancements

- 📊 Generate HTML reports with charts
- 📈 Add pass rate trend graphs
- 🔔 Send notifications on pass rate drops
- 📝 Generate weekly/monthly summaries
- 🎯 Set pass rate targets and alerts

---

**Status:** ✅ Fully Implemented  
**Last Updated:** November 1, 2025  
**Version:** 1.0.0

