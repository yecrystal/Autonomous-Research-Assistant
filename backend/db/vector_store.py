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
import weaviate

logger = logging.getLogger(__name__)

# Vector database configuration
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "pinecone")  # Options: "pinecone", "weaviate"