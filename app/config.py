from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    gemini_api_key: str

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"

settings = Settings()