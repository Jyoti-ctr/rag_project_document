"""
config.py
---------
Centralized application configuration using pydantic-settings.
All environment-dependent values are loaded from environment variables / .env file.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------
    APP_NAME: str = "RAG Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True

    # ---------------------------------------------------------------------
    # MongoDB
    # ---------------------------------------------------------------------
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB_NAME: str = "rag_backend"

    # ---------------------------------------------------------------------
    # JWT / Security
    # ---------------------------------------------------------------------
    JWT_SECRET_KEY: str = "CHANGE_ME_SUPER_SECRET_KEY"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ---------------------------------------------------------------------
    # AI / Embeddings
    # ---------------------------------------------------------------------
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"

    # ---------------------------------------------------------------------
    # Groq
    # ---------------------------------------------------------------------
    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "llama3-8b-8192"

    # ---------------------------------------------------------------------
    # Chunking
    # ---------------------------------------------------------------------
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_CHUNKS: int = 3

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance so the .env file / environment
    is only parsed once per process.
    """
    return Settings()


settings = get_settings()
