from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    groq_api_key: str | None = None
    ai_extract_model: str = "openai/gpt-oss-120b"
    ai_validator_model: str = "qwen/qwen3.8-27b"
    connection_dbgfc: str | None = None

    def require_groq_api_key(self) -> str:
        if not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required")
        return self.groq_api_key

    class Config:
        env_file = Path(__file__).resolve().parent.parent / ".env"

settings = Settings()
