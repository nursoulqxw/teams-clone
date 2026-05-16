#!/bin/bash
# =============================================================================
# clean.sh - Clean up temporary and cache files
# =============================================================================

echo "🧹 Starting cleanup..."

# -----------------------------------------------------------------------------
# 1. Remove __pycache__ directories
# -----------------------------------------------------------------------------
echo "🗑️  Removing __pycache__ directories..."
find . -type d -name "__pycache__" -not -path "./venv/*" -exec rm -rf {} + 2>/dev/null || true
echo "✅ __pycache__ removed"

# -----------------------------------------------------------------------------
# 2. Remove *.pyc files
# -----------------------------------------------------------------------------
echo "🗑️  Removing *.pyc files..."
find . -name "*.pyc" -not -path "./venv/*" -delete 2>/dev/null || true
echo "✅ *.pyc files removed"

# -----------------------------------------------------------------------------
# 3. Remove coverage files
# -----------------------------------------------------------------------------
echo "🗑️  Removing coverage files..."
rm -rf coverage_html/ 2>/dev/null || true
rm -f .coverage 2>/dev/null || true
rm -f coverage.xml 2>/dev/null || true
echo "✅ Coverage files removed"

# -----------------------------------------------------------------------------
# 4. Remove other temp files
# -----------------------------------------------------------------------------
echo "🗑️  Removing other temp files..."
find . -name "*.pyo" -not -path "./venv/*" -delete 2>/dev/null || true
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "*.log" -not -path "./venv/*" -delete 2>/dev/null || true
echo "✅ Temp files removed"

echo ""
echo "✅ Cleanup completed!"