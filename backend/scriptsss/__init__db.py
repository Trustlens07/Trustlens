#!/usr/bin/env python
"""
Initialize database tables
Run: python scripts/init_db.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
from app.models import Candidate, Score, BiasMetric, Feedback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Create all tables"""
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"✅ Tables created: {tables}")
        
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        raise

def drop_database():
    """Drop all tables (destructive)"""
    confirm = input("⚠️ This will delete ALL data. Type 'yes' to confirm: ")
    if confirm.lower() == 'yes':
        try:
            logger.info("Dropping all tables...")
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ All tables dropped")
        except Exception as e:
            logger.error(f"❌ Failed to drop tables: {e}")
            raise

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--drop", action="store_true", help="Drop all tables first")
    args = parser.parse_args()
    
    if args.drop:
        drop_database()
    
    init_database()