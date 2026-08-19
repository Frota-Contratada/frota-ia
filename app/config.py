from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    groq_api_key: str | None = None
    grok_api_key: str | None = None
    connection_dbgfc: str | None = None

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"

settings = Settings()