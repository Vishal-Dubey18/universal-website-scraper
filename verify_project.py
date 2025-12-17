#!/usr/bin/env python3
# verify_project.py

import os
import sys
import subprocess
import time
import json

def check_files():
    print("🔍 FINAL VERIFICATION CHECKLIST")
    print("===============================\n")

    print("📁 Checking required files...")
    required_files = [
        "requirements.txt",
        "run.sh",
        "README.md",
        "design_notes.md",
        "capabilities.json",
        "backend/main.py",
        "backend/schemas.py",
        "backend/config.py",
        "backend/scraper/engine.py",
        "backend/templates/index.html"
    ]

    missing_count = 0
    for file in required_files:
        if os.path.isfile(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} (MISSING)")
            missing_count += 1

    if missing_count > 0:
        print(f"\n⚠️  {missing_count} required files are missing!")
        return False
    return True

def test_server_import():
    print("\n🚀 Testing server startup...")
    try:
        sys.path.insert(0, '.')
        from backend.main import app
        print("✅ FastAPI app imports successfully")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def check_run_sh():
    print("\n⚡ Checking run.sh...")
    if os.path.isfile("run.sh"):
        print("✅ run.sh exists")
        return True
    else:
        print("❌ run.sh missing")
        return False

def test_basic_scraping():
    print("\n🧪 Quick functional test...")
    try:
        sys.path.insert(0, '.')
        from backend.scraper.engine import ScraperEngine
        import asyncio

        async def test():
            scraper = ScraperEngine('https://httpbin.org/html')
            result = await scraper.scrape()
            if result.get('sections'):
                print('✅ Basic scraping works')
                return True
            else:
                print('⚠️  No sections returned')
                return False

        result = asyncio.run(test())
        return result
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

def main():
    if not check_files():
        sys.exit(1)

    if not test_server_import():
        sys.exit(1)

    if not check_run_sh():
        sys.exit(1)

    if not test_basic_scraping():
        sys.exit(1)

    print("\n==================================")
    print("✅ VERIFICATION COMPLETE")
    print("==================================\n")
    print("📋 NEXT STEPS:")
    print("1. Run: python verify_project.py")
    print("2. Start server: python -m backend.main (or use run.sh)")
    print("3. Test manually at http://localhost:8000")

if __name__ == "__main__":
    main()
