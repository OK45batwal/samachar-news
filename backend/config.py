import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Samachar"
    APP_VERSION: str = "2.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "samachar-fact-intelligence-super-secret-key-2026-xyz-abc")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./samachar.db")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATE_LIMIT_PER_MINUTE: int = 120

    CORS_ORIGINS: str = "*"
    API_DOMAIN: str = os.getenv("API_DOMAIN", "http://localhost:8000")
    SENTRY_DSN: str = ""
    PROMETHEUS_ENABLED: bool = False

    FEED_INGESTION_INTERVAL_MINUTES: int = 30
    MAX_ARTICLES_PER_FEED: int = 25

    # Email / SMTP Configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "no-reply@samachar.news")
    SMTP_FROM_NAME: str = "Samachar Truth Intelligence"

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
