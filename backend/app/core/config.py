from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str

    DATABASE_URL: str

    EMBEDDING_MODEL: str
    VECTOR_DIMENSION: int


    # LLM Configuration
    LLM_PROVIDER: str
    GEMINI_MODEL: str
    OLLAMA_MODEL: str

    GEMINI_API_KEY: Optional[str] = None


    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env"
    )


settings = Settings()