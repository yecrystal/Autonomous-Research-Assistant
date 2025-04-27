import os
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import uuid

from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_weaviate import WeaviateVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_anthropic import AnthropicEmbeddings
import pinecone

logger = logging.getLogger(__name__)

# Vector database configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "pinecone")  # Options: "pinecone", "weaviate"

# Weaviate settings
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")

# Embedding settings
EMBEDDINGS_MODEL = os.getenv("EMBEDDINGS_MODEL", "openai").lower() # "openai" or anthropic
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class VectorDBType(str, Enum):
    PINECONE = "pinecone"

class EmbeddingsModelType(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"

# Global vector store instance
vector_store = None
embeddings_model = None

def get_embeddings_model() -> Embeddings:
    """
    Get the embeddings model based on configuration.

    Returns:
        Embeddings: The embeddings model instance
    """
    global embeddings_model

    if embeddings_model:
        return embeddings_model
    
    if EMBEDDINGS_MODEL == EmbeddingsModelType.OPENAI:
        embeddings_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    elif EMBEDDINGS_MODEL == EmbeddingsModelType.ANTHROPIC:
        embeddings_model = AnthropicEmbeddings(api_key=ANTHROPIC_API_KEY)
    else:
        # Default to OpenAI
        embeddings_model = OpenAIEmbeddings(api_key=OPENAI_API_KEY)
    
    return embeddings_model

async def initialize_vector_db():
    """
    Initialize the vector database connection.

    This should be called when the application starts.
    """
    global vector_store

    try:
        embeddings = get_embeddings_model()

        if VECTOR_DB_TYPE == VectorDBType.PINECONE:
            # Initialize Pinecone
            pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

            # Create the index if it doesn't exist
            if PINECONE_INDEX_NAME not in pinecone.list_index():
                pinecone.create_index(
                    name=PINECONE_INDEX_NAME,
                    dimensions=1530, # OpenAI embeddings dimension
                    metric="cosine"
                )

            vector_store = PineconeVectorStore(
                index_name=PINECONE_INDEX_NAME,
                embedding=embeddings,
                test_key="text"
            )
        
        logger.info(f"Initialized vector database: {VECTOR_DB_TYPE}")
    except Exception as e:
        logger.error(f"Failed to initialize vector database: {str(e)}")
        raise

async def add_documents(
        documents: List[Document],
        namespace: str = "default"
) -> List[str]:
    """
    Add documents to the vector store.

    Args:
        documents: List of documents to add
        namespace: Namespace/collection for the documents (used for filtering)

    Returns:
        List[str]: IDs of the aded documents
    """
    if vector_store is None: 
        await initialize_vector_db()
    try:
        # Add namespace to metadata for filtering
        for doc in documents:
            doc.metadata["namespace"] = namespace
            if "id" not in doc.metadata:
                doc.metadata["id"] = str[uuid.uuid4()]
        
        # Add documents to vector store
        ids = vector_store.add_documents(documents)
        return ids
    except Exception as e:
        logger.error(f"Error adding documents to vector store: {str(e)}")
        raise

async def similarity_search(
        query: str,
        k: int = 5,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None
) -> List[Document]:
    """
    Perform a similarity search in the vector store.

    Args:
        qeury: The query text
        k: Number of results to return
        namespace: Optional namespace to filter results
        filter: Additional filters to apply

    Returns:
        List[Document]: The msot similar documents
    """
    if vector_store is None:
        await initialize_vector_db()
    
    try:
        search_filter = filter or {}

        # Add namespace filter if provided
        if namespace:
            search_filter["namespace"] = namespace
        
        # Perform search with filters
        if search_filter:
            if VECTOR_DB_TYPE == VectorDBType.PINECONE:
                docs = vector_store.similarity_search(
                    query=query,
                    k=k,
                    filter=search_filter
                )
        else:
            docs = vector_store.similarity_search(query=query, k=k)
        
        return docs
    except Exception as e:
        logger.error(f"Error during similarity search: {str(e)}")
        raise

async def delete_documents(
    ids: Optional[List[str]] = None,
    filter: Optional[Dict[str, Any]] = None,
    namespace: Optional[str] = None
) -> bool:
    """
    Delete documents from the vector store.
    
    Args:
        ids: Specific document IDs to delete
        filter: Filter to select documents for deletion
        namespace: Namespace to filter documents
        
    Returns:
        bool: True if deletion was successful
    """
    if vector_store is None:
        await initialize_vector_db()
    
    try:
        delete_filter = filter or {}
        
        # Add namespace filter if provided
        if namespace:
            delete_filter["namespace"] = namespace
            
        if VECTOR_DB_TYPE == VectorDBType.PINECONE:
            index = pinecone.Index(PINECONE_INDEX_NAME)
            
            if ids:
                # Delete by IDs
                index.delete(ids=ids)
            elif delete_filter:
                # Delete by filter
                index.delete(filter=delete_filter)
            
        return True
    except Exception as e:
        logger.error(f"Error deleting documents from vector store: {str(e)}")
        return False

async def get_document_by_id(doc_id: str) -> Optional[Document]:
    """
    Retrieve a document by its ID.
    
    Args:
        doc_id: The document ID
        
    Returns:
        Optional[Document]: The document if found, None otherwise
    """
    if vector_store is None:
        await initialize_vector_db()
    
    try:
        if VECTOR_DB_TYPE == VectorDBType.PINECONE:
            index = pinecone.Index(PINECONE_INDEX_NAME)
            result = index.fetch([doc_id])
            
            if doc_id in result.vectors:
                vector = result.vectors[doc_id]
                return Document(
                    page_content=vector.metadata.get("text", ""),
                    metadata=vector.metadata
                )
        
        return None
    except Exception as e:
        logger.error(f"Error retrieving document by ID: {str(e)}")
        return None

async def health_check() -> bool:
    """
    Check if the vector database connection is healthy.
    
    Returns:
        bool: True if the connection is healthy, False otherwise
    """
    try:
        if vector_store is None:
            await initialize_vector_db()
            
        if VECTOR_DB_TYPE == VectorDBType.PINECONE:
            pinecone.list_indexes()  # Simple operation to check connection
            
        return True
    except Exception as e:
        logger.error(f"Vector database health check failed: {str(e)}")
        return False