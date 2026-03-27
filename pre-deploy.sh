#!/bin/bash
#
# Pre-deploy script for notes-flow
# Runs tests with coverage and blocks deployment if tests fail or coverage is below threshold
#

set -e

# Configuration
COVERAGE_THRESHOLD="${COVERAGE_THRESHOLD:-80}"
COVERAGE_MINUS_CHECK="${COVERAGE_MINUS_CHECK:-0}"
EXIT_CODE=0

# Use virtual environment Python if available
if [ -f "venv/bin/python" ]; then
    PYTHON_BIN="venv/bin/python"
else
    PYTHON_BIN="python3"
fi

echo "=========================================="
echo "  Pre-deploy checks for notes-flow"
echo "=========================================="
echo ""
echo "Configuration:"
echo "  COVERAGE_THRESHOLD: ${COVERAGE_THRESHOLD}%"
echo "  COVERAGE_MINUS_CHECK: ${COVERAGE_MINUS_CHECK}"
echo ""

# Run tests with coverage
echo "Running tests with coverage..."
echo ""

if ! "$PYTHON_BIN" -m coverage run -m pytest tests/ -v --tb=short 2>&1; then
    echo ""
    echo "ERROR: Tests failed!"
    EXIT_CODE=1
fi

# Generate coverage report
echo ""
echo "=========================================="
echo "  Coverage Report"
echo "=========================================="
echo ""

# Get total coverage percentage
TOTAL_COVERAGE=$("$PYTHON_BIN" -m coverage report 2>/dev/null | grep "^TOTAL" | awk '{print $NF}' | sed 's/%//')

# Round to integer
TOTAL_COVERAGE="${TOTAL_COVERAGE%.*}"

echo "Total coverage: ${TOTAL_COVERAGE}%"

# Show detailed coverage report
"$PYTHON_BIN" -m coverage report --show-missing || true

echo ""
echo "=========================================="
echo "  Validation Results"
echo "=========================================="
echo ""

# Check coverage threshold
if [ -z "$TOTAL_COVERAGE" ]; then
    echo "ERROR: Could not determine coverage percentage"
    EXIT_CODE=1
elif [ "$TOTAL_COVERAGE" -lt "$COVERAGE_THRESHOLD" ]; then
    echo "ERROR: Coverage ${TOTAL_COVERAGE}% is below threshold ${COVERAGE_THRESHOLD}%"
    EXIT_CODE=1
else
    echo "OK: Coverage ${TOTAL_COVERAGE}% >= ${COVERAGE_THRESHOLD}%"
fi

echo ""

# Final status
if [ $EXIT_CODE -eq 0 ]; then
    echo "=========================================="
    echo "  PRE-DEPLOY CHECKS PASSED"
    echo "=========================================="
else
    echo "=========================================="
    echo "  PRE-DEPLOY CHECKS FAILED"
    echo "=========================================="
    echo ""
    echo "Deployment will be blocked."
fi

exit $EXIT_CODE
