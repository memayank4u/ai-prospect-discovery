import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PORT: int = 4000
    HOST: str = "0.0.0.0"
    ENVIRONMENT: str = "development"

    # LLM Settings
    LLM_PROVIDER: str = "gemini"  # "gemini", "openai", "heuristic"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Search Engine Settings
    SEARCH_ENGINE: str = "duckduckgo"  # "duckduckgo", "serpapi", "google_cse"
    SERPAPI_API_KEY: Optional[str] = None
    GOOGLE_CSE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None

    # Discovery Tuning
    MAX_RESULTS_PER_PLATFORM: int = 5
    ENABLE_CACHE: bool = True
    CACHE_TTL_SECONDS: int = 3600
    TIMEOUT_SECONDS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
