import os

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
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    MEDIA_DIR: str = "./media"
    BASE_URL: str = "http://localhost:8000"

    class Config:
        env_file = ".env"

    @property
    def sqlalchemy_database_uri(self) -> str:
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
os.makedirs(settings.MEDIA_DIR, exist_ok=True)
