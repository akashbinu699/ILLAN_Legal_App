"""Configuration management for the backend."""
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gmail API
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    
    # Database
    database_path: str = "./data/database.db"
    
    # ChromaDB
    chroma_db_path: str = "./data/chroma_db"
    
    # LLM
    local_llm_path: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    
    # Embedding Model
    embedding_model: str = "nomic-embed-text-v1.5"
    
    # Re-ranker (Cohere)
    reranker_api_key: str = ""
    cohere_api_key: str = ""  # Alias for reranker_api_key (for backward compatibility)
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

# Create settings instance
settings = Settings()

# Ensure data directory exists
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.chroma_db_path).parent.mkdir(parents=True, exist_ok=True)

