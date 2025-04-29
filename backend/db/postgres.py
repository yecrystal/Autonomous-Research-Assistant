import os
import logging
from typing import Optional, Any

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_scoped_session
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Get database URL from environment variable or use default
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/dbname")

# Create an asynchronous engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True # Verify connection before using it
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create a scoped session for thread safety
async_session = async_scoped_session(SessionLocal, scopefunc=lambda:None)

# Base class for all models
Base = declarative_base()

# Metadata for schema creation/reflection
metadata = MetaData()

async def get_db() -> AsyncSession:
    """
    Get a database session for use in a request.
    This is a dependency that can be injected into FastAPI routes.
    
    Returns:
        AsyncSession: A database session.
    """
    async with SessionLocal() as session:
        try:
            yield session
        finally: 
            await session.close()

async def init_db() -> None:
    """
    Initialize the database by creating all tables if they do not exist.
    
    This should be called when the application starts.
    """
    try:
        # Create all tables from models
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

async def close_db_connection() -> None:
    """
    Close the database connection pool.
    
    This should be called when the applicaiton shuts down.
    """
    if engine is not None:
        await engine.dispose()
        logger.info("Database connection pool closed.")

async def execute_query(query: str, params: Optional[dict] = None) -> Any:
    """
    Execute a raw SQL query.
    
    Args:
        query (str): The SQL query to execute.
        params (Optional[dict]): Parameters for the SQL query.
    
    Returns:
        Any: The result of the query.
    """
    async with SessionLocal() as session:
        try:
            result = await session.execute(query, params or {})
            return result
        except Exception as e:
            await session.rollback()
            logger.error(f"Error executing query: {str(e)}")
            raise
        finally:
            await session.close()

async def health_check() -> bool:
    """
    Check if the database connection is healthy.
    
    Returns:
        bool: True if the connection is healthy, False otherwise.
    """
    try: 
        async with SessionLocal() as session:
            await session.execute("SELECT 1")
            return
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False
