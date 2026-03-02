import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_SECRET_KEY: str = "change-me"
    
    # Database
    DATABASE_URL: str
    
    # OpenRouter
    OPENROUTER_API_KEY: str
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    
    # Models
    MODEL_EXTRACT: str = "anthropic/claude-3.5-sonnet"
    MODEL_VERIFY_GROK: str = "x-ai/grok-3"
    MODEL_VERIFY_GEMINI: str = "google/gemini-2.5-pro"
    MODEL_ANALYZE: str = "anthropic/claude-opus-4-6"

    # Storage
    KNOWLEDGE_VAULT_PATH: str = "/app/knowledge-vault"
    ATTACHMENTS_PATH: str = "/app/attachments"

    # CORS
    CORS_ORIGINS: str = ""

    model_config = SettingsConfigDict(
        case_sensitive=True, 
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
