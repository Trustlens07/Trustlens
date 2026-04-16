from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def _create_engine():
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL is not set - database will not be available")
        return None
    try:
        return create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            pool_size=10,        # Number of connections to keep in pool
            max_overflow=20,     # Maximum overflow connections
            echo=settings.DEBUG,  # Log SQL queries in debug mode
        )
    except Exception as e:
        logger.error("Failed to create database engine: %s", str(e))
        return None


# Create database engine with connection pooling
engine = _create_engine()

def _require_engine():
    if engine is None:
        raise RuntimeError("Database is not configured or unreachable (engine not initialized)")
    return engine


# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_require_engine() if engine else None)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    if engine is None:
        raise RuntimeError("Database is not configured or unreachable")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_database_connection() -> bool:
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False

def init_database():
    """Initialize database (create tables if not exist)"""
    from app.models import candidate, score, bias_metric, feedback
    
    try:
        if engine is None:
            raise RuntimeError("Database is not configured or unreachable")
        # Check if tables exist
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        if not existing_tables:
            logger.info("Creating database tables...")
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables created successfully")
        else:
            logger.info(f"Tables already exist: {existing_tables}")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise