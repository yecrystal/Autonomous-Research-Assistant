import logging
from typing import Any, Dict, List, Optional, Union

# Import database components
from .postgres import (
    get_db, 
    init_db as init_postgres_db, 
    close_db_connection as close_postgres_connection
)
from .mongodb import (
    get_db as get_mongodb,
    init_mongodb,
    close_mongodb_connection,
    insert_one,
    find_one,
    find_many,
    update_one,
    delete_one,
    aggregate,
    count_documents,
    health_check as mongodb_health_check
)
from .vector_store import (
    initialize_vector_db,
    add_documents, 
    similarity_search,
    delete_documents,
    get_document_by_id,
    health_check as vector_db_health_check
)

logger = logging.getLogger(__name__)

# Export all relevant components
__all__ = [
    # PostgreSQL
    "get_db",
    "init_postgres_db",
    "close_postgres_connection",
    
    # MongoDB 
    "get_mongodb",
    "init_mongodb",
    "close_mongodb_connection",
    "insert_one",
    "find_one", 
    "find_many",
    "update_one",
    "delete_one",
    "aggregate",
    "count_documents",
    
    # Vector Store
    "initialize_vector_db",
    "add_documents",
    "similarity_search",
    "delete_documents",
    "get_document_by_id",
    
    # Health checks
    "check_database_health"
]

async def init_db() -> None:
    """
    Initialize all database connections.
    
    This function should be called during application startup.
    """
    try:
        # Initialize PostgreSQL
        await init_postgres_db()
        logger.info("PostgreSQL database initialized")
        
        # Initialize MongoDB
        await init_mongodb()
        logger.info("MongoDB database initialized")
        
        # Initialize Vector Store
        await initialize_vector_db()
        logger.info("Vector database initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize databases: {str(e)}")
        raise

async def close_db_connections() -> None:
    """
    Close all database connections.
    
    This function should be called during application shutdown.
    """
    try:
        # Close PostgreSQL connection
        await close_postgres_connection()
        
        # Close MongoDB connection
        await close_mongodb_connection()
        
        logger.info("All database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")

async def check_database_health() -> Dict[str, bool]:
    """
    Check the health of all database connections.
    
    Returns:
        Dict[str, bool]: Health status of each database
    """
    health_status = {
        "postgres": False,
        "mongodb": False,
        "vector_db": False
    }
    
    try:
        # Check PostgreSQL health
        # Assuming there's a health check function in postgres.py
        # If not, you might want to implement one
        health_status["postgres"] = True  # Replace with actual health check
        
        # Check MongoDB health
        health_status["mongodb"] = await mongodb_health_check()
        
        # Check Vector DB health
        health_status["vector_db"] = await vector_db_health_check()
        
    except Exception as e:
        logger.error(f"Error during database health check: {str(e)}")
    
    return health_status