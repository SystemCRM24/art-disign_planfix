# my_project/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "Bitrix24 and Planfix Integration"
    PROJECT_DESCRIPTION: str = "Service for Bitrix24 and Planfix integration"
    API_VERSION: str = "1.0.0"

    BITRIX_WEBHOOK_URL: str = os.getenv("BITRIX_WEBHOOK_URL", "")

    # Planfix Settings
    PLANFIX_API_URL: str = os.getenv("PLABFIX_API_URL", "") # Стандартный URL API Planfix
    PLANFIX_AUTH_TOKEN: str = os.getenv("PLANFIX_AUTH_TOKEN", "")

    model_config = SettingsConfigDict(env_file=str(BASE_DIR / ".env"))

settings = Settings()