#!/usr/bin/env python3
"""Check database schema"""
from sqlalchemy import inspect, text
from app.database.connection import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_schema():
    """Display database schema information"""
    inspector = inspect(engine)
    
    print("\n=== DATABASE SCHEMA ===\n")
    
    # Get all tables
    tables = inspector.get_table_names()
    
    for table_name in tables:
        print(f"Table: {table_name}")
        print("-" * 50)
        
        # Get columns
        columns = inspector.get_columns(table_name)
        print("Columns:")
        for col in columns:
            nullable = "NULL" if col['nullable'] else "NOT NULL"
            default = f"DEFAULT {col['default']}" if col.get('default') else ""
            print(f"  - {col['name']}: {col['type']} {nullable} {default}")
        
        # Get primary keys
        pk = inspector.get_pk_constraint(table_name)
        if pk['constrained_columns']:
            print(f"\nPrimary Key: {', '.join(pk['constrained_columns'])}")
        
        # Get foreign keys
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            print("\nForeign Keys:")
            for fk in fks:
                print(f"  - {', '.join(fk['constrained_columns'])} -> {fk['referred_table']}.{', '.join(fk['referred_columns'])}")
        
        # Get indexes
        indexes = inspector.get_indexes(table_name)
        if indexes:
            print("\nIndexes:")
            for idx in indexes:
                unique = "UNIQUE" if idx.get('unique') else ""
                print(f"  - {idx['name']}: ({', '.join(idx['column_names'])}) {unique}")
        
        print("\n")
    
    # Count records
    print("=== RECORD COUNTS ===")
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"{table}: {count} records")

if __name__ == "__main__":
    check_schema()