"""Application configuration."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # App
    app_name: str = "Stream Automation"
    debug: bool = False
    secret_key: str = "change-me-in-production"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/streamauto"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Google OAuth
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/auth/google/callback"

    # Return Zero API (RTZR)
    rtzr_client_id: str = ""
    rtzr_client_secret: str = ""
    rtzr_api_url: str = "https://openapi.vito.ai"

    # Anthropic Claude API
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-20250514"

    # Telegram
    telegram_bot_token: str = ""

    # Processing defaults
    silence_threshold_db: float = -40.0
    silence_min_duration: float = 0.5
    silence_padding: float = 0.1
    min_chapter_duration: int = 60
    max_chapters: int = 20

    # File watcher
    watcher_interval_seconds: int = 60

    # Temp storage
    temp_dir: str = "/tmp/streamauto"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
