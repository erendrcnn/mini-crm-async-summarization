from pydantic_settings import BaseSettings
from functools import lru_cache


def _normalize_db_url(url: str) -> str:
    if not url:
        return url
    # Normalize postgres URLs to psycopg v3 driver if unspecified or psycopg2
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    elif url.startswith("postgresql+psycopg2://"):
        url = "postgresql+psycopg://" + url[len("postgresql+psycopg2://") :]
    return url


class Settings(BaseSettings):
    ENV: str = "dev"
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    ALGORITHM: str = "HS256"

    # SQLite for local; override with Postgres DATABASE_URL in prod
    DATABASE_URL: str = "sqlite+aiosqlite:///./app.db"

    WORKER_POLL_INTERVAL_SECONDS: int = 2
    MAX_RETRIES: int = 3

    # Summarizer limits
    SUMMARY_MAX_CHARS: int = 300
    SUMMARY_MAX_SENTENCES: int = 3
    SUMMARY_MIN_SENT_CHARS: int = 20

    # Ollama host (used for optional LLM summarization)
    OLLAMA_HOST: str = "http://localhost:11434"

    # Summarization via LLM (optional)
    SUMMARIZE_PROVIDER: str = "extractive"  # "extractive" | "ollama"
    SUMMARIZE_LLM_MODEL: str = "llama3.1"

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }

    @property
    def db_url(self) -> str:
        return _normalize_db_url(self.DATABASE_URL)


@lru_cache

def get_settings() -> Settings:
    return Settings()


settings = get_settings()
