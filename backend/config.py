import os
import secrets
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_FILE = ".secret_key"

def _resolve_secret_key() -> str:
    env_key = os.environ.get("SAMACHAR_SECRET_KEY", "")
    if env_key:
        return env_key
    secret_path = Path(SECRET_FILE)
    if secret_path.exists():
        return secret_path.read_text().strip()
    key = secrets.token_urlsafe(32)
    secret_path.write_text(key)
    return key

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "sqlite+aiosqlite:///./samachar.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = _resolve_secret_key()
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: str = "http://localhost:8000,http://127.0.0.1:8000"
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = True
    NEWS_API_KEY: str = ""
    RATE_LIMIT_PER_MINUTE: int = 20

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

settings = Settings()
