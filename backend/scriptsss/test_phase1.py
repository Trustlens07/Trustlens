#!/usr/bin/env python
"""
Test Phase 1 setup
Run: python scripts/test_phase1.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("\n" + "="*60)
    print("Testing Phase 1 Setup")
    print("="*60 + "\n")
    
    # Test 1: Configuration
    print("1. Testing Configuration...")
    try:
        from app.core.config import settings
        print(f"   ✅ APP_NAME: {settings.APP_NAME}")
        print(f"   ✅ SUPABASE_URL: {settings.SUPABASE_URL[:30]}..." if settings.SUPABASE_URL else "   ⚠️ SUPABASE_URL not set")
        print(f"   ✅ DATABASE_URL: {settings.DATABASE_URL[:30]}..." if settings.DATABASE_URL else "   ⚠️ DATABASE_URL not set")
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return
    
    # Test 2: Database Connection
    print("\n2. Testing Database Connection...")
    try:
        from app.core.database import test_connection
        if test_connection():
            print("   ✅ Database connected")
        else:
            print("   ❌ Database connection failed")
    except Exception as e:
        print(f"   ❌ Database error: {e}")
    
    # Test 3: Supabase Connection
    print("\n3. Testing Supabase Connection...")
    try:
        from app.services.supabase_client import test_connection
        if test_connection():
            print("   ✅ Supabase connected")
        else:
            print("   ❌ Supabase connection failed")
    except Exception as e:
        print(f"   ❌ Supabase error: {e}")
    
    # Test 4: Models
    print("\n4. Testing Models...")
    try:
        from app.models import Candidate, Score, BiasMetric, Feedback
        print("   ✅ All models imported successfully")
    except Exception as e:
        print(f"   ❌ Model import failed: {e}")
    
    print("\n" + "="*60)
    print("Phase 1 Setup Complete")
    print("="*60 + "\n")
    
    print("Next steps:")
    print("1. Run: python scripts/init_db.py")
    print("2. Run: uvicorn app.main:app --reload")
    print("3. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()