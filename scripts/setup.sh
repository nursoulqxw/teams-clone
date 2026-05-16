#!/bin/bash
# =============================================================================
# setup.sh - Project setup script
# =============================================================================

set -e  # Exit on any error

echo "🚀 Starting project setup..."

# -----------------------------------------------------------------------------
# 1. Create virtual environment
# -----------------------------------------------------------------------------
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists, skipping..."
fi

# -----------------------------------------------------------------------------
# 2. Activate virtual environment
# -----------------------------------------------------------------------------
echo "🔄 Activating virtual environment..."
source venv/bin/activate || {
    echo "❌ Failed to activate virtual environment"
    exit 1
}

# -----------------------------------------------------------------------------
# 3. Install dependencies
# -----------------------------------------------------------------------------
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements/base.txt || {
    echo "❌ Failed to install dependencies"
    exit 1
}
echo "✅ Dependencies installed"

# -----------------------------------------------------------------------------
# 4. Copy .env.example → .env
# -----------------------------------------------------------------------------
echo "⚙️  Setting up environment variables..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env file created from .env.example"
    echo "⚠️  Please update .env with your settings before continuing"
else
    echo "⚠️  .env already exists, skipping..."
fi

# -----------------------------------------------------------------------------
# 5. Run migrations
# -----------------------------------------------------------------------------
echo "🗄️  Running migrations..."
python manage.py migrate || {
    echo "❌ Migrations failed"
    exit 1
}
echo "✅ Migrations completed"

# -----------------------------------------------------------------------------
# 6. Create superuser
# -----------------------------------------------------------------------------
echo "👤 Creating superuser..."
python manage.py createsuperuser || {
    echo "⚠️  Superuser creation skipped or failed"
}

# -----------------------------------------------------------------------------
# 7. Populate database
# -----------------------------------------------------------------------------
echo "🌱 Populating database..."
python manage.py populate_db || {
    echo "⚠️  populate_db failed or not found, skipping..."
}

echo ""
echo "✅ Setup completed successfully!"
echo "Run: source venv/bin/activate && python manage.py runserver"