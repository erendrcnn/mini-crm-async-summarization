from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # SQLite for local; override with Postgres DATABASE_URL in prod
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    WORKER_POLL_INTERVAL_SECONDS: int = 2
    MAX_RETRIES: int = 3

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
