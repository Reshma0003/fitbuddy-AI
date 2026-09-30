from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitBuddy – AI Fitness Plan Generator"

    gemini_api_key: str = ""

    gemini_workout_model: str = "gemini-3.8-flash"
    gemini_tip_model: str = "gemini-3.8-flash"

    database_url: str = "sqlite:///./data/fitbuddy.db"

    admin_token: str = "change-me"

    max_feedback_length: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()