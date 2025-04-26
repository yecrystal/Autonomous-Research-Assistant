import os
import logging
from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, OperationFailure

logger = logging.getLogger(__name__)

# MongoDB connection settings
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "research_assistant")

# Initialize MongoDB client
client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None

async def init_mongodb() -> None:
    """
    Connect to MongoDB and initialize the database.
    
    This function should be called at the startup of the application.
    """
    global client, db
    try:
        client = AsyncIOMotorClient(MONGODB_URL)
        # Test the connection 
        await client.admin.command("ping")

        # Initialize the database
        db = client[MONGODB_DB_NAME]

        # Create indexes for collections if needed 
        await db.researches.create_index("user_id")
        await db.researches.create_index("status")
        await db.researches.create_index("created_at")

        await db.projects.create_index("user_id")

        await db.documents.create_index("research_id")
        await db.documents.create_index("url", unique=True, sparse=True)

        logger.info(f"Connected to MongoDB at {MONGODB_URL} and database {MONGODB_DB_NAME} initialized.")
    except (ConnectionFailure, OperationFailure) as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise

async def close_mongodb_connection() -> None:
    """
    Close the MongoDB connection.
    
    This function should be called at the shutdown of the application.
    """
    global client
    if client:
        client.close()
        client = None
        logger.info("MongoDB connection closed.")

def get_db() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.
    
    Returns:
        AsyncIOMotorDatabase: The MongoDB database instance.
    """
    if db is None:
        raise RuntimeError("MongoDB connection is not initialized.")
    return db

async def insert_one(collection: str, document: Dict[str, Any]) -> str:
    """
    Insert a single document into a collection.
    
    Args:
        collection (str): The name of the collection.
        document (Dict[str, Any]): The document to insert.
    
    Returns:
        str: The ID of the inserted document.
    """
    result = await db[collection].insert_one(document)
    return str(result.inserted_id)

async def find_one(collection: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Find a document in a collection.
    
    Args: 
        collection: The name of the collection
        query: The query to find the document.
        
    Returns:
        Optional[Dict[str, Any]]: The found document or None if not found.
    """
    document = await db[collection].find_one(query)
    return document

async def find_many(
        collection: str,
        query: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
) -> List[Dict[str, Any]]:
    """
    Find multiple documents in a collection.
    
    Args:
        collection: The name of the collection
        query: The query to find the documents
        skip: Number of documents to skip
        limit: Maximum number of documents to return
        sort: Optional sort criteria as list of (key, direction) tuples
        
    Returns:
        List[Dict[str, Any]]: The found documents
    """
    cursor = db[collection].find(query).skip(skip).limit(limit)
    
    if sort:
        cursor = cursor.sort(sort)
        
    return await cursor.to_list(length=limit)

async def update_one(
    collection: str,
    query: Dict[str, Any],
    update: Dict[str, Any],
    upsert: bool = False
) -> bool:
    """
    Update a single document in a collection.
    
    Args: 
        collection: The name of the collection
        query: The query to find the document
        update: The update to apply
        upsert: Whether to insert the document if it does not exist

    Returns:
        bool: True if the update was successful, False otherwise
    """
    result = await db[collection].update_one(query, {"$set": update}, upsert=upsert)
    return result.modified_count > 0 or result.upserted_id is not None

async def delete_one(collection: str, query: Dict[str, Any]) -> bool:
    """
    Delete a single document from a collection.
    
    Args:
        collection: The name of the collection
        query: The query to find the document
        
    Returns:
        bool: True if the document was deleted, False otherwise
    """
    result = await db[collection].delete_one(query)
    return result.deleted_count > 0

async def aggregate(collection: str, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Perform an aggregation on a collection.
    
    Args:
        collection: The name of the collection
        pipeline: The aggregation pipeline
        
    Returns:
        List[Dict[str, Any]]: The result of the aggregation
    """
    return await db[collection].aggregate(pipeline).to_list(length=None)

async def count_documents(collection: str, query: Dict[str, Any]) -> int:
    """
    Count the number of documents in a collection that match a query.
    
    Args:
        collection: The name of the collection
        query: The query to count documents
    Returns:
        int: The number of documents that match the query
    """
    return await db[collection].count_documents(query)

async def health_check() -> bool:
    """
    Check if the MongoDB connection is healthy.
    
    Returns:
        bool: True if the connection is healthy, False otherwise.
    """
    try:
        if db:
            await db.command("ping")
            return True
    except Exception as e:
        logger.error(f"MongoDB health check failed: {str(e)}")
        return False