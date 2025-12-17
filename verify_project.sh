#!/bin/bash
# verify_project.sh

echo "🔍 FINAL VERIFICATION CHECKLIST"
echo "==============================="

# Check required files exist
echo ""
echo "📁 Checking required files..."
REQUIRED_FILES=(
    "requirements.txt"
    "run.sh"
    "README.md"
    "design_notes.md"
    "capabilities.json"
    "backend/main.py"
    "backend/schemas.py"
    "backend/config.py"
    "backend/scraper/engine.py"
    "backend/templates/index.html"
)

missing_count=0
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (MISSING)"
        missing_count=$((missing_count + 1))
    fi
done

if [ $missing_count -gt 0 ]; then
    echo ""
    echo "⚠️  $missing_count required files are missing!"
    exit 1
fi

# Test the server starts
echo ""
echo "🚀 Testing server startup..."
timeout 10 python -c "
import sys
sys.path.insert(0, '.')
from backend.main import app
print('✅ FastAPI app imports successfully')
"

# Check run.sh is executable
echo ""
echo "⚡ Checking run.sh permissions..."
if [ -x "run.sh" ]; then
    echo "✅ run.sh is executable"
else
    echo "⚠️  Making run.sh executable..."
    chmod +x run.sh
fi

# Quick scrape test
echo ""
echo "🧪 Quick functional test..."
timeout 30 python -c "
import sys
sys.path.insert(0, '.')
from backend.scraper.engine import ScraperEngine
import asyncio

async def test():
    try:
        scraper = ScraperEngine('https://httpbin.org/html')
        result = await scraper.scrape()
        if result.get('sections'):
            print('✅ Basic scraping works')
        else:
            print('⚠️  No sections returned')
    except Exception as e:
        print(f'❌ Error: {e}')

asyncio.run(test())
"

echo ""
echo "=================================="
echo "✅ VERIFICATION COMPLETE"
echo "=================================="
echo ""
echo "📋 NEXT STEPS:"
echo "1. Run: ./verify_project.sh"
echo "2. Make run.sh executable: chmod +x run.sh"
echo "3. Start server: ./run.sh"
echo "4. Test manually at http://localhost:8000"
