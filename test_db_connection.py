#!/usr/bin/env python3
"""Test database connection and create tables"""
import sys
from app.database.connection import engine, init_db, check_db_connection
from app.database.base import Base
from app.database.models import User, SMSMessage
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test database connection and create tables"""
    print(f"Testing connection to: {settings.database_url}")
    
    # Test connection
    if check_db_connection():
        print("✓ Database connection successful")
    else:
        print("✗ Database connection failed")
        return False
    
    # Show existing tables
    print("\nExisting tables in database:")
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        for table in tables:
            print(f"  - {table}")
        if not tables:
            print("  (No tables found)")
    except Exception as e:
        print(f"Error listing tables: {e}")
    
    # Create tables
    print("\nCreating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✓ Tables created successfully")
        
        # Verify tables were created
        inspector = inspect(engine)
        new_tables = inspector.get_table_names()
        print("\nTables after creation:")
        for table in new_tables:
            print(f"  - {table}")
            
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    if test_connection():
        print("\n✓ Database setup complete!")
    else:
        print("\n✗ Database setup failed!")
        sys.exit(1)