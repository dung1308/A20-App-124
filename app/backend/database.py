"""
database.py
-----------
Responsibility: Database connection and session management.
Provides database engine, session factory, and initialization utilities.
"""

import logging
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from config import get_database_url, USE_MOCK
from models.schemas import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
engine = None
SessionLocal = None


def init_database() -> None:
    """
    Initialize the database engine and create all tables.
    Called once at application startup.
    """
    global engine, SessionLocal
    
    if USE_MOCK:
        logger.info("Database initialization skipped (USE_MOCK=True)")
        return
    
    try:
        db_url = get_database_url()

        # For SQLite in development, use StaticPool to avoid threading issues
        if db_url.startswith("sqlite"):
            logger.info(f"Connecting to SQLite database at: {db_url}")
            engine = create_engine(
                db_url,
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            # For PostgreSQL or other databases
            logger.info(f"Connecting to PostgreSQL database: {db_url.split('@')[-1]}") # Log host/db only for security
            engine = create_engine(db_url, echo=False)

        # Enable pgcrypto extension (optional for database-side utilities)
        if not db_url.startswith("sqlite"):
            with engine.connect() as conn:
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto;"))
                    conn.commit()
                except Exception as e:
                    logger.warning(f"Could not enable 'pgcrypto' extension: {e}. Ensure the DB user has sufficient permissions.")
        
        # Create all tables defined in Base metadata
        Base.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)
        
        logger.info(f"Database initialized successfully: {db_url}")
        
        # Log existing tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Tables in database: {tables}")
        
    except Exception as e:
        error_msg = str(e)
        if "InsufficientPrivilege" in error_msg or "permission denied" in error_msg:
            logger.error("DATABASE PERMISSION ERROR: Your user does not have CREATE privileges on the 'public' schema.")
            logger.error("FIX: Run 'GRANT ALL ON SCHEMA public TO your_user;' in pgAdmin Query Tool.")
        else:
            logger.error(f"Failed to initialize database: {e}")
        raise


def get_db_session() -> Session:
    """
    Dependency injection function for FastAPI.
    Yields a SQLAlchemy session for request handling.
    
    Usage in FastAPI:
        @app.get("/endpoint")
        def my_endpoint(db: Session = Depends(get_db_session)):
            ...
    """
    if USE_MOCK or SessionLocal is None:
        return None
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """Returns the SQLAlchemy engine."""
    return engine


def get_database_info() -> dict:
    """
    Returns metadata about the current database connection.
    """
    if USE_MOCK:
        return {"connected": True, "type": "Mock", "name": "In-memory"}
    
    url = get_database_url()
    db_type = "SQLite" if url.startswith("sqlite") else "PostgreSQL"
    
    # Extract DB name from URL (handles SQLite files and PostgreSQL connection strings)
    db_name = url.split("/")[-1].split("?")[0]
        
    return {"connected": engine is not None, "type": db_type, "name": db_name}


def drop_all_tables() -> None:
    """
    Drop all tables from the database.
    WARNING: Use only for testing/development!
    """
    if USE_MOCK or engine is None:
        logger.warning("Cannot drop tables in mock mode or without engine")
        return
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("All tables dropped successfully")
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        raise


def recreate_database() -> None:
    """
    Drop all tables and recreate them.
    Useful for resetting the database during development.
    """
    if USE_MOCK:
        logger.warning("Cannot recreate database in mock mode")
        return
    
    try:
        drop_all_tables()
        Base.metadata.create_all(bind=engine)
        logger.info("Database recreated successfully")
    except Exception as e:
        logger.error(f"Failed to recreate database: {e}")
        raise
