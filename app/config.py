"""Configuration module for the bot."""
from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
BACKUP_DIR = PROJECT_ROOT / "backups"


class Settings(BaseSettings):
    """Application settings."""
    
    bot_token: str
    database_url: str = ""
    tz: str = "Europe/Moscow"
    
    # Default notification times in hours before interview
    default_notification_times: List[float] = [24.0, 12.0, 6.0, 3.0, 1.5, 0.5]
    
    # Admin user IDs (comma-separated in .env)
    admin_ids: str = ""
    
    # Backup settings
    backup_enabled: bool = True
    backup_interval_hours: int = 24
    backup_path: str = ""
    
    # Webhook settings (optional)
    webhook_enabled: bool = False
    webhook_url: str = ""
    
    # Locale
    default_locale: str = "ru"
    
    # Follow-up settings
    default_followup_days: int = 3
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create data directories if they don't exist
        DATA_DIR.mkdir(exist_ok=True)
        BACKUP_DIR.mkdir(exist_ok=True)
        
        # Set default database URL if not provided
        if not self.database_url:
            db_path = DATA_DIR / "interviews.db"
            self.database_url = f"sqlite+aiosqlite:///{db_path}"
        
        # Set default backup path if not provided
        if not self.backup_path:
            self.backup_path = str(BACKUP_DIR)
    
    @property
    def admin_list(self) -> List[int]:
        """Get list of admin IDs."""
        if not self.admin_ids:
            return []
        return [int(id.strip()) for id in self.admin_ids.split(",") if id.strip()]


settings = Settings()