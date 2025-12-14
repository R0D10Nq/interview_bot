"""Configuration module for the bot."""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    bot_token: str
    database_url: str = "sqlite+aiosqlite:///./interviews.db"
    tz: str = "Asia/Tomsk"
    
    # Default notification times in hours before interview
    default_notification_times: List[float] = [24.0, 12.0, 6.0, 3.0, 1.5, 0.5]
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )


settings = Settings()