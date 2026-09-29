from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "FitBuddy - AI Fitness Plan Generator"

    environment: str = "development"

    database_url: str = (
        f"sqlite:///{(BASE_DIR / 'fitbuddy.db').as_posix()}"
    )

    gemini_api_key: str = ""

    # These are configurable from .env
    workout_model: str = "gemini-3.1-pro-preview"
    fast_model: str = "gemini-3.8-flash"

    admin_token: str = "change-me"

    max_feedback_length: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()