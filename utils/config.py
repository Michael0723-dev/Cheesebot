import os
from dotenv import load_dotenv
from typing import Dict, Any

# Load environment variables from .env file
load_dotenv()

class Config:
    # OpenAI Configuration
    OPENAI_API_KEY = "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"
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "cheese-knowledge")

    # Scraping Configuration
    SCRAPING_URL = "https://shop.kimelo.com/department/cheese/3365"
    SCRAPING_DELAY = 2  # seconds between requests

    # Vector Database Configuration
    VECTOR_DIMENSION = 1536  # OpenAI embedding dimension
    VECTOR_METRIC = "cosine"

    # RAG Configuration
    TOP_K_RESULTS = int(os.getenv('TOP_K_RESULTS', '3'))
    CHUNK_SIZE = 1000  # size of text chunks for embedding
    CHUNK_OVERLAP = 200  # overlap between chunks

    # Streamlit Configuration
    STREAMLIT_THEME = {
        "primaryColor": "#FF4B4B",
        "backgroundColor": "#0E1117",
        "secondaryBackgroundColor": "#262730",
        "textColor": "#FAFAFA",
        "font": "sans serif"
    }

    # MySQL settings
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "cheese_db")

    @classmethod
    def validate(cls) -> Dict[str, Any]:
        """Validate configuration and return any missing required variables"""
        missing = {}

        if not cls.OPENAI_API_KEY:
            missing["OPENAI_API_KEY"] = "Required for OpenAI API access"

        if not cls.PINECONE_API_KEY:
            missing["PINECONE_API_KEY"] = "Required for Pinecone vector database"

        # MySQL validation
        if not cls.MYSQL_HOST:
            missing["MYSQL_HOST"] = "Required for MySQL connection"
        if not cls.MYSQL_USER:
            missing["MYSQL_USER"] = "Required for MySQL connection"
        if not cls.MYSQL_PASSWORD:
            missing["MYSQL_PASSWORD"] = "Required for MySQL connection"
            
        return missing
    
    @classmethod
    def get_pinecone_config(cls) -> Dict[str, Any]:
        """Get Pinecone configuration dictionary"""
        return {
            "api_key": cls.PINECONE_API_KEY,
            "environment": cls.PINECONE_ENVIRONMENT,
            "index_name": cls.PINECONE_INDEX_NAME,
            "dimension": cls.VECTOR_DIMENSION,
            "metric": cls.VECTOR_METRIC
        }
    
    @classmethod
    def get_rag_config(cls) -> Dict[str, Any]:
        """Get RAG configuration dictionary"""
        return {
            "top_k": cls.TOP_K_RESULTS,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP
        } 