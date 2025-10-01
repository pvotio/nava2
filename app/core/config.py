import os

from pydantic import computed_field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str = "DEBUG"
    PROJECT_NAME: str = "nava2"
    API_V1: str = "/api"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "appdb"
    POSTGRES_USER: str = "appuser"
    POSTGRES_PASSWORD: str = "apppass"
    MSSQL_DSN: str = ""
    GENERATOR_HOST: str = "generator:3000"
    REQUEST_MAX_RETRIES: int = 3
    REQUEST_BACKOFF_FACTOR: float = 0.2
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    MEDIA_DIR: str = "./media"
    BASE_URL: str = "http://localhost:8000"
    TEMPLATES_INDEX_URL: str = "https://raw.githubusercontent.com/<org>/<repo>/<branch>/map.json"
    GITHUB_TOKEN: str | None = None
    TEMPLATES_SYNC_INTERVAL_MINUTES: int = 5
    DOCS_URL: str | None = "/docs"
    REDOC_URL: str | None = "/redoc"
    OPENAPI_URL: str | None = "/openapi.json"

    class Config:
        env_file = ".env"

    @computed_field
    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
