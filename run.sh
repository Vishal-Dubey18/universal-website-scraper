#!/bin/bash

# ============================================
# Universal Website Scraper - Lyftr AI Assignment
# Run Script
# ============================================

set -e

echo "========================================"
echo "   Universal Website Scraper - Setup"
echo "========================================"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 10 ]; then
    echo "❌ Error: Python 3.10 or higher is required. Found Python $PYTHON_VERSION"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION detected"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
echo "📂 Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "❌ Error: Cannot activate virtual environment"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright Chromium..."
playwright install chromium

# Create folders
mkdir -p backend/templates backend/static logs data

echo ""
echo "========================================"
echo "          🚀 Ready to Launch"
echo "========================================"
echo ""
echo "🌍 Frontend: http://localhost:8000/"
echo "❤️  Health:   http://localhost:8000/healthz"
echo "📄 Docs:     http://localhost:8000/api/docs"
echo ""
echo "📋 Press Ctrl+C to stop the server"
echo "========================================"
echo ""

# Start server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
