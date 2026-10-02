import re
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Top Match Backend"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = []
    PUBLIC_APP_URL: str = "http://localhost:3000"

    DATABASE_URL: PostgresDsn
    GEMINI_API_KEY: SecretStr

    JWT_SECRET: SecretStr
    ACCESS_TOKEN_MINUTES: int = 15
    REFRESH_TOKEN_DAYS: int = 7

    GEMINI_MODEL: str = "gemini-3.8-flash"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_ATTEMPTS: int = 3
    LLM_MAX_CONCURRENCY: int = 2
    STUCK_APPLICATION_MINUTES: int = 5
    PIPELINE_ENABLED: bool = True
    RESUME_TOKEN_MINUTES: int = 15
    RETENTION_DAYS: int = 30
    GEMINI_DATA_USE_ACKNOWLEDGED: bool = False

    STORAGE_DIR: Path = Path("var/resumes")
    MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024
    MAX_RESUME_PAGES: int = 5
    OCR_DPI: int = 150
    OCR_MAX_PAGE_PIXELS: int = 4_000_000

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def use_asyncpg_driver(cls, value: object) -> object:
        # asyncpg needs the explicit driver scheme and takes `ssl`, not libpq's `sslmode`.
        if isinstance(value, str):
            value = re.sub(r"^postgres(ql)?://", "postgresql+asyncpg://", value)
            value = re.sub(r"([?&])sslmode=", r"\1ssl=", value)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
