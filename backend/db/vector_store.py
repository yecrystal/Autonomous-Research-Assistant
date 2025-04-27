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
        