#!/usr/bin/env python3
"""
Database management script for SMS Service
"""
import sys
import argparse
import subprocess
from app.database.connection import init_db, check_db_connection
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_migration(message: str):
    """Create a new migration"""
    cmd = f'alembic revision --autogenerate -m "{message}"'
    logger.info(f"Creating migration: {message}")
    subprocess.run(cmd, shell=True)


def run_migrations():
    """Run pending migrations"""
    logger.info("Running migrations...")
    subprocess.run("alembic upgrade head", shell=True)


def rollback_migration():
    """Rollback last migration"""
    logger.info("Rolling back migration...")
    subprocess.run("alembic downgrade -1", shell=True)


def show_history():
    """Show migration history"""
    subprocess.run("alembic history", shell=True)


def init_database():
    """Initialize database with tables"""
    logger.info("Initializing database...")
    if check_db_connection():
        init_db()
        logger.info("Database initialized successfully")
    else:
        logger.error("Failed to connect to database")
        sys.exit(1)


def check_connection():
    """Check database connection"""
    if check_db_connection():
        logger.info(f"Successfully connected to database: {settings.database_url}")
    else:
        logger.error(f"Failed to connect to database: {settings.database_url}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Database management for SMS Service")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Init command
    subparsers.add_parser('init', help='Initialize database tables')
    
    # Check command
    subparsers.add_parser('check', help='Check database connection')
    
    # Migration commands
    migrate_parser = subparsers.add_parser('migrate', help='Create a new migration')
    migrate_parser.add_argument('message', help='Migration message')
    
    subparsers.add_parser('upgrade', help='Run pending migrations')
    subparsers.add_parser('downgrade', help='Rollback last migration')
    subparsers.add_parser('history', help='Show migration history')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'init':
        init_database()
    elif args.command == 'check':
        check_connection()
    elif args.command == 'migrate':
        create_migration(args.message)
    elif args.command == 'upgrade':
        run_migrations()
    elif args.command == 'downgrade':
        rollback_migration()
    elif args.command == 'history':
        show_history()


if __name__ == "__main__":
    main()