import os
from dotenv import load_dotenv

load_dotenv

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")

# Database
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "research_assistant")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/research_assistant")

# Database URLs
POSTGRES_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Vector DB settings
PINECONE_INDEX_NAME = "research-assistant"
VECTOR_DIMENSION = 1536  # OpenAI embeddings dimension

# Model settings
DEFAULT_COMPLETION_MODEL = "gpt-4"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_ANTHROPIC_MODEL = "claude-3-opus-20240229"

# Research settings
DEFAULT_MAX_SOURCES = 5
DEFAULT_SEARCH_DEPTH = "medium"