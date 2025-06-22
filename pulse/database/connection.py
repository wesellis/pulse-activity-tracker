"""
Database connection and session management
Handles SQLAlchemy database setup and connection pooling
"""

import os
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base

logger = logging.getLogger(__name__)

# Database configuration
DB_NAME = os.getenv('PULSE_DB_NAME', 'pulse_activity.db')
DB_DIR = Path(os.getenv('PULSE_DB_DIR', os.path.expanduser('~/.pulse')))
DB_PATH = DB_DIR / DB_NAME

# Ensure database directory exists
DB_DIR.mkdir(parents=True, exist_ok=True)

# Create database URL
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with optimized settings for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Allow multiple threads
        "timeout": 30  # 30 second timeout for locks
    },
    poolclass=StaticPool,  # Use static pool for SQLite
    echo=False  # Set to True for SQL debugging
)

# Enable WAL mode for better concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA cache_size=10000")
    cursor.execute("PRAGMA temp_store=MEMORY")
    cursor.close()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)


def init_db():
    """Initialize database and create all tables"""
    try:
        logger.info(f"Initializing database at {DB_PATH}")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False


def drop_db():
    """Drop all tables (use with caution!)"""
    try:
        logger.warning("Dropping all database tables")
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped")
        return True
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session
    Use with FastAPI dependency injection or manually
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Session:
    """
    Context manager for database sessions
    Use in non-FastAPI contexts
    
    Example:
        with get_db_session() as db:
            user = db.query(User).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def test_connection() -> bool:
    """Test database connection"""
    try:
        with get_db_session() as db:
            db.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_db_stats() -> dict:
    """Get database statistics"""
    try:
        stats = {
            'database_path': str(DB_PATH),
            'database_exists': DB_PATH.exists(),
            'database_size_mb': 0,
            'table_count': 0,
            'connection_status': 'unknown'
        }
        
        if DB_PATH.exists():
            stats['database_size_mb'] = round(DB_PATH.stat().st_size / 1024 / 1024, 2)
        
        with get_db_session() as db:
            # Count tables
            result = db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table'"
            ).scalar()
            stats['table_count'] = result
            stats['connection_status'] = 'connected'
            
            # Get row counts for each table
            stats['row_counts'] = {}
            for table in Base.metadata.tables.keys():
                try:
                    count = db.execute(f"SELECT COUNT(*) FROM {table}").scalar()
                    stats['row_counts'][table] = count
                except:
                    stats['row_counts'][table] = 0
        
        return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {
            'error': str(e),
            'connection_status': 'error'
        }


def vacuum_db():
    """Vacuum database to reclaim space and optimize"""
    try:
        with engine.connect() as conn:
            conn.execute("VACUUM")
            conn.commit()
        logger.info("Database vacuum completed")
        return True
    except Exception as e:
        logger.error(f"Failed to vacuum database: {e}")
        return False


def analyze_db():
    """Analyze database to update statistics"""
    try:
        with engine.connect() as conn:
            conn.execute("ANALYZE")
            conn.commit()
        logger.info("Database analyze completed")
        return True
    except Exception as e:
        logger.error(f"Failed to analyze database: {e}")
        return False