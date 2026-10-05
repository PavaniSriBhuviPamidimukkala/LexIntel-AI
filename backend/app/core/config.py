from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str

    DATABASE_URL: str

    EMBEDDING_MODEL: str
    VECTOR_DIMENSION: int

    class Config:
        env_file = ".env"


settings = Settings()
