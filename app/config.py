"""
Application Configuration
Environment variables and settings for the BankBot application.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database Settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "bankbot"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "password"
    
    # Vector Database Settings
    VECTOR_DIMENSION: int = 1024
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Document Processing Settings
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: list = [".pdf", ".txt", ".doc", ".docx"]
    
    # OpenAI/AI Settings (optional)
    OPENAI_API_KEY: Optional[str] = None
    
    # Model path settings (optional for local LLMs)
    YI_MODEL_PATH: Optional[str] = None
    MISTRAL_MODEL_PATH: Optional[str] = None
    
    @property
    def database_url(self) -> str:
        """Construct database URL for asyncpg"""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def sync_database_url(self) -> str:
        """Construct database URL for psycopg2 (sync operations)"""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"

# Create settings instance
settings = Settings() 