#!/bin/bash
# API Test Runner for Investment Manager
# Tests all API endpoints and generates date-wise report

echo "========================================="
echo "Investment Manager - API Test Suite"
echo "Phase 4: Comprehensive API Testing"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get to testing root directory
cd "$(dirname "$0")/.."

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "Installing test dependencies..."
    pip install -r requirements.txt
fi

echo "Running API Tests..."
echo ""

# Run all API tests
pytest tests/test_all_apis_part1.py tests/test_all_apis_part2.py tests/test_all_apis_part3.py \
    -c config/pytest.ini \
    -v \
    --tb=short \
    2>&1 | tee reports/test_run_raw.log

TEST_RESULT=$?

echo ""
echo "========================================="

if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ All API tests passed!${NC}"
else
    echo -e "${YELLOW}⚠️ Some tests had issues${NC}"
fi

echo "========================================="
echo ""

# Update TEST_REPORTS.md with results
echo "Updating test report..."
python scripts/update_test_report.py

echo ""
echo "Test Results saved to: reports/test_run_raw.log"
echo "Report updated in: reports/TEST_REPORTS.md"
echo ""

# Count test statistics
echo "📊 Test Statistics:"
TOTAL_TESTS=$(grep -c "PASSED\|FAILED" reports/test_run_raw.log || echo "0")
PASSED_TESTS=$(grep -c "PASSED" reports/test_run_raw.log || echo "0")
FAILED_TESTS=$(grep -c "FAILED" reports/test_run_raw.log || echo "0")

echo "Total Tests: $TOTAL_TESTS"
echo -e "Passed: ${GREEN}$PASSED_TESTS${NC}"
if [ $FAILED_TESTS -gt 0 ]; then
    echo -e "Failed: ${RED}$FAILED_TESTS${NC}"
fi

echo ""
echo "========================================="

exit $TEST_RESULT

