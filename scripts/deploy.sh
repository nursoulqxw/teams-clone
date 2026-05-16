#!/bin/bash
# =============================================================================
# deploy.sh - Deployment script
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting deployment..."

VENV_DIR="/Users/china/Desktop/Django advance/teams-clone/venv"
PYTHON="${VENV_DIR}/bin/python"

# -----------------------------------------------------------------------------
# Activate virtual environment
# -----------------------------------------------------------------------------
if [ ! -f "$PYTHON" ]; then
    echo "❌ Virtual environment not found"
    exit 1
fi

# -----------------------------------------------------------------------------
# 1. Git pull
# -----------------------------------------------------------------------------
echo "📥 Pulling latest changes..."
git pull origin main --rebase || {
    echo "❌ Git pull failed"
    exit 1
}
echo "✅ Code updated"

# -----------------------------------------------------------------------------
# 2. Install/update dependencies
# -----------------------------------------------------------------------------
echo "📦 Installing dependencies..."
"$PYTHON" -m pip install -r requirements/prod.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}
echo "✅ Dependencies updated"

# -----------------------------------------------------------------------------
# 3. Collect static files
# -----------------------------------------------------------------------------
echo "📁 Collecting static files..."
"$PYTHON" manage.py collectstatic --noinput || {
    echo "❌ collectstatic failed"
    exit 1
}
echo "✅ Static files collected"

# -----------------------------------------------------------------------------
# 4. Run migrations
# -----------------------------------------------------------------------------
echo "🗄️  Running migrations..."
"$PYTHON" manage.py migrate || {
    echo "❌ Migrations failed"
    exit 1
}
echo "✅ Migrations completed"

# -----------------------------------------------------------------------------
# 5. Restart gunicorn
# -----------------------------------------------------------------------------
echo "🔄 Restarting gunicorn..."
if command -v systemctl &> /dev/null; then
    sudo systemctl restart gunicorn || {
        echo "❌ Failed to restart gunicorn"
        exit 1
    }
elif command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart gunicorn || {
        echo "❌ Failed to restart gunicorn"
        exit 1
    }
else
    echo "⚠️  Could not restart gunicorn: systemctl/supervisorctl not found"
fi
echo "✅ Gunicorn restarted"

echo ""
echo "✅ Deployment completed successfully!"