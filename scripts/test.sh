#!/bin/bash
# =============================================================================
# test.sh - Run tests, coverage report, and flake8 check
# =============================================================================

set -e  # Exit on any error

echo "🧪 Starting test suite..."

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
VENV_DIR="/Users/china/Desktop/Django advance/teams-clone/venv"
PYTHON="${VENV_DIR}/bin/python"
PYTEST="${VENV_DIR}/bin/pytest"
FLAKE8="${VENV_DIR}/bin/flake8"

# -----------------------------------------------------------------------------
# Check virtual environment
# -----------------------------------------------------------------------------
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found. Run setup.sh first."
    exit 1
fi

# -----------------------------------------------------------------------------
# Install test dependencies if needed
# -----------------------------------------------------------------------------
echo "📦 Checking test dependencies..."
"$PYTHON" -m pip install pytest-cov pytest-django -q

# -----------------------------------------------------------------------------
# 1. Run pytest with coverage
# -----------------------------------------------------------------------------
echo "🔬 Running tests with coverage..."
"$PYTEST" apps/ \
    --cov=apps \
    --cov-report=term-missing \
    --cov-report=html:coverage_html \
    --ds=settings.test \
    -v || {
    echo "❌ Tests failed"
    exit 1
}
echo "✅ Tests passed"

# -----------------------------------------------------------------------------
# 2. Coverage report
# -----------------------------------------------------------------------------
echo ""
echo "📊 Coverage report saved to: coverage_html/index.html"

# -----------------------------------------------------------------------------
# 3. Flake8 check
# -----------------------------------------------------------------------------
echo ""
echo "🔍 Running flake8..."
"$FLAKE8" apps/ settings/ || {
    echo "❌ Flake8 found issues"
    exit 1
}
echo "✅ Flake8 passed"

echo ""
echo "✅ All checks passed!"