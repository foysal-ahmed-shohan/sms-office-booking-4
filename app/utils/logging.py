import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler
from app.config import settings


def setup_logging():
    """Configure application logging with both console and file output"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.log_file_path).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(getattr(logging, settings.log_level))
    
    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        filename=settings.log_file_path,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all logs
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Log startup information
    root_logger.info("=" * 60)
    root_logger.info("Logging system initialized")
    root_logger.info(f"Log file: {settings.log_file_path}")
    root_logger.info(f"Log level: {settings.log_level}")
    root_logger.info(f"Max log size: {settings.log_max_size} bytes")
    root_logger.info(f"Backup count: {settings.log_backup_count}")
    root_logger.info("=" * 60)
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)
    
    # Reduce noise from libraries in console, but keep in file
    for logger_name in ["httpx", "httpcore"]:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)