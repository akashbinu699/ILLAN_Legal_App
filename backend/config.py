"""Configuration management for the backend."""
from pathlib import Path
from pydantic_settings import BaseSettings
import os

# Get the project root directory (parent of backend directory)
BACKEND_DIR = Path(__file__).parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env"

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Gmail API
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    notification_email: str = ""  # Email address to receive form submissions
    
    # Database
    database_path: str = "./data/database.db"
    
    # ChromaDB
    chroma_db_path: str = "./data/chroma_db"
    
    # LLM
    local_llm_path: str = ""
    gemini_api_key: str = ""
    openai_api_key: str = ""
    groq_api_key: str = ""
    
    # Embedding Model
    embedding_model: str = "nomic-embed-text-v1.5"
    nomic_api_key: str = ""  # Nomic API key for embeddings (alternative to nomic login)
    
    # Re-ranker (Cohere)
    reranker_api_key: str = ""
    cohere_api_key: str = ""  # Alias for reranker_api_key (for backward compatibility)
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = [
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://192.168.1.127:3001",
        "http://192.168.1.127:3000"
    ]
    
    class Config:
        # Use absolute path to .env file
        env_file = str(ENV_FILE.absolute()) if ENV_FILE.exists() else str(PROJECT_ROOT / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env
        # Also check parent directories
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Logging for debugging configuration
def log_config_status():
    """Log configuration status for debugging."""
    print("=" * 60)
    print("CONFIGURATION STATUS")
    print("=" * 60)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Looking for .env at: {ENV_FILE}")
    print(f".env file exists: {ENV_FILE.exists()}")
    
    if ENV_FILE.exists():
        print(f".env file size: {ENV_FILE.stat().st_size} bytes")
        # Check if GROQ_API_KEY is in file (without showing the value)
        try:
            with open(ENV_FILE, 'r') as f:
                content = f.read()
                has_gemini = 'GEMINI_API_KEY' in content
                has_groq = 'GROQ_API_KEY' in content
                print(f"GEMINI_API_KEY found in .env: {has_gemini}")
                print(f"GROQ_API_KEY found in .env: {has_groq}")
                if has_gemini:
                    for line in content.split('\n'):
                        if line.startswith('GEMINI_API_KEY='):
                            key_length = len(line.split('=', 1)[1]) if '=' in line else 0
                            print(f"  - GEMINI_API_KEY length: {key_length} characters")
                            break
                if has_groq:
                    # Show first few chars to verify it's there
                    for line in content.split('\n'):
                        if line.startswith('GROQ_API_KEY='):
                            key_length = len(line.split('=', 1)[1]) if '=' in line else 0
                            print(f"  - GROQ_API_KEY length: {key_length} characters")
                            break
        except Exception as e:
            print(f"Error reading .env file: {e}")
    
    print(f"\nLoaded API Keys:")
    print(f"  - GEMINI_API_KEY: {'SET' if settings.gemini_api_key else 'NOT SET'} ({len(settings.gemini_api_key)} chars)")
    print(f"  - GROQ_API_KEY: {'SET' if settings.groq_api_key else 'NOT SET'} ({len(settings.groq_api_key)} chars)")
    print(f"  - OPENAI_API_KEY: {'SET' if settings.openai_api_key else 'NOT SET'} ({len(settings.openai_api_key)} chars)")
    print(f"  - RERANKER_API_KEY: {'SET' if settings.reranker_api_key else 'NOT SET'}")
    print(f"  - COHERE_API_KEY: {'SET' if settings.cohere_api_key else 'NOT SET'}")
    print(f"  - NOTIFICATION_EMAIL: {'SET' if settings.notification_email else 'NOT SET'} ({settings.notification_email if settings.notification_email else 'N/A'})")
    
    # Also check environment variables directly
    env_gemini = os.getenv('GEMINI_API_KEY', '')
    env_groq = os.getenv('GROQ_API_KEY', '')
    print(f"\nEnvironment Variables (direct):")
    print(f"  - GEMINI_API_KEY: {'SET' if env_gemini else 'NOT SET'} ({len(env_gemini)} chars)")
    print(f"  - GROQ_API_KEY: {'SET' if env_groq else 'NOT SET'} ({len(env_groq)} chars)")
    print("=" * 60)

# Log on import (when module is loaded)
log_config_status()

# Ensure data directory exists
Path(settings.database_path).parent.mkdir(parents=True, exist_ok=True)
Path(settings.chroma_db_path).parent.mkdir(parents=True, exist_ok=True)

