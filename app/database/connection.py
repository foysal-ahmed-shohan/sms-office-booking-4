from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from contextlib import contextmanager
import logging
from typing import Generator
from app.config import settings
from app.database.base import Base

logger = logging.getLogger(__name__)


# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Log pool events
@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set connection parameters"""
    logger.debug("Database connection established")


@event.listens_for(Pool, "checkout")
def log_checkout(dbapi_connection, connection_record, connection_proxy):
    """Log when connection is checked out from pool"""
    logger.debug("Connection checked out from pool")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Usage in FastAPI:
        @app.get("/")
        def read_root(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        logger.debug("Database session created")
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database session closed")


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    Usage:
        with get_db_context() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        logger.debug("Database context session created")
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.debug("Database context session closed")


def init_db():
    """Initialize database - create all tables"""
    try:
        logger.info("Initializing database...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def check_db_connection():
    """Check if database is accessible"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False