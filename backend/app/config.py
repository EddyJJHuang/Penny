from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_RETRIES: int = 3
    GEMINI_BATCH_SIZE: int = 20
    CORS_ORIGINS: str = "http://localhost:5173"

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = "ignore"

settings = Settings()
