from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./app.db"
    
    # Google Gemini
    google_api_key: Optional[str] = None
    
    # SerpAPI (optional for web search)
    serpapi_api_key: Optional[str] = None
    
    # ChromaDB
    chroma_persist_directory: str = "./chroma_db"
    
    # Security
    secret_key: str = "your_secret_key_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Override with environment variables if they exist
if os.getenv("DATABASE_URL"):
    settings.database_url = os.getenv("DATABASE_URL")
if os.getenv("GOOGLE_API_KEY"):
    settings.google_api_key = os.getenv("GOOGLE_API_KEY")
if os.getenv("SERPAPI_API_KEY"):
    settings.serpapi_api_key = os.getenv("SERPAPI_API_KEY")
if os.getenv("SECRET_KEY"):
    settings.secret_key = os.getenv("SECRET_KEY")


